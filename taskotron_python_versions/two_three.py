from .common import log, write_to_artifact


NEVRS_STARTS = {
    2: ('python(abi) = 2.',),
    3: ('python(abi) = 3.',)
}

NAME_STARTS = {
    2: (
        'python-',
        'python2',
        '/usr/bin/python2',
        'libpython2',
        'pygtk2',
        'pygobject2',
        'pycairo',
        'py-',
    ),
    3: (
        'python3',
        '/usr/bin/python3',
        'libpython3',
        'system-python'
    )
}

NAME_EXACTS = {
    2: (
        '/usr/bin/python',
        'python',
    )
}

NAME_NOTS = (
    'python-rpm-macros',
    'python-srpm-macros',
    'python-sphinx-locale',
    'python-multilib-conf',
    'python-ldb-devel-common',
    'python-qt5-rpm-macros',
    'python-btchip-common',
    'python-matplotlib-data',
    'python-matplotlib-data-fonts',
    'python-cartopy-common',
    'python-django-bash-completion',
    'python-jupyter-filesystem',
    'python-pip-wheel',
    'python-setuptools-wheel',
    'python-wheel-wheel',
    'python-formencode-langpacks',
    'python-typeshed',
    'texlive-python',
    'python-jupyter-filesystem',
)


INFO_URL = ('https://python-rpm-porting.readthedocs.io/en/'
            'latest/applications.html'
            '#are-shebangs-dragging-you-down-to-python-2')

MESSAGE = 'These RPMs require both Python 2 and Python 3:\n{}'

# Whitelist package names here with reasons
# Note that those are binary package names, not srpm names
WHITELIST = (
    'eric',  # https://bugzilla.redhat.com/show_bug.cgi?id=1342492
    'pungi',  # https://bugzilla.redhat.com/show_bug.cgi?id=1342497
    'python2-devel',  # deliberately depends on python3-rpm-generators
    'postgresql-upgrade',  # rhbz#1571215
)


def check_two_three(package):
    '''
    Given the package object, report back what Python
    versions it depends on and why we think so
    Returns package name and a dictionary.
    The dictionary contains the 2 and/or 3 keys with the package we consider
    drags the appropriate Python version.
    '''
    py_versions = {}

    for nevr in package.require_nevrs:
        for py_version, starts in NEVRS_STARTS.items():
            if nevr.startswith(starts):
                log.debug('Found dependency {}'.format(nevr))
                log.debug('Requires Python {}'.format(py_version))
                py_versions[py_version] = nevr

    for name in package.require_names:
        for py_version, starts in NAME_STARTS.items():
            if py_version not in py_versions:
                if name.startswith(starts) and name not in NAME_NOTS:
                    log.debug('Found dependency {}'.format(name))
                    log.debug('Requires Python {}'.format(py_version))
                    py_versions[py_version] = name

        for py_version, exacts in NAME_EXACTS.items():
            if py_version not in py_versions:
                if name in exacts:
                    log.debug('Found dependency {}'.format(name))
                    log.debug('Requires Python {}'.format(py_version))
                    py_versions[py_version] = name

    package.py_versions = set(py_versions)
    return package.name, py_versions


def task_two_three(packages, koji_build, artifact):
    '''Check whether given rpms depends on Python 2 and 3 at the same time'''

    # libtaskotron is not available on Python 3, so we do it inside
    # to make the above function testable anyway
    from libtaskotron import check

    outcome = 'PASSED'
    bads = {}

    for package in packages:
        log.debug('Checking {}'.format(package.filename))
        name, py_versions = check_two_three(package)

        if name in WHITELIST:
            log.warn('{} is excluded from this check'.format(name))
        elif len(py_versions) == 0:
            log.info('{} does not require Python, that\'s OK'
                     .format(package.filename))
        elif len(py_versions) == 1:
            py_version = next(iter(py_versions))
            log.info('{} requires Python {} only, that\'s OK'
                     .format(package.filename, py_version))
        else:
            log.error('{} requires both Python 2 and 3, that\'s usually bad. '
                      'Python 2 dragged by {}. '
                      'Python 3 dragged by {}.'
                      .format(package.filename, py_versions[2],
                              py_versions[3]))
            outcome = 'FAILED'
            bads[package.filename] = py_versions

    detail = check.CheckDetail(checkname='two_three',
                               item=koji_build,
                               report_type=check.ReportType.KOJI_BUILD,
                               outcome=outcome)

    if bads:
        rpms = ''
        for name, py_versions in bads.items():
            rpms += ('{}\n'
                     ' * Python 2 dependency: {}\n'
                     ' * Python 3 dependecny: {}\n'.format(name,
                                                           py_versions[2],
                                                           py_versions[3]))
        write_to_artifact(artifact, MESSAGE.format(rpms), INFO_URL)
        detail.artifact = str(artifact)
        names = ', '.join(str(k) for k in bads.keys())
        problems = 'Problematic RPMs:\n' + names
    else:
        problems = 'No problems found.'

    summary = 'subcheck two_three {} for {}. {}'.format(
              outcome, koji_build, problems)
    log.info(summary)

    return detail
