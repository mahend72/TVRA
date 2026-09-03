"""Tests for deployment/src/medsec/api.py — threat simplification and risk
sorting logic used by GET /v1/threat/get_threats.

This is the transformation step between raw SpydeRisk threat records and the
simplified, risk-sorted output the TVRA API returns, so a regression here
directly affects the risk data an operator or downstream AI-assisted
mitigation step consumes.

Pure functions only; imports the same heavy dependency set as
test_lib_openvas_target_validation.py and skips gracefully if unavailable.
"""
import pytest

gvm = pytest.importorskip("gvm", reason="python-gvm not installed")
lxml = pytest.importorskip("lxml", reason="lxml not installed")
xmltodict = pytest.importorskip("xmltodict", reason="xmltodict not installed")
validators = pytest.importorskip("validators", reason="validators not installed")

api = pytest.importorskip("api", reason="api import failed")


def test_get_risk_level_value_orders_by_severity():
    levels = ["VeryHigh", "High", "Medium", "Low", "VeryLow", "Safe"]
    values = [api._get_risk_level_value({"label": label}) for label in levels]
    assert values == sorted(values, reverse=True)


def test_get_risk_level_value_ignores_spaces_in_label():
    assert api._get_risk_level_value({"label": "Very High"}) == api._get_risk_level_value(
        {"label": "VeryHigh"}
    )


def test_get_risk_level_value_unknown_label_defaults_to_zero():
    assert api._get_risk_level_value({"label": "NotARealLevel"}) == 0
    assert api._get_risk_level_value({}) == 0


def test_simplify_threat_extracts_asset_and_levels():
    raw_threat = {
        "description": "Unauthorized access via SSH",
        "pattern": {"nodes": [{"assetLabel": "Web Server"}, {"assetLabel": "Other"}]},
        "likelihood": {"label": "High", "description": "Likely to occur"},
        "riskLevel": {"label": "High", "description": "Significant impact"},
    }
    result = api.simplify_threat(raw_threat)
    assert result == {
        "description": "Unauthorized access via SSH",
        "threatens_assets": "Web Server",
        "likelihood": {"label": "High", "description": "Likely to occur"},
        "risk_level": {"label": "High", "description": "Significant impact"},
    }


def test_simplify_threat_handles_missing_likelihood_and_risk_level():
    result = api.simplify_threat({"description": "No risk data yet"})
    assert result["threatens_assets"] == ""
    assert result["likelihood"] == {"label": "", "description": ""}
    assert result["risk_level"] == {"label": "", "description": ""}
