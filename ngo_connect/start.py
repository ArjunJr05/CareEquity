"""
start.py
--------
Launches both the FastAPI backend and the Streamlit frontend
as separate subprocesses and waits for Ctrl-C.

Usage:
    python start.py

Ports:
    FastAPI   → http://localhost:8000   (API + Swagger UI at /docs)
    Streamlit → http://localhost:8501   (frontend)

Environment variables:
    API_HOST    override FastAPI host   (default 0.0.0.0)
    API_PORT    override FastAPI port   (default 8000)
    ST_PORT     override Streamlit port (default 8501)
"""
import os
import sys
import time
import signal
import subprocess

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
ST_PORT  = int(os.getenv("ST_PORT",  "8501"))

ROOT = os.path.dirname(os.path.abspath(__file__))


def _run(cmd: list[str], name: str) -> subprocess.Popen:
    print(f"  Starting {name} …")
    return subprocess.Popen(
        cmd,
        cwd=ROOT,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


def main():
    print("=" * 55)
    print(" CareEquity — Starting all services")
    print("=" * 55)

    # 1. FastAPI backend
    api_proc = _run(
        [sys.executable, "-m", "uvicorn",
         "api.main:app",
         "--host", API_HOST,
         "--port", str(API_PORT),
         "--reload"],
        f"FastAPI  → http://localhost:{API_PORT}/docs",
    )

    # 2. Brief pause so API is ready before Streamlit loads
    time.sleep(2)

    # 3. Streamlit frontend
    st_proc = _run(
        [sys.executable, "-m", "streamlit", "run", "app.py",
         "--server.port", str(ST_PORT),
         "--server.headless", "true"],
        f"Streamlit → http://localhost:{ST_PORT}",
    )

    print()
    print(f"  FastAPI  docs : http://localhost:{API_PORT}/docs")
    print(f"  Streamlit app : http://localhost:{ST_PORT}")
    print()
    print("  Press Ctrl-C to stop both services.")
    print("=" * 55)

    # Wait — kill both on Ctrl-C or either process exiting
    def _shutdown(signum=None, frame=None):
        print("\nShutting down …")
        for p in (api_proc, st_proc):
            try:
                p.terminate()
            except Exception:
                pass
        sys.exit(0)

    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        while True:
            # If either process dies unexpectedly, shut everything down
            if api_proc.poll() is not None:
                print("FastAPI process exited unexpectedly.")
                _shutdown()
            if st_proc.poll() is not None:
                print("Streamlit process exited unexpectedly.")
                _shutdown()
            time.sleep(1)
    except KeyboardInterrupt:
        _shutdown()


if __name__ == "__main__":
    main()
