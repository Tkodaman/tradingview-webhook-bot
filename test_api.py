import subprocess
import time
import urllib.request
import urllib.error

# Start server
proc = subprocess.Popen(["python", "main.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Wait for server to start
time.sleep(5)

try:
    req = urllib.request.Request("http://localhost:8000/api/positions/active")
    with urllib.request.urlopen(req) as response:
        print("Response:", response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code, e.reason)
    print("Response Body:", e.read().decode('utf-8'))
except Exception as e:
    print("Error:", e)

# terminate
proc.terminate()
print("STDOUT:", proc.stdout.read().decode('utf-8', errors='ignore')[:1000])
print("STDERR:", proc.stderr.read().decode('utf-8', errors='ignore')[:1000])
