import json, os, tempfile, time

def atomic_write_json(path: str, obj: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp_", suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(obj, f)
    os.replace(tmp, path)

def read_json(path: str):
    # Retry logic with exponential backoff
    max_attempts = 5
    base_delay = 0.1  # seconds
    
    for attempt in range(max_attempts):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except OSError as e:
            if attempt == max_attempts - 1:
                raise  # Re-raise on last attempt
            
            # Exponential backoff
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)
    

def now_iso():
    return time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime())
