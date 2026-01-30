import socket

def check_port(host, port):
    print(f"Checking {host}:{port}...", end=" ")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect((host, port))
        print("OPEN ✅")
        s.close()
        return True
    except Exception as e:
        print(f"CLOSED ❌ ({e})")
        return False

print("--- Network Diagnostic ---")
check_port("127.0.0.1", 27017)
check_port("localhost", 27017)
check_port("::1", 27017)
