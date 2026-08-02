import mlflow
import sqlite3
import os
from urllib.parse import urlparse

uri = mlflow.get_tracking_uri()
print(f"MLflow tracking URI: {uri}")

# Parse sqlite URI
parsed = urlparse(uri)
if parsed.scheme == "sqlite":
    db_path = parsed.path.lstrip("/")
    print(f"Parsed DB path: {db_path}")
else:
    db_path = os.path.join(os.path.dirname(__file__), "mlflow.db")
    print(f"Fallback DB path: {db_path}")

# End active runs via MLflow API
try:
    active = mlflow.active_run()
    while active:
        print(f"Ending active run via API: {active.info.run_id}")
        mlflow.end_run()
        active = mlflow.active_run()
    print("No more active runs (API)")
except Exception as e:
    print(f"API error: {e}")

# Direct DB cleanup
try:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cur.fetchall()]
    print(f"Tables: {tables}")

    if "runs" in tables:
        cur.execute("SELECT run_uuid, experiment_id, status, start_time FROM runs ORDER BY start_time DESC")
        runs = cur.fetchall()
        print(f"Runs ({len(runs)}):")
        for r in runs:
            print(f"  {r[0]} | experiment={r[1]} | status={r[2]} | start={r[3]}")

        cur.execute("UPDATE runs SET status='FINISHED' WHERE status='RUNNING'")
        print(f"Set {cur.rowcount} runs to FINISHED")
    
    if "experiments" in tables:
        # Check for active experiments
        cur.execute("SELECT experiment_id, name, lifecycle_stage, artifact_location FROM experiments")
        experiments = cur.fetchall()
        print(f"Experiments ({len(experiments)}):")
        for e in experiments:
            print(f"  {e[0]} | name={e[1]} | stage={e[2]} | location={e[3]}")

    conn.commit()
    conn.close()
except Exception as e:
    print(f"DB error: {e}")
