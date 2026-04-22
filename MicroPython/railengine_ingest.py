import sys

if sys.implementation.name == 'micropython':
    import urequests as requests  # type: ignore[import]
    import ujson as json  # type: ignore[import]
else:
    import requests  # type: ignore[no-redef]
    import json  # type: ignore[no-redef]

class RailengineIngest:
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key

    def send(self, payload):
        response = requests.post(
            self.api_url,
            headers={
                "x-rail-auth": self.api_key,
                "Content-Type": "application/json"
            },
            data=json.dumps(payload)
        )

        status = response.status_code
        response.close()
        return status
