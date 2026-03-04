import sys

if sys.implementation.name == 'micropython':
    import urequests as requests
    import ujson as json
else:
    import requests
    import json

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
