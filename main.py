from sentence_analysis import sentence_tagger, get_nodes, triples_extractor
from resources_loader import load_files, load_kgminer_resource
from ambiverse_api import entity_parser
from kb_query import get_entity_type, get_description, get_kgminer_predicates
from config import data_source, aux_verb, rank_threshold, kgminer_predicate_threshold
from KGMiner import get_training_set, invoke_kgminer
from gensim.models import Word2Vec
from nltk import word_tokenize
import operator, json
import collections, csv
from datetime import datetime
from os import path, getcwd, remove
import pprint, sys, getopt
import numpy as np

load_word2vec = True

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError ("Type not serializable")


def word2vec_score(rel, triple_k):
    global load_word2vec
    if load_word2vec:
        print "Loading Word2Vec"
        model_wv_g = Word2Vec.load_word2vec_format("/home/apradhan/Google_Vectors/GoogleNews-vectors-negative300.bin", \
                                                   binary=True)
        load_word2vec = False
        score = []
        try:
            for r in rel.split():
                if r not in aux_verb:
                    score.extend([model_wv_g.similarity(r, trip) for trip in triple_k.split() if trip not in aux_verb])
            return round(np.mean(score), 3)
        except:
            return 0


def word2vec_ranker(type_set, ent_dict):
    type_set_ranked = {}
    threshold_ranked = {}
    for k, v in ent_dict.iteritems():
        type_ranked = []
        for ent_type in type_set[k]:
            phrase = get_description(ent_type)
            if phrase:
                ph = phrase[0][0]
                score = word2vec_score(ph, v.lower())
                type_ranked.append([ent_type, score])
        sorted_values = sorted(type_ranked, key=operator.itemgetter(1), reverse=True)
        type_set_ranked[k] = sorted_values
        threshold_sorted = [vals for vals in sorted_values if vals[1] >= rank_threshold]
        threshold_ranked[k] = threshold_sorted
    return type_set_ranked, threshold_ranked


def predicate_ranker(predicates, triple):
    predicate_KG = {}
    predicate_KG_threshold = {}
    for ky in triple.keys():
        predicate_ranked = []
        for predicate in predicates:
            phrase = get_description(predicate)
            if phrase:
                ph = phrase[0][0]
                print ph, ky
                score = word2vec_score(ph, ky)
                print score
                predicate_ranked.append([predicate, score])
        sorted_values = sorted(predicate_ranked, key=operator.itemgetter(1), reverse=True)
        threshold_sorted = [vals for vals in sorted_values if vals[1] >= kgminer_predicate_threshold]
        # print sorted_values
        predicate_KG[ky] = sorted_values
        predicate_KG_threshold[ky] = threshold_sorted
    return predicate_KG, predicate_KG_threshold


def relation_processor(relations):
    predicate_set = []
    relation_graph = {}
    for item in relations:
        if item[1] not in predicate_set:
            predicate_set.append(item[1])
        if item[0] not in relation_graph.keys():
            relation_graph[item[0]] = [{'predicate':item[1], 'entity1':item[2], 'entity2':item[3], 'score':item[4]}]
        else:
            relation_graph[item[0]].extend([{'predicate': item[1], 'entity1': item[2], 'entity2': item[3],\
                                            'score': item[4]}])
    return relation_graph, predicate_set


def fact_checker(sentence_lis, id_list, true_labels, triple_flag, ambiverse_flag, kgminer_predicate_flag, kgminer_output_flag, KGMiner, lpmln):
    file_triples, ambiverse_resources, possible_kgminer_predicate, kgminer_output = load_files()
    sentence_list = [word_tokenize(sent) for sent in sentence_lis]
    named_tags = sentence_tagger(sentence_list)
    kgminer_evaluation = []
    for n, ne in enumerate(named_tags):
        sentence_id = id_list[n]
        true_label = true_labels[n]
        sentence_check = sentence_lis[n]
        print sentence_id, sentence_check, '\n'
        named_entities = get_nodes(ne)
        entity_dict = dict(named_entities)
        print "NER: "+str(entity_dict)
        if sentence_id in file_triples.keys():
            triple_dict = file_triples[sentence_id]
        else:
            triple_dict = triples_extractor(sentence_lis[n], named_entities)
            file_triples[sentence_id] = triple_dict
            triple_flag = True
        print "Relation Triples: "+str(triple_dict)
        if sentence_id in ambiverse_resources.keys():
            resource = ambiverse_resources[sentence_id]
        else:
            resource = entity_parser(sentence_lis[n])
            ambiverse_resources[sentence_id] = resource
            ambiverse_flag = True
        print "Resource Extractor"
        print "=================="
        pprint.pprint(resource)
        if KGMiner:
            kg_output = []
            print "Link Prediction with KG_Miner"
            if sentence_id not in kgminer_output.keys():
                type_ontology, type_resource, type_ontology_full, type_resource_full = get_entity_type(resource, triple_dict)
                print "Type of Entities"
                pprint.pprint(type_ontology)
                pprint.pprint(type_ontology_full)
                # resource_type_ranked, resource_threshold_ranked = word2vec_ranker(type_resource_full, \
                #                                                                       entity_dict, triple_dict)
                # ontology_type_ranked, ontology_threshold_ranked = word2vec_ranker(type_ontology_full, entity_dict,\
                #                                                                       triple_dict)
                if sentence_id in possible_kgminer_predicate.keys():
                    kgminer_predicate_ranked = possible_kgminer_predicate[sentence_id]
                else:
                    kgminer_predicates = get_kgminer_predicates(type_ontology, triple_dict)
                    kgminer_predicate_flag = True
                    kgminer_predicate_ranked, kgminer_predicate_threshold = predicate_ranker(kgminer_predicates, triple_dict)
                    possible_kgminer_predicate[sentence_id] = kgminer_predicate_ranked
                print "Ranked Possible Predicates"
                print kgminer_predicate_ranked
                if not kgminer_predicate_flag:
                    kgminer_status = get_training_set(kgminer_predicate_ranked, type_resource_full, type_ontology_full,\
                                                      triple_dict, resource, sentence_id)
                    if kgminer_status:
                        predicate_result = invoke_kgminer()
                        if predicate_result:
                            kg_output = predicate_result.values()
                            kgminer_output[sentence_id] = predicate_result
                            kgminer_output_flag = True
                        else:
                            print "kgminer failed"
                    else:
                        kg_output = [2]
            else:
                print kgminer_output[sentence_id]
                kg_output = kgminer_output[sentence_id].values()
            if kg_output:
                kgminer_score = float(kg_output[0])
                if kgminer_score < 0.5:
                    predicted_label = 'T'
                elif kgminer_score == 2:
                    predicted_label = 'N'
                else:
                    predicted_label = 'F'
                kgminer_evaluation.append([sentence_id, sentence_check, true_label, predicted_label])
        if triple_flag:
            print getcwd()
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
            if path.isfile('dataset/'+data_source+'possible_kgminer_predicate.json'):
                remove('dataset/'+data_source+'possible_kgminer_predicate.json')
            with open('dataset/'+data_source+'/possible_kgminer_predicate.json', 'w') as fp:
                json.dump(possible_kgminer_predicate, fp, default=json_serial)

        if kgminer_output_flag:
            print "Updating KGMiner Output"
            if path.isfile('dataset/' + data_source + 'kgminer_output.json'):
                remove('dataset/' + data_source + 'kgminer_output.json')
            with open('dataset/' + data_source + '/kgminer_output.json', 'w') as fp:
                json.dump(kgminer_output, fp, default=json_serial)

    print kgminer_evaluation
    with open('dataset/'+ data_source + '/evaluation.csv', 'wb') as csvfile:
        datawriter = csv.writer(csvfile)
        datawriter.writerows(kgminer_evaluation)

        # precision_ent, recall_ent, entity_matched = evaluation.precision_recall_entities(sentence_id, resource_text)
        # if precision_ent:
        #     precision_res = sum(precision_ent)/len(precision_ent)
        # else:
        #     precision_res = 0
        # if recall_ent:
        #     recall_res = sum(recall_ent)/len(recall_ent)
        # else:
        #     recall_res = 0
        # relation_ent, relation_ent_0, relation_ent_2 = fact_check.relation_extractor_triples(resource_text, triple_dict)
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
        # relations_0,  predicate_set_0 = fact_check.relation_processor(relation_ent_0)
        # relations, predicate_set = fact_check.relation_processor(relation_ent)
        # relations_2,  predicate_set_2 = fact_check.relation_processor(relation_ent_2)
        # print "0-hop Groundings"
        # print "================"
        # print relation_ent_0
        # print "0-hop Unique Predicates"
        # print "======================="
        # print predicate_set_0
        # print "1-hop Groundings"
        # print "================"
        # print relation_ent
        # print "1-hop Unique Predicates"
        # print "======================="
        # print predicate_set
        # # print "2-hop Groundings"
        # # print "================"
        # # print relation_ent_2
        # # print "2-hop Unique Predicates"
        # # print "======================="
        # # print predicate_set_2
        # # print "Relation Graph"
        # # print "--------------"
        #
        # lpmln_extention.evidence_writer(relation_ent, sentence_id)
        # probability = lpmln_extention.inference(sentence_id)
        # probability.append(sentence_id)
        # probabilities.append(probability)
        # print relations
        # sys.exit(0)
        # pprint.pprint(relations)
        # pprint.pprint(relations_0)
        # relations = False
        #
        # if relations:
        #     # output_relations[id_list[n]] = relations
        #
        #     execution_time = time.time() - res_time
        #     print execution_time
        #     # sys.exit(0)
        #     true_pos_rel, retrived_rels, ex_rels = evaluation.precision_recall_relations(sentence_id, relations)
        #     print true_pos_rel, retrived_rels, ex_rels
        #     true_pos_ent, retrieved_ents, ex_ent_all = evaluation.precision_recall_ent_match(sentence_id, relations)
        #     # print ex_ent_all
        #     print '\n'
        #     print "Precision & Recall for Entities"
        #     print "--------------------------------"
        #     precision_ent_out, recall_ent_out = evaluation.precision_recall(true_pos_ent, retrieved_ents, ex_ent_all)
        #     print "Entity Match: Precision: " + str(precision_ent_out), "Recall: " + str(recall_ent_out)
        #     print "------------------------------------------"
        #     print "Precision & Recall for Relations"
        #     print "--------------------------------"
        #     precision_rel, recall_rel = evaluation.precision_recall(true_pos_rel, retrived_rels, ex_rels)
        #     print "Relations: Precision: " + str(precision_rel), "Recall: " + str(recall_rel)
        #     precision_recall_stats[sentence_id] = [precision_res, recall_res, precision_rel, recall_rel, precision_ent_out, recall_ent_out]
        # else:
        #     precision_recall_stats[sentence_id] = [0, 0, 0, 0, 0, 0]

    #     if data_dump == True:
    #         with open(output_data+'/evaluation.json', 'w') as fp:
    #             json.dump(precision_recall_stats, fp, default=json_serial)
    #
    #         with open(output_data+'/kgminer_output.json', 'w') as fp:
    #             json.dump(output_linkprediction, fp, default=json_serial)
    #
    #         with open(output_data+'/training_data.json', 'w') as fp:
    #             json.dump(output_training_data, fp, default=json_serial)
    #
    #         with open(output_data+'/output_relations.json', 'w') as fp:
    #             json.dump(output_relations, fp, default=json_serial)
    # print output_linkprediction

    # with open('lpmln_tests/'+data_source +'/'+ data_source+'_prob.csv', 'wb') as csvfile:
    #     datawriter = csv.writer(csvfile)
    #     datawriter.writerows(probabilities)




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


#
# if os.path.isfile('lpmln_tests/predicate_set.json'):
#     with open('lpmln_tests/predicate_set.json') as json_data:
#         config.predicate_set = json.load(json_data)
# else:
#     config.predicate_set = {"a": "b"}


if __name__ == "__main__":
    with open('dataset/' + data_source + '/sentences.csv') as f:
        reader = csv.DictReader(f)
        sentences_list = []
        id_list = []
        true_label = []
        for row in reader:
            sentence = row['sentence']
            sentences_list.append(row['sentence'])
            true_label.append(row['label'])
            id_list.append(row['id'])
        fact_checker(sentences_list, id_list, true_label, triple_flag=False, ambiverse_flag=False, kgminer_predicate_flag=False,\
                     kgminer_output_flag=False, KGMiner=True, lpmln=False)
