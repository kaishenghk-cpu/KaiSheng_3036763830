"""Run from any working directory: python path/to/code/run_all.py."""
from pathlib import Path
from analysis import run

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    results = run(root)
    try:
        from build_report import build
    except ModuleNotFoundError as exc:
        if exc.name != 'build_report':
            raise
        print('Analysis complete; report builder not yet present.')
    else:
        build(root, results)
        print('Complete: Tables 2-4, Figure 1, extension, validation and report.pdf')
