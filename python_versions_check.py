# -*- coding: utf-8 -*-

import logging
if __name__ == '__main__':
    # Set up logging ASAP to see potential problems during import.
    # Don't set it up when not running as the main script, someone else handles
    # that then.
    logging.basicConfig()

import os
import pathlib
import sys

from libtaskotron import check

# before we import from pyversions, let's add our dir to sys.path
sys.path.insert(0, os.path.dirname(__file__))

from taskotron_python_versions import (
    task_two_three,
    task_naming_scheme,
    task_requires_naming_scheme,
    task_executables,
    task_unversioned_shebangs,
    task_py3_support,
    task_python_usage,
    task_python_usage_obsoleted,
)
from taskotron_python_versions.common import log, Package, PackageException


def run(koji_build, workdir='.', artifactsdir='artifacts',
        testcase='dist.python-versions', arches=['x86_64', 'noarch', 'src']):
    '''The main method to run from Taskotron'''
    artifactsdir = pathlib.Path(artifactsdir)
    workdir = pathlib.Path(workdir).resolve()
    resultsdir = artifactsdir / 'taskotron'
    resultspath = resultsdir / 'results.yml'
    artifact = artifactsdir / 'output.log'

    artifactsdir.mkdir(parents=True, exist_ok=True)
    resultsdir.mkdir(parents=True, exist_ok=True)

    # find files to run on
    files = sorted(os.listdir(workdir))
    logs = []
    packages = []
    srpm_packages = []
    for file_ in files:
        path = workdir / file_
        if file_.endswith('.rpm'):
            try:
                package = Package(path)
            except PackageException as err:
                log.error('{}: {}'.format(file_, err))
            else:
                if package.is_srpm:
                    srpm_packages.append(package)
                else:
                    packages.append(package)
        elif file_.startswith('build.log'):  # it's build.log.{arch}
            logs.append(path)
        else:
            log.debug('Ignoring non-rpm, non-build.log file: {}'.format(path))

    if not packages:
        log.warn('No binary rpm files found')

    if not logs:
        log.warn('No build.log found, that should not happen')

    # put all the details form subtask in this list
    details = []
    details.append(task_two_three(packages, koji_build, artifact))
    details.append(task_naming_scheme(packages, koji_build, artifact))
    details.append(task_requires_naming_scheme(
        srpm_packages + packages, koji_build, artifact))
    details.append(task_executables(packages, koji_build, artifact))
    details.append(task_unversioned_shebangs(
        packages, logs, koji_build, artifact))
    details.append(task_py3_support(
        srpm_packages + packages, koji_build, artifact))
    details.append(task_python_usage(
        srpm_packages + packages, koji_build, artifact))
    details.append(task_python_usage_obsoleted(
        logs, koji_build, artifact))  # TODO: remove with Fedora 28 EOL.

    for detail in details:
        # update testcase for all subtasks (use their existing testcase as a
        # suffix)
        detail.checkname = '{}.{}'.format(testcase, detail.checkname)
        detail.keyvals['arch'] = arches

    # finally, the main detail with overall results
    outcome = 'PASSED'
    for detail in details:
        if detail.outcome == 'FAILED':
            outcome = 'FAILED'
            break
    overall_detail = check.CheckDetail(checkname=testcase,
                                       item=koji_build,
                                       report_type=check.ReportType.KOJI_BUILD,
                                       outcome=outcome,
                                       keyvals={'arch': arches})
    if outcome == 'FAILED':
        overall_detail.artifact = str(artifact)
    details.append(overall_detail)

    summary = 'python-versions {} for {} ({}).'.format(
        outcome, koji_build, ', '.join(arches))
    log.info(summary)

    # generate output reportable to ResultsDB
    output = check.export_YAML(details)
    resultspath.write_text(output)

    return 0 if overall_detail.outcome in ['PASSED', 'INFO'] else 1


if __name__ == '__main__':
    arches = sys.argv[5].split(',')
    rc = run(koji_build=sys.argv[1],
             workdir=sys.argv[2],
             artifactsdir=sys.argv[3],
             testcase=sys.argv[4],
             arches=arches)
    sys.exit(rc)
