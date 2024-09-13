import json
import sys
import time

import requests

api_url = sys.argv[1]
all_records = set()
while True:
    try:
        response = requests.get(api_url)
        for record in response.json():
            record["input"] = json.loads(record["input"])
            record["output"] = json.loads(record["output"])
            line = json.dumps(record)
            if line in all_records:
                continue
            else:
                all_records.add(line)
                print(line)
        time.sleep(1)
    except KeyboardInterrupt:
        break
    except Exception as exc:
        print(f"WARNING: {exc}", file=sys.stderr)
        pass
