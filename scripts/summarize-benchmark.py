"""Generate a reviewable main summary; never push or merge automatically."""
import argparse
from pathlib import Path
from benchmark_support import read, validate_operator


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifests", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    rows = ["# Benchmark results", "", "Pilot은 순위 통계에서 제외한다. completed는 프로세스 종료 상태이며 제품 합격을 뜻하지 않는다.", "",
            "| Run | Phase | State | Model | Seconds | Tokens | Build | Hardware | Implementation |",
            "|---|---|---|---|---:|---:|---|---|---|"]
    def cell(value):
        return "미측정" if value is None else str(value).replace("|", "\\|").replace("\n", " ")
    for path in args.manifests:
        m = read(path)
        validate_operator(m)
        values = (m["run_id"], m["operator"]["phase"], m["operator"]["status"], m["agent"]["model"],
                  m["measurement"]["wall_clock_seconds"], m["measurement"]["tokens"]["total"],
                  m["outputs"]["build_status"], m["outputs"]["hardware_verification_status"], m["outputs"]["implementation_commit"])
        rows.append("| " + " | ".join(map(cell, values)) + " |")
    # Exclusive creation prevents accidentally replacing a reviewed result index.
    with args.output.open("x", encoding="utf-8") as f:
        f.write("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
