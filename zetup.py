# zetup.py
#
# My common stuff for Python package setups.
#
# Copyright (C) 2014 Stefan Zimmermann <zimmermann.code@gmail.com>
#
# zetup.py is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# zetup.py is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with zetup.py. If not, see <http://www.gnu.org/licenses/>.

import sys
if sys.version_info[0] == 3:
    # Just for simpler PY2/3 compatible code:
    unicode = str

import os
import re
from collections import OrderedDict
from pkg_resources import parse_version, parse_requirements

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


class Version(str):
    """Manage and compare version strings
       using :func:`pkg_resources.parse_version`.
    """
    @staticmethod
    def _parsed(value):
        """Parse a version `value` if needed.
        """
        if isinstance(value, (str, unicode)):
            value = parse_version(value)
        return value

    @property
    def parsed(self):
        """The version string as parsed version tuple.
        """
        return parse_version(self)

    def __eq__(self, other):
        return self.parsed == self._parsed(other)

    def __ne__(self, other):
        return self.parsed != self._parsed(other)

    def __lt__(self, other):
        return self.parsed < self._parsed(other)

    def __le__(self, other):
        return self.parsed <= self._parsed(other)

    def __gt__(self, other):
        return self.parsed > self._parsed(other)

    def __ge__(self, other):
        return self.parsed >= self._parsed(other)


class Requirements(str):
    """Package requirements manager.
    """
    def __new__(cls, text):
        reqs = parse_requirements(text)
        return str.__new__(cls, '\n'.join(map(str, reqs)))

    def __init__(self, text):
        self._list = list(parse_requirements(text))

    def __iter__(self):
        return iter(self._list)

    def __getitem__(self, name):
        for req in self._list:
            if name in [req.key, req.unsafe_name]:
                return req
        raise KeyError(name)

    def __add__(self, text):
        return type(self)('%s\n%s' % (self, text))

    def __repr__(self):
        return str(self)


class Extras(OrderedDict):
    """Package extra features/requirements manager.
    """
    def __repr__(self):
        return "\n\n".join((
          "[%s]\n" % key + '\n'.join(map(str, reqs))
          for key, reqs in self.items()))


SETUP_DATA = ['VERSION', 'requirements.txt']

VERSION = Version(open('VERSION').read().strip())

REQUIRES = Requirements(open('requirements.txt').read())

# Extra requirements to use with setup's extras_require=
EXTRAS = Extras()
_re = re.compile(r'^requirements\.(?P<name>[^\.]+)\.txt$')
for fname in sorted(os.listdir('.')):
    match = _re.match(fname)
    if match:
        SETUP_DATA.append(fname)

        EXTRAS[match.group('name')] = Requirements(open(fname).read())


# If installed with pip, add all build directories and src/ subdirs
#  of implicitly downloaded requirements
#  to sys.path and os.environ['PYTHONPATH']
#  to make them importable during installation:
sysbuildpath = os.path.join(sys.prefix, 'build')
try:
    fnames = os.listdir(sysbuildpath)
except OSError:
    pass
else:
    if 'pip-delete-this-directory.txt' in fnames:
        pkgpaths = []
        for fn in fnames:
            path = os.path.join(sysbuildpath, fn)
            if not os.path.isdir(path):
                continue
            path = os.path.abspath(path)
            pkgpaths.append(path)

            srcpath = os.path.join(path, 'src')
            if os.path.isdir(srcpath):
                pkgpaths.append(srcpath)

        for path in pkgpaths:
            sys.path.insert(0, path)

        PYTHONPATH = os.environ.get('PYTHONPATH')
        PATH = ':'.join(pkgpaths)
        if PYTHONPATH is None:
            os.environ['PYTHONPATH'] = PATH
        else:
            os.environ['PYTHONPATH'] = ':'.join([PATH, PYTHONPATH])


try:
    from jinja2 import FileSystemLoader
    from jinjatools.scons import JinjaBuilder
except ImportError:
    pass
else:
    class README_Builder(JinjaBuilder):
        def __init__(self):
            JinjaBuilder.__init__(self, FileSystemLoader('.'), context={
              'REQUIRES': self.REQUIRES(REQUIRES),
              'EXTRAS': self.EXTRAS(),
              'INSTALL': self.INSTALL(),
              })

        def REQUIRES(self, reqs):
            return '\n'.join(
              "* [`%s`](https://pypi.python.org/pypi/%s)" % (
                req, req.unsafe_name)
              for req in reqs)

        def EXTRAS(self):
            return '\n\n'.join(
              "Extra requirements for __[%s]__:\n\n" % key
              + self.REQUIRES(reqs)
              for key, reqs in EXTRAS.items())

        def INSTALL(self):
            mdtext = (
              "    python setup.py install"
              "\n\n"
              "Or with [pip](http://www.pip-installer.org):"
              "\n\n"
              "    pip install ."
              "\n\n"
              "Or from [PyPI](https://pypi.python.org/pypi/%s):"
              "\n\n"
              "    pip install %s"
              % tuple(2 * [PROJECT]))
            if EXTRAS:
              mdtext += (
                "\n\n"
                "* With all extra features:"
                "\n\n"
                "        pip install %s[%s]"
                % (PROJECT, ','.join(EXTRAS)))
            return mdtext


    README_BUILDER = README_Builder()
