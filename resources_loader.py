import os
import json
from config import data_source, KGMiner_data


def load_files():
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

    if os.path.isfile('dataset/' + data_source + '/kgminer_output.json'):
        with open('dataset/' + data_source + '/kgminer_output.json') as json_data:
            kgminer_output = json.load(json_data)
    else:
        kgminer_output = {"a": "b"}

    return file_triples, ambiverse_resources, possible_predicate, kgminer_output


def load_kgminer_resource():
    nodes_id, edge_id = dict(), dict()
    if os.path.isfile(KGMiner_data+'/nodes_id.json'):
        with open(KGMiner_data+'/nodes_id.json') as json_data:
            nodes_id = json.load(json_data)

    if os.path.isfile(KGMiner_data+'/edge_types_id.json'):
        with open(KGMiner_data+'/edge_types_id.json') as json_data:
            edge_id = json.load(json_data)
    return nodes_id, edge_id