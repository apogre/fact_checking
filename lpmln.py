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


def inference(sentence_id, data_source):
    print "LPMLN Inference"
    if path.isfile('LPmln/' +data_source + '/' + data_source + '_result.txt'):
        remove('LPmln/' +data_source + '/' + data_source + '_result.txt')
    evidence_source = 'LPmln/' + data_source + '/evidence/' + sentence_id + data_source
    cmd = "lpmln2asp -i {0}_top5_amie.lpmln -q founders -all -e {1}_initials.db -r {0}_result.txt ".format('LPmln/' +data_source +\
                                                                                             '/' + data_source, evidence_source)
    print cmd
    subprocess.call(cmd, shell=True)
    text = open('LPmln/' +data_source + '/' + data_source + '_result.txt', 'r')
    f = text.read()
    text.close()
    probs = re.findall("(\w+\(\w+\,\s\w+\)\s\d+\.\d+)",f)
    return probs


def evidence_writer1(filtered_evidence, sentence_id, data_source):
    item_set = OrderedSet()
    for evidence in filtered_evidence:
        rel_set = [r.replace(' ', '_') if isinstance(r, basestring) else str(r) for r in evidence]
        item_set.add(rel_set[1].lower() + '("' + rel_set[0] + '","' + rel_set[2] + '").')

    if not path.isdir('LPmln/' + data_source):
        mkdir('LPmln/' + data_source)
        mkdir('LPmln/' + data_source + '/evidence/')

    with open('LPmln/' + data_source + '/evidence/' + sentence_id + data_source + '_full.db', 'wb') as csvfile:
        for i in item_set:
            if '*' not in i:
                try:
                    csvfile.write(i+'\n')
                except:
                    pass
    return item_set


def amie_tsv(item_set, data_source):
    with open('/media/apradhan/DATA/' +data_source + '_founders_all.tsv', 'ab') as csvfile:
        datawriter = csv.writer(csvfile, quoting=csv.QUOTE_NONE, delimiter='\t', skipinitialspace=True)
        for i in item_set:
            try:
                if 'Text_used_to_link_from_a_Wikipage_to_another_Wikipage' not in i and \
                                'Link_from_a_Wikipage_to_an_external_page' not in i and 'Wikipage_disambiguates' not in i:
                    datawriter.writerow(i)
            except:
                pass


def amie_tsv_unique(data_source):
    with open('/media/apradhan/DATA/' +data_source + '_founders_all.tsv', 'r') as f, \
            open('/media/apradhan/DATA/' + data_source + '_founders_unique_full.tsv', 'wb') as out_file:
        out_file.writelines(unique_everseen(f))