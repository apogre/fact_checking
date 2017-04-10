import sparql
import fact_check
import operator
import csv
import sys
import os
import subprocess

entity_type_threshold=0
possible_predicate_threshold = 1
sparql_dbpedia = 'http://localhost:8890/sparql'
sparql_dbpedia_on = 'https://dbpedia.org/sparql'

kg_data_source = 'KG_Miner_data/'


def entity_type_extractor(resources, triples, ent_dict):
    # print resources
    type_set_ontology = {}
    type_set_resource = {}
    for triple_k, triples_v in triples.iteritems():
        for triple_v in triples_v:
            for ent in triple_v:
                item1_v = resources[ent]
                type_list_ontology = []
                type_list_resource = []
                for i1 in item1_v:
                    if 'dbpedia' in i1[0]:
                        url1 = i1[0]
                        q_type = ('PREFIX dbo: <http://dbpedia.org/ontology/> SELECT distinct ?t WHERE {{ <' + url1 + '> dbo:type ?t .} UNION { <' + url1 + '> rdf:type ?t .}}')
                        # print q_type
                        result = sparql.query(sparql_dbpedia, q_type)
                        type_values = [sparql.unpack_row(row_result) for row_result in result]
                        type_ontology = [val[0] for val in type_values if 'ontology' in val[0]]
                        type_resource = [val[0] for val in type_values if 'resource' in val[0]]
                        type_list_ontology.extend(type_ontology)
                        type_list_resource.extend(type_resource)
                type_set_ontology[ent] = list(set(type_list_ontology))
                type_set_resource[ent] = list(set(type_list_resource))
    return type_set_ontology, type_set_resource


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


def entity_type_ranker(type_set, ent_dict,triple_dict):
    type_set_ranked = {}
    threshold_ranked = {}
    for k, v in ent_dict.iteritems():
        # print k
        type_ranked = []
        for ent_type in type_set[k]:
            # type_full = "http://dbpedia.org/resource/" + ent_type
            phrase = fact_check.comment_extractor(ent_type)
            # print phrase
            if phrase:
                score_enitity_type = max(fact_check.compare(v, ph[0]) for ph in phrase if isinstance(ph[0], basestring))
                score_entity_relation = 0
                for kt,vt in triple_dict.iteritems():
                    # print k, vt
                    if k in vt[0]:
                        score_entity_relation = max(fact_check.compare(kt, ph[0]) for ph in phrase if isinstance(ph[0], basestring))
                score = (score_enitity_type+score_entity_relation)/2
                try:
                    score = round(score, 2)
                except:
                    pass
                # type_ranked.append([ent_type.split('/')[-1], score])
                type_ranked.append([ent_type, score])
        sorted_values = sorted(type_ranked, key=operator.itemgetter(1), reverse=True)
        # print len(sorted_values)
        type_set_ranked[k] = sorted_values
        threshold_sorted = [vals for vals in sorted_values if vals[1] >= entity_type_threshold]
        # print len(threshold_sorted)
        threshold_ranked[k] = threshold_sorted
    return type_set_ranked, threshold_ranked


def entity_id_finder(entity_set):
    # id_set = {}
    # for label, e_set in entity_set.iteritems():
    id_list = []
    # print entity_set
    with open("infobox.nodes", "rb") as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        # print label
        for row in reader:
            try:
                if row[1] in entity_set:
                    id_list.append(row)
                    print row
            except:
                pass
            # id_set[label] = id_list
    return id_list

def kg_miner_csv(training_data, file_name):
    with open(kg_data_source+file_name+'.csv', 'wb') as csvfile:
        datawriter = csv.writer(csvfile)
        # id_keys = id_set.keys()
        # for k,v in id_set.iteritems():
        # val1 = id_set[id_keys[0]]
        # val2 = id_set[id_keys[1]]
        # print val1, len(val1)
        # print val2, len(val2)
        # data_size = len(val1) * len(val2)
        for data in training_data:
            datawriter.writerow(data)


def possible_predicate_type(type_set, triples):
    predicate_list = []
    pair_list = []
    count = 0
    for triple_k, triples_v in triples.iteritems():
        for triple_v in triples_v:
            item1_v = type_set[triple_v[0]]
            item2_v = type_set[triple_v[1]]
            # print len(item1_v), len(item2_v)
            print "===================="
            for it1 in item1_v:
                for it2 in item2_v:
                    if it1[0] != it2[0]:
                        q_pp = 'SELECT distinct ?p WHERE { ?url1 rdf:type <' + \
                               it1[0] + '> . ?url2 rdf:type <' + it2[
                                   0] + '> . {?url1 ?p ?url2 .} UNION {?url2 ?p ?url1 .}}'
                    else:
                        q_pp = 'SELECT distinct ?p WHERE { ?url1 rdf:type <' + \
                               it1[0] + '> . ?url2 rdf:type <' + it2[
                                   0] + '> . ?url1 ?p ?url2 .}'
                    # print q_pp
                    pair = [it1[0], it2[0]]
                    if pair not in pair_list:
                        try:
                            result = sparql.query(sparql_dbpedia_on, q_pp)
                            pred_values = [sparql.unpack_row(row_result) for row_result in result]
                            if pred_values:
                                pair_list.append(pair)
                                pred_vals = [val[0].split('/')[-1] for val in pred_values if
                                             'ontology' in val[0]]
                                # print pred_vals
                                predicate_list.extend(pred_vals)
                                count = count + 1
                                print count
                        except:
                            pass
    predicate_list = list(set(predicate_list))
    return predicate_list


def predicate_ranker(predicates, triple):
    predicate_KG = {}
    predicate_KG_threshold = {}
    for ky in triple.keys():
        print ky
        predicate_ranked = []
        for k in ky.split():
            if k not in fact_check.aux_verb:
                for predicate in predicates:
                    predicate_full = "http://dbpedia.org/ontology/" + predicate
                    phrase = fact_check.comment_extractor(predicate_full)
                    if phrase:
                        # print k, predicate
                        score = max(fact_check.compare(k, ph[0]) for ph in phrase if isinstance(ph[0], basestring))
                        try:
                            score = round(score, 2)
                        except:
                            pass
                        # print score
                        predicate_ranked.append([predicate, score])
        sorted_values = sorted(predicate_ranked, key=operator.itemgetter(1), reverse=True)
        threshold_sorted = [vals for vals in sorted_values if vals[1] >= possible_predicate_threshold]
        # print sorted_values
        predicate_KG[ky] = sorted_values
        predicate_KG_threshold[ky] = threshold_sorted
    return predicate_KG , predicate_KG_threshold


def train_data_csv(train_ents, node_ids):
    training_data=[]
    test_data = []
    for i in range(0, len(train_ents)-2,2):
            id_one = [row[0] for row in node_ids if train_ents[i]==row[1]]
            if id_one:
                try:
                    # print id_one
                    id_two = [row[0] for row in node_ids if train_ents[i+1]==row[1]]
                    if id_two and train_ents[i] != 'Arizona' and train_ents[i+1] != 'Phoenix,_Arizona':
                        # print id_two
                        training_data.append([id_one[0], id_two[0]])
                    else:
                        test_data.append([id_one[0], id_two[0]])
                except:
                    pass
    return training_data, test_data


def or_query_prep(resource_type_set_ranked, ontology_threshold_ranked):
    q_part_base = '?url1 rdf:type <'
    q_part = ''
    for k, v in ontology_threshold_ranked.iteritems():
        # print k
        for val in v:
            # print val
            q_part = q_part + q_part_base + val[0] + '> . '
        q_part_base = '?url2 rdf:type <'
    # print q_part
    q_part_base_res = '?url1 dbo:type <'
    q_part_res = ''
    for k, v in resource_type_set_ranked.iteritems():
        # print k
        for val in v:
            # print val
            q_part_res = q_part_res + q_part_base_res + val[0] + '> . '
        q_part_base_res = '?url2 dbo:type <'
    return q_part, q_part_res


def and_query_prep(resource_type_set_ranked, ontology_threshold_ranked):
    q_part_base = '{?url1 rdf:type <'
    q_part = ''
    for k, v in ontology_threshold_ranked.iteritems():
        # print k
        for val in v:
            # print val
            q_part = q_part + q_part_base + val[0] + '> } UNION '
        q_part_base = '{ ?url2 rdf:type <'
    # print q_part
    q_part_base_res = '{ ?url1 dbo:type <'
    q_part_res = ''
    for k, v in resource_type_set_ranked.iteritems():
        # print k
        for val in v:
            # print val
            q_part_res = q_part_res + q_part_base_res + val[0] + '> } '
        q_part_base_res = '{?url2 dbo:type <'
    return q_part, q_part_res


def get_training_set(predicate_ranked, resource_type_set_ranked, ontology_threshold_ranked):
    # print resource_type_set_ranked
    # print ontology_type_set_ranked
    # q_part, q_part_res = or_query_prep(resource_type_set_ranked,ontology_threshold_ranked)
    q_part, q_part_res = and_query_prep(resource_type_set_ranked,ontology_threshold_ranked)
    # sys.exit(0)
    for sent_pred in predicate_ranked.keys():
        predicate_of_interest = predicate_ranked[sent_pred]
        for poi in predicate_of_interest:
            print poi
            q_ts = 'PREFIX dbo: <http://dbpedia.org/ontology/> select distinct ?url1 ?url2 where { {?url1 <http://dbpedia.org/ontology/' + poi[
                0] + '> ?url2} UNION {?url2 <http://dbpedia.org/ontology/' + poi[
                0] + '> ?url1}. ' + q_part+q_part_res+'.} limit 50'
                     # ' ?url1 rdf:type <http://dbpedia.org/ontology/Region> . ?url1 rdf:type <http://dbpedia.org/ontology/PopulatedPlace>. ' \
                     # '?url1 rdf:type <http://dbpedia.org/ontology/Place> . ?url2 dbo:type <http://dbpedia.org/resource/List_of_capitals_in_the_United_States>. ' \
                     # '?url2 rdf:type <http://dbpedia.org/ontology/PopulatedPlace>. ?url2 rdf:type <http://dbpedia.org/ontology/Place> .' \
            # print q_ts
            result = sparql.query(sparql_dbpedia, q_ts)
            training_set = [sparql.unpack_row(row_result) for row_result in result]
            if training_set:
                # print "here--------------"
                print q_ts
                # sys.exit(0)
                training_set = sum(training_set, [])
                train_ents = [val.split('/')[-1] for val in training_set]
                print train_ents
                node_ids = entity_id_finder(train_ents)
                # print node_ids
                training_data, test_data = train_data_csv(train_ents, node_ids)
                print training_data, test_data
                # execute the KGMINER script
                if training_data:
                    kg_miner_csv(training_data, file_name='training_data')
                # if test_data:
                #     kg_miner_csv(test_data, file_name='test_data')
                    os.chdir('KGMiner')
                    print "here"
                    subprocess.call('./run_test.sh')
                    os.chdir('..')