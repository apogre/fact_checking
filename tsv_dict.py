import csv, json
from datetime import datetime

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError ("Type not serializable")

with open('infobox.nodes') as f:
    reader = csv.reader(f,delimiter='\t')
    mydict = dict((rows[1], rows[0]) for rows in reader)

print mydict
with open('nodes_id.json', 'w') as fp:
    json.dump(mydict, fp, default=json_serial)