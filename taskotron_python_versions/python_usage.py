from .common import log, write_to_artifact


MESSAGE = """The following packages (Build)Require `/usr/bin/python`
(or `python-unversioned-command`):

  * {}

Use /usr/bin/python3 or /usr/bin/python2 explicitly.
/usr/bin/python will be removed or switched to Python 3 in the future.
"""

INFO_URL = ('https://fedoraproject.org/wiki/Changes/'
            'Move_usr_bin_python_into_separate_package')

PYTHON_COMMAND = (
    '/usr/bin/python',
    'python-unversioned-command',
)


def task_python_usage(packages, koji_build, artifact):
    """Check if the packages depend on /usr/bin/python.
    """
    # libtaskotron is not available on Python 3, so we do it inside
    # to make the above functions testable anyway
    from libtaskotron import check

    outcome = 'PASSED'

    problem_rpms = set()

    for package in packages:
        log.debug('Checking {}'.format(package.filename))

        for name in package.require_names:
            if name in PYTHON_COMMAND:
                log.error(
                    '{} requires {}'.format(package.filename, name))
                problem_rpms.add(package.filename)
                outcome = 'FAILED'

    detail = check.CheckDetail(
        checkname='python_usage',
        item=koji_build,
        report_type=check.ReportType.KOJI_BUILD,
        outcome=outcome)

    if problem_rpms:
        write_to_artifact(
            artifact, MESSAGE.format('\n  * '.join(problem_rpms)),
            INFO_URL)
        detail.artifact = str(artifact)
        problems = 'Problematic RPMs:\n' + ', '.join(problem_rpms)
    else:
        problems = 'No problems found.'

    summary = 'subcheck python_usage {} for {}. {}'.format(
        outcome, koji_build, problems)
    log.info(summary)

    return detail
