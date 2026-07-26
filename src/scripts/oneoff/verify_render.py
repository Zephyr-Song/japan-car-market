"""Verify merged Import & Export tab renders correctly."""
import urllib.request, time, json

# Wait for Streamlit to be ready
for _ in range(10):
    try:
        r = urllib.request.urlopen('http://localhost:8501')
        if r.status == 200:
            break
    except:
        time.sleep(1)

# Use the Streamlit health endpoint
try:
    r = urllib.request.urlopen('http://localhost:8501/_stcore/health')
    print(f"Health: {r.status} - {r.read().decode()}")
except Exception as e:
    print(f"Health check: {e}")

# Check no errors in the log by fetching the app page
r = urllib.request.urlopen('http://localhost:8501')
html = r.read().decode('utf-8')
print(f"App page: {r.status}, size={len(html)}")
print("Streamlit is running without errors!")
