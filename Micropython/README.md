## Railengine for IoT

railengine_ingest.py can be used by python and Micropython programs to send data to a Railengine

## Example

```
from railengine_ingest import RailengineIngest

EPOCH_OFFSET = 946684800
# == x-rail-auth 
API_KEY = ""
# == ENGINE INGEST URL ==
API_URL = ""

# get some sensor data

ingestor = RailengineIngest(API_URL, API_KEY)

ingestor.send({
                "id": new_id,
                "data": sensor_data,
                "timestamp": (time() + EPOCH_OFFSET) * 1000,
            })
```
