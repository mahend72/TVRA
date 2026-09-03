"""Tests for centralDB/app/exceptions.py — evidence-not-found error messages.

Pure, stdlib-only logic used by the evidence management API.
"""
from app.exceptions import EvidenceNotFound


def test_message_includes_filename_and_version_when_both_known():
    err = EvidenceNotFound(category="vuln_scan", version_id=2, filename="report.json")
    assert "vuln_scan" in str(err)
    assert "report.json" in str(err)
    assert "2" in str(err)


def test_message_omits_version_when_not_found():
    err = EvidenceNotFound(category="vuln_scan", version_id=0, filename="report.json")
    assert "version_id" not in str(err)
    assert "report.json" in str(err)


def test_message_without_filename_references_category_and_version():
    err = EvidenceNotFound(category="vuln_scan", version_id=3)
    assert "vuln_scan" in str(err)
    assert "3" in str(err)
    assert err.filename is None
