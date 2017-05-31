import collections

import dnf

from .common import log, write_to_artifact
from .naming_scheme import is_unversioned

MESSAGE = """These RPMs use `python-` prefix without Python version in *Requires:
{}
This is strongly discouraged and should be avoided. Please check
the required packages, and use names with either `python2-` or
`python3-` prefix.
"""

# TODO: Should be a link to guidelines when considered.
INFO_URL = 'https://pagure.io/packaging-committee/issue/686'


def add_repo(base, reponame, repourl):
    try:
        # Fedora 26
        repo = dnf.repo.Repo(reponame, parent_conf=base.conf)
    except TypeError:
        # Fedora 25
        repo = dnf.repo.Repo(reponame, cachedir=base.conf.cachedir)

    metalink = ('https://mirrors.fedoraproject.org/'
                'metalink?repo={}&arch=$basearch'.format(repourl))
    repo.metalink = dnf.conf.parser.substitute(metalink,
                                               base.conf.substitutions)

    base.repos.add(repo)
    repo.skip_if_unavailable = False
    repo.enable()
    repo.load()
    return repo


def get_dnf_query(release):
    """Create dnf repoquery for the release."""
    log.debug('Creating repoquery for {}'.format(release))
    base = dnf.Base()
    base.conf.substitutions['releasever'] = release

    # Only add fedora and updates
    # Better to have a false PASSED than false FAILED,
    # so we do NOT add updates-testing
    try:
        add_repo(base, 'fedora', 'fedora-$releasever')
        add_repo(base, 'updates', 'updates-released-f$releasever')
    except dnf.exceptions.RepoError as err:
        if release == 'rawhide':
            log.error('{} (rawhide)'.format(err))
            return
        log.warning(
            'Failed to load repos for {}, assuming rawhide'.format(release))
        return get_dnf_query('rawhide')

    base.fill_sack(load_system_repo=False, load_available_repos=True)
    return base.sack.query()


def get_versioned_name(require, repoquery):
    """Given the require with not versioned Python prefix,
    find one with the versioned Python prefix
    using the provided repoquery.

    Return: (str) Available versioned name or None
    """
    if not repoquery:
        return
    log.debug('Checking requirement {}'.format(require))

    query = repoquery.filter(provides=require)
    packages = query.run()

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
        name = name.decode()

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
    repoquery = get_dnf_query(fedora_release)

    outcome = 'PASSED'
    misnamed_requires = collections.defaultdict(set)

    for package in packages:
        log.debug('Checking requires of {}'.format(package.filename))

        requires = check_requires_naming_scheme(package, repoquery)
        if requires:
            misnamed_requires[package.nvr].update(requires)
            outcome = 'FAILED'

    message_rpms = ''
    for package_name, requires in misnamed_requires.items():
        message_rpms += '{}\n * Requires: {}\n'.format(
            package_name, ', '.join(sorted(requires)))

    detail = check.CheckDetail(
        checkname='python-versions.requires_naming_scheme',
        item=koji_build,
        report_type=check.ReportType.KOJI_BUILD,
        outcome=outcome)

    if misnamed_requires:
        detail.artifact = artifact
        write_to_artifact(artifact, MESSAGE.format(message_rpms), INFO_URL)
        problems = 'Problematic RPMs:\n' + ', '.join(misnamed_requires.keys())
    else:
        problems = 'No problems found.'

    summary = 'python-versions.requires_naming_scheme {} for {}. {}'.format(
        outcome, koji_build, problems)
    log.info(summary)

    return detail
