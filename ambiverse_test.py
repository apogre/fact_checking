import requests, pprint

url = "https://api.ambiverse.com/v1/entitylinking/analyze"

payload = "{\"text\" : \"Who is the CEO of Apple?\"}"
headers = {
    'content-type': "application/json",
    'accept': "application/json",
    'authorization': "Bearer 6f201bca5ca30a5c8d7d07f69ba6aa8c27ffd7de"
    }

response = requests.request("POST", url, data=payload, headers=headers)

pprint.pprint(response.text)
