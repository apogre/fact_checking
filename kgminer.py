import csv
from os import listdir, path, remove, chdir, environ, mkdir
import subprocess
from gensim.models import Word2Vec
from sematch.semantic.similarity import EntitySimilarity
from config import KGMiner_data
from resources_loader import load_kgminer_resource
from kb_query import or_query_prep, kgminer_training_data
from shutil import copyfile
import sys
load_dbpedia_word2vec = True
load_encodings = True
model_wv = None
nodes_id, edge_id = dict(), dict()


def invoke_kgminer():
    predicate_results = dict()
    print "Executing KGMiner"
    if path.isfile(KGMiner_data + '/predicate_probability.csv'):
        remove(KGMiner_data + '/predicate_probability.csv')
    chdir('KGMiner')
    subprocess.call('./run_test.sh')
    chdir('..')
    if path.isfile(KGMiner_data + '/predicate_probability.csv'):
        with open(KGMiner_data + '/predicate_probability.csv') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                predicate_results[row['poi']] = row['score']
        print predicate_results
    return predicate_results


def write_to_kgminer(poi, q_part, resource_v, sentence_id, data_source):
    training_set = kgminer_training_data(poi, q_part)
    training_set = sum(training_set, [])
    train_ents = [val.split('/')[-1] for val in training_set]
    word_vec_train = word2vec_dbpedia(train_ents, resource_v)
    word_vec_train = list(set(map(tuple, word_vec_train)))
    word_vec_train = map(list, word_vec_train)
    if len(word_vec_train) > 6:
        csv_writer(word_vec_train, data_source + '/' + sentence_id + data_source)
        word_vec_train = sum(word_vec_train, [])
    # else:
    #     print "Word2Vec Failed, Training at Random"
    #     word_vec_train = train_ents[:100]
    #     print word_vec_train
    #     csv_writer(word_vec_train, data_source + '/' + sentence_id + data_source)
        node_ids = entity_id_finder(word_vec_train)
        training_data, test_data = train_data_csv(word_vec_train, node_ids, resource_v)
        csv_writer(training_data, file_name=data_source + '/' + sentence_id + data_source + '_ids')
        copyfile(KGMiner_data + '/' + data_source + '/' + sentence_id + data_source + '_ids.csv', KGMiner_data + '/' + \
                 'training_data.csv')
        return True
    else:
        print "Insufficient Training Data. Using Next Predicate."
        return False


def get_training_set(predicate_ranked, resource_type_set_ranked, ontology_threshold_ranked, triple_dict, resource_ids,\
                     sentence_id, data_source):
    print resource_ids
    global load_encodings, nodes_id, edge_id
    if load_encodings:
        print "Loading Nodes & Edges Id"
        nodes_id, edge_id = load_kgminer_resource()
        load_encodings = False
    kgminer_status = False
    for triples_k, triples_v in triple_dict.iteritems():
        for triple_v in triples_v:
            print triple_v, resource_ids
            if len(triple_v) <= len(resource_ids):
                resource_v = [resource_ids.get(trip_v).get('dbpedia_id') for trip_v in triple_v]
                q_part = or_query_prep(resource_type_set_ranked, ontology_threshold_ranked, triple_v)
                test_data = get_test_data(resource_v)
                csv_writer([test_data], file_name='test_data')
                print test_data
                predicate_set = predicate_ranked.values()
                for predicate_of_interest in predicate_set[0][:10]:
                    if None not in test_data and predicate_of_interest and kgminer_status == False:
                        poi = predicate_of_interest[0]
                        print poi
                        poi_writer(poi, sentence_id, data_source)
                        if not path.isdir(KGMiner_data+'/'+data_source):
                            mkdir(KGMiner_data+'/'+data_source)
                        training_files = listdir(KGMiner_data+'/'+data_source)
                        if sentence_id+data_source+'_ids.csv' not in training_files:
                            kgminer_status = write_to_kgminer(poi, q_part, resource_v, sentence_id, data_source)
                        else:
                            kgminer_status = True
                            copyfile(KGMiner_data+'/'+data_source+'/'+sentence_id+data_source+'_ids.csv', KGMiner_data+'/' + \
                                     'training_data.csv')
                            copyfile(KGMiner_data + '/' + data_source + '/' + sentence_id + data_source + '_poi.csv',
                                     KGMiner_data + '/' + \
                                     'poi.csv')
            else:
                print "Ambiverse Error"
        return kgminer_status
    return False


def get_test_data(resource_v):
    test_node_ids = entity_id_finder(resource_v)
    test_data = [test_node_ids.get(resource_v[0]), test_node_ids.get(resource_v[1])]
    return test_data


def entity_id_finder(entity_set):
    id_set = {}
    for ent in entity_set:
        id_set[ent] = nodes_id.get(ent)
    return id_set


def poi_writer(poi, sentence_id, data_source):
    id_list = [edge_id.get(poi.split('/')[-1], ''), poi]
    print id_list
    if path.isfile(KGMiner_data + '/poi.csv'):
        remove(KGMiner_data + '/poi.csv')
    with open(KGMiner_data + '/' + data_source + '/' + sentence_id + data_source + '_poi.csv', 'wb') as csvfile:
        datawriter = csv.writer(csvfile)
        datawriter.writerow(id_list)
    copyfile(KGMiner_data + '/' + data_source + '/' + sentence_id + data_source + '_poi.csv', KGMiner_data + '/' + \
             'poi.csv')


def csv_writer(input_data, file_name):
    with open(KGMiner_data + '/' + file_name+'.csv', 'wb') as csvfile:
        datawriter = csv.writer(csvfile)
        for data in input_data:
            try:
                datawriter.writerow(data)
            except:
                pass


def train_data_csv(train_ents, node_ids, expected_entities):
    training_data = []
    test_data = []
    for i in range(0, len(train_ents)-2, 2):
        id_one = node_ids.get(train_ents[i], '')
        if id_one:
            try:
                id_two = node_ids.get(train_ents[i+1], '')
                if id_two and train_ents[i] not in expected_entities and train_ents[i+1] not in expected_entities:
                    training_data.append([id_one, id_two])
                else:
                    test_data.append([id_one, id_two])
            except:
                pass
    return training_data, test_data


def word2vec_dbpedia(train_ents, resource_v):
    word_vec_train = []
    entity_tracker = dict()
    global load_dbpedia_word2vec
    global model_wv
    if load_dbpedia_word2vec:
        print "Loading Word2Vec DBpedia"
        model_wv = Word2Vec.load(str(environ['STANFORDTOOLSDIR']) + "/en_1000_no_stem/en.model")
        load_dbpedia_word2vec = False

    for j in range(0, len(train_ents) - 1, 2):
        if entity_tracker.get(train_ents[j+1], 0) < 5 and entity_tracker.get(train_ents[j], 0) < 5:
            try:
                sim1 = model_wv.similarity('DBPEDIA_ID/' + resource_v[0], 'DBPEDIA_ID/' + train_ents[j])
                sim2 = model_wv.similarity('DBPEDIA_ID/' + resource_v[1], 'DBPEDIA_ID/' + train_ents[j + 1])
                # print resource_v[0], train_ents[j], sim1
                # print resource_v[1], train_ents[j+1], sim2
                if sim1 > 0.20 and sim2 > 0.20:
                    sim1_1 = model_wv.similarity('DBPEDIA_ID/' + resource_v[1], 'DBPEDIA_ID/' + train_ents[j])
                    sim2_1 = model_wv.similarity('DBPEDIA_ID/' + resource_v[0], 'DBPEDIA_ID/' + train_ents[j + 1])
                    if sim1_1 > sim1 and sim2_1 > sim2:
                        word_vec_train.append([train_ents[j+1], train_ents[j]])

                    else:
                        word_vec_train.append([train_ents[j], train_ents[j + 1]])
                    if train_ents[j] not in entity_tracker.keys():
                        entity_tracker[train_ents[j]] = 1
                    else:
                        entity_tracker[train_ents[j]] += 1
                    if train_ents[j+1] not in entity_tracker.keys():
                        entity_tracker[train_ents[j+1]] = 1
                    else:
                        entity_tracker[train_ents[j+1]] += 1

                    if len(word_vec_train) > 50:
                        return word_vec_train
            except Exception as e:
                # print e
                pass
    return word_vec_train


if __name__ == "__main__":
    nodes_id, edge_id = load_kgminer_resource()
    with open(KGMiner_data+'/sample_case/0sample_case.csv', 'rb') as f:
        reader = csv.reader(f)
        entity_sets = list(reader)
        entity_set = sum(entity_sets,[])
        node_ids = entity_id_finder(entity_set)
        expected_entities = entity_set[:2]
        training_data, test_data = train_data_csv(entity_set, node_ids, expected_entities)
        print training_data, test_data
        csv_writer(training_data, file_name='/sample_case/0sample_case_ids_backup')
        copyfile(KGMiner_data + '/sample_case/0sample_case_ids_backup.csv', KGMiner_data + '/training_data.csv')
        invoke_kgminer()
