#!/usr/bin/env python3
"""Generate a static HTML dashboard from bench history."""
import json
import sys
from pathlib import Path

MODEL_COLORS = {
    "gpt-5.3-codex-xhigh": ("#22c55e", "rgba(34, 197, 94, 0.1)"),
    "claude-opus-4-6": ("#f97316", "rgba(249, 115, 22, 0.1)"),
    "glm-5": ("#3b82f6", "rgba(59, 130, 246, 0.1)"),
}
FALLBACK_COLORS = [
    ("#a855f7", "rgba(168, 85, 247, 0.1)"),
    ("#ec4899", "rgba(236, 72, 153, 0.1)"),
    ("#14b8a6", "rgba(20, 184, 166, 0.1)"),
    ("#eab308", "rgba(234, 179, 8, 0.1)"),
]

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
  h2 { font-size: 1.1rem; margin: 2rem 0 1rem; }
  table { width: 100%; border-collapse: collapse; background: #161616; border: 1px solid #222; border-radius: 8px; overflow: hidden; margin-bottom: 1.5rem; }
  th, td { text-align: left; padding: 0.75rem 1rem; border-bottom: 1px solid #1a1a1a; }
  th { color: #888; font-weight: 500; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; }
  td { font-size: 0.9rem; }
  .badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.8rem; font-weight: 500; }
  .badge-green { background: #052e16; color: #22c55e; }
  .badge-red { background: #2a0a0a; color: #ef4444; }
  .badge-gray { background: #1a1a1a; color: #888; }
  .model-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 0.5rem; vertical-align: middle; }
  footer { margin-top: 2rem; color: #555; font-size: 0.8rem; }
</style>
</head>
<body>
<h1>mikiri-bench</h1>
<p class="subtitle">Detection quality tracking for <a href="https://mikiri.dev">Mikiri</a></p>

<div class="stats">
  <div class="stat">
    <div class="stat-value">{models_count}</div>
    <div class="stat-label">Models</div>
  </div>
  <div class="stat">
    <div class="stat-value">{cases_count}</div>
    <div class="stat-label">Cases</div>
  </div>
  <div class="stat">
    <div class="stat-value">{total_issues}</div>
    <div class="stat-label">Issues per model</div>
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

{model_tables}

<footer>
  Updated {last_run} &middot; Run #{run_number}
</footer>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script>
const history = {history_json};
const models = Object.keys(history);

// Collect all unique dates across models
const allDates = [...new Set(models.flatMap(m => history[m].map(e => e.date)))].sort();

const datasets = models.map((model, i) => {{
  const colors = {colors_json};
  const [borderColor, bgColor] = colors[model] || colors._fallback[i % colors._fallback.length];

  // Map model entries to date-aligned data
  const dateMap = {{}};
  history[model].forEach(e => {{ dateMap[e.date] = (e.detection_rate * 100).toFixed(1); }});
  const data = allDates.map(d => dateMap[d] ?? null);

  return {{
    label: model,
    data,
    borderColor,
    backgroundColor: bgColor,
    fill: false,
    tension: 0.3,
    pointRadius: 3,
    pointBackgroundColor: borderColor,
    spanGaps: true,
  }};
}});

new Chart(document.getElementById('chart'), {{
  type: 'line',
  data: {{ labels: allDates, datasets }},
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
      legend: {{
        display: true,
        labels: {{ color: '#ccc', usePointStyle: true, pointStyle: 'circle' }},
      }},
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

    # history is { model: [ {date, ...}, ... ] }
    models = sorted(history.keys())
    if not models:
        print("No model data yet")
        return

    # Find the latest entry across all models
    last_run = "unknown"
    run_number = "?"
    for model in models:
        if history[model]:
            entry = history[model][-1]
            last_run = entry.get("date", last_run)
            run_number = entry.get("run_number", run_number)

    # Count cases from any model's latest run
    cases_count = 0
    total_issues = 0
    for model in models:
        if history[model]:
            latest = history[model][-1]
            cases_count = max(cases_count, len(latest.get("cases", [])))
            total_issues = max(total_issues, latest.get("total_issues", 0))

    # Build per-model tables
    model_tables = []
    for model in models:
        if not history[model]:
            continue
        latest = history[model][-1]
        rate = latest.get("detection_rate", 0) * 100
        color = MODEL_COLORS.get(model, ("#888", ""))[0]

        rows = []
        for case in latest.get("cases", []):
            if case["missed"] == 0 and case["status"] == "ok":
                badge = '<span class="badge badge-green">PASS</span>'
            elif case["status"] == "no_result":
                badge = '<span class="badge badge-gray">NO DATA</span>'
            else:
                badge = '<span class="badge badge-red">PARTIAL</span>'
            rows.append(
                f'<tr><td>{case["case"]}</td><td>{case["total"]}</td>'
                f'<td>{case["detected"]}</td><td>{case["missed"]}</td>'
                f"<td>{badge}</td></tr>"
            )

        model_tables.append(
            f'<h2><span class="model-dot" style="background:{color}"></span>'
            f"{model} — {rate:.0f}%</h2>\n"
            f"<table><thead><tr><th>Case</th><th>Issues</th><th>Found</th>"
            f"<th>Missed</th><th>Status</th></tr></thead><tbody>\n"
            + "\n".join(rows)
            + "\n</tbody></table>"
        )

    # Build colors map for JS
    colors_map = {m: list(c) for m, c in MODEL_COLORS.items()}
    colors_map["_fallback"] = [list(c) for c in FALLBACK_COLORS]

    html = TEMPLATE.format(
        models_count=len(models),
        cases_count=cases_count,
        total_issues=total_issues,
        last_run=last_run,
        run_number=run_number,
        model_tables="\n".join(model_tables),
        history_json=json.dumps(history),
        colors_json=json.dumps(colors_map),
    )

    Path(output_path).write_text(html)
    print(f"Dashboard written to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <history.json> <output.html>")
        sys.exit(1)
    generate(sys.argv[1], sys.argv[2])
