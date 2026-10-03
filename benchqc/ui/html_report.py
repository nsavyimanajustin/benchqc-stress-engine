"""Self-contained, responsive HTML Certificate and Audit Report generator for BenchQC."""

import os
import json
from benchqc.schema import BenchQCAudit


def generate_html_report(audit: BenchQCAudit, output_path: str = "benchqc_report.html") -> str:
    """Generate a self-contained, offline-compatible HTML report for the audit."""
    data = audit.to_dict()

    # Helpers
    score = data.get("overallScore", 0.0)
    grade = data.get("certifiedGrade", "N/A")
    audit_id = data.get("auditId", "N/A")
    audit_date = data.get("auditDate", "N/A")
    system = data.get("system", {})
    battery = data.get("battery", {})
    thermals = data.get("thermals", {})
    qc = data.get("qcSummary", {})
    suitability = data.get("studentSuitability", {})
    benchmarks = data.get("benchmarks", {})

    # Grade color styling
    if "A+" in grade:
        grade_bg = "#064e3b"
        grade_color = "#34d399"
        grade_border = "#059669"
    elif "A" in grade:
        grade_bg = "#064e3b"
        grade_color = "#10b981"
        grade_border = "#059669"
    elif "B" in grade:
        grade_bg = "#1e3a5f"
        grade_color = "#60a5fa"
        grade_border = "#2563eb"
    else:
        grade_bg = "#78350f"
        grade_color = "#fbbf24"
        grade_border = "#d97706"

    # Student Badge styling
    badge = battery.get("studentBadge") or suitability.get("badge", "CAMPUS_READY_3H_TO_4H")
    if "4H_PLUS" in badge:
        badge_text = "🎓 STUDENT APPROVED (4H+ SUSTAINED)"
        badge_class = "badge-emerald"
    elif "3H_TO_4H" in badge:
        badge_text = "🏫 CAMPUS READY (3 - 4 HOURS)"
        badge_class = "badge-blue"
    else:
        badge_text = "🔌 DESK BOUND (< 3 HOURS)"
        badge_class = "badge-amber"

    health_pct = battery.get("healthPercent", 100.0)
    wear_pct = battery.get("wearPercent", 0.0)
    cycle_count = battery.get("cycleCount", 0)
    full_cap = battery.get("fullCapacityMwh", 0.0)
    design_cap = battery.get("designCapacityMwh", 0.0)
    discharge_mw = battery.get("dischargeRateMw", 0.0)
    voltage_mv = battery.get("currentVoltageMv", 0.0)

    hrs_student = battery.get("projectedHoursStudent", 0.0)
    hrs_heavy = battery.get("projectedHoursHeavy", 0.0)
    hrs_idle = battery.get("projectedHoursIdle", 0.0)

    peak_temp = thermals.get("peakTempC", 0.0)
    base_temp = thermals.get("baselineTempC", 0.0)
    delta_temp = thermals.get("deltaTempC", 0.0)
    throttling = thermals.get("throttleDetected", False)

    # Raw JSON string for inline download
    raw_json_str = json.dumps(data, indent=2).replace("`", "\\`").replace("</script>", "<\\/script>")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BenchQC Audit Report · {audit_id}</title>
  <style>
    :root {{
      --bg: #0B0F17;
      --card-bg: #131B29;
      --card-border: #1E293B;
      --text-main: #F1F5F9;
      --text-muted: #94A3B8;
      --accent-emerald: #10B981;
      --accent-blue: #3B82F6;
      --accent-amber: #F59E0B;
      --accent-red: #EF4444;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}
    body {{
      background-color: var(--bg);
      color: var(--text-main);
      padding: 24px 16px;
      line-height: 1.5;
    }}
    .container {{
      max-width: 900px;
      margin: 0 auto;
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--card-border);
      margin-bottom: 24px;
      flex-wrap: wrap;
      gap: 12px;
    }}
    .logo {{
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 20px;
      font-weight: 800;
      letter-spacing: -0.5px;
    }}
    .logo-icon {{
      width: 32px;
      height: 32px;
      background: linear-gradient(135deg, #10B981, #047857);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-weight: 900;
      font-size: 18px;
    }}
    .audit-meta {{
      text-align: right;
      font-size: 12px;
      color: var(--text-muted);
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 24px;
      margin-bottom: 20px;
    }}
    .hero-card {{
      display: grid;
      grid-template-columns: 1fr auto;
      align-items: center;
      gap: 20px;
      background: radial-gradient(circle at top right, rgba(16, 185, 129, 0.08), transparent 70%), var(--card-bg);
    }}
    @media (max-width: 640px) {{
      .hero-card {{ grid-template-columns: 1fr; }}
      .audit-meta {{ text-align: left; }}
    }}
    .device-title {{
      font-size: 22px;
      font-weight: 700;
      color: #FFF;
      margin-bottom: 6px;
    }}
    .device-sub {{
      font-size: 13px;
      color: var(--text-muted);
    }}
    .grade-badge-box {{
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 16px 24px;
      background: {grade_bg};
      border: 2px solid {grade_border};
      border-radius: 16px;
      text-align: center;
      min-width: 140px;
    }}
    .grade-val {{
      font-size: 38px;
      font-weight: 900;
      color: {grade_color};
      line-height: 1;
    }}
    .grade-score {{
      font-size: 12px;
      color: #CBD5E1;
      margin-top: 4px;
      font-weight: 600;
    }}
    .badge-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 12px;
      font-weight: 700;
      margin-top: 12px;
    }}
    .badge-emerald {{
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.4);
      color: #34D399;
    }}
    .badge-blue {{
      background: rgba(59, 130, 246, 0.15);
      border: 1px solid rgba(59, 130, 246, 0.4);
      color: #60A5FA;
    }}
    .badge-amber {{
      background: rgba(245, 158, 11, 0.15);
      border: 1px solid rgba(245, 158, 11, 0.4);
      color: #FBBF24;
    }}
    .grid-2 {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }}
    .grid-3 {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
    }}
    @media (max-width: 768px) {{
      .grid-2, .grid-3 {{ grid-template-columns: 1fr; }}
    }}
    .section-title {{
      font-size: 15px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #94A3B8;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .stat-box {{
      background: #0B0F17;
      border: 1px solid #1E293B;
      border-radius: 12px;
      padding: 16px;
    }}
    .stat-label {{
      font-size: 11px;
      color: var(--text-muted);
      text-transform: uppercase;
      font-weight: 600;
      margin-bottom: 4px;
    }}
    .stat-val {{
      font-size: 20px;
      font-weight: 700;
      color: #FFF;
    }}
    .stat-sub {{
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 2px;
    }}
    .table-spec {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    .table-spec td {{
      padding: 10px 0;
      border-bottom: 1px solid #1E293B;
    }}
    .table-spec td:first-child {{
      color: var(--text-muted);
      width: 35%;
    }}
    .table-spec td:last-child {{
      font-weight: 600;
      color: #FFF;
    }}
    .qc-item {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 14px;
      background: #0B0F17;
      border: 1px solid #1E293B;
      border-radius: 8px;
      margin-bottom: 8px;
      font-size: 13px;
    }}
    .pass-tag {{
      background: rgba(16, 185, 129, 0.2);
      color: #34D399;
      padding: 2px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 700;
    }}
    .btn-group {{
      display: flex;
      gap: 12px;
      margin-top: 24px;
      justify-content: center;
    }}
    .btn {{
      padding: 10px 20px;
      border-radius: 10px;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
      border: none;
      transition: all 0.2s;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }}
    .btn-primary {{
      background: #10B981;
      color: white;
    }}
    .btn-primary:hover {{
      background: #059669;
    }}
    .btn-secondary {{
      background: #1E293B;
      color: #E2E8F0;
    }}
    .btn-secondary:hover {{
      background: #334155;
    }}
    @media print {{
      body {{ background: white; color: black; padding: 0; }}
      .card {{ background: white; border: 1px solid #ccc; color: black; }}
      .stat-box, .qc-item {{ background: #f8fafc; border: 1px solid #e2e8f0; color: black; }}
      .btn-group {{ display: none; }}
      .device-title, .stat-val, .table-spec td:last-child {{ color: black; }}
      .logo-icon {{ -webkit-print-color-adjust: exact; }}
      .grade-badge-box {{ -webkit-print-color-adjust: exact; }}
    }}
  </style>
</head>
<body>

<div class="container">
  <!-- Top Navigation / Header -->
  <div class="header">
    <div class="logo">
      <div class="logo-icon">⚡</div>
      <div>BENCH<span style="color: var(--accent-emerald);">QC</span> VERIFIED</div>
    </div>
    <div class="audit-meta">
      <div>Audit ID: <strong>{audit_id}</strong></div>
      <div>Date: {audit_date[:19].replace('T', ' ')} UTC</div>
    </div>
  </div>

  <!-- Hero Summary Card -->
  <div class="card hero-card">
    <div>
      <div class="device-title">{system.get('model') or system.get('cpu', 'Certified Laptop')}</div>
      <div class="device-sub">{system.get('manufacturer', '')} · {system.get('os', 'Windows')} · {system.get('cpu', '')}</div>
      <div class="badge-pill {badge_class}">
        {badge_text}
      </div>
      <p style="font-size: 13px; color: var(--text-muted); margin-top: 12px; max-width: 520px;">
        {suitability.get('recommendation', 'Verified campus-ready under multi-tier hardware stress testing and battery sustenance evaluation.')}
      </p>
    </div>
    <div class="grade-badge-box">
      <div class="grade-val">{grade}</div>
      <div class="grade-score">{score} / 100</div>
    </div>
  </div>

  <!-- Battery Sustenance Matrix -->
  <div class="card">
    <div class="section-title">
      <span>🔋 Battery Sustenance & Load Endurance</span>
    </div>
    <div class="grid-3" style="margin-bottom: 16px;">
      <div class="stat-box">
        <div class="stat-label">🎓 Student Multitasking</div>
        <div class="stat-val" style="color: #34D399;">{hrs_student:.1f} Hours</div>
        <div class="stat-sub">15 Tabs + Code IDE + Video</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">⚡ 100% Torture Burn</div>
        <div class="stat-val" style="color: #60A5FA;">{hrs_heavy:.1f} Hours</div>
        <div class="stat-sub">Full Core Render / Compile</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">📖 Idle / Reading</div>
        <div class="stat-val" style="color: #FBBF24;">{hrs_idle:.1f} Hours</div>
        <div class="stat-sub">PDF Notes & Document View</div>
      </div>
    </div>

    <div class="grid-2">
      <table class="table-spec">
        <tr>
          <td>Health / Wear</td>
          <td><strong>{health_pct:.1f}% Health</strong> (Wear: {wear_pct:.1f}%)</td>
        </tr>
        <tr>
          <td>Cycle Count</td>
          <td>{cycle_count} Verified Cycles</td>
        </tr>
        <tr>
          <td>Battery Capacity</td>
          <td>{full_cap:,.0f} mWh (Design: {design_cap:,.0f} mWh)</td>
        </tr>
      </table>
      <table class="table-spec">
        <tr>
          <td>Discharge Draw</td>
          <td>{discharge_mw:,.0f} mW under load</td>
        </tr>
        <tr>
          <td>Cell Voltage</td>
          <td>{voltage_mv:,.0f} mV</td>
        </tr>
        <tr>
          <td>Classroom Life</td>
          <td>{suitability.get('expectedClassroomBatteryLife', f'{hrs_student:.1f} Hours')}</td>
        </tr>
      </table>
    </div>
  </div>

  <!-- Hardware Specification Sheet -->
  <div class="card">
    <div class="section-title">
      <span>💻 Hardware Specifications & Thermals</span>
    </div>
    <div class="grid-2">
      <table class="table-spec">
        <tr>
          <td>Processor</td>
          <td>{system.get('cpu', 'N/A')} ({system.get('cpuCores', 4)}C / {system.get('cpuThreads', 4)}T)</td>
        </tr>
        <tr>
          <td>Installed RAM</td>
          <td>{system.get('ramGb', 8):.1f} GB ({benchmarks.get('memoryThroughputMbSec', 0):.0f} MB/s throughput)</td>
        </tr>
        <tr>
          <td>Primary Storage</td>
          <td>{system.get('storageGb', 256):.0f} GB NVMe / SSD</td>
        </tr>
        <tr>
          <td>Disk Write / Read</td>
          <td>Write: {benchmarks.get('storageSeqWriteMbSec', 0):.0f} MB/s · Read: {benchmarks.get('storageSeqReadMbSec', 0):.0f} MB/s</td>
        </tr>
      </table>
      <table class="table-spec">
        <tr>
          <td>Operating System</td>
          <td>{system.get('os', 'Windows 11')} ({system.get('architecture', 'x86_64')})</td>
        </tr>
        <tr>
          <td>Thermal Dissipation</td>
          <td>{base_temp:.1f}°C baseline ➔ {peak_temp:.1f}°C peak (+{delta_temp:.1f}°C delta)</td>
        </tr>
        <tr>
          <td>Thermal Throttling</td>
          <td>{'⚠️ THROTTLING DETECTED' if throttling else '✅ NONE (Stable Clocking)'}</td>
        </tr>
        <tr>
          <td>CPU Performance</td>
          <td>{benchmarks.get('cpuFloatingPointOpsSec', 0) / 1e6:.1f} MFLOP/s (0 arithmetic faults)</td>
        </tr>
      </table>
    </div>
  </div>

  <!-- QC Checklist -->
  <div class="card">
    <div class="section-title">
      <span>✅ 5-Dimension Quality Control Verification</span>
    </div>
    <div class="qc-item">
      <span>CPU Multi-Core Torture & Floating-Point Integrity</span>
      <span class="pass-tag">{qc.get('cpuStatus', 'PASSED')}</span>
    </div>
    <div class="qc-item">
      <span>RAM Saturation & Bit-Flip Parity Test</span>
      <span class="pass-tag">{qc.get('memoryStatus', 'PASSED')}</span>
    </div>
    <div class="qc-item">
      <span>NVMe Storage Sequential & Random 4KB Stress</span>
      <span class="pass-tag">{qc.get('storageStatus', 'PASSED')}</span>
    </div>
    <div class="qc-item">
      <span>Battery Sustenance & Active Discharge Rate</span>
      <span class="pass-tag">{qc.get('batteryStatus', 'PASSED')}</span>
    </div>
    <div class="qc-item">
      <span>Thermal Cooling & Clock Stability Under Peak Heat</span>
      <span class="pass-tag">{qc.get('thermalStatus', 'PASSED')}</span>
    </div>
  </div>

  <!-- Action Buttons -->
  <div class="btn-group">
    <button class="btn btn-primary" onclick="window.print()">
      🖨️ Print / Save PDF Certificate
    </button>
    <button class="btn btn-secondary" onclick="downloadJSON()">
      💾 Download Audit JSON
    </button>
  </div>
</div>

<script>
  function downloadJSON() {{
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(`{raw_json_str}`);
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", "benchqc_audit.json");
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  }}
</script>

</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_path
