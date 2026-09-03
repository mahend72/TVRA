"""Tests for deployment/src/medsec/tvra_asset.py — parsing of Spyderisk/TVRA
model records into typed dataclasses. Pure functions, no I/O or network.
"""
from tvra_asset import ControlSet, Misbehaviour, NetworkDomain, TrustworthinessAttributeSet, TVRAAsset


def test_tvra_asset_from_dict_extracts_name_from_base_class():
    record = {
        "id": "system#asset1",
        "data": {
            "base_Class": "/0/Patients%20Phone",
            "kind": "Adult",
            "misbehaviours": ["m1"],
            "trustworthinessattributesets": ["t1"],
            "controlsets": ["c1"],
        },
    }
    asset = TVRAAsset.from_dict(record)
    assert asset.id == "system#asset1"
    assert asset.name == "Patients Phone"
    assert asset.misbehaviours == ["m1"]
    assert asset.resolved_misbehaviours == []


def test_tvra_asset_from_dict_handles_missing_base_class():
    asset = TVRAAsset.from_dict({"id": "x", "data": {}})
    assert asset.name == ""
    assert asset.base_class == ""


def test_control_set_from_dict_reports_coverage_level():
    with_coverage = ControlSet.from_dict(
        {"id": "cs1", "data": {"kind": "CSUsesNoEmail", "coverageLevel": "High"}}
    )
    assert with_coverage.has_coverage_level is True

    without_coverage = ControlSet.from_dict({"id": "cs2", "data": {"kind": "CSOther"}})
    assert without_coverage.has_coverage_level is False


def test_misbehaviour_from_dict_reports_level():
    misb = Misbehaviour.from_dict({"id": "m1", "data": {"kind": "MSLossOfIntegrity", "level": "High"}})
    assert misb.has_level is True
    assert misb.kind == "MSLossOfIntegrity"


def test_trustworthiness_attribute_set_from_dict():
    twas = TrustworthinessAttributeSet.from_dict(
        {"id": "t1", "data": {"kind": "TWASAvailability", "trustworthinessLevel": "VeryHigh"}}
    )
    assert twas.has_level is True
    assert twas.trustworthiness_level == "VeryHigh"


def test_network_domain_resolves_source_and_target_names():
    record = {
        "id": "nd1",
        "data": {
            "name": "manages",
            "memberEnd": ["/0/manages/patient", "/0/manages/device"],
            "navigableOwnedEnd": ["/0/manages/patient"],
            "ownedEnd": [
                {"data": {"name": "patient", "type": "/0/Patient", "association": "/0/manages"}},
                {"data": {"name": "device", "type": "/0/Device", "association": "/0/manages"}},
            ],
        },
    }
    domain = NetworkDomain.from_dict(record)
    assert domain.get_from_asset() == "Device"
    assert domain.get_to_asset() == "Patient"
    assert domain.get_source_type_name() == "Device"
    assert domain.get_target_type_name() == "Patient"


def test_network_domain_handles_incomplete_ends_gracefully():
    domain = NetworkDomain.from_dict({"id": "nd2", "data": {"name": "isolated"}})
    assert domain.source_name == ""
    assert domain.target_name == ""
