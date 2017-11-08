import csv
import sys
from config import evidence_threshold, rule_threshold, unwanted_predicates
import subprocess
import re
from nltk.stem.wordnet import WordNetLemmatizer
from ordered_set import OrderedSet
from kb_query import distance_three_query, distance_one_query, distance_two_query
from os import path, remove, mkdir
from more_itertools import unique_everseen
import json
from resource_writer import json_serial

lemmatizer = WordNetLemmatizer()


def get_rules(poi, data_source):
    with open('LPmln/' + data_source + '/spouse_relation.csv') as f:
        reader = csv.DictReader(f)
        rules = []
        confidence = []
        for row in reader:
            if row['PCA Confidence'] > rule_threshold:
                print row['Rule'],   row['PCA Confidence']


def relation_extractor_triples(resources, triples):
    distance_three = []
    distance_one = []
    distance_two = []
    unique_predicates = []
    for triple_k, triples_v in triples.iteritems():
        for triple_v in triples_v:
            item1_v = resources.get(triple_v[0])
            item2_v = resources.get(triple_v[1])
            if item1_v and item2_v:
                dbpedia_id1 = item1_v.get('dbpedia_id')
                dbpedia_id2 = item2_v.get('dbpedia_id')
                # wikidata_id1 = item1_v.get('wikidata_id')
                # wikidata_id2 = item2_v.get('wikidata_id')
                score1 = item1_v.get('confidence')
                score2 = item2_v.get('confidence')
                # distance_one, unique_predicates = distance_one_query('dbpedia', dbpedia_id1, distance_one,
                #                                                      unique_predicates)
                # distance_one, unique_predicates = distance_one_query('dbpedia', dbpedia_id2, distance_one,
                #                                                      unique_predicates)
                # distance_two, unique_predicates = distance_two_query('dbpedia', dbpedia_id1, distance_two, unique_predicates)
                # distance_two, unique_predicates = distance_two_query('dbpedia', dbpedia_id2, distance_two, unique_predicates)
                distance_three, unique_predicates = distance_three_query('dbpedia', dbpedia_id1, distance_three,
                                                                     unique_predicates)
                distance_three, unique_predicates = distance_three_query('dbpedia', dbpedia_id2, distance_three,
                                                                     unique_predicates)
    return distance_one, distance_two, distance_three


def inference(sentence_id, data_source, resource_v, top_k, predicate):
    print "LPMLN Inference"
    if path.isfile('LPmln/' +data_source + '/' + data_source + '_result.txt'):
        remove('LPmln/' +data_source + '/' + data_source + '_result.txt')
    evidence_source = 'LPmln/' + data_source + '/new_evidence_top'+top_k+'/' + sentence_id + data_source
    cmd = "lpmln2asp -i {0}new_rules/amie_confidence_top{2}.lpmln -q {3} -e {1}_full.db -r {0}result.txt ".format('LPmln/' +data_source + '/', evidence_source,top_k, predicate)
    print cmd
    subprocess.call(cmd, shell=True)
    text = open('LPmln/' +data_source + '/' + 'result.txt', 'r')
    f = text.read()
    text.close()
    probs = re.findall("(\w+\(\'[\s\S].+)",f)
    probs = [p for p in probs if resource_v[1] in p or resource_v[0] in p]
    probs_test = [p for p in probs if resource_v[1] in p and resource_v[0] in p and predicate in p]
    return probs, probs_test


def clingo_map(sentence_id, data_source, resource_v,top_k, predicate):
    print "Clingo"
    evidence_source = 'LPmln/' + data_source + '/new_evidence_top'+top_k+'/' + sentence_id + data_source
    cmd = "clingo {0}new_rules/amie_hard_top{1}.lpmln {2}_full.db > {0}clingo_result.txt ".format('LPmln/' +data_source +\
                                                                                             '/', top_k,evidence_source)
    print cmd
    subprocess.call(cmd, shell=True)
    text = open('LPmln/' +data_source + '/' + 'clingo_result.txt', 'r')
    f = text.read()
    text.close()
    probs = re.findall("(\w+\([\s\S]+\"\))",f)
    # print probs
    if probs:
        probs = probs[0].split(' ')
        probs = [p for p in probs if resource_v[1] in p or resource_v[0] in p]
        probs_test = [p for p in probs if resource_v[1] in p and resource_v[0] in p and predicate in p]
    else:
        probs = []
        probs_test = []
    return probs, probs_test


def inference_hard(sentence_id, data_source, resource_v,top_k, predicate):
    print "LPMLN Hard Inference"
    evidence_source = 'LPmln/' + data_source + '/new_evidence_top'+top_k+'/' + sentence_id + data_source
    cmd = "lpmln2asp -i {0}new_rules/amie_hard_top{2}.lpmln -q {3} -e {1}_full.db -r {0}hard_result.txt".format(
        'LPmln/' + data_source + '/', evidence_source, top_k,predicate)
    print cmd
    subprocess.call(cmd, shell=True)
    text = open('LPmln/' + data_source + '/' + 'hard_result.txt', 'r')
    f = text.read()
    text.close()
    probs = re.findall("(\w+\(\'[\s\S].+)", f)
    probs = [p for p in probs if resource_v[1] in p or resource_v[0] in p]
    probs_test = [p for p in probs if resource_v[1] in p and resource_v[0] in p and predicate in p]
    return probs, probs_test


def evidence_writer1(filtered_evidence, sentence_id, data_source,resource_v,top_k, predicate):
    item_set = OrderedSet()
    print resource_v
    for evidence in filtered_evidence:
        rel_set = [r for r in evidence]
        if rel_set[0] in resource_v and rel_set[2] in resource_v and rel_set[1] == predicate:
            pass
        else:
            item_set.add(rel_set[1] + '("' + rel_set[0] + '","' + rel_set[2] + '").')
    with open('LPmln/' + data_source + '/new_evidence_top'+top_k+'/' + sentence_id + data_source + '_full.db', 'wb') as csvfile:
        for i in item_set:
            if '*' not in i:
                try:
                    csvfile.write(i+'\n')
                except:
                    pass
    return item_set


def get_rule_predicates(data_source,top_k):
    text = open('LPmln/' + data_source + '/new_rules/amie_hard_top'+top_k+'.lpmln', 'r')
    f = text.read()
    text.close()
    probs = re.findall("(\w+\()", f)
    probs = list(set(probs))
    predicates = [p.replace('(','') for p in probs]
    return predicates



def amie_tsv(item_set, data_source):
    with open('/media/apradhan/DATA/' +data_source + '/test_neg.tsv', 'wb') as csvfile:
        datawriter = csv.writer(csvfile, quoting=csv.QUOTE_NONE, delimiter='\t', skipinitialspace=True)
        for i in item_set:
            try:
                datawriter.writerow(i)
            except:
                pass
    # amie_tsv_unique(data_source)


def amie_tsv_unique(data_source):
    with open('/media/apradhan/DATA/' +data_source + '/founders_ntn.tsv', 'r') as f, \
            open('/media/apradhan/DATA/' + data_source + '/founders_unique_ntn.tsv', 'wb') as out_file:
        out_file.writelines(unique_everseen(f))


def amie_negative_tsv(item_set, data_source):
    with open('/media/apradhan/DATA/' +data_source + 'negative_all.tsv', 'wb') as csvfile:
        datawriter = csv.writer(csvfile, quoting=csv.QUOTE_NONE, delimiter='\t', skipinitialspace=True)
        for i in item_set:
            j = [entity.split('/')[-1] for entity in i]
            print j
            try:
               datawriter.writerow(j)
            except:
                pass