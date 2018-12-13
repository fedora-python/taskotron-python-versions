import bugzilla

from .common import log, write_to_artifact, packages_by_version


INFO_URL = 'https://fedoraproject.org/wiki/Packaging:Python'

MESSAGE = """
This software supports Python 3 upstream, but is not
packaged for Python 3 in Fedora.

Software MUST be packaged for Python 3 if upstream supports it.
See the following Bugzilla:
{}
"""

BUGZILLA_URL = "bugzilla.redhat.com"
PY3_TRACKER_BUG = 1285816
# Bugzilla trackers, for which taskotron checks already exist.
IGNORE_TRACKER_BUGS = [
    1432186,  # Missing PY3-EXECUTABLES
    1340802,  # Depends on both Py2 and Py3
]
IGNORE_STATUSES = [
    'CLOSED',
    'VERIFIED',
    'RELEASE_PENDING',
    'ON_QA',
]


def ignored(bug):
    """Check if the Bugzilla should be ignored.

    Reasons to ignore a bug:
     - tracked by any of IGNORE_TRACKER_BUGS, so there is a
     separate check for it;
     - status is one of IGNORE_STATUSES, so the package is most
     probably ported in rawhide.

    Return: (bool) True if bug should be ignored, False otherwise
    """
    for tracker in bug.blocks:
        if tracker in IGNORE_TRACKER_BUGS:
            return True
    return bug.status in IGNORE_STATUSES


def filter_urls(bugs):
    """Given the list of bugs, return the list of URLs
    for those which should not be ignored.

    Return: (list of str) List of links
    """
    return [bug.weburl for bug in bugs if not ignored(bug)]


def get_py3_bugzillas_for(srpm_name):
    """Fetch all Bugzillas for the package given it's SRPM name,
    which are tracked by PY3_TRACKER_BUG.

    Return: (list) List of Bugzilla URLs
    """
    bzapi = bugzilla.Bugzilla(BUGZILLA_URL, cookiefile=None, tokenfile=None)
    query = bzapi.build_query(
        product="Fedora",
        component=srpm_name)
    query['blocks'] = PY3_TRACKER_BUG
    bugs = bzapi.query(query)
    return filter_urls(bugs)


def ported_to_py3(packages):
    """Check if the package is ported to Python 3,
    by comparing the number of it's binary RPMs for each
    Python version.

    Return: (bool) True if ported, False otherwise
    """
    pkg_by_version = packages_by_version(packages)
    return len(pkg_by_version[2]) <= len(pkg_by_version[3])


def task_py3_support(packages, koji_build, artifact):
    """Check that the package is packaged for Python 3,
    if upstream is Python 3 ready.

    Source of data: https://bugzilla.redhat.com/show_bug.cgi?id=1285816
    """
    # libtaskotron is not available on Python 3, so we do it inside
    # to make the above functions testable anyway
    from libtaskotron import check

    outcome = 'PASSED'
    message = ''

    srpm, packages = packages[0], packages[1:]
    if not ported_to_py3(packages):
        bugzilla_urls = get_py3_bugzillas_for(srpm.name)
        if bugzilla_urls:
            outcome = 'FAILED'
            log.error(
                'This software supports Python 3 upstream,'
                ' but is not packaged for Python 3 in Fedora')
            message = ', '.join(bugzilla_urls)
        else:
            log.info(
                'This software does not support Python 3'
                ' upstream, skipping Py3 support check')

    detail = check.CheckDetail(
        checkname='py3_support',
        item=koji_build,
        report_type=check.ReportType.KOJI_BUILD,
        outcome=outcome)

    if message:
        write_to_artifact(artifact, MESSAGE.format(message), INFO_URL)
        detail.artifact = str(artifact)

    log.info('subcheck py3_support {} for {}'.format(
        outcome, koji_build))

    return detail
