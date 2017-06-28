from sentence_analysis import sentence_tagger, get_nodes, triples_extractor
from resources_loader import load_files
from ambiverse_api import entity_parser
from kb_query import get_entity_type, get_description, get_kgminer_predicates
from config import data_source, aux_verb, rank_threshold, kgminer_predicate_threshold
from KGMiner import get_training_set, invoke_kgminer
from gensim.models import Word2Vec
from nltk import word_tokenize
import operator
import csv

import pprint
import numpy as np
from lpmln import relation_extractor_triples, evidence_writer, inference, get_rules
from resource_writer import update_resources

load_word2vec = True
model_wv_g = None


def word2vec_score(rel, triple_k):
    global load_word2vec
    global model_wv_g
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
                score = word2vec_score(ph, ky)
                predicate_ranked.append([predicate, score])
        sorted_values = sorted(predicate_ranked, key=operator.itemgetter(1), reverse=True)
        threshold_sorted = [vals for vals in sorted_values if vals[1] >= kgminer_predicate_threshold]
        # print sorted_values
        predicate_KG[ky] = sorted_values
        predicate_KG_threshold[ky] = threshold_sorted
    return predicate_KG, predicate_KG_threshold


def fact_checker(sentence_lis, id_list, true_labels, triple_flag, ambiverse_flag, kgminer_predicate_flag, \
                 lpmln_predicate_flag, kgminer_output_flag, KGMiner, lpmln):
    file_triples, ambiverse_resources, possible_kgminer_predicate, kgminer_output, lpmln_predicate = load_files()
    sentence_list = [word_tokenize(sent) for sent in sentence_lis]
    named_tags = sentence_tagger(sentence_list)
    kgminer_evaluation = []
    lpmln_evaluation = []
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
        # get poi
        type_ontology, type_resource, type_ontology_full, type_resource_full = get_entity_type(resource, \
                                                                                               triple_dict)
        if sentence_id not in possible_kgminer_predicate.keys():                

            kgminer_predicates = get_kgminer_predicates(type_ontology, triple_dict)
            kgminer_predicate_ranked, kgminer_predicate_threshold = predicate_ranker(kgminer_predicates,\
                                                                                                 triple_dict)
            if kgminer_predicate_ranked:
                kgminer_predicate_flag = True
                possible_kgminer_predicate[sentence_id] = kgminer_predicate_ranked
        else:
            kgminer_predicate_ranked = possible_kgminer_predicate[sentence_id]

        print "Ranked Possible Predicates"
        print kgminer_predicate_ranked
        predicate_of_interest = kgminer_predicate_ranked.values()[0]
                
        if KGMiner:
            kg_output = []
            print "Link Prediction with KG_Miner"
            if sentence_id not in kgminer_output.keys():
                if kgminer_predicate_ranked.values()[0]:
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
                    predicted_label = 'A'
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

        if lpmln:
            print "Executing LPMLN"
            if sentence_id not in lpmln_predicate.keys():
                relation_ent, relation_ent_0, relation_ent_2 = relation_extractor_triples(resource, triple_dict)
                unique_predicates = [evidence[1] for evidence in relation_ent]
                unique_predicates = list(set(unique_predicates))
                relation = triple_dict.keys()[0]
                scored_predicates = [[unique_predicate, word2vec_score(unique_predicate, relation)] for unique_predicate \
                                     in unique_predicates]
                predicate_dict = dict(scored_predicates)
                print predicate_dict
                for ev in relation_ent:
                    ev.append(predicate_dict.get(ev[1], 0))
                sorted_predicates = sorted(relation_ent, key=operator.itemgetter(4), reverse=True)
                lpmln_predicate[sentence_id] = sorted_predicates
                lpmln_predicate_flag = True
            else:
                sorted_predicates = lpmln_predicate.get(sentence_id, {})
            print sorted_predicates
            evidence_writer(sorted_predicates, sentence_id)
            print predicate_of_interest
            get_rules(predicate_of_interest)
            probability = inference(sentence_id)
            lpmln_evaluation.append([probability.extend(sentence_id)])

        update_resources(triple_flag, ambiverse_flag, kgminer_predicate_flag, lpmln_predicate_flag, \
                         kgminer_output_flag, file_triples, ambiverse_resources, possible_kgminer_predicate,\
                         lpmln_predicate, kgminer_output)

    print kgminer_evaluation
    if kgminer_evaluation:
        with open('dataset/'+ data_source + '/kgminer_evaluation.csv', 'wb') as csvfile:
            datawriter = csv.writer(csvfile)
            datawriter.writerows(kgminer_evaluation)

    print lpmln_evaluation
    if lpmln_evaluation:
        with open('dataset/' + data_source + '/lpmln_evaluation.csv', 'wb') as csvfile:
            datawriter = csv.writer(csvfile)
            datawriter.writerows(lpmln_evaluation)


if __name__ == "__main__":
    with open('dataset/' + data_source + '/sentences_test.csv') as f:
        reader = csv.DictReader(f)
        sentences_list = []
        id_list = []
        true_label = []
        for row in reader:
            sentence = row['sentence']
            sentences_list.append(row['sentence'])
            true_label.append(row['label'])
            id_list.append(row['id'])
        fact_checker(sentences_list, id_list, true_label, triple_flag=False, ambiverse_flag=False, \
                     kgminer_predicate_flag=False, lpmln_predicate_flag=False, kgminer_output_flag=False, \
                     KGMiner=False, lpmln=True)