This project is a massive fork of [Gitless](http://gitless.com), which I am then repurposing for trunk based development.


TBD
===

[![PyPI version](https://badge.fury.io/py/tbd.png)](
    http://badge.fury.io/py/tbd "PyPI version")
[![Homebrew Formula](https://img.shields.io/homebrew/v/tbd.svg)](http://braumeister.org/formula/tbd "Homebrew Formula")    
[![Travis Build Status](https://travis-ci.org/sdg-mit/tbd.png?branch=master)](https://travis-ci.org/sdg-mit/tbd "Travis Build Status")
[![AppVeyor Build Status](https://ci.appveyor.com/api/projects/status/github/sdg-mit/tbd?svg=true)](https://ci.appveyor.com/project/spderosso/tbd "AppVeyor Build Status")

[tbd](http://tbd.com "tbd's website") is an experimental version
control system built on top of [Gitless](http://gitless.com), which is built on top of Git. 
Many
people complain that Git is hard to use. We think the problem lies deeper than
the user interface, in the concepts underlying Git. tbd is an experiment to
see what happens if you put a simple veneer on an app that changes the
underlying concepts. Because tbd is implemented on top of Git (could be
considered what Git pros call a "porcelain" of Git), you can always fall
back on Git. And of course your coworkers you share a repository with need never
know that you're not a Git aficionado.


Install
-------

Note that the installation **won't interfere** with your Git installation in any
way, you can keep using Git, and switch between Git and tbd seamlessly.

We currently require Git (1.7.12+) to be installed (but this requirement is
going to disappear soon once we finish with our migration to pygit2).


### Binary releases (macOS and Linux only)

Binary releases for macOS and Linux are available from the
[tbd website](http://tbd.com "tbd's website").

If you've downloaded a binary release of tbd everything is contained in the
tbd binary, so to install simply do:

    $ cp path-to-downloaded-tbd-binary /usr/local/bin/tbd

You can put the binary in other locations as well, just be sure to update your
`PATH`.

If for some reason this doesn't work (maybe you are running an old version of
your OS?), try one of the other options (installing from source or via
the Python Package Index).


### Installing from source

To install from source you need to have Python (2.7, 3.2+ or PyPy)
installed.

Note to Windows users: Python 3 is not supported yet,
see [#146](https://github.com/sdg-mit/tbd/issues/146) for more info.

Additionally, you need to [install pygit2](
http://www.pygit2.org/install.html "pygit2 install").

Then, [download the source code tarball](http://tbd.com "tbd's website")
and do:

    $ ./setup.py install


### Installing via the Python Package Index

If you are a Python fan you might find it easier to install
tbd via the Python Package Index. To do this, you need to have
Python (2.7, 3.2+ or PyPy) installed.

Note to Windows users: Python 3 is not supported yet,
see [#146](https://github.com/sdg-mit/tbd/issues/146) for more info.

Additionally, you need to [install pygit2](
http://www.pygit2.org/install.html "pygit2 install").

Then, just do:

    $ pip install tbd

### Installing via Homebrew (macOS only)

If you are using [Homebrew](http://brew.sh/ "Homebrew homepage"), a package
manager for macOS, you can install tbd with:

```
brew update
brew install tbd
```

Documentation
-------------

`tbd -h`, `tbd subcmd -h` or check
[our documentation](http://tbd.com "tbd's website")


Contribute
----------

There are several ways you can contribute to the project:

- Bugs: did you find a bug? create an issue for it and we'll fix it
ASAP
- Code: you can browse through the open issues and see if there's something
there you would like to work on. Is something missing? feel free to propose it!
- Design: if you have any feedback about tbd's design we would love to
hear from you. You can create an issue in the project with your
feedback/questions/suggestions or shoot us an email


If you're planning on submitting code here are some useful things to know:

- We follow (to some extent) the [Google Python Style Guide](
    https://google.github.io/styleguide/pyguide.html
    "Google Python Style Guide").
Before submitting code, take a few seconds to look at the style guide and the
tbd's code so that your edits are consistent with the codebase

- Finally, if you don't want [Travis](
    https://travis-ci.org/sdg-mit/tbd "Travis") to
be mad at you, check that tests pass in Python 2.7 and 3.2+. Tests can be run with
  ```
  pip install nose
  nosetests # run tests other than end-to-end tests
  nosetests ./tbd/tests/test_e2e.py # run end-to-end tests
  ```
