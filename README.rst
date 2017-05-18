`Taskotron <https://fedoraproject.org/wiki/Taskotron>`__ task regarding Python versions
=======================================================================================

| This represents the automatic checks happening in the Fedora
  infrastructure
| after any package is built.

Currently the following checks are available:

-  Whether a package does not require Python 2 and Python 3 at the same
   time.

Running
-------

| You can run the checks locally with
  `Taskotron <https://fedoraproject.org/wiki/Taskotron>`__. First,
  install it (you can
| follow the
  `Quickstart <https://qa.fedoraproject.org/docs/libtaskotron/latest/quickstart.html>`__).
| You'll also need the ``rpm`` Python 2 module (``python2-rpm``).
| Note that Taskotron unfortunately runs on Python 2, but the code in
  this
| repository is Python 3 compatible as well.

| Once everything is installed you can run the task on a Koji build
  using the
| ``name-(epoch:)version-release`` (``nevr``) identifier.

.. code:: console

    $ runtask -i <nevr> -t koji_build runtask.yml

For example:

.. code:: console

    $ runtask -i eric-6.1.6-2.fc25 -t koji_build runtask.yml

Tests
-----

| There are also automatic tests available. You can run them using
  `tox <https://tox.readthedocs.io/>`__.
| You'll need the above mentioned dependencies and ``python3-rpm``
  installed as well.

.. code:: console

    $ tox

| Automatic tests also happen on `Tarvis
  CI <https://travis-ci.org/fedora-python/task-python-versions/>`__.
  Since Travis CI runs on Ubuntu
| and Ubuntu lacks the RPM Python bindings and Taskotron,
  `Docker <https://docs.travis-ci.com/user/docker/>`__ is used
| to run the tests on Fedora. You can run the tests in Docker as well,
| just use the commands from the ``.travis.yml`` file.

License
-------

| This code has been dedicated to the Public Domain, it is licensed with
| `CC0 1.0 Universal Public Domain
  Dedication <https://creativecommons.org/publicdomain/zero/1.0/>`__,
| full text of the license is available in the LICENSE file in this
  repository.

| Please note that the RPM packages in this repository used for testing
  have
| their own license terms and are not dedicated to the Public Domain.

| The sources of those packages can be found in
  `Koji <https://koji.fedoraproject.org/koji/>`__ by searching the
  package
| name and selecting the appropriate version.
