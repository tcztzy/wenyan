#!/usr/bin/env python
import argparse
import logging
import os
import subprocess
import sys
from shutil import copyfileobj

try:
    from shutil import which
except ImportError:
    from distutils.spawn import find_executable as which
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

from setuptools import Distribution

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("wenyan:build")

BUILD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".build")
if os.path.exists(BUILD_DIR) and not os.path.isdir(BUILD_DIR):
    sys.exit("`{}` is not a directory!".format(BUILD_DIR))
elif not os.path.exists(BUILD_DIR):
    os.mkdir(BUILD_DIR)
ignore = os.path.join(BUILD_DIR, ".gitignore")
if not os.path.exists(ignore):
    with open(ignore, "w") as f:
        f.write("*")

PYPY_URL = "https://downloads.python.org/pypy/{}"
DEFAULT_PYPY_VERSION = "pypy3.7-v7.3.3"
PYPY_SCM = {
    "scm": "hg",
    "cmd": "clone",
    "url": "https://foss.heptapod.net/pypy/pypy",
    "dst": os.path.join(BUILD_DIR, "pypy"),
}


def download_pypy_src(tar_filename, tar_path):
    with urlopen(PYPY_URL.format(tar_filename)) as src, open(tar_path, "wb") as dst:
        copyfileobj(src, dst)


def clone_pypy_repo():
    if os.path.isdir(PYPY_SCM["dst"]):
        return
    subprocess.check_output([PYPY_SCM[key] for key in ("scm", "cmd", "url", "dst")])


class Pyenv(object):
    def __init__(self, executable):
        self.executable = executable

    def __getattr__(self, __name):
        def cmd(*args):
            return subprocess.check_output(
                [self.executable, __name].extend(args), encoding="utf-8"
            )

        return cmd

    def __str__(self):
        return str(self.executable)

    def __repr__(self):
        return self.__str__()

    @property
    def versions(self):
        output = subprocess.check_output(
            [self.executable, "versions"], encoding="utf-8"
        )
        return [
            line.split()[1] if line.startswith("*") else line.strip()
            for line in output.splitlines()
        ]

    @property
    def root(self):
        return subprocess.check_output(
            [self.executable, "root"], encoding="utf-8"
        ).strip()


def find_pyenv():
    pyenv = which("pyenv")
    if pyenv is not None:
        return pyenv
    pyenv_root = os.environ.get("PYENV_ROOT", os.path.expanduser("~/.pyenv"))
    pyenv = os.path.join(pyenv_root, "bin", "pyenv")
    if os.path.exists(pyenv):
        subprocess.check_call([pyenv, "--help"])
        return pyenv


def find_rpython(src_dir):
    rpython = os.path.join(src_dir, "rpython", "bin", "rpython")
    if os.path.exists(rpython):
        return rpython


def find_pypy(pypy="pypy", pyenv=None):
    if sys.version_info[:2] == (2, 7):  # Even CPython 2.7 can run rpython
        return sys.executable
    pypy = which(pypy)
    if pypy is not None:
        version = subprocess.check_output(
            [
                pypy,
                "-c",
                "import sys;print('{}.{}'.format(sys.version_info[0], sys.version_info[1]))",
            ],
            encoding="utf-8",
        )
        if version == "2.7":
            return pypy
    if pyenv is not None:
        for version in pyenv.versions:
            if version.startswith("pypy2.7"):
                return os.path.join(pyenv.root, "versions", version, "bin", "pypy")
        for version in pyenv.versions:
            if version.startswith("2.7"):
                return os.path.join(pyenv.root, "versions", version, "bin", "pypy")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pypy", default=os.environ.get("PYPY", "pypy"))
    parser.add_argument("--rpython", default=os.environ.get("RPYTHON", "rpython"))
    parser.add_argument("--scm", action="store_true")
    parser.add_argument("--latest", action="store_const", const="")
    parser.add_argument("--verbose", "-v", action="count", default=0)
    args = parser.parse_args()
    if args.verbose > 3:
        logger.warning("Too verbose!")
        level = logging.DEBUG
    else:
        level = logging.ERROR - 10 * args.verbose
    logger.setLevel(level)
    pyenv = find_pyenv()
    if pyenv is not None:
        logger.info("Pyenv found!")
        pyenv = Pyenv(pyenv)
    src_dir = os.path.join(
        BUILD_DIR, "pypy" if args.scm else "{}-src".format(DEFAULT_PYPY_VERSION)
    )
    if args.scm:
        if which(PYPY_SCM["scm"]) is None:
            sys.exit("`{}` is required for source code clone.".format(PYPY_SCM["scm"]))
        clone_pypy_repo()
    pypy = find_pypy(args.pypy, pyenv)
    if pypy is None:
        sys.exit("Pypy 2.7 or CPython 2.7 not found!")
    rpython = which(args.rpython) or find_rpython(src_dir)
    if rpython is None:
        sys.exit("RPython not found!")
    logger.debug("Using Python `{}`".format(pypy))
    logger.debug("Using RPython `{}`".format(rpython))
    subprocess.check_output([pypy, rpython, "wenyan.py"])
    Distribution({"name": "wenyan", "scripts": ["wenyan"]})


if __name__ == "__main__":
    main()
