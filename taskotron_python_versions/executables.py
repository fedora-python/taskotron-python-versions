import collections

from .common import log, write_to_artifact, packages_by_version


INFO_URL = ('https://fedoraproject.org/wiki/Packaging:Python#'
            'Executables_in_.2Fusr.2Fbin')

MESSAGE = """
The following executables are available only in Python 2 subpackages:
{}

If the functionality of those executables is the same regardless of the
used Python version, you should switch to Python 3.
In case the Python version matter, also create an additional
executables for Python 3.
"""

WHITELIST = (
    'dreampie-',  # http://fedora.portingdb.xyz/pkg/dreampie/
)


def is_binary(filepath):
    """Check if the filepath is a binary (executable).

    Return: (bool) True if it is a binary, False otherwise
    """
    return filepath.startswith(('/usr/bin', '/usr/sbin'))


def have_binaries(packages):
    """Check if there are any binaries (executables) in the packages.
    Note: This function is also being used in portingdb.

    Return: (bool) True if packages have any binaries, False otherwise
    """
    for pkg in packages:
        for filepath in pkg.files:
            if is_binary(filepath):
                return True
    return False


def get_binaries(packages):
    """Return a list of binaries for each package in packages.

    Return: (dict) Package NVR: set of binaries
    """
    result = collections.defaultdict(set)
    for pkg in packages:
        for filepath in pkg.files:
            if is_binary(filepath):
                result[pkg.nvr].add(filepath)
    return result


def task_executables(packages, koji_build, artifact):
    """Check that if there are any executables in Python 2 packages,
    there should be executables in Python 3 packages as well.
    """
    # libtaskotron is not available on Python 3, so we do it inside
    # to make the above functions testable anyway
    from libtaskotron import check

    outcome = 'PASSED'
    message = ''

    pkg_by_version = packages_by_version(packages)
    py2_packages = pkg_by_version[2]
    py3_packages = pkg_by_version[3]

    if koji_build.startswith(WHITELIST):
        log.warn('This package is excluded from executables check')

    elif not py2_packages or not py3_packages:
        log.info('The package is not built for both Python 2 and Python 3. '
                 'Skipping executables check')

    elif len(py2_packages) > len(py3_packages):
        log.info('The package is not fully ported to Python 3. '
                 'Skipping executables check')

    elif have_binaries(py2_packages) and not have_binaries(py3_packages):
        outcome = 'FAILED'
        for package, bins in get_binaries(py2_packages).items():
            log.error('{} contains executables which are missing in '
                      'the Python 3 version of this package'.format(package))
            message += '\n{}:\n * {}'.format(
                package, '\n * '.join(sorted(bins)))

    detail = check.CheckDetail(
        checkname='executables',
        item=koji_build,
        report_type=check.ReportType.KOJI_BUILD,
        outcome=outcome)

    if message:
        write_to_artifact(artifact, MESSAGE.format(message), INFO_URL)
        detail.artifact = str(artifact)

    log.info('subcheck executables {} for {}'.format(
        outcome, koji_build))

    return detail
