import json
from os import remove, path
from datetime import datetime


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError ("Type not serializable")


def update_resources(triple_flag, ambiverse_flag, kgminer_predicate_flag, lpmln_predicate_flag, kgminer_output_flag, \
                     file_triples, ambiverse_resources, possible_kgminer_predicate, lpmln_predicate, kgminer_output,\
                     lpmln_output_flag, data_source, kgminer_random_output_flag, kgminer_output_random):
    if triple_flag:
        print "Updating Relation Triples"
        if path.isfile('dataset/' + data_source + '/triples_raw.json'):
            remove('dataset/' + data_source + '/triples_raw.json')
        with open('dataset/' + data_source + '/triples_raw.json', 'w') as fp:
            json.dump(file_triples, fp, default=json_serial)

    if ambiverse_flag:
        print "Updating Resources"
        if path.isfile('dataset/' + data_source + '/ambiverse_resources.json'):
            remove('dataset/' + data_source + '/ambiverse_resources.json')
        with open('dataset/' + data_source + '/ambiverse_resources.json', 'w') as fp:
            json.dump(ambiverse_resources, fp, default=json_serial)

    if kgminer_predicate_flag:
        print "Updating KGMiner Predicate List"
        if path.isfile('dataset/' + data_source + 'possible_kgminer_predicate.json'):
            remove('dataset/' + data_source + 'possible_kgminer_predicate.json')
        with open('dataset/' + data_source + '/possible_kgminer_predicate.json', 'w') as fp:
            json.dump(possible_kgminer_predicate, fp, default=json_serial)

    if lpmln_predicate_flag:
        print "Updating LPmln Predicate List"
        if path.isfile('dataset/' + data_source + 'lpmln_predicate.json'):
            remove('dataset/' + data_source + 'lpmln_predicate.json')
        with open('dataset/' + data_source + '/lpmln_predicate.json', 'w') as fp:
            json.dump(lpmln_predicate, fp, default=json_serial)

    if kgminer_output_flag:
        print "Updating KGMiner Output"
        if path.isfile('dataset/' + data_source + '/kgminer_output.json'):
            remove('dataset/' + data_source + '/kgminer_output.json')
        with open('dataset/' + data_source + '/kgminer_output.json', 'w') as fp:
            json.dump(kgminer_output, fp, default=json_serial)

    if kgminer_random_output_flag:
        print "Updating KGMiner Random Output"
        if path.isfile('dataset/' + data_source + '/kgminer_output_random.json'):
            remove('dataset/' + data_source + '/kgminer_output_random.json')
        with open('dataset/' + data_source + '/kgminer_output_random.json', 'w') as fp:
            json.dump(kgminer_output_random, fp, default=json_serial)

    if lpmln_output_flag:
        print "Updating LPmln Output"
        if path.isfile('dataset/' + data_source + '/lpmln_output.json'):
            remove('dataset/' + data_source + '/lpmln_output.json')
        with open('dataset/' + data_source + '/lpmln_output.json', 'w') as fp:
            json.dump(kgminer_output, fp, default=json_serial)
