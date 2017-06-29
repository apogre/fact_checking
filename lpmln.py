import csv
from config import data_source, evidence_threshold, rule_threshold
import subprocess
import sys
import re
from nltk.stem.wordnet import WordNetLemmatizer
from ordered_set import OrderedSet
from kb_query import relation_extractor_0hop, relation_extractor_1hop, relation_extractor_2hop
from os import path, remove


lemmatizer = WordNetLemmatizer()


def get_rules(poi):
    with open('LPmln/' + data_source + '/spouse_relation.csv') as f:
        reader = csv.DictReader(f)
        rules = []
        confidence = []
        for row in reader:
            if row['PCA Confidence'] > rule_threshold:
                print row['Rule']  ,   row['PCA Confidence']


def relation_extractor_triples(resources, triples):
    relation = []
    relation_0 = []
    relation_2 = []
    for triple_k, triples_v in triples.iteritems():
        for triple_v in triples_v:
            item1_v = resources.get(triple_v[0])
            item2_v = resources.get(triple_v[1])
            if item1_v and item2_v:
                dbpedia_id1 = item1_v.get('dbpedia_id')
                dbpedia_id2 = item2_v.get('dbpedia_id')
                wikidata_id1 = item1_v.get('wikidata_id')
                wikidata_id2 = item2_v.get('wikidata_id')
                score1 = item1_v.get('confidence')
                score2 = item2_v.get('confidence')
                relation = relation_extractor_1hop('wikidata', wikidata_id1, wikidata_id2, triple_v, relation, triple_k)
                relation = relation_extractor_1hop('dbpedia', dbpedia_id1, dbpedia_id2, triple_v, relation, triple_k)
                relation_0 = relation_extractor_0hop('wikidata', wikidata_id1, wikidata_id2, triple_v, relation_0, triple_k)
                relation_0 = relation_extractor_0hop('dbpedia', dbpedia_id1, dbpedia_id2, triple_v, relation_0, triple_k)
                relation_2 = relation_extractor_2hop('wikidata', wikidata_id1, wikidata_id2, triple_v, relation_2, triple_k)
                relation_2 = relation_extractor_2hop('dbpedia', dbpedia_id1, dbpedia_id2, triple_v, relation_2, triple_k)
    return relation, relation_0, relation_2


def inference(sentence_id):
    print "LPMLN Inference"
    if path.isfile('LPmln/' +data_source + '/' + data_source + '_result.txt'):
        remove('LPmln/' +data_source + '/' + data_source + '_result.txt')
    evidence_source = 'LPmln/' + data_source + '/evidence/' + sentence_id + data_source
    cmd = "lpmln2asp -i {0}.lpmln -q spouse -all -e {1}_filter.db -r {0}_result.txt ".format('LPmln/' +data_source + '/' + data_source, evidence_source)
    print cmd
    subprocess.call(cmd, shell=True)
    text = open('LPmln/' +data_source + '/' + data_source + '_result.txt', 'r')
    f = text.read()
    text.close()
    probs = re.findall("(\w+\(\w+\,\s\w+\)\s\d+\.\d+)",f)
    return probs


def evidence_writer(sorted_predicates, sentence_id):
    entity_mapping = dict()
    maps_set = []
    count = 1
    item_set = OrderedSet()
    item_set_initials = OrderedSet()
    final_list = []
    for rel in sorted_predicates:
        if rel[2] not in entity_mapping.keys():
            if rel[2][:2] not in maps_set:
                entity_mapping[rel[2]] = rel[2][:2]
                maps_set.append(rel[2][:2])
            else:
                entity_mapping[rel[2]] = str(rel[2][:2]) + str(count)
                maps_set.append(str(rel[2][:2]) + str(count))
                count += 1
        if rel[3] not in entity_mapping.keys():
            if rel[3][:2] not in maps_set:
                entity_mapping[rel[3]] = rel[3][:2]
                maps_set.append(rel[3][:2])
            else:
                entity_mapping[rel[3]] = str(rel[3][:2]) + str(count)
                maps_set.append(str(rel[3][:2]) + str(count))
                count += 1
        rel_set = [r.replace(' ', '_') for r in rel if isinstance(r, basestring)]
        item_set.add(lemmatizer.lemmatize(rel_set[1].lower()) + '(' + rel_set[2] + ',' + rel_set[3] + ').')
        item_set_initials.add(lemmatizer.lemmatize(rel_set[1].lower()) + '(' + entity_mapping.get(rel[2],'').lower() + \
                              ',' + entity_mapping.get(rel[3], '').lower() + ').')

    with open('LPmln/' + data_source + '/evidence/' + sentence_id + data_source + '_full.db', 'wb') as csvfile:
        datawriter = csv.writer(csvfile, quoting=csv.QUOTE_NONE, delimiter=' ', skipinitialspace=True)
        datawriter.writerows([[i] for i in item_set])

    with open('LPmln/' + data_source + '/evidence/' + sentence_id + data_source + '_initials.db', 'wb') as csvfile:
        datawriter = csv.writer(csvfile, quoting=csv.QUOTE_NONE, delimiter=' ', skipinitialspace=True)
        datawriter.writerows([[i] for i in item_set_initials])

    with open('LPmln/' + data_source + '/evidence/' + sentence_id + data_source + '_filter.db', 'wb') as csvfile:
        datawriter = csv.writer(csvfile, quoting=csv.QUOTE_NONE, delimiter=' ', skipinitialspace=True)
        for rel in sorted_predicates:
            rel_set = [r.replace(' ', '_') for r in rel if isinstance(r, basestring)]
            if rel[4] >= evidence_threshold:
                item_set = [lemmatizer.lemmatize(rel_set[1].lower())+'('+entity_mapping.get(rel[2],'').lower()+',' + \
                            entity_mapping.get(rel[3],'').lower()+').']
                if item_set[0] not in final_list:
                    final_list.append(item_set[0])
                    datawriter.writerow(item_set)


