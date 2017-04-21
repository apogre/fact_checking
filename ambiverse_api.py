import requests, pprint, json

url = "https://api.ambiverse.com/v1/entitylinking/analyze"

# payload = "{\"text\" : \"Who is the CEO of Apple?\"}"
headers = {
    'content-type': "application/json",
    'accept': "application/json",
    'authorization': "Bearer 6f201bca5ca30a5c8d7d07f69ba6aa8c27ffd7de"
    }

def entity_parser(text):
    payload = '{\"text\" : \"'+text+'\", "language":"en"}'
    response = requests.request("POST", url, data=payload, headers=headers)
    # print response.text
    json_data = json.loads(response.text)
    entitites = json_data['matches']

    resource = {}
    for entity in entitites:
        url1=entity['entity']['url'].split('/')[-1]
        if '%' in url1:
            url1 = url1.replace('%20','_')
            url1 = url1.replace('%2C', ',')
        resource[entity.get('text')] = [['http://dbpedia.org/resource/'+url1, entity.get('text'),
                                        entity['entity']['confidence']]]
    return resource


if __name__ == '__main__':
    entitites = entity_parser("Phoenix is the capital of Arizona.")
    resource = {}
    for entity in entitites:
        print entity
        resource[entity.get('text')] = [entity['entity']['url'].split('/')[-1],entity.get('text'),entity['entity']['confidence']]
    print resource

