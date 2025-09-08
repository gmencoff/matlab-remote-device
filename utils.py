import json, os, tempfile, time

def atomic_write_json(path: str, obj: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp_", suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(obj, f)
    os.replace(tmp, path)

def read_json(path: str):
    with open(path, "r") as f:
        return json.load(f)

def now_iso():
    return time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime())
