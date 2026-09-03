"""Tests for lib_openvas.check_valid_target (deployment/src/medsec).

lib_openvas.py imports several heavy third-party packages (python-gvm, lxml,
xmltodict, validators) that are only required for the full OpenVAS scanning
workflow. These tests skip gracefully if that dependency set is not
installed, rather than failing an environment that only needs the core TVRA
parsing logic.
"""
import pytest

gvm = pytest.importorskip("gvm", reason="python-gvm not installed")
lxml = pytest.importorskip("lxml", reason="lxml not installed")
xmltodict = pytest.importorskip("xmltodict", reason="xmltodict not installed")
validators = pytest.importorskip("validators", reason="validators not installed")

lib_openvas = pytest.importorskip("lib_openvas", reason="lib_openvas import failed")


@pytest.mark.parametrize("target", ["192.168.1.10", "10.0.0.1", "example.com", "scanner.internal.lan"])
def test_valid_targets_accepted(target):
    assert lib_openvas.check_valid_target(target) is True


@pytest.mark.parametrize("target", ["not a host!!", "", "-invalid-", "300.300.300.300"])
def test_invalid_targets_rejected(target):
    assert lib_openvas.check_valid_target(target) is False
