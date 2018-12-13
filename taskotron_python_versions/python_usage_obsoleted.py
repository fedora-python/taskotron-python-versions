"""Remove after Fedora 28 EOL.

Obsoleted by https://fedoraproject.org/wiki/Changes/
Move_usr_bin_python_into_separate_package.
"""
from .common import log, write_to_artifact, file_contains


WARNING = 'DEPRECATION WARNING: python2 invoked with /usr/bin/python'

MESSAGE = """You've used /usr/bin/python during build on the following arches:

  {{}}

Use /usr/bin/python3 or /usr/bin/python2 explicitly.
/usr/bin/python will be removed or switched to Python 3 in the future.

Grep the build.log for the following to find out where:

    {}
""".format(WARNING)

INFO_URL = ('https://fedoraproject.org/wiki/Changes/'
            'Avoid_usr_bin_python_in_RPM_Build')


def task_python_usage_obsoleted(logs, koji_build, artifact):
    """Parses the build.logs for /usr/bin/python invocation warning
    """
    # libtaskotron is not available on Python 3, so we do it inside
    # to make the above functions testable anyway
    from libtaskotron import check

    outcome = 'PASSED'

    problem_arches = set()

    for buildlog in logs:  # not "log" because we use that name for logging
        log.debug('Will parse {}'.format(buildlog))

        if file_contains(buildlog, WARNING):
            log.debug('{} contains our warning'.format(buildlog))
            arch = buildlog.suffix.lstrip('.')
            problem_arches.add(arch)
            outcome = 'FAILED'

    detail = check.CheckDetail(
        checkname='python_usage_obsoleted',
        item=koji_build,
        report_type=check.ReportType.KOJI_BUILD,
        outcome=outcome)

    if problem_arches:
        info = '{}: {}'.format(koji_build, ', '.join(sorted(problem_arches)))
        write_to_artifact(artifact, MESSAGE.format(info), INFO_URL)
        detail.artifact = str(artifact)
        problems = 'Problematic architectures: ' + info
    else:
        problems = 'No problems found.'

    summary = 'subcheck python_usage {} for {}. {}'.format(
        outcome, koji_build, problems)
    log.info(summary)

    return detail
