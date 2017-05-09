# [Taskotron] task regarding Python versions

This represents the automatic checks happening in the Fedora infrastructure
after any package is built.

Currently the following checks are available:

 * Whether a package does not require Python 2 and Python 3 at the same time.


[Taskotron]: https://fedoraproject.org/wiki/Taskotron


## Running

You can run the checks locally with [Taskotron]. First, install it (you can
follow the [Quickstart]).
You'll also need the `rpm` Python 2 module (`python2-rpm`).
Note that Taskotron unfortunately runs on Python 2, but the code in this
repository is Python 3 compatible as well.

[Quickstart]: https://qa.fedoraproject.org/docs/libtaskotron/latest/quickstart.html

Once everything is installed you can run the task on a Koji build using the
`name-(epoch:)version-release` (`nevr`) identifier.

```console
$ runtask -i <nevr> -t koji_build runtask.yml
```

For example:

```console
$ runtask -i eric-6.1.6-2.fc25 -t koji_build runtask.yml
```

## Tests

There are also automatic tests available. You can run them using [tox].
You'll need the above mentioned dependencies installed as well.

```console
$ tox
```

[tox]: https://tox.readthedocs.io/

## License

This code has been dedicated to the Public Domain, it is licensed with
[CC0 1.0 Universal Public Domain Dedication](https://creativecommons.org/publicdomain/zero/1.0/),
full text of the license is available in the LICENSE file in this repository.

Please note that the RPM packages in this repository used for testing have
their own license terms and are not dedicated to the Public Domain.

The sources of those packages can be found in [Koji] by searching the package
name and selecting the appropriate version.

[Koji]: https://koji.fedoraproject.org/koji/
