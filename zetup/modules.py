# zetup.py
#
# Zimmermann's Python package setup.
#
# Copyright (C) 2014-2015 Stefan Zimmermann <zimmermann.code@gmail.com>
#
# zetup.py is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# zetup.py is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with zetup.py. If not, see <http://www.gnu.org/licenses/>.

"""zetup.modules

(top-level) package module object wrappers.

.. moduleauthor:: Stefan Zimmermann <zimmermann.code@gmail.com>
"""
import sys
from types import ModuleType

from .annotate import annotate

__all__ = ['package', 'toplevel']


class package(ModuleType):
    """Package module object wrapper
       for clean dynamic API import from sub-modules.
    """
    def __init__(self, __name__, __all__):
        """Wrap package module given by its `__name__`.

        - Replaces module object in ``sys.modules``.
        - Define the package API by passing a ``dict`` to `__all__`,
          which maps sub-module names (with leading dots)
          to the names of API members defined in those sub-modules.
        - Original package module object is stored in ``self.__module__``.
        """
        self.__name__ = __name__
        self.__module__ = sys.modules[__name__]
        sys.modules[__name__] = self
        self.__dict__['__all__'] = {}
        for submodname, members in __all__.items():
            self.__dict__['__all__'].update(
                (name, submodname) for name in members)

    @property
    def __all__(self):
        """Get API member name list.
        """
        return list(self.__dict__['__all__'])

    def __getattr__(self, name):
        """Dynamically import API members from sub-modules.
        """
        try:
            return getattr(self.__module__, name)
        except AttributeError:
            pass
        if name in self.__all__:
            submodname = self.__dict__['__all__'][name]
            submod = __import__(self.__name__ + submodname, fromlist=[name])
            submodname = submodname.lstrip('.')
            # was sub-module added to self.__dict__ during __import__?
            if submodname in self.__dict__:
                # ==> move it to original module object to keep API clean
                self.__module__.__dict__[submodname] \
                    = self.__dict__.pop(submodname)
            obj = getattr(submod, name)
            setattr(self, name, obj)
            return obj
        raise AttributeError("%s has no attribute %s" % (self, repr(name)))

    def __dir__(self):
        """Get all API member names.
        """
        return super(package, self).__dir__() + self.__all__


class toplevel(package):
    """Special top-level package module object wrapper
       for clean dynamic API import from sub-modules
       and automatic application of func:`zetup.annotate`.
    """
    def __init__(self, __name__, __all__, check_requirements=True,
                 check_packages=True):
        """Wrap top-level package module given by its `__name__`.

        - See :class:`zetup.package`
          for details about defining the package API.
        - See :func:`zetup.annotate` for details about the extra options.
        """
        super(toplevel, self).__init__(__name__, __all__)
        annotate(__name__, check_requirements=check_requirements,
                 check_packages=check_packages)