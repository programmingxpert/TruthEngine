#!/usr/bin/env python3
"""TruthEngine Unified Run Script.

Launches the PostgreSQL/SQLite database migration, backend API server (FastAPI),
and frontend development server (Vite) concurrently with a single command.
Automatically falls back to local SQLite if PostgreSQL is not running.
"""

import os
import sys
import time
import socket
import subprocess
import threading
from pathlib import Path


def is_postgres_running(host: str = "localhost", port: int = 5432) -> bool:
    """Check if PostgreSQL is running on the specified host and port."""
    try:
        with socket.create_connection((host, port), timeout=1.0) as s:
            return True
    except OSError:
        return False


def load_env_file(dotenv_path: Path):
    """Load variables from .env file into os.environ if not already set."""
    if not dotenv_path.exists():
        return
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key not in os.environ:
                    os.environ[key] = val


def stream_output(process, prefix: str):
    """Stream stdout/stderr from a subprocess with a prefix."""
    try:
        for line in iter(process.stdout.readline, ""):
            if line:
                sys.stdout.write(f"{prefix} | {line}")
                sys.stdout.flush()
    except Exception:
        pass


def main():
    root_dir = Path(__file__).parent.resolve()
    dotenv_path = root_dir / ".env"
    
    # 1. Load env file
    load_env_file(dotenv_path)

    # 2. Check and configure database url
    db_url = os.environ.get("TRUTHENGINE_DATABASE_URL", "")
    if not db_url or "localhost:5432" in db_url:
        print("Checking local database server status...")
        if not is_postgres_running():
            print("\n[DB CONFIG] WARNING: PostgreSQL is not running on localhost:5432.")
            print("[DB CONFIG] INFO: Falling back to a local SQLite database (truthengine.db) for development.")
            print("[DB CONFIG] INFO: To use PostgreSQL, start the service or run 'docker compose up db -d'.\n")
            os.environ["TRUTHENGINE_DATABASE_URL"] = "sqlite:///./truthengine.db"
        else:
            print("[DB CONFIG] Connected to PostgreSQL on localhost:5432.")

    # Pass the database URL to frontend Vite env if not set
    os.environ["VITE_API_URL"] = "http://localhost:8000"

    print("==================================================================")
    print("Starting TruthEngine Services...")
    print(f"Database URL: {os.environ.get('TRUTHENGINE_DATABASE_URL')}")
    print("==================================================================\n")

    # 3. Run Database Migrations
    print("Running database migrations...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=root_dir,
            env=os.environ,
            capture_output=True,
            text=True,
            check=True
        )
        print("Database migrations applied successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error applying database migrations:\n{e.stderr or e.stdout}")
        sys.exit(1)

    # 4. Start Backend API Server
    print("Starting Backend API (FastAPI) on port 8000...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "truthengine.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=root_dir,
        env=os.environ,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # 5. Start Frontend Dev Server
    print("Starting Frontend Dev Server (Vite) on port 5173...")
    frontend_dir = root_dir / "frontend"
    # Detect shell type for npm run
    shell = True if os.name == 'nt' else False
    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        env=os.environ,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        shell=shell
    )

    # 6. Stream outputs concurrently in daemon threads
    backend_thread = threading.Thread(
        target=stream_output, args=(backend_proc, "BACKEND"), daemon=True
    )
    frontend_thread = threading.Thread(
        target=stream_output, args=(frontend_proc, "FRONTEND"), daemon=True
    )
    
    backend_thread.start()
    frontend_thread.start()

    # 7. Monitor processes and catch keyboard interrupt
    try:
        while True:
            # Check if either process died unexpectedly
            if backend_proc.poll() is not None:
                print("Backend process terminated unexpectedly.")
                break
            if frontend_proc.poll() is not None:
                print("Frontend process terminated unexpectedly.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping TruthEngine services...")
    finally:
        # Gracefully terminate both processes
        for proc, name in [(backend_proc, "Backend"), (frontend_proc, "Frontend")]:
            if proc.poll() is None:
                print(f"Terminating {name}...")
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    print(f"Force-killing {name}...")
                    proc.kill()
                    proc.wait()
        print("All services stopped. Goodbye!")


if __name__ == "__main__":
    main()
