
def have_binaries(packages):
    """Check if there are any binaries in the packages."""
    for pkg in packages:
        for filepath in pkg.files:
            if filepath.startswith(('/usr/bin', '/usr/sbin')):
                return True
    return False
