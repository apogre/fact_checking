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
    entity_mapping = dict()
    item_set = OrderedSet()
    item_set_initials = OrderedSet()
    maps_set = []
    count = 1
    for evidence in filtered_evidence:
        print evidence
        if evidence[0] not in entity_mapping.keys():
            if evidence[0][:2] not in maps_set:
                entity_mapping[evidence[0]] = evidence[0][:2]
                maps_set.append(evidence[0][:2])
            else:
                entity_mapping[evidence[0]] = str(evidence[0][:2]) + str(count)
                maps_set.append(str(evidence[0][:2]) + str(count))
                count += 1
        if evidence[2] not in entity_mapping.keys():
                if evidence[2][:2] not in maps_set:
                    entity_mapping[evidence[2]] = evidence[2][:2]
                    maps_set.append(evidence[2][:2])
                else:
                    entity_mapping[evidence[2]] = str(evidence[2][:2]) + str(count)
                    maps_set.append(str(evidence[2][:2]) + str(count))
                    count += 1
        rel_set = [r.replace(' ', '_') if isinstance(r, basestring) else str(r) for r in evidence]
        # item_set.add(lemmatizer.lemmatize(rel_set[1].lower()) + '(' + rel_set[0] + ',' + rel_set[2] + ').')
        item_set.add(rel_set[1].lower() + '(' + rel_set[0] + ',' + rel_set[2] + ').')
        item_set_initials.add(rel_set[1].lower() + '(' + entity_mapping.get(evidence[0], '').lower() + \
                              ',' + entity_mapping.get(evidence[2], '').lower() + ').')
    # print item_set_initials
    if not path.isdir('LPmln/' + data_source):
        mkdir('LPmln/' + data_source)
        mkdir('LPmln/' + data_source + '/evidence/')
    with open('LPmln/' + data_source + '/evidence/' + sentence_id + data_source + '_full.db', 'wb') as csvfile:
        datawriter = csv.writer(csvfile, quoting=csv.QUOTE_NONE, delimiter=' ', skipinitialspace=True)
        for i in item_set:
            try:
                datawriter.writerow([i])
            except:
                pass

    with open('LPmln/' + data_source + '/evidence/' + sentence_id + data_source + '_initials.db', 'wb') as csvfile:
        datawriter = csv.writer(csvfile, quoting=csv.QUOTE_NONE, delimiter=' ', skipinitialspace=True)
        # datawriter.writerows([[i] for i in item_set_initials])
        for i in item_set_initials:
            try:
                if '&' not in i and '*' not in i:
                    datawriter.writerow([i])
            except:
                pass
    inv_map = {v: k for k, v in entity_mapping.iteritems()}
    with open('LPmln/' + data_source + '/evidence/' + sentence_id + '_mappings.json', 'wb') as fp:
        json.dump(inv_map, fp, default=json_serial)
    return item_set


def evidence_writer(sorted_predicates, sentence_id, data_source):
    entity_mapping = dict()
    maps_set = []
    count = 1
    item_set = OrderedSet()
    item_set_initials = OrderedSet()
    final_list = []
    print sorted_predicates
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
        item_set_initials.add(lemmatizer.lemmatize(rel_set[1].lower()) + '(' + entity_mapping.get(rel[2], '').lower() + \
                              ',' + entity_mapping.get(rel[3], '').lower() + ').')
    print item_set
    if not path.isdir('LPmln/' + data_source):
        mkdir('LPmln/' + data_source)
        mkdir('LPmln/' + data_source + '/evidence/')
    with open('LPmln/' + data_source + '/evidence/' + sentence_id + data_source + '_full.db', 'wb') as csvfile:
        datawriter = csv.writer(csvfile, quoting=csv.QUOTE_NONE, delimiter=' ', skipinitialspace=True)
        for i in item_set:
            try:
                datawriter.writerow([i])
            except:
                pass

    with open('LPmln/' + data_source + '/evidence/' + sentence_id + data_source + '_initials.db', 'wb') as csvfile:
        datawriter = csv.writer(csvfile, quoting=csv.QUOTE_NONE, delimiter=' ', skipinitialspace=True)
        # datawriter.writerows([[i] for i in item_set_initials])
        for i in item_set_initials:
            try:
                datawriter.writerow([i])
            except:
                pass

    with open('LPmln/' + data_source + '/evidence/' + sentence_id + data_source + '_filter.db', 'wb') as csvfile:
        datawriter = csv.writer(csvfile, quoting=csv.QUOTE_NONE, delimiter=' ', skipinitialspace=True)
        for rel in sorted_predicates:
            rel_set = [r.replace(' ', '_') for r in rel if isinstance(r, basestring)]
            if rel[4] >= evidence_threshold:
                item_set = [lemmatizer.lemmatize(rel_set[1].lower())+'('+entity_mapping.get(rel[2],'').lower()+',' + \
                            entity_mapping.get(rel[3],'').lower()+').']
                if item_set[0] not in final_list:
                    final_list.append(item_set[0])
                    try:
                        datawriter.writerow(item_set)
                    except:
                        pass


def amie_tsv(item_set, data_source):
    with open('LPmln/' + data_source + '/' +data_source + '_full_3.tsv', 'wb') as csvfile:
        datawriter = csv.writer(csvfile, quoting=csv.QUOTE_NONE, delimiter='\t', skipinitialspace=True)
        for i in item_set:
            try:
                datawriter.writerow(i)
            except:
                pass
    with open('LPmln/' + data_source + '/' +data_source + '_full_3.tsv', 'r') as f, \
            open('LPmln/' + data_source + '/' +data_source + '_unique_3.tsv', 'w') as out_file:
        out_file.writelines(unique_everseen(f))