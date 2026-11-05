"""Run the data/RFM pipeline followed by the segmentation experiment."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    subprocess.run([sys.executable, str(ROOT / "scripts/run_pipeline.py")], check=True, cwd=ROOT)
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/run_segmentation.py"),
            "--expected-rows",
            "234359",
        ],
        check=True,
        cwd=ROOT,
    )
