# mikiri-bench

Benchmark suite for [Mikiri](https://mikiri.dev) — measures detection quality across Python web apps with known performance anti-patterns.

## Quick start

```bash
# Prerequisites: mikiri CLI, Docker, Python 3.11+

# Run all cases
./run.sh

# Run a single case
./run.sh cases/fastapi-n-plus-1

# Score results against ground truth
python score.py
```

## Cases

| Case | Framework | DB | Anti-pattern |
|---|---|---|---|
| `fastapi-n-plus-1` | FastAPI (async) | PostgreSQL | N+1 lazy loading |
| `fastapi-sync-n-plus-1` | FastAPI (sync) | PostgreSQL | N+1 lazy loading |
| `django-n-plus-1` | Django | SQLite | N+1 missing prefetch_related |
| `flask-n-plus-1` | Flask | SQLite | N+1 lazy loading |

Each case has a `manifest.json` with ground-truth issues that Mikiri should detect.

## Scoring

`score.py` compares Mikiri's `--json` output against each case's `manifest.json`:

- **Detection rate** — did Mikiri find the known issues? (`TP / (TP + FN)`)
- **Severity accuracy** — did it rate severity correctly?
- **Actionability** — does the suggested fix address the root cause? (manual review)

## Adding a case

1. Create a directory under `cases/` with the app code
2. Write a `manifest.json` with ground-truth issues
3. Ensure `seed.py` populates enough data to make the anti-pattern observable
4. Use `random.seed(42)` for deterministic seeding
5. Test: `./run.sh cases/your-new-case`

## Structure

```
cases/<name>/
├── app.py              # the buggy application
├── models.py           # ORM models
├── seed.py             # data population script
├── requirements.txt    # Python dependencies
└── manifest.json       # ground truth (expected issues)
```
