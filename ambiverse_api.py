import requests
import json

url = "https://api.ambiverse.com/v1/entitylinking/analyze"

# payload = "{\"text\" : \"Who is the CEO of Apple?\"}"
headers = {
    'content-type': "application/json",
    'accept': "application/json",
    'authorization': "Bearer 6f201bca5ca30a5c8d7d07f69ba6aa8c27ffd7de"
    }


def entity_parser(text):
    print "ambiverse query"
    payload = '{\"text\" : \"'+text+'\", "language":"en", "coherentDocument": true}'
    response = requests.request("POST", url, data=payload, headers=headers)
    json_data = json.loads(response.text)
    entities = json_data['matches']

    resource = dict()
    for entity in entities:
        try:
            url1 = entity['entity']['url'].split('/')[-1]
            wikidata_url = entity['entity']['id'].split('/')[-1]
            confidence = entity['entity']['confidence']
        except:
            url1 = ''
            confidence = 0
            wikidata_url = ''
        if '%' in url1:
            url1 = url1.replace('%20', '_')
            url1 = url1.replace('%2C', ',')
            url1 = url1.replace('%28', '(')
            url1 = url1.replace('%29', ')')
            url1 = url1.replace('%21', '!')
        resource[entity.get('text')] = {"dbpedia_id": url1, "confidence": confidence, "wikidata_id": wikidata_url}
    return resource


if __name__ == '__main__':
    ambiverse_resources = {'a': 'b'}
    resource = entity_parser("Springfield is the capital of Illinois.")
    print resource

