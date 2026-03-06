#!/usr/bin/env python3
"""Generate a static HTML dashboard from bench history."""
import json
import sys
from pathlib import Path

TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>mikiri-bench</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0a0a0a; color: #e0e0e0; padding: 2rem; }
  h1 { font-size: 1.5rem; margin-bottom: 0.25rem; }
  .subtitle { color: #888; margin-bottom: 2rem; font-size: 0.9rem; }
  .subtitle a { color: #888; }
  .stats { display: flex; gap: 2rem; margin-bottom: 2rem; flex-wrap: wrap; }
  .stat { background: #161616; border: 1px solid #222; border-radius: 8px; padding: 1.25rem 1.5rem; min-width: 180px; }
  .stat-value { font-size: 2rem; font-weight: 700; }
  .stat-value.green { color: #22c55e; }
  .stat-value.yellow { color: #eab308; }
  .stat-value.red { color: #ef4444; }
  .stat-label { color: #888; font-size: 0.85rem; margin-top: 0.25rem; }
  .chart-container { background: #161616; border: 1px solid #222; border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem; }
  .chart-title { font-size: 0.95rem; font-weight: 600; margin-bottom: 1rem; }
  canvas { width: 100% !important; max-height: 300px; }
  table { width: 100%; border-collapse: collapse; background: #161616; border: 1px solid #222; border-radius: 8px; overflow: hidden; }
  th, td { text-align: left; padding: 0.75rem 1rem; border-bottom: 1px solid #1a1a1a; }
  th { color: #888; font-weight: 500; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; }
  td { font-size: 0.9rem; }
  .badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.8rem; font-weight: 500; }
  .badge-green { background: #052e16; color: #22c55e; }
  .badge-red { background: #2a0a0a; color: #ef4444; }
  .badge-gray { background: #1a1a1a; color: #888; }
  footer { margin-top: 2rem; color: #555; font-size: 0.8rem; }
</style>
</head>
<body>
<h1>mikiri-bench</h1>
<p class="subtitle">Detection quality tracking for <a href="https://mikiri.dev">Mikiri</a></p>

<div class="stats">
  <div class="stat">
    <div class="stat-value {rate_class}">{detection_rate}</div>
    <div class="stat-label">Detection rate</div>
  </div>
  <div class="stat">
    <div class="stat-value">{detected}/{total}</div>
    <div class="stat-label">Issues found</div>
  </div>
  <div class="stat">
    <div class="stat-value">{cases}</div>
    <div class="stat-label">Cases</div>
  </div>
  <div class="stat">
    <div class="stat-value">{last_run}</div>
    <div class="stat-label">Last run</div>
  </div>
</div>

<div class="chart-container">
  <div class="chart-title">Detection rate over time</div>
  <canvas id="chart"></canvas>
</div>

<table>
  <thead>
    <tr><th>Case</th><th>Issues</th><th>Found</th><th>Missed</th><th>Status</th></tr>
  </thead>
  <tbody>
    {case_rows}
  </tbody>
</table>

<footer>
  Updated {last_run} &middot; Run #{run_number}
</footer>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script>
const history = {history_json};
const labels = history.map(h => h.date);
const rates = history.map(h => (h.detection_rate * 100).toFixed(1));

new Chart(document.getElementById('chart'), {{
  type: 'line',
  data: {{
    labels,
    datasets: [{{
      label: 'Detection rate (%)',
      data: rates,
      borderColor: '#22c55e',
      backgroundColor: 'rgba(34, 197, 94, 0.1)',
      fill: true,
      tension: 0.3,
      pointRadius: 3,
      pointBackgroundColor: '#22c55e',
    }}]
  }},
  options: {{
    responsive: true,
    scales: {{
      y: {{
        min: 0,
        max: 100,
        ticks: {{ color: '#888', callback: v => v + '%' }},
        grid: {{ color: '#1a1a1a' }},
      }},
      x: {{
        ticks: {{ color: '#888', maxTicksLimit: 15 }},
        grid: {{ color: '#1a1a1a' }},
      }}
    }},
    plugins: {{
      legend: {{ display: false }},
    }}
  }}
}});
</script>
</body>
</html>
"""


def generate(history_path: str, output_path: str):
    with open(history_path) as f:
        history = json.load(f)

    if not history:
        print("No history data yet")
        return

    latest = history[-1]
    total = latest["total_issues"]
    detected = latest["total_detected"]
    rate = latest["detection_rate"] * 100
    cases = len(latest.get("cases", []))
    last_run = latest.get("date", "unknown")
    run_number = latest.get("run_number", "?")

    if rate >= 80:
        rate_class = "green"
    elif rate >= 50:
        rate_class = "yellow"
    else:
        rate_class = "red"

    # Build case rows from latest run
    case_rows = []
    for case in latest.get("cases", []):
        if case["missed"] == 0 and case["status"] == "ok":
            badge = '<span class="badge badge-green">PASS</span>'
        elif case["status"] == "no_result":
            badge = '<span class="badge badge-gray">NO DATA</span>'
        else:
            badge = '<span class="badge badge-red">PARTIAL</span>'

        case_rows.append(
            f'<tr><td>{case["case"]}</td><td>{case["total"]}</td>'
            f'<td>{case["detected"]}</td><td>{case["missed"]}</td>'
            f"<td>{badge}</td></tr>"
        )

    html = TEMPLATE.format(
        detection_rate=f"{rate:.0f}%",
        rate_class=rate_class,
        detected=detected,
        total=total,
        cases=cases,
        last_run=last_run,
        run_number=run_number,
        case_rows="\n    ".join(case_rows),
        history_json=json.dumps(history),
    )

    Path(output_path).write_text(html)
    print(f"Dashboard written to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <history.json> <output.html>")
        sys.exit(1)
    generate(sys.argv[1], sys.argv[2])
