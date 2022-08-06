from docker import APIClient
import json

cli = APIClient(base_url="unix://var/run/docker.sock")
for line in cli.build(path=".", tag="frontend:test"):
    decoded = str(line, encoding="utf-8").split("\n")
    for data in decoded:
        if not data: continue
        obj = json.loads(data)
        print(obj.get("stream", obj), end="")


