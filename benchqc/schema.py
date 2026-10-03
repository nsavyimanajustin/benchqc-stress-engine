"""Schema models, JSON serialization, and validation for BenchQC Storefront audit artifacts."""

import json
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from benchqc.version import DEFAULT_VERIFICATION_BASE_URL, SCHEMA_VERSION


@dataclass
class SystemSpecs:
    os: str = "Unknown OS"
    osVersion: str = ""
    cpu: str = "Unknown CPU"
    cpuCores: int = 1
    cpuThreads: int = 1
    ramGb: float = 0.0
    storageGb: float = 0.0
    model: str = "Generic System"
    manufacturer: str = "Generic OEM"
    architecture: str = "x86_64"
    biosVersion: Optional[str] = None


@dataclass
class BatteryTelemetry:
    healthPercent: float = 100.0
    wearPercent: float = 0.0
    cycleCount: int = 0
    designCapacityMwh: float = 50000.0
    fullCapacityMwh: float = 50000.0
    currentCapacityMwh: float = 50000.0
    currentVoltageMv: float = 11400.0
    dischargeRateMw: float = 12000.0
    projectedHoursStudent: float = 4.5
    projectedHoursHeavy: float = 2.1
    projectedHoursIdle: float = 8.0
    studentBadge: str = "STUDENT_APPROVED_4H_PLUS"
    isSimulatedOrAC: bool = False
    powerState: str = "Battery"
    modelName: str = "Primary Battery"


@dataclass
class ThermalTelemetry:
    baselineTempC: float = 42.0
    peakTempC: float = 72.0
    deltaTempC: float = 30.0
    throttleDetected: bool = False
    throttlingPercent: float = 0.0
    frequencyBaselineGhz: float = 2.4
    frequencyUnderStressGhz: float = 2.3


@dataclass
class QCSummary:
    cpuStatus: str = "PASSED"
    memoryStatus: str = "PASSED"
    storageStatus: str = "PASSED"
    batteryStatus: str = "PASSED"
    thermalStatus: str = "PASSED"
    overallStatus: str = "CERTIFIED"
    passedChecksCount: int = 5
    totalChecksCount: int = 5
    notes: List[str] = field(default_factory=list)


@dataclass
class StudentSuitability:
    recommendation: str = "Highly recommended for full-day campus lectures, note-taking, and development without frequent charging."
    expectedClassroomBatteryLife: str = "4+ Hours (Sustained Workload)"
    badge: str = "STUDENT_APPROVED_4H_PLUS"
    workloadReadiness: Dict[str, str] = field(default_factory=lambda: {
        "webBrowsingAndResearch": "EXCELLENT",
        "videoLecturesAndZoom": "EXCELLENT",
        "codingAndIDEs": "EXCELLENT",
        "multitaskingAndDocs": "EXCELLENT",
    })


@dataclass
class BenchmarkMetrics:
    cpuFloatingPointOpsSec: float = 0.0
    cpuMultiCoreScore: float = 0.0
    memoryThroughputMbSec: float = 0.0
    memoryErrorsDetected: int = 0
    storageSeqWriteMbSec: float = 0.0
    storageSeqReadMbSec: float = 0.0
    storageRandWriteIops: float = 0.0
    storageRandReadIops: float = 0.0
    stressDurationSeconds: float = 0.0


@dataclass
class BenchQCAudit:
    auditId: str
    auditDate: str
    certifiedGrade: str
    overallScore: float
    system: SystemSpecs
    battery: BatteryTelemetry
    thermals: ThermalTelemetry
    qcSummary: QCSummary
    studentSuitability: StudentSuitability
    benchmarks: BenchmarkMetrics
    officialVerificationUrl: str
    schemaVersion: str = SCHEMA_VERSION

    @classmethod
    def create_skeleton(cls) -> "BenchQCAudit":
        now = datetime.now(timezone.utc)
        unique_suffix = uuid.uuid4().hex[:8].upper()
        audit_id = f"BQC-{now.strftime('%Y%m%d')}-{unique_suffix}"
        verification_url = f"{DEFAULT_VERIFICATION_BASE_URL}{audit_id}"
        
        return cls(
            auditId=audit_id,
            auditDate=now.isoformat(),
            certifiedGrade="A",
            overallScore=90.0,
            system=SystemSpecs(),
            battery=BatteryTelemetry(),
            thermals=ThermalTelemetry(),
            qcSummary=QCSummary(),
            studentSuitability=StudentSuitability(),
            benchmarks=BenchmarkMetrics(),
            officialVerificationUrl=verification_url,
            schemaVersion=SCHEMA_VERSION,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def save_to_file(self, file_path: str) -> None:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchQCAudit":
        return cls(
            auditId=data["auditId"],
            auditDate=data["auditDate"],
            certifiedGrade=data["certifiedGrade"],
            overallScore=data["overallScore"],
            system=SystemSpecs(**data["system"]),
            battery=BatteryTelemetry(**data["battery"]),
            thermals=ThermalTelemetry(**data["thermals"]),
            qcSummary=QCSummary(**data["qcSummary"]),
            studentSuitability=StudentSuitability(**data["studentSuitability"]),
            benchmarks=BenchmarkMetrics(**data.get("benchmarks", {})),
            officialVerificationUrl=data["officialVerificationUrl"],
            schemaVersion=data.get("schemaVersion", SCHEMA_VERSION),
        )

    @classmethod
    def from_file(cls, file_path: str) -> "BenchQCAudit":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
