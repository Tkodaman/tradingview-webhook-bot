import urllib.request, json
req = urllib.request.Request('http://127.0.0.1:8000/api/debug/dump_memory')
# Wait, I don't know if such an endpoint exists. I will add one quickly to position_router.py
