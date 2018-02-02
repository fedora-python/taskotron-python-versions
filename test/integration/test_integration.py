from collections import namedtuple
import contextlib
import glob
import shutil
import subprocess
import sys
from textwrap import dedent

import yaml

import pytest


Result = namedtuple('Result', ['outcome', 'artifact', 'item'])


class MockEnv:
    '''Use this to work with mock. Mutliple instances are not safe.'''

    def __init__(self):
        self.mock = ['mock', '-r', './mock.cfg']
        self._run(['--init'], check=True)

    def _run(self, what, **kwargs):
        return subprocess.run(self.mock + what, **kwargs)

    def copy_in(self, files):
        self._run(['--copyin'] + files + ['/'], check=True)

    def copy_out(self, directory, *, clean_target=False):
        if clean_target:
            with contextlib.suppress(FileNotFoundError):
                shutil.rmtree(directory)
        self._run(['--copyout', directory, directory], check=True)

    def shell(self, command):
        cp = self._run(['--shell', command])
        return cp.returncode

    def orphanskill(self):
        self._run(['--orphanskill'])


@pytest.fixture(scope="session")
def mock():
    '''Setup a mock we can run Ansible tasks in under root'''
    mockenv = MockEnv()
    files = ['taskotron_python_versions'] + glob.glob('*.py') + ['tests.yml']
    mockenv.copy_in(files)
    yield mockenv
    mockenv.orphanskill()


def parse_results(path):
    '''
    From the given result file, parse the results
    '''
    with open(path) as f:
        return yaml.load(f)['results']


def run_task(nevr, *, mock):
    '''
    Run the task on a Koji build in given mock.
    Returns a dict with Results (outcome, artifact, item)
    Actually returns a tuple with the above and captured log
    '''
    exit_code = mock.shell('ansible-playbook tests.yml '
                           '-e taskotron_item={}'.format(nevr))
    mock.copy_out('artifacts', clean_target=True)

    with open('artifacts/test.log') as f:
        log = f.read()

    # 0 for PASSED
    # 2 for FAILED
    if exit_code not in (0, 2):
        print(log, file=sys.stderr)
        raise RuntimeError('mock shell ended with {}'.format(exit_code))

    results = parse_results('artifacts/taskotron/results.yml')

    ret = {r['checkname']: Result(r.get('outcome'),
                                  r.get('artifact'),
                                  r.get('item')) for r in results}

    return ret, log


def fixtures_factory(nevr):
    '''Given the NEVR and later name, create a fixture with the results

    Note that this has to be called twice and assigned to correct names!

    See examples bellow.'''
    if not nevr.startswith('_'):
        @pytest.fixture(scope="session")
        def _results(mock):
            return run_task(nevr, mock=mock)

        return _results

    @pytest.fixture()
    def results(request):
        _results = request.getfixturevalue(nevr)
        print(_results[1], file=sys.stderr)
        return _results[0]

    return results


_tracer = fixtures_factory('tracer-0.6.9-1.fc23')
tracer = fixtures_factory('_tracer')

_copr = fixtures_factory('python-copr-1.77-1.fc26')
copr = fixtures_factory('_copr')

_eric = fixtures_factory('eric-6.1.6-2.fc25')
eric = fixtures_factory('_eric')

_six = fixtures_factory('python-six-1.10.0-3.fc25')
six = fixtures_factory('_six')

_admesh = fixtures_factory('python-admesh-0.98.5-3.fc25')
admesh = fixtures_factory('_admesh')

_epub = fixtures_factory('python-epub-0.5.2-8.fc26')
epub = fixtures_factory('_epub')

_twine = fixtures_factory('python-twine-1.8.1-3.fc26')
twine = fixtures_factory('_twine')

_yum = fixtures_factory('yum-3.4.3-512.fc26')
yum = fixtures_factory('_yum')

_vdirsyncer = fixtures_factory('vdirsyncer-0.16.0-1.fc27')
vdirsyncer = fixtures_factory('_vdirsyncer')

_docutils = fixtures_factory('python-docutils-0.13.1-4.fc26')
docutils = fixtures_factory('_docutils')

_nodejs = fixtures_factory('nodejs-semver-5.1.1-2.fc26')
nodejs = fixtures_factory('_nodejs')

_bucky = fixtures_factory('python-bucky-2.2.2-7.fc27')
bucky = fixtures_factory('_bucky')

_jsonrpc = fixtures_factory('jsonrpc-glib-3.27.4-1.fc28')
jsonrpc = fixtures_factory('_jsonrpc')


@pytest.mark.parametrize('results', ('eric', 'six', 'admesh', 'tracer',
                                     'copr', 'epub', 'twine', 'yum',
                                     'vdirsyncer', 'docutils', 'nodejs',
                                     'bucky', 'jsonrpc'))
def test_number_of_results(results, request):
    # getting a fixture by name
    # https://github.com/pytest-dev/pytest/issues/349#issuecomment-112203541
    results = request.getfixturevalue(results)

    # Each time a new check is added, this number needs to be increased
    assert len(results) == 8


@pytest.mark.parametrize('results', ('eric', 'six', 'admesh',
                                     'copr', 'epub', 'twine',
                                     'bucky'))
def test_two_three_passed(results, request):
    results = request.getfixturevalue(results)
    assert results['dist.python-versions.two_three'].outcome == 'PASSED'


def test_two_three_failed(tracer):
    assert tracer['dist.python-versions.two_three'].outcome == 'FAILED'


@pytest.mark.parametrize('results', ('tracer', 'copr', 'admesh'))
def test_one_failed_result_is_total_failed(results, request):
    results = request.getfixturevalue(results)
    assert results['dist.python-versions'].outcome == 'FAILED'


@pytest.mark.parametrize(('results', 'task'),
                         (('tracer', 'two_three'),
                          ('copr', 'naming_scheme'),
                          ('admesh', 'requires_naming_scheme')))
def test_artifact_is_the_same(results, task, request):
    results = request.getfixturevalue(results)
    assert (results['dist.python-versions'].artifact ==
            results['dist.python-versions.' + task].artifact)


def test_artifact_contains_two_three_and_looks_as_expected(tracer):
    result = tracer['dist.python-versions.two_three']
    with open(result.artifact) as f:
        artifact = f.read()

    assert dedent('''
        These RPMs require both Python 2 and Python 3:
        {}.noarch.rpm
         * Python 2 dependency: python(abi) = 2.7
         * Python 3 dependecny: python(abi) = 3.4
    ''').strip().format(result.item) in artifact.strip()


@pytest.mark.parametrize('results', ('eric', 'epub', 'twine', 'vdirsyncer'))
def test_naming_scheme_passed(results, request):
    results = request.getfixturevalue(results)
    assert results['dist.python-versions.naming_scheme'].outcome == 'PASSED'


@pytest.mark.parametrize('results', ('copr', 'six', 'admesh', 'bucky'))
def test_naming_scheme_failed(results, request):
    results = request.getfixturevalue(results)
    assert results['dist.python-versions.naming_scheme'].outcome == 'FAILED'


def test_artifact_contains_naming_scheme_and_looks_as_expected(copr):
    result = copr['dist.python-versions.naming_scheme']
    with open(result.artifact) as f:
        artifact = f.read()

    assert dedent("""
        These RPMs' names violate the new Python package naming guidelines:
        {}
    """).strip().format(result.item) in artifact.strip()


@pytest.mark.parametrize('results', ('eric', 'twine', 'six'))
def test_requires_naming_scheme_passed(results, request):
    results = request.getfixturevalue(results)
    task_result = results['dist.python-versions.requires_naming_scheme']
    assert task_result.outcome == 'PASSED'


@pytest.mark.parametrize('results', ('admesh', 'copr'))
def test_requires_naming_scheme_failed(results, request):
    results = request.getfixturevalue(results)
    task_result = results['dist.python-versions.requires_naming_scheme']
    assert task_result.outcome == 'FAILED'


def test_artifact_contains_requires_naming_scheme_and_looks_as_expected(
        tracer):
    result = tracer['dist.python-versions.requires_naming_scheme']
    with open(result.artifact) as f:
        artifact = f.read()

    print(artifact)

    assert dedent("""
        These RPMs use `python-` prefix without Python version in *Requires:

        tracer-0.6.9-1.fc23 BuildRequires:
         * python-psutil (python2-psutil is available)

        tracer-0.6.9-1.fc23 Requires:
         * python-psutil (python2-psutil is available)

        This is strongly discouraged and should be avoided. Please check
        the required packages, and use names with either `python2-` or
        `python3-` prefix.
    """).strip() in artifact.strip()


def test_requires_naming_scheme_contains_python(yum):
    result = yum['dist.python-versions.requires_naming_scheme']
    with open(result.artifact) as f:
        artifact = f.read()

    print(artifact)

    assert 'python (python2 is available)' in artifact.strip()


@pytest.mark.parametrize('results', ('eric', 'six', 'admesh', 'tracer',
                                     'copr', 'epub', 'twine', 'bucky'))
def test_executables_passed(results, request):
    results = request.getfixturevalue(results)
    task_result = results['dist.python-versions.executables']
    assert task_result.outcome == 'PASSED'


@pytest.mark.parametrize('results', ('docutils',))
def test_executables_failed(results, request):
    results = request.getfixturevalue(results)
    task_result = results['dist.python-versions.executables']
    assert task_result.outcome == 'FAILED'


def test_artifact_contains_executables_and_looks_as_expected(
        docutils):
    result = docutils['dist.python-versions.executables']
    with open(result.artifact) as f:
        artifact = f.read()

    print(artifact)

    assert dedent("""
        The following executables are available only in Python 2 subpackages:

        python2-docutils-0.13.1-4.fc26:
         * /usr/bin/rst2html
         * /usr/bin/rst2html5
         * /usr/bin/rst2latex
         * /usr/bin/rst2man
         * /usr/bin/rst2odt
         * /usr/bin/rst2odt_prepstyles
         * /usr/bin/rst2pseudoxml
         * /usr/bin/rst2s5
         * /usr/bin/rst2xetex
         * /usr/bin/rst2xml
         * /usr/bin/rstpep2html

        If the functionality of those executables is the same regardless of the
        used Python version, you should switch to Python 3.
        In case the Python version matter, also create an additional
        executables for Python 3.
    """).strip() in artifact.strip()


@pytest.mark.parametrize('results', ('eric', 'six', 'admesh', 'copr',
                                     'epub', 'twine', 'nodejs'))
def test_unvesioned_shebangs_passed(results, request):
    results = request.getfixturevalue(results)
    result = results['dist.python-versions.unversioned_shebangs']
    assert result.outcome == 'PASSED'


@pytest.mark.parametrize('results', ('yum', 'tracer', 'bucky'))
def test_unvesioned_shebangs_failed(results, request):
    results = request.getfixturevalue(results)
    result = results['dist.python-versions.unversioned_shebangs']
    assert result.outcome == 'FAILED'


def test_artifact_contains_unversioned_shebangs_and_looks_as_expected(
        tracer):
    result = tracer['dist.python-versions.unversioned_shebangs']
    with open(result.artifact) as f:
        artifact = f.read()

    print(artifact)

    assert dedent("""
        These RPMs contain problematic shebang in some of the scripts:
        tracer-0.6.9-1.fc23
         * Scripts containing `#!/usr/bin/python` shebang:
           /usr/bin/tracer
        This is discouraged and should be avoided. Please check the shebangs
        and use either `#!/usr/bin/python2` or `#!/usr/bin/python3`.
   """).strip() in artifact.strip()


@pytest.mark.parametrize('results', ('eric', 'six', 'admesh', 'tracer',
                                     'copr', 'epub', 'twine', 'docutils'))
def test_py3_support_passed(results, request):
    results = request.getfixturevalue(results)
    task_result = results['dist.python-versions.py3_support']
    assert task_result.outcome == 'PASSED'


@pytest.mark.parametrize('results', ('bucky',))
def test_py3_support_failed(results, request):
    results = request.getfixturevalue(results)
    task_result = results['dist.python-versions.py3_support']
    assert task_result.outcome == 'FAILED'


def test_artifact_contains_py3_support_and_looks_as_expected(
        bucky):
    """Test that py3_support check fails if the package is mispackaged.

    NOTE: The test will start to fail as soon as python-bucky
    gets ported to Python 3 and its Bugzilla gets closed.
    See https://bugzilla.redhat.com/show_bug.cgi?id=1367012
    """
    result = bucky['dist.python-versions.py3_support']
    with open(result.artifact) as f:
        artifact = f.read()

    print(artifact)

    assert dedent("""
        This software supports Python 3 upstream, but is not
        packaged for Python 3 in Fedora.

        Software MUST be packaged for Python 3 if upstream supports it.
        See the following Bugzilla:
        https://bugzilla.redhat.com/show_bug.cgi?id=1367012
    """).strip() in artifact.strip()


@pytest.mark.parametrize('results', ('eric', 'six', 'admesh', 'tracer',
                                     'copr', 'epub', 'twine', 'docutils'))
def test_python_usage_passed(results, request):
    results = request.getfixturevalue(results)
    task_result = results['dist.python-versions.python_usage']
    assert task_result.outcome == 'PASSED'


@pytest.mark.parametrize('results', ('jsonrpc',))
def test_python_usage_failed(results, request):
    results = request.getfixturevalue(results)
    task_result = results['dist.python-versions.python_usage']
    assert task_result.outcome == 'FAILED'


def test_artifact_contains_python_usage_and_looks_as_expected(jsonrpc):
    result = jsonrpc['dist.python-versions.python_usage']
    with open(result.artifact) as f:
        artifact = f.read()

    print(artifact)

    assert dedent("""
        You've used /usr/bin/python during build on the following arches:

          jsonrpc-glib-3.27.4-1.fc28: x86_64

        Use /usr/bin/python3 or /usr/bin/python2 explicitly.
        /usr/bin/python will be removed or switched to Python 3 in the future.
    """).strip() in artifact.strip()
