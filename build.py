import os
import subprocess
import sys
import tarfile
from distutils.core import Distribution
from shutil import copyfileobj, rmtree
import logging

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen
try:
    from subprocess import DEVNULL
except ImportError:
    from os import devnull

    DEVNULL = open(devnull)

logger = logging.getLogger("wenyan:build")

PYPY_URL = "https://downloads.python.org/pypy/{}"
DEFAULT_PYPY_VERSION = "pypy3.7-v7.3.3"


def build():
    rpython = os.environ.get("RPYTHON")
    if rpython is None:
        logger.debug("${RPYTHON} not set, skip the rpython translation!")
        return
    tar_basename = "{}-src".format(os.environ.get("PYPY_VERSION", DEFAULT_PYPY_VERSION))
    if not rpython:
        rpython = os.path.join("build", tar_basename, "rpython", "bin", "rpython")
    pypy = os.environ.get(
        "PYPY", sys.executable if sys.version_info[0] == 2 else "pypy"
    )
    if (
        int(
            subprocess.check_output(
                [pypy, "-c", "import sys;print(sys.version_info[0])"]
            )
        )
        != 2
    ):
        raise Exception("python2 or pypy need to run rpython")
    if (
        subprocess.call(
            [pypy, rpython, "--help"],
            stdout=DEVNULL,
            stderr=DEVNULL,
        )
        != 0
    ):
        tar_filename = "{}.tar.bz2".format(tar_basename)
        tar_path = os.path.join("build", tar_filename)
        if not os.path.exists(tar_path):
            with urlopen(PYPY_URL.format(tar_filename)) as src, open(
                tar_path, "wb"
            ) as dst:
                copyfileobj(src, dst)
        rmtree(os.path.join("build", tar_basename), ignore_errors=True)
        with tarfile.open(tar_path, "r:bz2") as tar:
            tar.extractall("build")
    subprocess.check_output([pypy, rpython, "wenyan.py"])
    Distribution({"name": "wenyan", "scripts": ["wenyan"]})


if __name__ == "__main__":
    build()
