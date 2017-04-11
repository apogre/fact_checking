import KG_Miner_Extension
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
import evaluation

aux_verb = ['was', 'is', 'become']
KG_Miner = True
precision_recall_stats = collections.OrderedDict()


# data_source = 'ug_data/all_'
data_source = 'main_data/'

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError ("Type not serializable")


def fact_checker(sentence_lis, id_list):
    dates = fact_check.date_parser(sentence_lis)
    sentence_list = [word_tokenize(sent) for sent in sentence_lis]
    # print sentence_list
    # sys.exit(0)
    ne_s, pos_s, dep_s = fact_check.st_tagger(sentence_list)
    # print dep_s
    verb_entity = fact_check.verb_entity_matcher(dep_s)
    start_time = time.time()
    new_triple_flag = 0
    new_predicate_flag = 0
    for i in range(0, 1):
        for n, ne in enumerate(ne_s):
            sent_id = id_list[n]
            print sent_id, sentence_lis[n],'\n'
            ent = fact_check.get_nodes_updated(ne)
            # print ent
            new_loc = fact_check.location_update(ne)
            if new_loc:
                new_ent = (new_loc[0], 'LOCATION')
                ent.append(new_ent)
            if dates[n]:
                date_string = (dates[n][0], 'DATE')
                ent.append(date_string)
            vb = fact_check.get_verb(pos_s[n])
            # print ent
            ent_dict = dict(ent)
    #         # sys.exit(0)
            res_time = time.time()
            # try:
            resources, ent_size, date_labels, raw_resources = fact_check.resource_extractor(ent)
            # except:
            #     print "resource error"
            # sys.exit(0)
            if sent_id in file_triples.keys():
                triple_dict = file_triples[sent_id]
            else:
                try:
                    os.remove('sentences.txt')
                except:
                    pass
                with open('sentences.txt', 'a') as text:
                    text.write(sentence_lis[n])
                triples_raw = stanford_ie("sentences.txt", verbose=False)
                triples = [[trip.lstrip() for trip in triple] for triple in triples_raw]
                triple_dict = fact_check.svo_finder(ent,triples)
                file_triples[sent_id] = triple_dict
                new_triple_flag = 1
            print triple_dict
            precision_ent, recall_ent, entity_matched = evaluation.precision_recall_entities(sent_id, resources)
            # print entity_matched
            # print resources
            resources = entity_matched
            # sys.exit(0)
            relation = []
            # Using entity_matched instead of all resource
            relation_ent = fact_check.relation_extractor_triples(resources, triple_dict, relation)
            # sys.exit(0)
            if not relation_ent:
                print "here"
                relation_ent, rel_count = fact_check.relation_extractor_all(resources, verb_entity[n])
            print "Precision & Recall for Resource Extractor"
            print "-----------------------------------------"
            relations = fact_check.relation_processor(relation_ent)
            print "Relation Graph"
            print "--------------"
            # print relations
            # sys.exit(0)
            if relations:
                pprint.pprint(relations)
                execution_time = time.time() - res_time
                print execution_time
                # sys.exit(0)
                true_pos_rel, retrived_rels, ex_rels = evaluation.precision_recall_relations1(sent_id, relations)
                true_pos_ent, retrieved_ents, ex_ent_all = evaluation.precision_recall_ent_match(sent_id, relations)
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
                precision_recall_stats[sent_id] = [precision_rel, recall_rel, precision_ent_out, recall_ent_out]
                if KG_Miner:
                    print "================================================================="
                    print "Using KG_Miner"
                    entity_type_ontology, entity_type_resource = KG_Miner_Extension.entity_type_extractor(resources, triple_dict, ent_dict)
                    pprint.pprint(entity_type_ontology)
                    pprint.pprint(entity_type_resource)
                    # sys.exit(0)
                    resource_type_set_ranked, resource_threshold_ranked = KG_Miner_Extension.entity_type_ranker(entity_type_resource, ent_dict, triple_dict)
                    ontology_type_set_ranked, ontology_threshold_ranked = KG_Miner_Extension.entity_type_ranker(entity_type_ontology, ent_dict, triple_dict)
                    pprint.pprint(resource_type_set_ranked)
                    pprint.pprint(ontology_threshold_ranked)
                    if sent_id in possible_predicate.keys():
                        possible_predicate_set = possible_predicate[sent_id]
                    else:
                        possible_predicate_set = KG_Miner_Extension.possible_predicate_type(ontology_type_set_ranked,triple_dict)
                        new_predicate_flag=1
                    # print possible_predicate_set
                    possible_predicate_set_ranked, possible_predicate_set_threshold = KG_Miner_Extension.predicate_ranker(possible_predicate_set,triple_dict)
                    # print possible_predicate_set
                    print possible_predicate_set_ranked
                    print possible_predicate_set_threshold
                    # sys.exit(0)

                    KG_Miner_Extension.get_training_set(possible_predicate_set_threshold, resource_type_set_ranked, ontology_threshold_ranked,ex_ent_all)


            else:
                precision_recall_stats[sent_id] = [0, 0, 0, 0]
            execution_time = time.time() - res_time
            print "Execution Time: " + str(round(execution_time, 2))
            print "================================================="

    if new_triple_flag == 1:
        os.remove(data_source+'triples_raw.json')
        with open(data_source+'/triples_raw.json', 'w') as fp:
            json.dump(file_triples, fp, default=json_serial)

    if new_predicate_flag == 1:
        os.remove(data_source+'possible_predicate.json')
        with open(data_source+'/possible_predicate.json', 'w') as fp:
            json.dump(possible_predicate_set, fp, default=json_serial)

    ex_time = time.time() - start_time
    print "Total Execution Time: " + str(round(ex_time, 2))
    print "{:<8} {:<10} {:<10} {:<10} {:<10} ".format('S.N.', 'p_rel', 'r_rel', 'p_ent', 'r_ent')
    vals_sum=0
    for k1,v1 in precision_recall_stats.iteritems():
        vals = v1
        p_r,r_r,p_eo,r_eo = vals
        print "{:<8} {:<10} {:<10} {:<10} {:<10}".format(k1, p_r, r_r,p_eo, r_eo)
        if k1 == '1':
            vals1 = vals
        else:
            vals_sum = map(operator.add,vals1,vals)
            # print vals,vals1,vals_avg
            vals1 = vals_sum
    num_sent = len(sentence_list)
    if vals_sum>0:
        vals_avg = [round((x/num_sent),2) for x in vals_sum]
        print "average",vals_avg



with open(data_source+'triples_raw.json') as json_data:
    file_triples = json.load(json_data)

with open(data_source+'possible_predicate.json') as json_data:
    possible_predicate = json.load(json_data)


with open(data_source+'sentences1.csv') as f:
    reader = csv.DictReader(f)
    sentences_list = []
    id_list = []
    for i,row in enumerate(reader):
        sentence = row['sentence']
        sentences_list.append(row['sentence'])
        id_list.append(row['id'])
    fact_checker(sentences_list,id_list)
        # if i % 20 != 0:
        #     sentence_list.append(sentence)
        #     if i == len(sentences):
        #         fact_checker(sentence_list)
        # else:
        #     fact_checker(sentence_list)
        #     sentence_list = []
        #     sentence_list.append(sentence)
