#!/usr/bin/env python3

from setuptools import setup, find_packages


description = """Taskotron checks regarding Python versions"""

with open('README.rst') as readme:
    long_description = readme.read()

setup(
    name='taskotron-python-versions',
    version='0.1.dev1',
    description=description,
    long_description=long_description,
    keywords='taskotron fedora python rpm',
    author='Miro Hrončok, Iryna Shcherbina',
    author_email='mhroncok@redhat.com, ishcherb@redhat.com',
    url='https://github.com/fedora-python/task-python-versions',
    license='Public Domain',
    packages=find_packages(),
    setup_requires=['setuptools', 'pytest-runner'],
    tests_require=['pytest', 'pyyaml'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Testing',
    ]
)
