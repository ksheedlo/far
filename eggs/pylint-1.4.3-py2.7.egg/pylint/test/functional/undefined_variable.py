"""Test warnings about access to undefined variables."""
# pylint: disable=too-few-public-methods, no-init, no-self-use, old-style-class,print-statement

DEFINED = 1

if DEFINED != 1:
    if DEFINED in (unknown, DEFINED):  # [undefined-variable]
        DEFINED += 1


def in_method(var):
    """method doc"""
    var = nomoreknown  # [undefined-variable]
    assert var

DEFINED = {DEFINED:__revision__}  # [undefined-variable]
# +1:[undefined-variable]
DEFINED[__revision__] = OTHER = 'move this is astroid test'

OTHER += '$'

def bad_default(var, default=unknown2):  # [undefined-variable]
    """function with defaut arg's value set to an unexistant name"""
    print var, default
    print xxxx  # [undefined-variable]
    augvar += 1  # [undefined-variable,unused-variable]
    del vardel  # [undefined-variable]

LMBD = lambda x, y=doesnotexist: x+y  # [undefined-variable]
LMBD2 = lambda x, y: x+z  # [undefined-variable]

try:
    POUET # don't catch me
except NameError:
    POUET = 'something'

try:
    POUETT # don't catch me
except Exception: # pylint:disable = broad-except
    POUETT = 'something'

try:
    POUETTT # don't catch me
except: # pylint:disable = bare-except
    POUETTT = 'something'

print POUET, POUETT, POUETTT


try:
    PLOUF  # [used-before-assignment]
except ValueError:
    PLOUF = 'something'

print PLOUF

def if_branch_test(something):
    """hop"""
    if something == 0:
        if xxx == 1:  # [used-before-assignment]
            pass
    else:
        print xxx
        xxx = 3


def decorator(arg):
    """Decorator with one argument."""
    return lambda: list(arg)


@decorator(arg=[i * 2 for i in range(15)])
def func1():
    """A function with a decorator that contains a listcomp."""

@decorator(arg=(i * 2 for i in range(15)))
def func2():
    """A function with a decorator that contains a genexpr."""

@decorator(lambda x: x > 0)
def main():
    """A function with a decorator that contains a lambda."""

# Test shared scope.

def test_arguments(arg=TestClass):  # [used-before-assignment]
    """ TestClass isn't defined yet. """
    return arg

class TestClass(Ancestor):  # [used-before-assignment]
    """ contains another class, which uses an undefined ancestor. """

    class MissingAncestor(Ancestor1):  # [used-before-assignment]
        """ no op """

    def test1(self):
        """ It should trigger here, because the two classes
        have the same scope.
        """
        class UsingBeforeDefinition(Empty):  # [used-before-assignment]
            """ uses Empty before definition """
        class Empty(object):
            """ no op """
        return UsingBeforeDefinition

    def test(self):
        """ Ancestor isn't defined yet, but we don't care. """
        class MissingAncestor1(Ancestor):
            """ no op """
        return MissingAncestor1

class Self(object):
    """ Detect when using the same name inside the class scope. """
    obj = Self # [undefined-variable]

class Self1(object):
    """ No error should be raised here. """

    def test(self):
        """ empty """
        return Self1


class Ancestor(object):
    """ No op """

class Ancestor1(object):
    """ No op """
