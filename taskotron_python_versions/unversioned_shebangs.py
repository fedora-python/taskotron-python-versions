import libarchive

from .common import log, write_to_artifact

MESSAGE = """These RPMs contain problematic shebang in some of the scripts:
{}
This is discouraged and should be avoided. Please check the shebangs
and use either `#!/usr/bin/python2` or `#!/usr/bin/python3`.
"""

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
    the shebang query has to be of the same type.
    """
    problematic = set()
    with libarchive.file_reader(archive) as a:
        for entry in a:
            try:
                first_line = next(entry.get_blocks(), '').splitlines()[0]
            except IndexError:
                continue  # file is empty
            if matches(first_line, query.encode()):
                problematic.add(entry.pathname.lstrip('.'))

    return problematic


def shebang_to_require(shebang, use_bytes=True):
    """Convert shebang to the format of requirement.
    If the use_bytes argument is set to False, executable path
    is returned as a string instead of the default bytes type."""
    executable_path = shebang.split()[0][2:]
    if use_bytes:
        return executable_path.encode()
    else:
        return executable_path


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
                    shebang, use_bytes=False)))
            problematic = get_problematic_files(package.path, shebang)
            if problematic:
                log.debug('{} shebang was found in scripts: {}'.format(
                    shebang, ', '.join(problematic)))
                scripts_summary[shebang] = problematic
    return scripts_summary


def task_unversioned_shebangs(packages, koji_build, artifact):
    """Check if some of the binaries contains '/usr/bin/python'
    shebang or '/usr/bin/env python' shebang.
    """
    # libtaskotron is not available on Python 3, so we do it inside
    # to make the above functions testable anyway
    from libtaskotron import check

    outcome = 'PASSED'

    problem_rpms = {}
    shebang_message = ''

    for package in packages:
        log.debug('Checking shebangs of {}'.format(package.filename))
        problem_rpms[package.nvr] = get_scripts_summary(package)

    for package, pkg_summary in problem_rpms.items():
        for shebang, scripts in pkg_summary.items():
            outcome = 'FAILED'
            shebang_message += \
                '{}\n * Scripts containing `{}` shebang:\n   {}'.format(
                    package, shebang, '\n   '.join(sorted(scripts)))

    detail = check.CheckDetail(
        checkname='python-versions.unversioned_shebangs',
        item=koji_build,
        report_type=check.ReportType.KOJI_BUILD,
        outcome=outcome)

    if outcome == 'FAILED':
        detail.artifact = artifact
        write_to_artifact(artifact, MESSAGE.format(shebang_message), INFO_URL)
    else:
        shebang_message = 'No problems found.'

    log.info('python-versions.unversioned_shebangs {} for {}. {}'.format(
        outcome, koji_build, shebang_message))

    return detail
