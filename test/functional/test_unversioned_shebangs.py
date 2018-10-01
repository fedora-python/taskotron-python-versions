import pytest

from taskotron_python_versions.unversioned_shebangs import (
    matches,
    get_problematic_files,
    shebang_to_require,
    get_scripts_summary,
)
from .common import gpkg, gpkg_path


@pytest.mark.parametrize(('line', 'query', 'expected'), (
    (b'#!/usr/bin/python', b'#!/usr/bin/python', True),
    (b'#!/usr/bin/python ', b'#!/usr/bin/python', True),
    (b'#!/usr/bin/python -I', b'#!/usr/bin/python', True),
    (b'#!/usr/bin/python #comment', b'#!/usr/bin/python', True),
    (b'#!/usr/bin/python3', b'#!/usr/bin/python', False),
    (b'#!/usr/bin/python2', b'#!/usr/bin/python', False),
    (b'#!/usr/bin/env python', b'#!/usr/bin/env python', True),
    (b'#!/usr/bin/env python -I', b'#!/usr/bin/env python', True),
    (b'#!/usr/bin/env python3', b'#!/usr/bin/env python', False),
    (b'#!/usr/bin/env python2', b'#!/usr/bin/env python', False),
    (b'#!/usr/bin/env perl', b'#!/usr/bin/env python', False),
))
def test_matches(line, query, expected):
    assert matches(line, query) == expected


@pytest.mark.parametrize(('archive', 'query', 'expected'), (
    ('tracer*',
     '#!/usr/bin/python', {'/usr/bin/tracer'}),
    ('python3-django*', '#!/usr/bin/env python',
     {'/usr/lib/python3.6/site-packages/django/bin/django-admin.py',
      ('/usr/lib/python3.6/site-packages/'
       'django/conf/project_template/manage.py-tpl')}),
    ('python3-django*', '#!/usr/bin/python', set()),
    ('pyserial*', '#!/usr/bin/python', set()),
))
def test_get_problematic_files(archive, query, expected):
    assert get_problematic_files(gpkg_path(archive), query) == expected


@pytest.mark.parametrize(('shebang', 'expected'), (
    ("#!/foo", "/foo"),
    ("#!/usr/bin/python", "/usr/bin/python"),
    ("#!/usr/bin/env python", "/usr/bin/env"),
))
def test_shebang_to_require(shebang, expected):
    assert shebang_to_require(shebang) == expected


@pytest.mark.parametrize(('glob', 'expected'), (
    ('tracer*',
     {'#!/usr/bin/python': {'/usr/bin/tracer'}}),
    ('python3-django*',
     {'#!/usr/bin/env python':
      {'/usr/lib/python3.6/site-packages/django/bin/django-admin.py',
       ('/usr/lib/python3.6/site-packages/'
        'django/conf/project_template/manage.py-tpl')}}),
    ('pyserial*', {}),
    ('nodejs-semver*', {}),
))
def test_get_scripts_summary(glob, expected):
    assert get_scripts_summary(gpkg(glob)) == expected
