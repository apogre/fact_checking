import json
import urllib

api_key = open(".api_key").read()
query = 'blue bottle'
service_url = 'https://www.googleapis.com/freebase/v1/search'
params = {
        'query': query,
        'key': api_key
}
url = service_url + '?' + urllib.urlencode(params)
print url
response = json.loads(urllib.urlopen(url).read())
print response
for result in response['result']:
    print result['name'] + ' (' + str(result['score']) + ')'