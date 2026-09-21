import subprocess
import sys
import os
import time
import signal

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_HTML_DIR = os.path.join(ROOT_DIR, "frontend-html")

processes = []

def cleanup(signum=None, frame=None):
    print("\n[AgriGo] Stopping all services...")
    for p in processes:
        try:
            if sys.platform == "win32":
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                p.terminate()
        except Exception:
            pass
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def free_ports():
    if sys.platform == "win32":
        for port in [8000, 3000]:
            try:
                cmd = f"Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}"
                subprocess.call(["powershell", "-NoProfile", "-Command", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

def main():
    print("=" * 65)
    print("   AgriGo — Pure Agricultural AI Platform (Python + HTML/CSS/JS)")
    print("=" * 65)
    
    free_ports()

    # Start Python FastAPI Backend (Serves pure HTML/CSS/JS frontend directly at root /)
    print("\n[*] Starting AgriGo Agricultural Server on http://127.0.0.1:8000 ...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
        cwd=BACKEND_DIR
    )
    processes.append(backend_proc)

    time.sleep(1.5)

    print("\n" + "=" * 65)
    print("  AgriGo Agricultural Services are LIVE!")
    print("=" * 65)
    print("  * Unified Gateway:         http://127.0.0.1:8000/")
    print("  * Farmer AI Companion:     http://127.0.0.1:8000/farmer.html")
    print("  * Material 3 Weather Hub:  http://127.0.0.1:8000/weather.html")
    print("  * Smart Reminder Dashboard http://127.0.0.1:8000/reminders.html")
    print("  * Admin Mission Control:   http://127.0.0.1:8000/admin.html")
    print("  * Swagger API Docs:        http://127.0.0.1:8000/docs")
    print("  * Health Check Endpoint:   http://127.0.0.1:8000/health")
    print("=" * 65)
    print("  Zero Node.js dependency. Purely Python + HTML/CSS/JavaScript.")
    print("  Press Ctrl + C anytime to stop.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
