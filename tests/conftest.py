"""Shared pytest fixtures.

The services in this repository are deployed as standalone containers and
therefore use flat, non-package imports internally (e.g. `import tvra_asset`
inside deployment/src/medsec). To exercise that code without changing it,
tests add each service's source directory to sys.path directly rather than
importing it as an installed package.
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEDSEC_SRC = os.path.join(REPO_ROOT, "deployment", "src", "medsec")
CENTRALDB_SRC = os.path.join(REPO_ROOT, "centralDB")
FINAL_FILES_SRC = os.path.join(REPO_ROOT, "Final_Files")

for path in (MEDSEC_SRC, CENTRALDB_SRC, FINAL_FILES_SRC):
    if path not in sys.path:
        sys.path.insert(0, path)

# lib_openvas.py / lib_spyderisk.py read MEDSEC_HOME at import time with no
# default, mirroring the container environment set by deployment/Dockerfile.
os.environ.setdefault("MEDSEC_HOME", "/tmp/medsec-test-home")

# medsec modules (tvra_asset, tvra_parser, api, main, lib_openvas, lib_spyderisk)
# call logger.get_logger('TVRA', '/proc/1/fd/1') at import time, with a fallback
# to /dev/stdout only on PermissionError. Outside a Linux container running as
# PID 1, /proc/1/fd/1 does not exist at all, which raises FileNotFoundError
# instead and is not caught (see README "Known limitations"). Attaching a
# handler to the 'TVRA' logger up front makes get_logger()'s
# `if not logger.handlers` guard skip FileHandler creation, so tests can
# import this code on any OS without touching the source files themselves.
import logging as _logging

_tvra_logger = _logging.getLogger("TVRA")
if not _tvra_logger.handlers:
    _tvra_logger.addHandler(_logging.NullHandler())
