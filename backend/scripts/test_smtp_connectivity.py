import os
import smtplib
import socket
from dotenv import load_dotenv
from pathlib import Path

# Load env from root
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)

def test_smtp():
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")

    print(f"--- SMTP Diagnostic ---")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"User: {user}")
    print(f"Password set: {'Yes' if password else 'No'}")
    print("-" * 25)

    if not all([host, user, password]):
        print("ERROR: Missing SMTP configuration in .env")
        return

    # 1. DNS check
    try:
        ip = socket.gethostbyname(host)
        print(f"1. DNS Resolve: SUCCESS (IP: {ip})")
    except socket.gaierror as e:
        print(f"1. DNS Resolve: FAILED ({e})")
        print("   Check if SMTP_HOST is correct (e.g., smtp.gmail.com).")
        return

    # 2. Connection check
    try:
        print(f"2. Connecting to {host}:{port}...")
        server = smtplib.SMTP(host, port, timeout=10)
        print("   Connection: SUCCESS")
        
        # 3. TLS check
        try:
            print("3. Starting TLS...")
            server.starttls()
            print("   TLS: SUCCESS")
        except Exception as e:
            print(f"   TLS: FAILED ({e})")
            server.quit()
            return

        # 4. Login check
        try:
            print(f"4. Attempting Login for {user}...")
            server.login(user, password)
            print("   Login: SUCCESS")
        except smtplib.SMTPAuthenticationError:
            print("   Login: FAILED (Authentication Error)")
            print("   Check your password. If using Gmail, you MUST use an 'App Password'.")
        except Exception as e:
            print(f"   Login: FAILED ({e})")
        
        server.quit()
    except Exception as e:
        print(f"2. Connection: FAILED ({e})")

if __name__ == "__main__":
    test_smtp()
