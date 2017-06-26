import sparql
import operator
import csv
import sys
import os
import subprocess
from config import sparql_dbpedia, KGMiner_data
from resources_loader import load_kgminer_resource

nodes_id, edge_id = load_kgminer_resource()


def remove_stats():
    print "Remove KGMiner POI Files"
    if os.path.isfile(KGMiner_data + 'predicate_probability.csv'):
        os.remove(KGMiner_data + 'predicate_probability.csv')


def resource_type_extractor(resources, triples):
    type_of_resource = {}
    for triple_k, triples_v in triples.iteritems():
        for triple_v in triples_v:
            for ent in triple_v:
                item1_v = resources[ent]
                type_list_resource = []
                for i1 in item1_v:
                    if 'dbpedia' in i1[0]:
                        url1 = i1[0]
                        q_type = ('PREFIX dbo: <http://dbpedia.org/ontology/> SELECT distinct ?t WHERE {{ <' + url1 + '> dbo:type ?t .} UNION {?t dbo:type  <' + url1 + '>  .}}')
                        # print q_type
                        result = sparql.query(sparql_dbpedia, q_type)
                        type_values = [sparql.unpack_row(row_result) for row_result in result]
                        type_resource = [val[0] for val in type_values]
                        type_list_resource.extend(type_resource)
                type_of_resource[ent] = list(set(type_list_resource))
    return type_of_resource


def get_test_data(resource_v):
    test_node_ids = entity_id_finder(resource_v)
    test_data = [test_node_ids.get(resource_v[0]), test_node_ids.get(resource_v[1])]
    return test_data


def entity_id_finder(entity_set):
    id_set = {}
    for ent in entity_set:
        id_set[ent] = nodes_id.get(ent, '')
    return id_set


def poi_writer(poi):
    id_list = [edge_id.get(poi[0], ''), poi]
    if os.path.isfile(KGMiner_data + 'poi.csv'):
        os.remove(KGMiner_data + 'poi.csv')
    with open(KGMiner_data + 'poi.csv', 'wb') as csvfile:
        datawriter = csv.writer(csvfile)
        datawriter.writerow(id_list)


def csv_writer(input_data, file_name):
    with open(KGMiner_data+file_name+'.csv', 'wb') as csvfile:
        datawriter = csv.writer(csvfile)
        for data in input_data:
            datawriter.writerow(data)


def train_data_csv(train_ents, node_ids, expected_entities):
    training_data=[]
    test_data = []
    # print">>>>>"
    # print train_ents
    # print node_ids
    # print expected_entities
    for i in range(0, len(train_ents)-2,2):
        id_one = node_ids.get(train_ents[i],'')
        if id_one:
            try:
                # print id_one
                id_two = node_ids.get(train_ents[i+1],'')
                if id_two and train_ents[i] not in expected_entities and train_ents[i+1] not in expected_entities:
                    # print id_two
                    training_data.append([id_one, id_two])
                else:
                    test_data.append([id_one, id_two])
            except:
                pass
    return training_data, test_data


def word2vec_dbpedia(train_ents, resource_v):
    word_vec_train = []
    for j in range(0, len(train_ents) - 1, 2):
        try:
            sim1 = config.model_wv.similarity('DBPEDIA_ID/' + resource_v[0],
                                                       'DBPEDIA_ID/' + train_ents[j])
            sim2 = config.model_wv.similarity('DBPEDIA_ID/' + resource_v[1],
                                                       'DBPEDIA_ID/' + train_ents[j + 1])
            if sim1 > 0.2 and sim2 > 0.2:
                sim1_1 = config.model_wv.similarity('DBPEDIA_ID/' + resource_v[1],
                                                       'DBPEDIA_ID/' + train_ents[j])
                sim2_1 = config.model_wv.similarity('DBPEDIA_ID/' + resource_v[0],
                                                       'DBPEDIA_ID/' + train_ents[j + 1])
                if sim1_1 > sim1 and sim2_1>sim2:
                    word_vec_train.append([train_ents[j+1], train_ents[j]])
                else:
                    word_vec_train.append([train_ents[j], train_ents[j + 1]])
                if len(word_vec_train) > 50:
                    return word_vec_train
        except:
            pass
    return word_vec_train
