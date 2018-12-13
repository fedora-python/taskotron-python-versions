import collections
import os

from .common import log, write_to_artifact


INFO_URL = (
    'https://python-rpm-porting.readthedocs.io/en/latest/naming-scheme.html')

MESSAGE = ('These RPMs\' names violate the new Python '
           'package naming guidelines:\n{}')


def has_pythonX_package(pkg_name, name_by_version, version):
    """Given the package name, check if python<version>-<pkg_name>
    or <pkg_name>-python<version> exists in name_by_version.

    Return: (bool) True if such package name exists, False otherwise
    """
    return (
        'python{}-{}'.format(version, pkg_name) in name_by_version[version] or
        '{}-python{}'.format(pkg_name, version) in name_by_version[version])


def is_unversioned(name):
    """Check whether unversioned python prefix is used
    in the name (e.g. python-foo).

    Return: (bool) True if used, False otherwise
    """
    if (os.path.isabs(name) or  # is an executable
            os.path.splitext(name)[1] or  # has as extension
            name.startswith(('python2-', 'python3-'))):  # is versioned
        return False

    return (
        name.startswith('python-') or
        '-python-' in name or
        name.endswith('-python') or
        name == 'python')


def check_naming_policy(pkg, name_by_version):
    """Check if the package is correctly named.

    Return: (bool) True if package name is not correct, False otherwise
    """
    # Missing python2- prefix (e.g. foo and python3-foo).
    missing_prefix = (
        'python' not in pkg.name and
        has_pythonX_package(pkg.name, name_by_version, 3) and
        not has_pythonX_package(pkg.name, name_by_version, 2)
    )
    if is_unversioned(pkg.name) or missing_prefix:
        return True
    return False


def task_naming_scheme(packages, koji_build, artifact):
    """Check if the given packages are named according
    to Python package naming guidelines.
    """
    # libtaskotron is not available on Python 3, so we do it inside
    # to make the above functions testable anyway
    from libtaskotron import check

    outcome = 'PASSED'
    incorrect_names = set()

    name_by_version = collections.defaultdict(set)
    for package in packages:
        for version in package.py_versions:
            name_by_version[version].add(package.name)

    for package in packages:
        log.debug('Checking {}'.format(package.filename))
        if 2 not in package.py_versions:
            log.info('{} does not require Python 2, '
                     'skipping name check'.format(package.filename))
            continue

        misnamed = check_naming_policy(package, name_by_version)
        if misnamed:
            log.error(
                '{} violates the new Python package'
                ' naming guidelines'.format(package.filename))
            outcome = 'FAILED'
            incorrect_names.add(package.nvr)
        else:
            log.info('{} is using a correct naming scheme'.format(
                package.filename))

    detail = check.CheckDetail(
        checkname='naming_scheme',
        item=koji_build,
        report_type=check.ReportType.KOJI_BUILD,
        outcome=outcome)

    if incorrect_names:
        names = ', '.join(incorrect_names)
        write_to_artifact(artifact, MESSAGE.format(names), INFO_URL)
        detail.artifact = str(artifact)
        problems = 'Problematic RPMs:\n' + names
    else:
        problems = 'No problems found.'

    summary = 'subcheck naming_scheme {} for {}. {}'.format(
        outcome, koji_build, problems)
    log.info(summary)

    return detail
