import KG_Miner_Extension
import ambiverse_api
import fact_check
from nltk import word_tokenize
import sys
import time
import operator, json
import collections, csv
import pprint, os
from StanfordOpenIEPython.main import stanford_ie
from datetime import datetime
import subprocess
import global_settings
import evaluation
import os.path
import lpmln_extention


aux_verb = ['was', 'is', 'become']
KG_Miner = False
precision_recall_stats = collections.OrderedDict()
stanford_setup = True
ambiverse = True
data_dump = False

global_settings.init()
# data_source = 'ug_data/all_'
data_source = global_settings.data_source
output_data = ''
# data_source = 'ug_final/'
# if not os.path.exists('output_data'+str(time.time())+'/'):
#     os.makedirs('output_data'+str(time.time())+'/')
#     output_data = 'output_data'+str(time.time())+'/'

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError ("Type not serializable")


def triples_extractor(sent_id, sentence, ne, new_triple_flag):
    if sent_id in file_triples.keys():
        triple_dict = file_triples[sent_id]
    else:
        try:
            os.remove('sentences.txt')
        except:
            pass
        with open('sentences.txt', 'a') as text:
            text.write(sentence)
        triples_raw = stanford_ie("sentences.txt", verbose=False)
        triples = [[trip.lstrip() for trip in triple] for triple in triples_raw]
        ent = fact_check.get_nodes_updated(ne)
        triple_dict = fact_check.svo_finder(ent, triples)
        file_triples[sent_id] = triple_dict
        new_triple_flag = 1
    return new_triple_flag, triple_dict


def fact_checker(sentence_lis, id_list):
    print sentence_lis
    output_relations = {}
    probabilities = []
    dates = fact_check.date_parser(sentence_lis)
    if stanford_setup:
        sentence_list = [word_tokenize(sent) for sent in sentence_lis]
        ne_s, pos_s, dep_s = fact_check.st_tagger(sentence_list)
        verb_entity = fact_check.verb_entity_matcher(dep_s)
    else:
        ne_s = sentence_lis
    start_time = time.time()
    new_triple_flag = 0
    new_predicate_flag = 0
    output_linkprediction = {}
    output_training_data = {}
    for n, ne in enumerate(ne_s):
        sent_id = id_list[n]
        print sent_id, sentence_lis[n],'\n'
        if stanford_setup:
            ent = fact_check.get_nodes_updated(ne)
            if dates[n]:
                date_string = (dates[n][0], 'DATE')
                ent.append(date_string)
            vb = fact_check.get_verb(pos_s[n])
            ent_dict = dict(ent)
            print "NER: "+str(ent_dict)
            fact_check.get_labels(ent)
        res_time = time.time()
        new_triple_flag, triple_dict = triples_extractor(sent_id, sentence_lis[n],ne, new_triple_flag)
        print "Relation Triples: "+str(triple_dict)
        if ambiverse:
            resource_text = ambiverse_api.entity_parser(sentence_lis[n],id_list[n])
            resources = resource_text
        print "Resource Extractor"
        print "=================="
        pprint.pprint(resource_text)
        # precision_ent, recall_ent, entity_matched = evaluation.precision_recall_entities(sent_id, resource_text)
        # if precision_ent:
        #     precision_res = sum(precision_ent)/len(precision_ent)
        # else:
        #     precision_res = 0
        # if recall_ent:
        #     recall_res = sum(recall_ent)/len(recall_ent)
        # else:
        #     recall_res = 0
        relation_ent, relation_ent_0, relation_ent_2 = fact_check.relation_extractor_triples(resource_text, triple_dict)
        # print relation_ent
        # if not relation_ent:
        #     sentence_list = [word_tokenize(sent) for sent in sentence_lis]
        #     ne_s, pos_s, dep_s = fact_check.st_tagger(sentence_list)
        #     verb_entity = fact_check.verb_entity_matcher(dep_s)
        #     relation_ent, rel_count = fact_check.relation_extractor_all(resource_text, verb_entity[n])
        #     # print relation_ent
            # sys.exit(0)
        # print "Precision & Recall for Resource Extractor"
        # print "-----------------------------------------"
        relations_0,  predicate_set_0 = fact_check.relation_processor(relation_ent_0)
        relations, predicate_set = fact_check.relation_processor(relation_ent)
        relations_2,  predicate_set_2 = fact_check.relation_processor(relation_ent_2)
        print "0-hop Groundings"
        print "================"
        print relation_ent_0
        print "0-hop Unique Predicates"
        print "======================="
        print predicate_set_0
        print "1-hop Groundings"
        print "================"
        print relation_ent
        print "1-hop Unique Predicates"
        print "======================="
        print predicate_set
        # print "2-hop Groundings"
        # print "================"
        # print relation_ent_2
        # print "2-hop Unique Predicates"
        # print "======================="
        # print predicate_set_2
        # print "Relation Graph"
        # print "--------------"

        lpmln_extention.evidence_writer(relation_ent, sent_id)
        probability = lpmln_extention.inference()
        probability.append(sent_id)
        probabilities.append(probability)
        # print relations
        # sys.exit(0)
        # pprint.pprint(relations)
        # pprint.pprint(relations_0)
        relations = False

        if relations:
            # output_relations[id_list[n]] = relations

            execution_time = time.time() - res_time
            print execution_time
            # sys.exit(0)
            true_pos_rel, retrived_rels, ex_rels = evaluation.precision_recall_relations(sent_id, relations)
            print true_pos_rel, retrived_rels, ex_rels
            true_pos_ent, retrieved_ents, ex_ent_all = evaluation.precision_recall_ent_match(sent_id, relations)
            # print ex_ent_all
            print '\n'
            print "Precision & Recall for Entities"
            print "--------------------------------"
            precision_ent_out, recall_ent_out = evaluation.precision_recall(true_pos_ent, retrieved_ents, ex_ent_all)
            print "Entity Match: Precision: " + str(precision_ent_out), "Recall: " + str(recall_ent_out)
            print "------------------------------------------"
            print "Precision & Recall for Relations"
            print "--------------------------------"
            precision_rel, recall_rel = evaluation.precision_recall(true_pos_rel, retrived_rels, ex_rels)
            print "Relations: Precision: " + str(precision_rel), "Recall: " + str(recall_rel)
            precision_recall_stats[sent_id] = [precision_res, recall_res, precision_rel, recall_rel, precision_ent_out, recall_ent_out]
        else:
            precision_recall_stats[sent_id] = [0, 0, 0, 0, 0, 0]
        if KG_Miner:
            print "Using KG_Miner"
            entity_type_ontology, entity_type_resource = KG_Miner_Extension.entity_type_extractor(resources,\
                                                                                                  triple_dict)
            training_entity_type, training_resource_type = KG_Miner_Extension.training_entity_type(resources, triple_dict)

            print "Type of Entities"
            pprint.pprint(entity_type_ontology)
            pprint.pprint(entity_type_resource)
            # sys.exit(0)
            # sys.exit(0)
            # resource_type_set_ranked, resource_threshold_ranked = KG_Miner_Extension.entity_type_ranker(entity_type_resource, ent_dict, triple_dict)
            # ontology_type_set_ranked, ontology_threshold_ranked = KG_Miner_Extension.entity_type_ranker\
            #     (entity_type_ontology, ent_dict, triple_dict)
            # pprint.pprint(resource_type_set_ranked)
            # pprint.pprint(ontology_type_set_ranked)
            # pprint.pprint(ontology_threshold_ranked)
            # sys.exit(0)
            if sent_id in possible_predicate.keys():
                possible_predicate_set = possible_predicate[sent_id]
            else:
                possible_predicate_set = KG_Miner_Extension.possible_predicate_type(entity_type_ontology, triple_dict, resource_text)
                possible_predicate[sent_id] = possible_predicate_set
                new_predicate_flag=1
            # print possible_predicate_set
            # possible_predicate_set_ranked, possible_predicate_set_threshold = KG_Miner_Extension.predicate_ranker(possible_predicate_set,triple_dict)
            # print possible_predicate_set_ranked
            # print possible_predicate_set_threshold
            # sys.exit(0)
            try:
                os.remove('KG_Miner_data/poi.csv')
                os.remove('KG_Miner_data/predicate_probability.csv')
            except:
                pass
            # print entity_type_ontology
            # print training_entity_type
            # print training_resource_type
            # sys.exit(0)
            predicate_results, training_data_set = KG_Miner_Extension.get_training_set(possible_predicate_set, \
                                                                    training_resource_type, training_entity_type, \
                                                                    triple_dict, resource_text)
            output_linkprediction[id_list[n]] = predicate_results
            output_training_data[id_list[n]] = training_data_set

        execution_time = time.time() - res_time
        print "Execution Time: " + str(round(execution_time, 2))
        print "================================================="
        if data_dump == True:
            with open(output_data+'/evaluation.json', 'w') as fp:
                json.dump(precision_recall_stats, fp, default=json_serial)

            with open(output_data+'/link_prediction.json', 'w') as fp:
                json.dump(output_linkprediction, fp, default=json_serial)

            with open(output_data+'/training_data.json', 'w') as fp:
                json.dump(output_training_data, fp, default=json_serial)

            with open(output_data+'/output_relations.json', 'w') as fp:
                json.dump(output_relations, fp, default=json_serial)
    print output_linkprediction

    with open('lpmln_tests/'+data_source +'/'+ data_source+'_prob.csv', 'wb') as csvfile:
        datawriter = csv.writer(csvfile)
        datawriter.writerows(probabilities)

    if new_triple_flag == 1:
        if os.path.isfile('dataset/'+data_source + '/triples_raw.json'):
            os.remove('dataset/'+data_source+'/triples_raw.json')
        with open('dataset/'+data_source+'/triples_raw.json', 'w') as fp:
            json.dump(file_triples, fp, default=json_serial)

    if global_settings.new_ambi_query==1:
        first_query = ambiverse_api.first_ambiverse()
        if os.path.isfile('dataset/'+data_source+'/ambiverse_resources.json'):
            os.remove('dataset/'+data_source+'/ambiverse_resources.json')
        with open('dataset/'+data_source+'/ambiverse_resources.json', 'w') as fp:
            json.dump(first_query, fp, default=json_serial)


    if new_predicate_flag == 1:
        if os.path.isfile('dataset/'+data_source+'possible_predicate.json'):
            os.remove('dataset/'+data_source+'possible_predicate.json')
        with open('dataset/'+data_source+'/possible_predicate.json', 'w') as fp:
            json.dump(possible_predicate, fp, default=json_serial)

    ex_time = time.time() - start_time
    # print "Total Execution Time: " + str(round(ex_time, 2))
    # print "{:<8} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} ".format('S.N.','p_res','r_res' 'p_rel', 'r_rel', 'p_ent', 'r_ent')
    # vals_sum=0
    # for k1,v1 in precision_recall_stats.iteritems():
    #     vals = v1
    #     p_res, r_res, p_r,r_r,p_eo,r_eo = vals
    #     print "{:<8} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}".format(k1,p_res, r_res, p_r, r_r,p_eo, r_eo)
    #     if k1 == '1':
    #         vals1 = vals
    #     else:
    #         vals_sum = map(operator.add,vals1,vals)
    #         # print vals,vals1,vals_avg
    #         vals1 = vals_sum
    # num_sent = len(sentence_list)
    # if vals_sum>0:
    #     vals_avg = [round((x/num_sent),2) for x in vals_sum]
    #     print "average",vals_avg


if os.path.isfile(data_source+'/triples_raw.json'):
    with open('dataset/'+data_source+'/triples_raw.json') as json_data:
        file_triples = json.load(json_data)
else:
    file_triples = {"a":"b"}


if KG_Miner:
    if os.path.isfile('nodes_id.json'):
        with open('nodes_id.json') as json_data:
            global_settings.nodes_id = json.load(json_data)

    if os.path.isfile('edge_types_id.json'):
        with open('edge_types_id.json') as json_data:
            global_settings.edge_id = json.load(json_data)

    if os.path.isfile('dataset/' + data_source + '/possible_predicate.json'):
        with open('dataset/' + data_source + '/possible_predicate.json') as json_data:
            possible_predicate = json.load(json_data)
    else:
        possible_predicate = {"a": "b"}


if os.path.isfile('dataset/'+data_source+'/ambiverse_resources.json'):
    with open('dataset/'+data_source+'/ambiverse_resources.json') as json_data:
        ambiverse_api.ambiverse_resources = json.load(json_data)
else:
    ambiverse_api.ambiverse_resources = {"a":"b"}

if os.path.isfile('lpmln_tests/predicate_set.json'):
    with open('lpmln_tests/predicate_set.json') as json_data:
        global_settings.predicate_set = json.load(json_data)
else:
    global_settings.predicate_set = {"a":"b"}




with open('dataset/'+data_source+'/sentences_test.csv') as f:
    reader = csv.DictReader(f)
    sentences_list = []
    id_list = []
    for i,row in enumerate(reader):
        sentence = row['sentence']
        sentences_list.append(row['sentence'])
        id_list.append(row['id'])
    fact_checker(sentences_list, id_list)
        # if i % 20 != 0:
        #     sentence_list.append(sentence)
        #     if i == len(sentences):
        #         fact_checker(sentence_list)
        # else:
        #     fact_checker(sentence_list)
        #     sentence_list = []
        #     sentence_list.append(sentence)
