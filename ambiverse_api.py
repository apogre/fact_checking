import requests, pprint, json
import global_settings
url = "https://api.ambiverse.com/v1/entitylinking/analyze"

# payload = "{\"text\" : \"Who is the CEO of Apple?\"}"
headers = {
    'content-type': "application/json",
    'accept': "application/json",
    'authorization': "Bearer 6f201bca5ca30a5c8d7d07f69ba6aa8c27ffd7de"
    }

global ambiverse_resources

def entity_parser(text,sentence_id):
    if sentence_id in ambiverse_resources.keys():
        resource = ambiverse_resources[sentence_id]
    else:
        print "ambiverse query"
        global_settings.new_ambi_query = 1
        payload = '{\"text\" : \"'+text+'\", "language":"en"}'
        response = requests.request("POST", url, data=payload, headers=headers)
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
        ambiverse_resources[sentence_id] = resource
    return resource

def first_ambiverse():
    return ambiverse_resources


if __name__ == '__main__':
    entitites = entity_parser("Trump decided to send missiles to Syria.")
    print resource

