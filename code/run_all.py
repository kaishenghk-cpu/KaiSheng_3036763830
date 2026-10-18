"""Run from any working directory: python path/to/code/run_all.py."""
from pathlib import Path
from analysis import run
from build_report import build

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    results = run(root)
    build(root, results)
    print('Complete: Tables 2-4, Figure 1, extension, validation and report.pdf')
