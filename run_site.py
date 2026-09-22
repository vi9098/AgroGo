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

def get_local_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def start_tunnel():
    cloudflared_bin = os.path.join(BACKEND_DIR, "cloudflared.exe")
    if os.path.exists(cloudflared_bin):
        print("\n[*] Starting Cloudflare Secure Mobile Tunnel...")
        tunnel_proc = subprocess.Popen(
            [cloudflared_bin, "tunnel", "--url", "http://127.0.0.1:8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=BACKEND_DIR
        )
        processes.append(tunnel_proc)
        
        import re, threading
        def monitor_tunnel():
            pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
            for line in iter(tunnel_proc.stdout.readline, ''):
                match = pattern.search(line)
                if match:
                    tunnel_url = match.group(0)
                    print("\n" + "=" * 65)
                    print("  🌐 PUBLIC MOBILE INTERNET LINK (Open from ANY Phone!):")
                    print(f"  👉 Farmer Companion: {tunnel_url}/farmer.html")
                    print(f"  👉 Admin Control:    {tunnel_url}/admin.html")
                    print("=" * 65 + "\n")
                    try:
                        with open(os.path.join(ROOT_DIR, "mobile_link.txt"), "w", encoding="utf-8") as f:
                            f.write(f"Farmer Portal: {tunnel_url}/farmer.html\nAdmin Portal: {tunnel_url}/admin.html\n")
                    except Exception:
                        pass
                    break
        t = threading.Thread(target=monitor_tunnel, daemon=True)
        t.start()

def main():
    print("=" * 65)
    print("   AgriGo — Pure Agricultural AI Platform (Python + HTML/CSS/JS)")
    print("=" * 65)
    
    free_ports()

    # Start Python FastAPI Backend (Serves pure HTML/CSS/JS frontend directly at root /)
    print("\n[*] Starting AgriGo Agricultural Server on http://0.0.0.0:8000 ...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=BACKEND_DIR
    )
    processes.append(backend_proc)

    time.sleep(1.5)
    local_ip = get_local_ip()

    print("\n" + "=" * 65)
    print("  AgriGo Agricultural Services are LIVE!")
    print("=" * 65)
    print(f"  * Unified Gateway:         http://127.0.0.1:8000/")
    print(f"  * Farmer AI Companion:     http://127.0.0.1:8000/farmer.html")
    print(f"  * Wi-Fi Mobile Link:       http://{local_ip}:8000/farmer.html")
    print(f"  * Material 3 Weather Hub:  http://127.0.0.1:8000/weather.html")
    print(f"  * Smart Reminder Dashboard http://127.0.0.1:8000/reminders.html")
    print(f"  * Admin Mission Control:   http://127.0.0.1:8000/admin.html")
    print(f"  * Swagger API Docs:        http://127.0.0.1:8000/docs")
    print(f"  * Health Check Endpoint:   http://127.0.0.1:8000/health")
    print("=" * 65)
    print("  Zero Node.js dependency. Purely Python + HTML/CSS/JavaScript.")
    print("  Press Ctrl + C anytime to stop.\n")

    # Start Cloudflare Mobile Tunnel
    start_tunnel()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
