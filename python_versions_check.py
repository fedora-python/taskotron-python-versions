import rpm


NEVRS_STARTS = {
    2: (b'python(abi) = 2.',),
    3: (b'python(abi) = 3.',)
}

NAME_STARTS = {
    2: (
        b'python-',
        b'python2',
        b'/usr/bin/python2',
        b'libpython2',
        b'pygtk2',
        b'pygobject2',
        b'pycairo',
        b'py-',
    ),
    3: (
        b'python3',
        b'/usr/bin/python3',
        b'libpython3',
        b'system-python'
    )
}

NAME_EXACTS = {
    2: (
        b'/usr/bin/python',
        b'python',
    )
} 


def python_versions_check(path):
    '''
    For the binary RPM in path, report back what Python
    versions it depends on
    '''
    ts = rpm.TransactionSet()
    with open(path, 'rb') as fdno:
        hdr = ts.hdrFromFdno(fdno)
    
    py_versions = set()

    for nevr in hdr[rpm.RPMTAG_REQUIRENEVRS]:
        for py_version, starts in NEVRS_STARTS.items():
            for start in starts:
                if nevr.startswith(start):
                    py_versions.add(py_version)
                    break

    for name in hdr[rpm.RPMTAG_REQUIRENAME]:
        for py_version, starts in NAME_STARTS.items():
            if py_version not in py_versions:
                for start in starts:
                    if name.startswith(start):
                        py_versions.add(py_version)
                        break
        for py_version, exacts in NAME_EXACTS.items():
            if py_version not in py_versions:
                if name in exacts:
                    py_versions.add(py_version)

    return py_versions


if __name__ == '__main__':
    import sys
    print(python_versions_check(sys.argv[1]))
