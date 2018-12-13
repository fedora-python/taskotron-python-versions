from collections import namedtuple
import contextlib
import glob
import pathlib
import pprint
import shutil
import subprocess
import sys
from textwrap import dedent

import yaml

import pytest


Result = namedtuple('Result', ['outcome', 'artifact', 'item'])


class MockEnv:
    '''Use this to work with mock. Mutliple concurrent instances are safe.'''
    mock = ['mock', '-r', './mock.cfg']

    def __init__(self, worker_id):
        self.worker_id = worker_id
        self._run(['--init'], check=True)

    @property
    def root(self):
        return 'taskotron-python-versions-{}'.format(self.worker_id)

    @property
    def rootdir(self):
        return pathlib.Path('./mockroots').resolve() / self.root

    def _run(self, what, **kwargs):
        command = list(self.mock)  # needs a copy not to change in place
        command.append('--enable-network')
        command.append('--config-opts=root={}'.format(self.root))
        command.append('--rootdir={}'.format(self.rootdir))
        command.extend(what)
        return subprocess.run(command, **kwargs)

    def copy_in(self, files):
        self._run(['--copyin'] + files + ['/'], check=True)

    def copy_out(self, directory, target, *, clean_target=False):
        if clean_target:
            with contextlib.suppress(FileNotFoundError):
                shutil.rmtree(target)
        self._run(['--copyout', directory, target], check=True)

    def shell(self, command):
        cp = self._run(['--shell', command])
        return cp.returncode

    def orphanskill(self):
        self._run(['--orphanskill'])


class FakeMockEnv(MockEnv):
    '''Use this to fake the mock interactions'''
    mock = ['echo', 'mock']

    def copy_out(self, directory, target, *, clean_target=False):
        '''Fake it, never clean target'''
        return super().copy_out(directory, target, clean_target=False)


@pytest.fixture(scope="session")
def mock(worker_id, request):
    '''Setup a mock we can run Ansible tasks in under root'''
    if request.config.getoption('--fake'):
        mockenv = FakeMockEnv(worker_id)
    else:
        mockenv = MockEnv(worker_id)
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
    '''
    exit_code = mock.shell('ansible-playbook tests.yml '
                           '-e taskotron_item={}'.format(nevr))
    artifacts = 'artifacts-{}'.format(nevr)
    mock.copy_out('artifacts', artifacts, clean_target=True)
    mock.shell('rm artifacts -rf')  # purge the logs

    # 0 for PASSED
    # 2 for FAILED
    if exit_code not in (0, 2):
        raise RuntimeError('mock shell ended with {}'.format(exit_code))

    results = parse_results(artifacts + '/taskotron/results.yml')

    # we need to preserve the artifacts for each nevr separately
    # but the saved path is just ./artifacts/...
    def fix_artifact_path(path):
        if path is None:
            return None
        newpath = path.replace('artifacts/', '{}/'.format(artifacts))
        return pathlib.Path(newpath)

    return {r['checkname']: Result(r.get('outcome'),
                                   fix_artifact_path(r.get('artifact')),
                                   r.get('item')) for r in results}


def fixtures_factory(nevr):
    '''Given the NEVR and later name, create a fixture with the results

    Note that this has to be called twice and assigned to correct names!

    See examples bellow.'''
    if not nevr.startswith('_'):
        @pytest.fixture(scope="session")
        def _results(mock):
            return run_task(nevr, mock=mock), nevr

        return _results

    @pytest.fixture()
    def results(request):
        _results = request.getfixturevalue(nevr)
        pprint.pprint(_results[0], stream=sys.stderr)
        path = './artifacts-{}/'.format(_results[1])
        print('\nLogs and results are in {}'.format(path), file=sys.stderr)
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

_pycallgraph = fixtures_factory('python-pycallgraph-0.5.1-13.fc28')
pycallgraph = fixtures_factory('_pycallgraph')

_ttystatus = fixtures_factory('python-ttystatus-0.34-7.fc29')
ttystatus = fixtures_factory('_ttystatus')

# TODO: remove with Fedora 28 EOL.
_jsonrpc = fixtures_factory('jsonrpc-glib-3.27.4-2.fc28')
jsonrpc = fixtures_factory('_jsonrpc')

_teeworlds = fixtures_factory('teeworlds-0.6.4-8.fc29')
teeworlds = fixtures_factory('_teeworlds')


def parametrize(*fixtrues):
    return pytest.mark.parametrize('results', fixtrues)


@parametrize('eric', 'six', 'admesh', 'tracer', 'copr', 'epub', 'twine', 'yum',
             'vdirsyncer', 'docutils', 'nodejs', 'pycallgraph', 'teeworlds',
             'ttystatus')
def test_number_of_results(results, request):
    # getting a fixture by name
    # https://github.com/pytest-dev/pytest/issues/349#issuecomment-112203541
    results = request.getfixturevalue(results)

    # Each time a new check is added, this number needs to be increased
    assert len(results) == 9


@parametrize('eric', 'six', 'admesh', 'copr', 'epub', 'twine', 'pycallgraph')
def test_two_three_passed(results, request):
    results = request.getfixturevalue(results)
    assert results['dist.python-versions.two_three'].outcome == 'PASSED'


@parametrize('tracer')
def test_two_three_failed(results, request):
    results = request.getfixturevalue(results)
    assert results['dist.python-versions.two_three'].outcome == 'FAILED'


@parametrize('tracer', 'copr', 'admesh')
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


@parametrize('tracer')
def test_artifact_contains_two_three_and_looks_as_expected(results, request):
    results = request.getfixturevalue(results)
    result = results['dist.python-versions.two_three']
    artifact = result.artifact.read_text()

    assert dedent('''
        These RPMs require both Python 2 and Python 3:
        {}.noarch.rpm
         * Python 2 dependency: python(abi) = 2.7
         * Python 3 dependecny: python(abi) = 3.4
    ''').strip().format(result.item) in artifact.strip()


@parametrize('eric', 'epub', 'twine', 'vdirsyncer', 'pycallgraph')
def test_naming_scheme_passed(results, request):
    results = request.getfixturevalue(results)
    assert results['dist.python-versions.naming_scheme'].outcome == 'PASSED'


@parametrize('copr', 'six', 'admesh')
def test_naming_scheme_failed(results, request):
    results = request.getfixturevalue(results)
    assert results['dist.python-versions.naming_scheme'].outcome == 'FAILED'


@parametrize('copr')
def test_artifact_contains_naming_scheme_and_looks_as_expected(results,
                                                               request):
    results = request.getfixturevalue(results)
    result = results['dist.python-versions.naming_scheme']
    artifact = result.artifact.read_text()

    assert dedent("""
        These RPMs' names violate the new Python package naming guidelines:
        {}
    """).strip().format(result.item) in artifact.strip()


@parametrize('eric', 'twine', 'six')
def test_requires_naming_scheme_passed(results, request):
    results = request.getfixturevalue(results)
    task_result = results['dist.python-versions.requires_naming_scheme']
    assert task_result.outcome == 'PASSED'


@parametrize('admesh', 'copr')
def test_requires_naming_scheme_failed(results, request):
    results = request.getfixturevalue(results)
    task_result = results['dist.python-versions.requires_naming_scheme']
    assert task_result.outcome == 'FAILED'


@parametrize('tracer')
def test_artifact_contains_requires_naming_scheme_and_looks_as_expected(
        results, request):
    results = request.getfixturevalue(results)
    result = results['dist.python-versions.requires_naming_scheme']
    artifact = result.artifact.read_text()

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


@parametrize('yum')
def test_requires_naming_scheme_contains_python(results, request):
    results = request.getfixturevalue(results)
    result = results['dist.python-versions.requires_naming_scheme']
    artifact = result.artifact.read_text()

    print(artifact)

    assert 'python (python2 is available)' in artifact.strip()


@parametrize('eric', 'six', 'admesh', 'tracer',
             'copr', 'epub', 'twine', 'pycallgraph')
def test_executables_passed(results, request):
    results = request.getfixturevalue(results)
    task_result = results['dist.python-versions.executables']
    assert task_result.outcome == 'PASSED'


@parametrize('docutils')
def test_executables_failed(results, request):
    results = request.getfixturevalue(results)
    task_result = results['dist.python-versions.executables']
    assert task_result.outcome == 'FAILED'


@parametrize('docutils')
def test_artifact_contains_executables_and_looks_as_expected(
        results, request):
    results = request.getfixturevalue(results)
    result = results['dist.python-versions.executables']
    artifact = result.artifact.read_text()

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


@parametrize('eric', 'six', 'admesh', 'copr', 'epub', 'twine', 'nodejs')
def test_unvesioned_shebangs_passed(results, request):
    results = request.getfixturevalue(results)
    result = results['dist.python-versions.unversioned_shebangs']
    assert result.outcome == 'PASSED'


@parametrize('yum', 'tracer', 'pycallgraph')
def test_unvesioned_shebangs_failed(results, request):
    results = request.getfixturevalue(results)
    result = results['dist.python-versions.unversioned_shebangs']
    assert result.outcome == 'FAILED'


@parametrize('tracer')
def test_artifact_contains_unversioned_shebangs_and_looks_as_expected(
        results, request):
    results = request.getfixturevalue(results)
    result = results['dist.python-versions.unversioned_shebangs']
    artifact = result.artifact.read_text()

    print(artifact)

    assert dedent("""
        These RPMs contain problematic shebang in some of the scripts:
        tracer-0.6.9-1.fc23
         * Scripts containing `#!/usr/bin/python` shebang:
           /usr/bin/tracer

        This is discouraged and should be avoided. Please check the shebangs
        and use either `#!/usr/bin/python2` or `#!/usr/bin/python3`.
   """).strip() in artifact.strip()


@parametrize('pycallgraph')
def test_unvesioned_shebangs_mangled_failed(results, request):
    results = request.getfixturevalue(results)
    result = results['dist.python-versions.unversioned_shebangs']
    assert result.outcome == 'FAILED'


@parametrize('pycallgraph')
def test_artifact_contains_mangled_unversioned_shebangs_and_looks_as_expected(
        results, request):
    results = request.getfixturevalue(results)
    result = results['dist.python-versions.unversioned_shebangs']
    artifact = result.artifact.read_text()

    print(artifact)

    assert dedent("""
        The package uses either `#!/usr/bin/python` or
        `#!/usr/bin/env python` shebangs. They are forbidden by the guidelines
        and have been automatically mangled during build on the following
        arches:

            noarch

        Please check the shebangs and use either `#!/usr/bin/python2` or
        `#!/usr/bin/python3` explicitly.

        Look for the following warning in the build.log to find out which
        files are affected and need to be fixed:

            WARNING: mangling shebang in <file name> from <wrong shebang>
            to <correct shebang>. This will become an ERROR, fix it manually!
    """).strip() in artifact.strip()


@parametrize('eric', 'six', 'admesh', 'tracer',
             'copr', 'epub', 'twine', 'docutils')
def test_py3_support_passed(results, request):
    results = request.getfixturevalue(results)
    task_result = results['dist.python-versions.py3_support']
    assert task_result.outcome == 'PASSED'


@parametrize('ttystatus')
def test_py3_support_failed(results, request):
    results = request.getfixturevalue(results)
    task_result = results['dist.python-versions.py3_support']
    assert task_result.outcome == 'FAILED'


@parametrize('ttystatus')
def test_artifact_contains_py3_support_and_looks_as_expected(
        results, request):
    """Test that py3_support check fails if the package is mispackaged.

    NOTE: The test will start to fail as soon as python-ttystatus
    gets ported to Python 3 and its Bugzilla gets closed.
    See https://bugzilla.redhat.com/show_bug.cgi?id=1458531
    """
    results = request.getfixturevalue(results)
    result = results['dist.python-versions.py3_support']
    artifact = result.artifact.read_text()

    print(artifact)

    assert dedent("""
        This software supports Python 3 upstream, but is not
        packaged for Python 3 in Fedora.

        Software MUST be packaged for Python 3 if upstream supports it.
        See the following Bugzilla:
        https://bugzilla.redhat.com/show_bug.cgi?id=1458531
    """).strip() in artifact.strip()


# TODO: remove with Fedora 28 EOL.
@parametrize('eric', 'six', 'admesh', 'tracer',
             'copr', 'epub', 'twine', 'docutils')
def test_python_usage_obsoleted_passed(results, request):
    results = request.getfixturevalue(results)
    task_result = results['dist.python-versions.python_usage_obsoleted']
    assert task_result.outcome == 'PASSED'


# TODO: remove with Fedora 28 EOL.
@parametrize('jsonrpc')
def test_python_usage_obsoleted_failed(results, request):
    results = request.getfixturevalue(results)
    task_result = results['dist.python-versions.python_usage_obsoleted']
    assert task_result.outcome == 'FAILED'


# TODO: remove with Fedora 28 EOL.
@parametrize('jsonrpc')
def test_artifact_of_python_usage_obsoleted_looks_as_expected(results,
                                                              request):
    results = request.getfixturevalue(results)
    result = results['dist.python-versions.python_usage_obsoleted']
    artifact = result.artifact.read_text()

    print(artifact)

    assert dedent("""
        You've used /usr/bin/python during build on the following arches:

          jsonrpc-glib-3.27.4-2.fc28: x86_64

        Use /usr/bin/python3 or /usr/bin/python2 explicitly.
        /usr/bin/python will be removed or switched to Python 3 in the future.

        Grep the build.log for the following to find out where:

            DEPRECATION WARNING: python2 invoked with /usr/bin/python
    """).strip() in artifact.strip()


@parametrize('eric', 'six', 'admesh',
             'copr', 'epub', 'twine', 'docutils')
def test_python_usage_passed(results, request):
    results = request.getfixturevalue(results)
    task_result = results['dist.python-versions.python_usage']
    assert task_result.outcome == 'PASSED'


@parametrize('tracer', 'yum', 'teeworlds')
def test_python_usage_failed(results, request):
    results = request.getfixturevalue(results)
    task_result = results['dist.python-versions.python_usage']
    assert task_result.outcome == 'FAILED'


@parametrize('teeworlds')
def test_artifact_contains_python_usage_and_looks_as_expected(results,
                                                              request):
    results = request.getfixturevalue(results)
    result = results['dist.python-versions.python_usage']
    artifact = result.artifact.read_text()

    print(artifact)

    assert dedent("""
        The following packages (Build)Require `/usr/bin/python`
        (or `python-unversioned-command`):

          * teeworlds-0.6.4-8.fc29.src.rpm

        Use /usr/bin/python3 or /usr/bin/python2 explicitly.
        /usr/bin/python will be removed or switched to Python 3 in the future.
    """).strip() in artifact.strip()
