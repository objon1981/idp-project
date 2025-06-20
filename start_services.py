
#!/usr/bin/env python3
"""
Service Startup Helper for SOGUM AI Platform
"""
import subprocess
import sys
import os
import time
from pathlib import Path

def start_email_router():
    """Start the email router service"""
    service_path = Path("services/email-router-service")
    if not service_path.exists():
        print("❌ Email router service directory not found")
        return False
    
    print("🚀 Starting Email Router Service...")
    try:
        # Change to service directory and run
        os.chdir(service_path)
        subprocess.Popen([sys.executable, "main.py"])
        print("✅ Email Router Service started on port 5001")
        return True
    except Exception as e:
        print(f"❌ Failed to start Email Router Service: {e}")
        return False

def main():
    print("🔧 SOGUM AI Service Manager")
    print("=" * 40)
    
    print("Available services to start:")
    print("1. Email Router Service (port 5001)")
    print("\nNote: Other services require their dependencies to be installed.")
    print("For now, starting Email Router as an example...")
    
    if start_email_router():
        print("\n✅ Service started successfully!")
        print("You can now test the service in the dashboard.")
    else:
        print("\n❌ Failed to start services.")
        print("Please check the service configurations.")

if __name__ == "__main__":
    main()
