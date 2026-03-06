#!/usr/bin/env bash
set -euo pipefail

BENCH_DIR="$(cd "$(dirname "$0")" && pwd)"
RESULTS_DIR="$BENCH_DIR/results"
mkdir -p "$RESULTS_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

# If a specific case is passed, run only that one
if [[ $# -gt 0 ]]; then
  CASES=("$@")
else
  CASES=("$BENCH_DIR"/cases/*)
fi

PG_CONTAINER="mikiri-bench-pg"
PG_RUNNING=false

start_postgres() {
  if $PG_RUNNING; then return; fi
  echo -e "${YELLOW}Starting PostgreSQL...${NC}"
  docker run -d --rm \
    --name "$PG_CONTAINER" \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=test \
    -e POSTGRES_DB=test \
    -p 5432:5432 \
    postgres:16-alpine \
    >/dev/null 2>&1 || true

  # Wait for readiness
  for i in $(seq 1 30); do
    if docker exec "$PG_CONTAINER" pg_isready -U postgres >/dev/null 2>&1; then
      PG_RUNNING=true
      echo -e "${GREEN}PostgreSQL ready${NC}"
      return
    fi
    sleep 1
  done
  echo -e "${RED}PostgreSQL failed to start${NC}"
  exit 1
}

stop_postgres() {
  if $PG_RUNNING; then
    echo -e "${YELLOW}Stopping PostgreSQL...${NC}"
    docker stop "$PG_CONTAINER" >/dev/null 2>&1 || true
    PG_RUNNING=false
  fi
}

cleanup() {
  stop_postgres
}
trap cleanup EXIT

total=0
passed=0
failed=0

for case_dir in "${CASES[@]}"; do
  case_dir="${case_dir%/}"  # strip trailing slash
  if [[ ! -f "$case_dir/manifest.json" ]]; then
    echo -e "${RED}Skipping $case_dir (no manifest.json)${NC}"
    continue
  fi

  case_name="$(basename "$case_dir")"
  echo ""
  echo -e "${BOLD}━━━ $case_name ━━━${NC}"
  total=$((total + 1))

  # Read manifest
  db=$(python3 -c "import json; print(json.load(open('$case_dir/manifest.json'))['db'])")
  seed_cmd=$(python3 -c "import json; print(json.load(open('$case_dir/manifest.json'))['seed'])")

  # Start PostgreSQL if needed
  if [[ "$db" == "postgresql" ]]; then
    start_postgres
    # Reset the database
    docker exec "$PG_CONTAINER" psql -U postgres -c "DROP DATABASE IF EXISTS test;" >/dev/null 2>&1
    docker exec "$PG_CONTAINER" psql -U postgres -c "CREATE DATABASE test;" >/dev/null 2>&1
  fi

  # Set up virtualenv
  if [[ ! -d "$case_dir/.venv" ]]; then
    echo "  Creating virtualenv..."
    python3 -m venv "$case_dir/.venv"
    "$case_dir/.venv/bin/pip" install -q -r "$case_dir/requirements.txt"
  fi

  # Seed
  echo "  Seeding database..."
  (cd "$case_dir" && .venv/bin/python seed.py)

  # Run mikiri
  result_dir="$RESULTS_DIR/$case_name"
  mkdir -p "$result_dir"

  echo "  Running mikiri..."
  if (cd "$case_dir" && mikiri run --json > "$result_dir/output.json" 2>"$result_dir/stderr.log"); then
    echo -e "  ${GREEN}OK${NC}"

    # Copy the report if generated
    if [[ -f "$case_dir/mikiri_report.md" ]]; then
      cp "$case_dir/mikiri_report.md" "$result_dir/report.md"
    fi

    passed=$((passed + 1))
  else
    echo -e "  ${RED}FAILED${NC} (exit code $?)"
    failed=$((failed + 1))
  fi
done

echo ""
echo -e "${BOLD}━━━ Summary ━━━${NC}"
echo -e "  Total:  $total"
echo -e "  ${GREEN}Passed: $passed${NC}"
if [[ $failed -gt 0 ]]; then
  echo -e "  ${RED}Failed: $failed${NC}"
fi
echo ""
echo "Results saved to $RESULTS_DIR/"
echo "Run 'python score.py' to evaluate detection accuracy."
