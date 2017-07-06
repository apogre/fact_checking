import os
import json
import csv
from config import KGMiner_data
from resource_writer import json_serial


def load_files(data_source):
    if os.path.isfile('dataset/'+data_source+'/triples_raw.json'):
        with open('dataset/'+data_source+'/triples_raw.json') as json_data:
            file_triples = json.load(json_data)
    else:
        file_triples = {"a": "b"}

    if os.path.isfile('dataset/'+data_source+'/ambiverse_resources.json'):
        with open('dataset/'+data_source+'/ambiverse_resources.json') as json_data:
            ambiverse_resources = json.load(json_data)
    else:
        ambiverse_resources = {"a":"b"}

    if os.path.isfile('dataset/' + data_source + '/possible_kgminer_predicate.json'):
        with open('dataset/' + data_source + '/possible_kgminer_predicate.json') as json_data:
            possible_predicate = json.load(json_data)
    else:
        possible_predicate = {"a": "b"}

    if os.path.isfile('dataset/' + data_source + '/lpmln_predicate.json'):
        with open('dataset/' + data_source + '/lpmln_predicate.json') as json_data:
            lpmln_predicate = json.load(json_data)
    else:
        lpmln_predicate = {"a": "b"}

    if os.path.isfile('dataset/' + data_source + '/kgminer_output.json'):
        with open('dataset/' + data_source + '/kgminer_output.json') as json_data:
            kgminer_output = json.load(json_data)
    else:
        kgminer_output = {"a": "b"}

    if os.path.isfile('dataset/' + data_source + '/lpmln_output.json'):
        with open('dataset/' + data_source + '/lpmln_output.json') as json_data:
            lpmln_output = json.load(json_data)
    else:
        lpmln_output = {"a": "b"}

    return file_triples, ambiverse_resources, possible_predicate, kgminer_output, lpmln_predicate, lpmln_output


def load_kgminer_resource():
    nodes_id, edge_id = dict(), dict()
    if os.path.isfile('KGMiner/input_data/nodes_id.json'):
        with open('KGMiner/input_data/nodes_id.json') as json_data:
            nodes_id = json.load(json_data)
    else:
        process_input_data('KGMiner/input_data/infobox.nodes', 'KGMiner/input_data/nodes_id.json')

    if os.path.isfile('KGMiner/input_data/edge_types_id.json'):
        with open('KGMiner/input_data/edge_types_id.json') as json_data:
            edge_id = json.load(json_data)
    else:
        process_input_data('KGMiner/input_data/infobox.edgetypes', 'KGMiner/input_data/edge_types_id.json')
        load_kgminer_resource()
    return nodes_id, edge_id


def process_input_data(input_file, output_file):
    with open(input_file) as f:
        reader = csv.reader(f, delimiter='\t')
        mydict = dict((rows[1], rows[0]) for rows in reader)

    with open(output_file, 'w') as fp:
        json.dump(mydict, fp, default=json_serial)