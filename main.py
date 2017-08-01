from sentence_analysis import sentence_tagger, get_nodes, triples_extractor
from resources_loader import load_files, load_lpmln_resource
from ambiverse_api import ambiverse_entity_parser, spotlight_entity_parser
from kb_query import get_entity_type, get_description, get_kgminer_predicates, resource_extractor
from config import aux_verb, rank_threshold, kgminer_predicate_threshold, KGMiner_data
from kgminer import get_training_set, invoke_kgminer, get_perfect_training, poi_writer, entity_id_finder, train_data_csv, \
    csv_writer
from gensim.models import Word2Vec
from shutil import copyfile
from nltk import word_tokenize
from os import environ, listdir, remove
import operator
import csv
import argparse
import sys
import pprint
import numpy as np
from lpmln import relation_extractor_triples, evidence_writer, inference, get_rules, amie_tsv
from resource_writer import update_resources

load_word2vec = True
model_wv_g = None


def word2vec_score_dummy(rel,triple):
    return 0


def word2vec_score(rel, triple_k):
    global load_word2vec
    global model_wv_g
    if load_word2vec:
        try:
            print "Loading Word2Vec"
            model_wv_g = Word2Vec.load_word2vec_format(str(environ['STANFORDTOOLSDIR']) + \
                                                       "/Google_Vectors/GoogleNews-vectors-negative300.bin", binary=True)
            load_word2vec = False
        except:
            print "Loading Word2Vec Failed"
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
            comment, label = get_description(predicate)
            # print comment, label
            score_label = 0
            score_comment = 0
            if comment:
                ph = comment[0][0]
                score_comment = word2vec_score(ph, ky)
            if label:
                ph = label[0][0]
                score_label = word2vec_score(ph, ky)
            score = max(score_label, score_comment)
            predicate_ranked.append([predicate, score])
        sorted_values = sorted(predicate_ranked, key=operator.itemgetter(1), reverse=True)
        threshold_sorted = [vals for vals in sorted_values if vals[1] >= kgminer_predicate_threshold]
        # print sorted_values
        predicate_KG[ky] = sorted_values
        predicate_KG_threshold[ky] = threshold_sorted
    return predicate_KG, predicate_KG_threshold


def fact_checker(sentence_lis, id_list, true_labels, load_mappings, triple_flag, ambiverse_flag, kgminer_predicate_flag, \
                 lpmln_predicate_flag, kgminer_output_flag, KGMiner, lpmln, lpmln_output_flag, data_source, kr, \
                 kgminer_output_random_flag, kp, kgminer_output_perfect_flag):
    file_triples, ambiverse_resources, possible_kgminer_predicate, kgminer_output, lpmln_predicate, lpmln_output, \
    kgminer_output_random, kgminer_output_perfect = load_files(data_source)
    sentence_count = len(sentence_lis)
    executed_sentence = 0
    kgminer_true_count = 0
    pre_kgminer = 0
    sentence_list = [word_tokenize(sent) for sent in sentence_lis]
    named_tags = sentence_tagger(sentence_list)
    kgminer_evaluation = []
    lpmln_evaluation = []
    amie_training = []
    accuracy = []
    stored_query = dict()
    for n, ne in enumerate(named_tags):
        kgminer_predicate_ranked = dict()
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
            triple_dict = triples_extractor(sentence_check, named_entities)
            if triple_dict:
                file_triples[sentence_id] = triple_dict
                triple_flag = True
        print "Relation Triples: "+str(triple_dict)
        if sentence_id in ambiverse_resources.keys():
            resource = ambiverse_resources[sentence_id]
        else:
            resource = ambiverse_entity_parser(sentence_check)
            ambiverse_resources[sentence_id] = resource
            ambiverse_flag = True
        print len(resource)
        if len(resource) < 2:
            # for entity_pair in triple_dict.values():
            #     print "here"
            #     for entity in entity_pair[0]:
            #         if entity not in resource.keys():
            #             resource_ids = resource_extractor(entity)
            #             resource[entity] = resource_ids
            resource = spotlight_entity_parser(sentence_check)
        print "Resource Extractor"
        print "=================="
        pprint.pprint(resource)
        # get poi
        type_ontology, type_resource, type_ontology_full, type_resource_full = get_entity_type(resource, triple_dict)
        print type_ontology, type_resource, type_ontology_full, type_resource_full
        if sentence_id not in possible_kgminer_predicate.keys():
            vals = sum(type_ontology.values(), [])
            relation = triple_dict.keys()
            print vals, relation
            if len(vals) > 1:
                if str(relation[0] + vals[0] + vals[1]) not in stored_query.keys():
                    kgminer_predicates = get_kgminer_predicates(type_ontology, triple_dict)
                    print kgminer_predicates
                    if kgminer_predicates:
                        kgminer_predicate_ranked, kgminer_predicate_threshold = predicate_ranker(kgminer_predicates, triple_dict)
                        if kgminer_predicate_ranked.values():
                            possible_kgminer_predicate[sentence_id] = kgminer_predicate_ranked
                            kgminer_predicate_flag = True
                            stored_query[str(relation[0] + vals[0] + vals[1])] = kgminer_predicate_ranked
                            stored_query[str(relation[0] + vals[1] + vals[0])] = kgminer_predicate_ranked
                else:
                    print "Using Stored Predicate"
                    kgminer_predicate_ranked = stored_query[str(relation[0] + vals[0] + vals[1])]
                    possible_kgminer_predicate[sentence_id] = kgminer_predicate_ranked
                    kgminer_predicate_flag = True
        else:
            kgminer_predicate_ranked = possible_kgminer_predicate[sentence_id]
        # print "Ranked Predicates"
        # print kgminer_predicate_ranked
        if KGMiner:
            if kgminer_predicate_ranked:
                kg_output = []
                print "Link Prediction with KG_Miner"
                if kr:
                    if sentence_id not in kgminer_output_random.keys():
                        kgminer_status = get_training_set(kgminer_predicate_ranked, type_resource_full,
                                                          type_ontology_full, \
                                                          triple_dict, resource, sentence_id, data_source, kr)
                        if kgminer_status:
                            predicate_result = invoke_kgminer()
                            if predicate_result:
                                kg_output = predicate_result.values()
                                kgminer_output_random[sentence_id] = predicate_result
                                kgminer_output_random_flag = True
                            else:
                                print "kgminer random failed"
                    else:
                        print kgminer_output_random[sentence_id]
                        kg_output = kgminer_output_random[sentence_id].values()
                elif kp:
                    if sentence_id not in kgminer_output_perfect.keys():
                        training_set, test_data, resource_v = get_perfect_training(data_source, resource, triple_dict)
                        print resource_v
                        predicate_set = kgminer_predicate_ranked.values()
                        for predicate_of_interest in predicate_set[0][:10]:
                            if None not in test_data and predicate_of_interest:
                                poi = predicate_of_interest[0]
                                print poi
                                poi_writer(poi, sentence_id, data_source)
                                node_ids = entity_id_finder(training_set)
                                training_data, test_data = train_data_csv(training_set, node_ids, resource_v)
                                csv_writer(training_data,
                                           file_name=data_source + '/' + sentence_id + data_source + 'perfect_ids')
                                copyfile(KGMiner_data + '/' + data_source + '/' + sentence_id + data_source +\
                                         'perfect_ids.csv', KGMiner_data + '/' + 'training_data.csv')
                                predicate_result = invoke_kgminer()
                                if predicate_result:
                                    kg_output = predicate_result.values()
                                    kgminer_output_perfect[sentence_id] = predicate_result
                                    kgminer_output_perfect_flag = True
                                    break
                                else:
                                    print "kgminer random failed"
                    else:
                        print kgminer_output_perfect[sentence_id]
                        kg_output = kgminer_output_perfect[sentence_id].values()
                else:
                    if sentence_id not in kgminer_output.keys():
                        if kgminer_predicate_ranked.values():
                            # print kgminer_predicate_ranked
                            kgminer_status = get_training_set(kgminer_predicate_ranked, type_resource_full, type_ontology_full,\
                                                              triple_dict, resource, sentence_id, data_source, kr)
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
                            kgminer_predicted_label = 'A'
                    else:
                        print kgminer_output[sentence_id]
                        kg_output = kgminer_output[sentence_id].values()
                if kg_output:
                    kgminer_score = float(kg_output[0])
                    if kgminer_score <= 0.5:
                        kgminer_predicted_label = 'T'
                    elif kgminer_score > 0.5:
                        kgminer_predicted_label = 'F'
                    else:
                        kgminer_predicted_label = 'N'
                else:
                    kgminer_predicted_label = 'N'
            if kgminer_predicted_label == 'N' or kgminer_predicted_label == 'A':
                pre_kgminer += 1
            else:
                executed_sentence += 1
            if true_label == kgminer_predicted_label:
                kgminer_true_count += 1
            kgminer_evaluation.append([sentence_id, sentence_check, true_label, kgminer_predicted_label])

        if lpmln:
            print "Executing LPMLN"
            if load_mappings:
                print "Loading DBpedia to Wikidata Mappings"
                predicate_dict = load_lpmln_resource()
                load_mappings = False
            relation_ent, relation_ent_0, relation_ent_2, distance_one = relation_extractor_triples(resource,\
                                                                                                    triple_dict)
            amie_training.extend(distance_one)
            if sentence_id not in lpmln_predicate.keys():
                sorted_predicates = []
                relation_ent, relation_ent_0, relation_ent_2, distance_two = relation_extractor_triples(resource, triple_dict)
                amie_training.extend(distance_two)
                print relation_ent
                print relation_ent_0
                print relation_ent_2
                # print distance_one
                relation_ent += relation_ent_0
                if relation_ent:
                    unique_predicates = [evidence[1] for evidence in relation_ent]
                    unique_predicates = list(set(unique_predicates))
                    print unique_predicates
                    relation = triple_dict.keys()[0]
                    scored_predicates = [[unique_predicate, word2vec_score_dummy(unique_predicate, relation)] for unique_predicate \
                                         in unique_predicates]
                    predicate_dict = dict(scored_predicates)
                    for ev in relation_ent:
                        ev.append(predicate_dict.get(ev[1], 0))
                    sorted_predicates = sorted(relation_ent, key=operator.itemgetter(4), reverse=True)
                    lpmln_predicate[sentence_id] = sorted_predicates
                    lpmln_predicate_flag = True
            else:
                sorted_predicates = lpmln_predicate.get(sentence_id, {})
            print sorted_predicates
            if sentence_id not in lpmln_output.keys():
                if sorted_predicates:
                    evidence_writer(sorted_predicates, sentence_id, data_source)
                    # get_rules(predicate_of_interest)
                    # probability = inference(sentence_id, data_source)
                    probability = [1]
                    print probability
                else:
                    probability = 'Evidence Not Found'
            else:
                probability = lpmln_output[sentence_id]
            lpmln_evaluation.append([sentence_id, sentence_check, str(probability)])
            print probability
        update_resources(triple_flag, ambiverse_flag, kgminer_predicate_flag, lpmln_predicate_flag, \
                         kgminer_output_flag, file_triples, ambiverse_resources, possible_kgminer_predicate,\
                         lpmln_predicate, kgminer_output, lpmln_output_flag, data_source, kgminer_output_random_flag, \
                         kgminer_output_random, kgminer_output_perfect_flag, kgminer_output_perfect)

    amie_tsv(amie_training, data_source)

    if KGMiner:
        kgminer_accuracy = float(kgminer_true_count)/float(executed_sentence)
        accuracy.append([data_source, (sentence_count-executed_sentence), kgminer_true_count, executed_sentence, kgminer_accuracy])
        print accuracy

    if kgminer_evaluation and kr:
        print kgminer_evaluation
        with open('dataset/'+ data_source + '/kgminer_evaluation.csv', 'wb') as csvfile:
            datawriter = csv.writer(csvfile)
            datawriter.writerows(kgminer_evaluation)
    else:
        print kgminer_evaluation
        with open('dataset/' + data_source + '/kgminer_random_evaluation.csv', 'wb') as csvfile:
            datawriter = csv.writer(csvfile)
            datawriter.writerows(kgminer_evaluation)

    if lpmln_evaluation:
        print lpmln_evaluation
        with open('dataset/' + data_source + '/lpmln_evaluation.csv', 'wb') as csvfile:
            datawriter = csv.writer(csvfile)
            datawriter.writerows(lpmln_evaluation)


def cleanup_data(sentence_id, test_data):
    training_files = listdir(KGMiner_data + '/' + test_data)
    resource_files = listdir('dataset/' + test_data)
    if 'kgminer_output.json' in resource_files:
        remove('dataset/' + test_data + '/kgminer_output.json')
    if sentence_id + test_data + '_ids.csv' in training_files:
        print "Removing Training Data"
        remove(KGMiner_data + '/' + test_data + '/' + sentence_id + test_data + '_ids.csv')
        remove(KGMiner_data + '/' + test_data + '/' + sentence_id + test_data + '.csv')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", default='sentences_test.csv')
    parser.add_argument("-k", "--kgminer", default=False)
    parser.add_argument("-kr", "--kgminer_random", default=False)
    parser.add_argument("-kp", "--kgminer_perfect", default=False)
    parser.add_argument("-l", "--lpmln", default=False)
    parser.add_argument("-t", "--test_data", default='sample_case')
    parser.add_argument("-s", "--sentence", default='')
    parser.add_argument("-c", "--cleanup_id", default=None)
    args = parser.parse_args()
    if args.cleanup_id:
        cleanup_data(args.cleanup_id, args.test_data)
    with open('dataset/' + args.test_data + '/' + args.input) as f:
        reader = csv.DictReader(f)
        sentences_list = []
        id_list = []
        true_label = []
        if args.sentence:
            sentences_list = [args.sentence]
            id_list = ['0']
            true_label = ['X']
        else:
            for row in reader:
                sentences_list.append(row.get('sentence'))
                true_label.append(row.get('label'))
                id_list.append(row.get('id'))
        if args.lpmln:
            load_mappings = True
        else:
            load_mappings = False
        fact_checker(sentences_list, id_list, true_label, load_mappings, triple_flag=False, ambiverse_flag=False, \
                     kgminer_predicate_flag=False, lpmln_predicate_flag=False, kgminer_output_flag=False, \
                     KGMiner=args.kgminer, lpmln=args.lpmln, lpmln_output_flag=False, data_source=args.test_data, \
                     kr=args.kgminer_random, kgminer_output_random_flag=False, kp=args.kgminer_perfect, \
                     kgminer_output_perfect_flag = False)
