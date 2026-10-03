"""Tests for BenchQC Storefront schema conformity."""

import json
from benchqc.schema import BenchQCAudit, SystemSpecs, BatteryTelemetry, ThermalTelemetry, QCSummary, StudentSuitability, BenchmarkMetrics


def test_schema_skeleton_creation():
    audit = BenchQCAudit.create_skeleton()
    data = audit.to_dict()
    assert "auditId" in data
    assert "auditDate" in data
    assert "certifiedGrade" in data
    assert "overallScore" in data
    assert "system" in data
    assert "battery" in data
    assert "thermals" in data
    assert "qcSummary" in data
    assert "studentSuitability" in data
    assert "benchmarks" in data
    assert "officialVerificationUrl" in data
    assert data["officialVerificationUrl"].startswith("https://benchqc.com/verify/BQC-")


def test_schema_json_roundtrip():
    audit = BenchQCAudit.create_skeleton()
    audit.overallScore = 96.5
    audit.certifiedGrade = "A+"
    audit.system.cpu = "AMD Ryzen 7 7840U"
    audit.battery.healthPercent = 98.2
    
    json_str = audit.to_json()
    loaded = json.loads(json_str)
    
    assert loaded["overallScore"] == 96.5
    assert loaded["certifiedGrade"] == "A+"
    assert loaded["system"]["cpu"] == "AMD Ryzen 7 7840U"
    
    audit_obj = BenchQCAudit.from_dict(loaded)
    assert audit_obj.overallScore == 96.5
    assert audit_obj.system.cpu == "AMD Ryzen 7 7840U"
