"""Runs the whole pipeline: ingest, then transform and load."""
import subprocess
import sys


def run(script, *args):
    print(f"\n{'=' * 60}\nRunning {script}\n{'=' * 60}")
    result = subprocess.run([sys.executable, script, *args])
    if result.returncode != 0:
        print(f"{script} failed with exit code {result.returncode}")
        sys.exit(result.returncode)


if __name__ == "__main__":
    run("src/ingest.py")
    run("src/transform_load.py", *sys.argv[1:])
    print("\nPipeline complete.")
