"""Run the whole pipeline end to end: generate -> clean -> db -> queries -> report -> review gate."""
import subprocess
import sys

for script in ["generate_dataset.py", "clean_data.py", "build_db.py", "queries.py",
               "draft_report.py"]:
    print(f"\n{'=' * 8} {script} {'=' * 8}", flush=True)
    subprocess.run([sys.executable, script], check=True)
print("\nPipeline complete. Next: python3 review_gate.py --review  (human sign-off), then streamlit run app.py")
