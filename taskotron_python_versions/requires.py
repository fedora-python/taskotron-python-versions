import dnf

from .common import log, write_to_artifact
from .naming_scheme import is_unversioned

MESSAGE = """These RPMs use `python-` prefix without Python version in *Requires:
{}
This is strongly discouraged and should be avoided. Please check
the required packages, and use names with either `python2-` or
`python3-` prefix.
"""


INFO_URL = 'https://fedoraproject.org/wiki/Packaging:Python#Dependencies'


class DNFQuery(object):

    """DNF Qeuery API.

    Initializes the query only when needed
    and saves it for reuse.
    """

    def __init__(self, release):
        self.release = release
        self._query = None

    @property
    def query(self):
        if not self._query:
            self._query = self.get_dnf_query()
        return self._query

    def get_packages_by(self, **kwargs):
        """Return the result of the DNF query execution,
        filtered by kwargs.
        """
        if self.query is not None:
            return self.query.filter(**kwargs).run()
        else:
            log.debug('No query, we continue, but it is bad...')
            return []

    @staticmethod
    def add_repo(base, reponame, repourl):
        metalink = ('https://mirrors.fedoraproject.org/'
                    'metalink?repo={}&arch=$basearch'.format(repourl))
        repo = base.repos.add_new_repo(reponame,
                                       base.conf,
                                       metalink=metalink,
                                       skip_if_unavailable=False)
        repo.enable()
        repo.load()
        return repo

    def get_dnf_query(self):
        """Create dnf repoquery for the release."""
        log.debug('Creating repoquery for {}'.format(self.release))
        base = dnf.Base()
        base.conf.substitutions['releasever'] = self.release

        # Only add fedora and updates
        # Better to have a false PASSED than false FAILED,
        # so we do NOT add updates-testing
        try:
            self.add_repo(base, 'fedora', 'fedora-$releasever')
            self.add_repo(base, 'updates', 'updates-released-f$releasever')
        except dnf.exceptions.RepoError as err:
            if self.release == 'rawhide':
                log.error('{} (rawhide)'.format(err))
                # TODO Do not silently ignore the error
                return
            log.warning('Failed to load repos for {}, '
                        'assuming rawhide'.format(self.release))
            self.release = 'rawhide'
            return self.get_dnf_query()

        base.fill_sack(load_system_repo=False, load_available_repos=True)
        return base.sack.query()


def get_versioned_name(require, repoquery):
    """Given the require with not versioned Python prefix,
    find one with the versioned Python prefix
    using the provided repoquery.

    Return: (str) Available versioned name or None
    """
    log.debug('Checking requirement {}'.format(require))

    packages = repoquery.get_packages_by(provides=require)
    for pkg in packages:
        if not is_unversioned(pkg.name):
            log.debug(
                'Found a name with a versioned '
                'Python prefix: {}'.format(pkg.name))
            return pkg.name


def check_requires_naming_scheme(package, repoquery):
    """Given the package, check the naming scheme of its
    requirements and return a list of those misnamed.

    Return: (set) Misnamed requirements
    """
    misnamed_requires = set()

    for name in package.require_names:
        if is_unversioned(name):
            versioned = get_versioned_name(name, repoquery)

            if versioned:
                log.error(
                    '{} package requires {}, while {} is '
                    'available'.format(package.filename, name, versioned))
                misnamed_requires.add('{} ({} is available)'.format(
                    name, versioned))
            else:
                log.debug('A versioned name for {} not found'.format(name))

    return misnamed_requires


def task_requires_naming_scheme(packages, koji_build, artifact):
    """Check if the given packages use names with `python-` prefix
    without a version in Requires.
    """
    # libtaskotron is not available on Python 3, so we do it inside
    # to make the above functions testable anyway
    from libtaskotron import check

    fedora_release = koji_build.split('fc')[-1]
    repoquery = DNFQuery(fedora_release)

    outcome = 'PASSED'

    problem_rpms = set()
    message_rpms = ''

    for package in packages:
        log.debug('Checking requires of {}'.format(package.filename))

        requires = check_requires_naming_scheme(package, repoquery)
        if requires:
            outcome = 'FAILED'
            problem_rpms.add(package.nvr)

            message = '\n{} {}Requires:\n * {}\n'.format(
                package.nvr,
                'Build' if package.is_srpm else '',
                '\n * '.join(sorted(requires)))
            if message not in message_rpms:
                message_rpms += message

    detail = check.CheckDetail(
        checkname='requires_naming_scheme',
        item=koji_build,
        report_type=check.ReportType.KOJI_BUILD,
        outcome=outcome)

    if problem_rpms:
        write_to_artifact(artifact, MESSAGE.format(message_rpms), INFO_URL)
        detail.artifact = str(artifact)
        problems = 'Problematic RPMs:\n' + ', '.join(problem_rpms)
    else:
        problems = 'No problems found.'

    summary = 'subcheck requires_naming_scheme {} for {}. {}'.format(
        outcome, koji_build, problems)
    log.info(summary)

    return detail
