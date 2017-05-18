
def has_pythonX_package(pkg_name, name_by_version, version):
    """Check whether pythonX-foo or foo-pythonX exists."""
    return (
        'python{}-{}'.format(version, pkg_name) in name_by_version[version] or
        '{}-python{}'.format(pkg_name, version) in name_by_version[version])


def is_unversioned(name):
    """Check whether unversioned python is used in name (e.g. python-foo)."""
    return (
        name.startswith('python-') or
        '-python-' in name or
        name.endswith('-python'))


def check_naming_policy(pkg, name_by_version):
    """Check if Python 2 subpackages are correctly named."""
    # Missing python2- prefix (e.g. foo and python3-foo).
    missing_prefix = (
        'python' not in pkg.name and
        has_pythonX_package(pkg.name, name_by_version, 3) and
        not has_pythonX_package(pkg.name, name_by_version, 2)
    )
    if is_unversioned(pkg.name) or missing_prefix:
        return True
    return False
