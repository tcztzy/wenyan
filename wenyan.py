#!/usr/bin/env python
# coding: utf-8
import sys

try:
    from importlib.metadata import version, PackageNotFoundError

    try:
        __version__ = version("wenyan")
    except PackageNotFoundError:
        __version__ = "unknown"
except ImportError:
    from pkg_resources import get_distribution, DistributionNotFound

    try:
        __version__ = get_distribution("wenyan").version
    except DistributionNotFound:
        __version__ = "unknown"
try:
    from rpython.jit.codewriter.policy import JitPolicy

    def jitpolicy(driver):
        return JitPolicy()

    def target(driver, *args):
        driver.exe_name = "wenyan"
        return entry_point, None

except ImportError:
    pass

__logo__ = r"""
 ,_ ,_
 \/ ==
 /\ []
"""

__doc__ = """{}
WENYAN LANG 文言 Compiler {}
""".format(
    __logo__,
    __version__,
)


class WenyanException(Exception):
    pass


class Stop(WenyanException):
    pass


class ArgumentParseError(WenyanException):
    pass


class Arguments(object):
    files = []
    help_message = """%s
Usage: %s [options] [files...]
 -v, --version        Output the version
 -h, --help           Display help
"""

    def __init__(self, argv):
        args = iter(argv)
        executable = next(args)
        while True:
            try:
                arg = next(args)
            except StopIteration:
                break
            if arg == "-h" or arg == "--help":
                print(self.help_message % (__doc__, executable))
                raise Stop
            elif arg == "-v" or arg == "--version":
                print(" ".join([executable, __version__]))
                raise Stop
            elif arg == "-":
                self.files.append(next(args))
            elif arg.startswith("-"):
                print("error: unknown option '%s'" % arg)
                raise ArgumentParseError
            else:
                self.files.append(arg)
        if len(self.files) == 0:
            print(self.help_message % (__doc__, executable))
            raise ArgumentParseError


def entry_point(argv):
    try:
        Arguments(argv)
    except Stop:
        pass
    except WenyanException:
        return 1
    return 0


def main():
    sys.exit(entry_point(sys.argv))


if __name__ == "__main__":
    main()
