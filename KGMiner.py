import sparql
import kb_query
import operator
import csv
import sys
import os
import subprocess
import config
import time

sparql_dbpedia = 'http://localhost:8890/sparql'
sparql_dbpedia_on = 'https://dbpedia.org/sparql'


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


def entity_id_finder_json(entity_set):
    # print entity_set
    id_set = {}
    for ent in entity_set:
        id_set[ent] = config.nodes_id.get(ent, '')
    return id_set


def predicate_id_finder_json(poi):
    id_list = [config.edge_id.get(poi, ''), poi]
    with open(kg_data_source + 'poi.csv', 'wb') as csvfile:
        datawriter = csv.writer(csvfile)
        datawriter.writerow(id_list)
    return id_list


def kg_miner_csv(input_data, file_name):
    with open(kg_data_source+file_name+'.csv', 'wb') as csvfile:
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


def or_query_prep(resource_type_set_ranked, ontology_threshold_ranked, ex_ent_all):
    q_part_base = '{ ?url1 rdf:type <'
    q_part_base_res = 'UNION { ?url1 dbo:type <'
    q_part = ''
    # print ">>>>>>>>>>>"
    # print ontology_threshold_ranked
    # print ex_ent_all
    # try:
    for v in ex_ent_all:
        q_part_res = ''
        ont_types = ontology_threshold_ranked.get(v,[])
        res_types = resource_type_set_ranked.get(v,[])
        # print ont_types
        # print res_types
        for i,val in enumerate(ont_types):
            # print val            
            if i == (len(ont_types)-1):
                q_part = q_part + q_part_base + val + '>} '
            else:
                q_part = q_part + q_part_base + val + '>} UNION '
        if res_types:
            for j,res_val in enumerate(res_types):
                if j == (len(res_types)-1):
                    q_part_res = q_part_res + q_part_base_res + res_val + '>}  .'
                else:
                    q_part_res = q_part_res + q_part_base_res + res_val + '>} UNION '
        else:
            q_part_res = ' .'
        q_part = q_part + q_part_res
        q_part_base = ' { ?url2 rdf:type <'
        q_part_base_res = 'UNION { ?url2 dbo:type <'

    return q_part


def word2vec_dbpedia(train_ents, resource_v):
    word_vec_train = []
    for j in range(0, len(train_ents) - 1, 2):
        # print 'DBPEDIA_ID/' + ex_ent_all[1], 'DBPEDIA_ID/' + train_ents[j]
        # print 'DBPEDIA_ID/' + ex_ent_all[0], 'DBPEDIA_ID/' + train_ents[j+1]
        try:
            # print global_settings.model_wv.similarity('DBPEDIA_ID/Barack_Obama', 'DBPEDIA_ID/Michelle_Obama')
            sim1 = config.model_wv.similarity('DBPEDIA_ID/' + resource_v[0],
                                                       'DBPEDIA_ID/' + train_ents[j])
            # print sim1
            sim2 = config.model_wv.similarity('DBPEDIA_ID/' + resource_v[1],
                                                       'DBPEDIA_ID/' + train_ents[j + 1])
            # print sim2
            # print train_ents[j], train_ents[j+1]
            if sim1 > 0.2 and sim2 > 0.2:
                sim1_1 = config.model_wv.similarity('DBPEDIA_ID/' + resource_v[1],
                                                       'DBPEDIA_ID/' + train_ents[j])
            # print sim1
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


def get_training_set(predicate_ranked, resource_type_set_ranked, ontology_threshold_ranked, triple_dict, resource_ids):
    triple_predicates = {}
    training_data_set= {}
    for triples_k, triples_v in triple_dict.iteritems():
        for triple_v in triples_v:
            # print triples_k, triple_v
            resource_v = [resource_ids.get(trip_v) for trip_v in triple_v]
            print resource_v
            predicate_results = {}
            if None not in resource_v:
                q_part = or_query_prep(resource_type_set_ranked, ontology_threshold_ranked, resource_v)
                # print q_part
                # print "---------"
                # sys.exit(0)
                test_node_ids = entity_id_finder_json(resource_v)
                # print time.time() - r_time
                # print test_node_ids
                test_data = [test_node_ids.get(resource_v[0]), test_node_ids.get(resource_v[1])]
                print test_data
                if None not in test_data:
                    kg_miner_csv([test_data], file_name='test_data')
                    print predicate_ranked
                    for sent_pred in predicate_ranked.keys():
                        # print sent_pred
                        predicate_of_interest = predicate_ranked[sent_pred]
                        for poi in predicate_of_interest:
                            print poi
                            pred_id = predicate_id_finder_json(poi)
                            # print pred_id
                            # sys.exit(0)
                            q_ts = 'PREFIX dbo: <http://dbpedia.org/ontology/> select distinct ?url1 ?url2 where { \
                            {?url1 <http://dbpedia.org/ontology/' + poi + '> ?url2} . ' + q_part+\
                                   ' FILTER(?url1 != ?url2).} '
                            # print q_ts
                            training_set = []

                            # try:
                            #     result = sparql.query(sparql_dbpedia, q_ts)
                            #     training_set = [sparql.unpack_row(row_result) for row_result in result]
                            # except:
                            #     print "Sparql Error"
                                
                            if not training_set:
                                try:
                                    result = sparql.query(sparql_dbpedia_on, q_ts)
                                    training_set = [sparql.unpack_row(row_result) for row_result in result]
                                except:
                                    print "Online Sparql Error"                            
                            print len(training_set)
                            # sys.exit(0)
                            if len(training_set)>5:
                                training_set = sum(training_set, [])
                                train_ents = [val.split('/')[-1] for val in training_set]
                                word_vec_train = word2vec_dbpedia(train_ents, resource_v)
                                # print word_vec_train
                                if len(word_vec_train) > 5:
                                    print word_vec_train
                                    # sys.exit(0)
                                    word_vec_train = sum(word_vec_train,[])

                                    # print len(word_vec_train)
                                    node_ids = entity_id_finder_json(word_vec_train)
                                    # print node_ids
                                    # sys.exit(0)
                                    training_data, test_data = train_data_csv(word_vec_train, node_ids, resource_v)
                                    # print training_data, test_data
                                    print len(training_data)
                                    if training_data:
                                        print "Executing Classification"
                                        kg_miner_csv(training_data, file_name='training_data')
                                        os.chdir('KGMiner')
                                        subprocess.call('./run_test.sh')
                                        try:
                                            with open('../KGMiner_data/predicate_probability.csv') as f:
                                                reader = csv.DictReader(f)
                                                for i,row in enumerate(reader):
                                                    predicate_results[row['poi']] = row['score']
                                        except:
                                            pass
                                        print predicate_results
                                        training_data_set[(str(triples_k)+'-'+str(triple_v))+'-'+str(poi)] = word_vec_train
                                        os.chdir('..')
                                else:
                                    print "Insufficient Training Set"
                else:
                    print "test data error"

            triple_predicates[(str(triples_k)+'-'+str(triple_v))] = predicate_results
            
    return triple_predicates, training_data_set
