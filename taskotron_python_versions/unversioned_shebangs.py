import libarchive

from .common import log, write_to_artifact, file_contains

MESSAGE = """These RPMs contain problematic shebang in some of the scripts:
{}
This is discouraged and should be avoided. Please check the shebangs
and use either `#!/usr/bin/python2` or `#!/usr/bin/python3`.
"""

WARNING = 'WARNING: mangling shebang in'

MANGLED_MESSAGE = """The package uses either `#!/usr/bin/python` or
`#!/usr/bin/env python` shebangs. They are forbidden by the guidelines
and have been automatically mangled during build on the following
arches:

    {{}}

Please check the shebangs and use either `#!/usr/bin/python2` or
`#!/usr/bin/python3` explicitly.

Look for the following warning in the build.log to find out which
files are affected and need to be fixed:

    {} <file name> from <wrong shebang>
    to <correct shebang>. This will become an ERROR, fix it manually!
""".format(WARNING)

INFO_URL = \
    'https://fedoraproject.org/wiki/Packaging:Python#Multiple_Python_Runtimes'

FORBIDDEN_SHEBANGS = ['#!/usr/bin/python', '#!/usr/bin/env python']


def matches(line, query):
    """Both arguments must be of a type bytes"""
    return line == query or line.startswith(query + b' ')


def get_problematic_files(archive, query):
    """Search for the files inside archive with the first line
    matching given query. Some of the files can contain data, which
    are not in the plain text format. Bytes are read from the file and
    the shebang query is encoded as well. We only test for ASCII shebangs.
    """
    problematic = set()
    with libarchive.file_reader(str(archive)) as a:
        for entry in a:
            try:
                first_line = next(entry.get_blocks(), '').splitlines()[0]
            except IndexError:
                continue  # file is empty
            if matches(first_line, query.encode('ascii')):
                problematic.add(entry.pathname.lstrip('.'))

    return problematic


def shebang_to_require(shebang):
    """Convert shebang to the format of requirement."""
    return shebang.split()[0][2:]


def get_scripts_summary(package):
    """Collect problematic scripts data for given RPM package.
    Content of archive is processed only if package requires
    unversioned python binary or env.
    """
    scripts_summary = {}

    for shebang in FORBIDDEN_SHEBANGS:
        if shebang_to_require(shebang) in package.require_names:
            log.debug('Package {} requires {}'.format(
                package.filename, shebang_to_require(
                    shebang)))
            problematic = get_problematic_files(package.path, shebang)
            if problematic:
                log.debug('{} shebang was found in scripts: {}'.format(
                    shebang, ', '.join(problematic)))
                scripts_summary[shebang] = problematic
    return scripts_summary


def check_packages(packages):
    """Check if the packages have executables with shebangs
    forbidden by the guidelines.

    Return: (str) problem packages along with file names
    """
    problem_rpms = {}
    for package in packages:
        log.debug('Checking shebangs of {}'.format(package.filename))
        problem_rpms[package.nvr] = get_scripts_summary(package)

    shebang_message = ''
    for package, pkg_summary in problem_rpms.items():
        for shebang, scripts in pkg_summary.items():
            shebang_message += \
                '{}\n * Scripts containing `{}` shebang:\n   {}\n'.format(
                    package, shebang, '\n   '.join(sorted(scripts)))
    return shebang_message


def check_logs(logs):
    """Check the build log for the warning message
    that the shebangs were automatically mangled.

    Return: (str) architectures where warning was found
    """
    problem_arches = set()
    for buildlog in logs:
        if file_contains(buildlog, WARNING):
            log.debug('{} contains our warning'.format(buildlog))
            arch = buildlog.suffix.lstrip('.')
            problem_arches.add(arch)
    return ', '.join(sorted(problem_arches))


def task_unversioned_shebangs(packages, logs, koji_build, artifact):
    """Check if some of the binaries contain '/usr/bin/python'
    shebang or '/usr/bin/env python' shebang or whether those
    shebangs were mangled during the build.
    """
    # libtaskotron is not available on Python 3, so we do it inside
    # to make the above functions testable anyway
    from libtaskotron import check

    outcome = 'PASSED'
    message = ''
    problems = ''

    problems = check_packages(packages)
    if problems:
        outcome = 'FAILED'
        message = MESSAGE.format(problems)

    mangled_on_arches = check_logs(logs)
    if mangled_on_arches:
        outcome = 'FAILED'
        message = MANGLED_MESSAGE.format(mangled_on_arches)
        problems = 'Shebangs mangled on: {}'.format(mangled_on_arches)

    detail = check.CheckDetail(
        checkname='unversioned_shebangs',
        item=koji_build,
        report_type=check.ReportType.KOJI_BUILD,
        outcome=outcome)

    if outcome == 'FAILED':
        write_to_artifact(artifact, message, INFO_URL)
        detail.artifact = str(artifact)
    else:
        problems = 'No problems found.'

    log.info('subcheck unversioned_shebangs {} for {}. {}'.format(
        outcome, koji_build, problems))

    return detail
