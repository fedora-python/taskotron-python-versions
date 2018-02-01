`Taskotron <https://fedoraproject.org/wiki/Taskotron>`__ task regarding Python versions
=======================================================================================

This represents the automatic checks happening in the Fedora
infrastructure after any package is built.

Currently the following checks are available:

-  Whether a package does not require Python 2 and Python 3 at the same
   time;

-  Whether the package name follows the Python package naming scheme;

-  Whether the package uses versioned Python prefix in requirements' names;

-  Whether only Python 2 version of the package contains the executables;

-  Whether the package uses versioned shebangs in its executables;

-  Whether the package supports Python 3 upstream but not in the package.

-  Whether ``/usr/bin/python`` was invoked during the build.


Running
-------

To run this task locally, execute the following command as root (don't do this
on a production machine!)::

  $ ansible-playbook tests.yml -e taskotron_item=<nevr>

where ``nevr`` is a Koji build ``name-(epoch:)version-release`` identifier.

For example::

  $ ansible-playbook tests.yml -e taskotron_item=python-gear-0.11.0-1.fc27

You can see the results in ``./artifacts/`` directory.

You can run the above in mock::

  $ mock -r ./mock.cfg --init
  $ mock -r ./mock.cfg --copyin taskotron_python_versions *.py tests.yml /
  $ mock -r ./mock.cfg --shell 'ansible-playbook tests.yml -e taskotron_item=python-gear-0.11.0-1.fc27'
  $ mock -r ./mock.cfg --copyout artifacts artifacts


Tests
-----

There are also automatic tests available. You can run them using
`tox <https://tox.readthedocs.io/>`__.
You'll need the above mentioned dependencies and ``python3-rpm``
and ``python3-dnf`` installed as well.

.. code:: console

    $ tox

Automatic tests also happen on `Tarvis
CI <https://travis-ci.org/fedora-python/taskotron-python-versions/>`__.
Since Travis CI runs on Ubuntu
and Ubuntu lacks the RPM Python bindings and Taskotron,
`Docker <https://docs.travis-ci.com/user/docker/>`__ is used
to run the tests on Fedora. You can run the tests in Docker as well,
just use the commands from the ``.travis.yml`` file.

License
-------

This code has been dedicated to the Public Domain, it is licensed with
`CC0 1.0 Universal Public Domain
Dedication <https://creativecommons.org/publicdomain/zero/1.0/>`__,
full text of the license is available in the LICENSE file in this
repository.

Please note that the RPM packages in this repository used for testing
have their own license terms and are not dedicated to the Public Domain.

The sources of those packages can be found in
`Koji <https://koji.fedoraproject.org/koji/>`__ by searching the
package name and selecting the appropriate version.
