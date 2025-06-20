
#!/usr/bin/env python3
import subprocess
import sys
import os
import threading
import time
from pathlib import Path

def run_service(name, port, script_path, working_dir=None):
    """Run a service in a separate thread"""
    def service_runner():
        try:
            if working_dir:
                os.chdir(working_dir)
            print(f"🚀 Starting {name} on port {port}...")
            subprocess.run([sys.executable, script_path], check=True)
        except Exception as e:
            print(f"❌ Failed to start {name}: {e}")
    
    thread = threading.Thread(target=service_runner, daemon=True)
    thread.start()
    return thread

def main():
    print("🔧 SOGUM AI Service Manager - Starting All Services")
    print("=" * 60)
    
    # Start all microservices
    services = []
    
    # OCR Service (port 8080)
    services.append(run_service("OCR Service", 8080, "services/ocr-service/app/main.py"))
    time.sleep(2)
    
    # DocETL (port 5000 - changed to 5001 to avoid conflict)
    services.append(run_service("DocETL", 5001, "services/docetl/src/main.py"))
    time.sleep(2)
    
    # File Organizer (port 4000)
    services.append(run_service("File Organizer", 4000, "services/local_file_organizer/app/main.py"))
    time.sleep(2)
    
    # AnythingLLM (port 3001)
    services.append(run_service("AnythingLLM", 3001, "services/anything-llm/server.js"))
    time.sleep(2)
    
    # JSON Crack (port 3000)
    services.append(run_service("JSON Crack", 3000, "services/json-crack/build/main.py"))
    time.sleep(2)
    
    # LocalSend (port 5050)
    services.append(run_service("LocalSend", 5050, "services/local-send/app/main.py"))
    time.sleep(2)
    
    # Pake (port 8081)
    services.append(run_service("Pake", 8081, "services/pake/server/main.py"))
    time.sleep(2)
    
    # Kestra (port 8082)
    services.append(run_service("Kestra", 8082, "services/kestra-windmill/kestra/main.py"))
    time.sleep(2)
    
    # Windmill (port 7780)
    services.append(run_service("Windmill", 7780, "services/kestra-windmill/windmill/main.py"))
    time.sleep(2)
    
    print("\n✅ All services started!")
    print("🌐 Dashboard available at http://0.0.0.0:5000")
    print("📊 Services will be available on their respective ports")
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")

if __name__ == "__main__":
    main()
