import collections

from .common import log, write_to_artifact
from .naming_scheme import is_unversioned

MESSAGE = """These RPMs use `python-` prefix without Python version in Requires:
{}
This is strongly discouraged and should be avoided. Please check
the required packages, and use names with either `python2-` or
`python3-` prefix if available.
"""

# Should be a link to guidelines when
# https://pagure.io/packaging-committee/issue/686 accepted.
INFO_URL = ''


def task_requires_naming_scheme(packages, koji_build, artifact):
    """Check if the given packages use names with `python-` prefix
    without a version in Requires.
    """
    # libtaskotron is not available on Python 3, so we do it inside
    # to make the above functions testable anyway
    from libtaskotron import check

    outcome = 'PASSED'
    misnamed_requires = collections.defaultdict(set)

    for package in packages:
        log.debug('Checking requires of {}'.format(package.filename))
        for name in package.require_names:
            name = name.decode()
            if is_unversioned(name):
                log.error(
                    '{} package uses `python-` prefix without version in '
                    'the requirement name {}'.format(package.filename, name))
                misnamed_requires[package.nvr].add(name)
                outcome = 'FAILED'

    message_rpms = ''
    for pakcage_name, requires in misnamed_requires.items():
        message_rpms += '{}\n * Requires: {}\n'.format(
            pakcage_name, ', '.join(sorted(requires)))

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
