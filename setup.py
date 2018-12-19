#!/usr/bin/env python3

import pathlib
from setuptools import setup, find_packages


description = """Taskotron checks regarding Python versions"""
long_description = pathlib.Path('README.rst').read_text()

setup(
    name='taskotron-python-versions',
    version='0.1.dev5',
    description=description,
    long_description=long_description,
    keywords='taskotron fedora python rpm',
    author='Miro Hrončok, Iryna Shcherbina, Michal Cyprian',
    author_email=('mhroncok@redhat.com, ishcherb@redhat.com, '
                  'mcyprian@redhat.com'),
    url='https://github.com/fedora-python/taskotron-python-versions',
    license='Public Domain',
    packages=find_packages(),
    install_requires=['libarchive-c', 'python-bugzilla'],
    setup_requires=['setuptools', 'pytest-runner'],
    tests_require=['pytest', 'pyyaml'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Testing',
    ]
)
