import sparql
import fact_check
import operator
import csv
import sys
import os
import subprocess
import global_settings

entity_type_threshold=0.16
possible_predicate_threshold = 0.25
sparql_dbpedia = 'http://localhost:8890/sparql'
sparql_dbpedia_on = 'https://dbpedia.org/sparql'

kg_data_source = 'KG_Miner_data/'


def get_leaf_nodes(type_values):
    leaf, root = [x[0] for x in type_values], [x[1] for x in type_values]
    leaves = [le for le in leaf if le not in root]
    return leaves

def entity_type_extractor(resources, triples):
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
                        q_type = ('PREFIX dbo: <http://dbpedia.org/ontology/> SELECT distinct ?t ?t1 WHERE {{ <' + url1 +\
                                  '> dbo:type ?t } UNION { <' + url1 + '> rdf:type ?t }. ?t rdfs:subClassOf ?t1 . \
                                  FILTER(STRSTARTS(STR(?t), "http://dbpedia.org/ontology") || STRSTARTS(STR(?t), \
                                  "http://dbpedia.org/resource")).}')
                        # print q_type
                        result = sparql.query(sparql_dbpedia, q_type)
                        type_values = [sparql.unpack_row(row_result) for row_result in result]
                        # print type_values
                        leaves = get_leaf_nodes(type_values)
                        # print leaves
                        # sys.exit(0)
                        type_ontology = [val for val in leaves if 'ontology' in val]
                        type_resource = [val for val in leaves if 'resource' in val]
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
    id_set = {}
    with open("infobox.nodes", "rb") as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        for row in reader:
            try:
                if row[1] in entity_set:
                    id_set[row[1]] =row[0]
            except:
                pass
    return id_set

def predicate_id_finder(poi):
    id_list = []
    with open("infobox.edgetypes", "rb") as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        # print label
        for row in reader:
            try:
                if row[1] == poi:
                    id_list.append(row)
                    print row
                    with open(kg_data_source + 'poi.csv', 'wb') as csvfile:
                        datawriter = csv.writer(csvfile)
                        datawriter.writerow([row[0]])
            except:
                pass
            # id_set[label] = id_list
    return id_list


def kg_miner_csv(input_data, file_name):
    with open(kg_data_source+file_name+'.csv', 'wb') as csvfile:
        datawriter = csv.writer(csvfile)
        for data in input_data:
            datawriter.writerow(data)


def possible_predicate_type(type_set, triples):
    predicate_list = []
    count = 0
    sort_list = {}
    for triple_k, triples_v in triples.iteritems():
        for triple_v in triples_v:
            item1_v = type_set[triple_v[0]]
            item2_v = type_set[triple_v[1]]
            for it1 in item1_v:
                for it2 in item2_v:
                    if it1 != it2:
                        if it2 in sort_list.keys() and it1 in sort_list.get(it2,[]):
                            q_pp = ''
                        else:
                            if it1 not in sort_list.keys():
                                sort_list[it1] = [it2]
                            else:
                                sort_list[it1].append(it2)
                            q_pp = 'SELECT distinct ?p WHERE { ?url1 rdf:type <' + \
                                   it1 + '> . ?url2 rdf:type <' + it2 + '> . {?url1 ?p ?url2 } UNION {?url2 ?p ?url1 } \
                                                        . FILTER(STRSTARTS(STR(?p), "http://dbpedia.org/ontology")). }'
                    else:
                        q_pp = 'SELECT distinct ?p WHERE { ?url1 rdf:type <' + \
                               it1 + '> . ?url2 rdf:type <' + it2 + '> . ?url1 ?p ?url2 .\
                                FILTER(STRSTARTS(STR(?p), "http://dbpedia.org/ontology")).}'
                    # print q_pp
                    try:
                        if len(q_pp)>1:
                            count = count + 1
                            print count
                            result = sparql.query(sparql_dbpedia_on, q_pp)
                            pred_values = [sparql.unpack_row(row_result) for row_result in result]
                            if pred_values:
                                pred_vals = [val[0].split('/')[-1] for val in pred_values]
                                # print pred_vals
                                # print len(pred_vals)
                                predicate_list.extend(pred_vals)
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


def train_data_csv(train_ents, node_ids, expected_entities):
    training_data=[]
    test_data = []
    for i in range(0, len(train_ents)-2,2):
            id_one = [row[0] for row in node_ids if train_ents[i]==row[1]]
            if id_one:
                try:
                    # print id_one
                    id_two = [row[0] for row in node_ids if train_ents[i+1]==row[1]]
                    if id_two and train_ents[i] not in expected_entities and train_ents[i+1] not in expected_entities:
                        # print id_two
                        training_data.append([id_one[0], id_two[0]])
                    else:
                        test_data.append([id_one[0], id_two[0]])
                except:
                    pass
    return training_data, test_data


def or_query_prep(resource_type_set_ranked, ontology_threshold_ranked):
    q_part_base = '{ ?url1 rdf:type <'
    q_part = ''
    for k, v in ontology_threshold_ranked.iteritems():
        # print k
        for i,val in enumerate(v):
            # print val
            q_part = q_part + q_part_base + val[0] + '>} UNION '
            if i == (len(v)-1):
                q_part = q_part + q_part_base + val[0] + '>} . '
        q_part_base = '{ ?url2 rdf:type <'
    # print q_part
    q_part_base_res = '{ ?url1 dbo:type <'
    q_part_res = ''
    for k, v in resource_type_set_ranked.iteritems():
        # print k
        for val in v:
            # print val
            q_part_res = q_part_res + q_part_base_res + val[0] + '> } UNION '
        q_part_base_res = '{ ?url2 dbo:type <'
    return q_part, q_part_res


def and_query_prep(resource_type_set_ranked, ontology_threshold_ranked):
    q_part_base = '{?url1 rdf:type <'
    q_part = ''
    for k, v in ontology_threshold_ranked.iteritems():
        # print k
        for i, val in enumerate(v):
            # print val
            if i==len(v)-1:
                q_part = q_part + q_part_base + val[0] + '> } '
            else:
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


def get_training_set(predicate_ranked, resource_type_set_ranked, ontology_threshold_ranked,ex_ent_all):
    print resource_type_set_ranked
    print ontology_threshold_ranked
    print predicate_ranked
    q_part, q_part_res = or_query_prep(resource_type_set_ranked,ontology_threshold_ranked)
    # q_part, q_part_res = and_query_prep(resource_type_set_ranked,ontology_threshold_ranked)
    print ex_ent_all
    # print q_part
    # print q_part_res
    test_node_ids = entity_id_finder(ex_ent_all)
    print test_node_ids
    test_data = [test_node_ids[ex_ent_all[0]],test_node_ids[ex_ent_all[1]]]
    print test_data
    kg_miner_csv([test_data], file_name='test_data')
    for sent_pred in predicate_ranked.keys():
        predicate_of_interest = predicate_ranked[sent_pred]
        for poi in predicate_of_interest:
            print poi
            # poi = ['spouse','1']
            pred_id = predicate_id_finder(poi[0])
            q_ts = 'PREFIX dbo: <http://dbpedia.org/ontology/> select distinct ?url1 ?url2 where { {?url1 <http://dbpedia.org/ontology/' + poi[
                0] + '> ?url2} . ' + q_part+q_part_res+'} '
            # print q_ts
            result = sparql.query(sparql_dbpedia, q_ts)
            training_set = [sparql.unpack_row(row_result) for row_result in result]
            print len(training_set)
            if training_set:
                training_set = sum(training_set, [])
                train_ents = [val.split('/')[-1] for val in training_set]
                word_vec_train = []
                for j in range(0, len(train_ents)-1, 2):
                    # print 'DBPEDIA_ID/' + ex_ent_all[1], 'DBPEDIA_ID/' + train_ents[j]
                    # print 'DBPEDIA_ID/' + ex_ent_all[0], 'DBPEDIA_ID/' + train_ents[j+1]
                    try:
                        # print global_settings.model_wv.similarity('DBPEDIA_ID/Barack_Obama', 'DBPEDIA_ID/Michelle_Obama')
                        sim1 = global_settings.model_wv.similarity('DBPEDIA_ID/' + ex_ent_all[1],
                                                                  'DBPEDIA_ID/' + train_ents[j])
                        # print sim1
                        sim2 = global_settings.model_wv.similarity('DBPEDIA_ID/' + ex_ent_all[0],
                                                                  'DBPEDIA_ID/' + train_ents[j + 1])
                        # print sim2
                        # print train_ents[j], train_ents[j+1]
                        if sim1 > 0.2 and sim2 > 0.2:
                            # print [train_ents[j],train_ents[j+1]]
                            # print 'here'
                            word_vec_train.append([train_ents[j],train_ents[j+1]])
                    except:
                        pass

                if len(word_vec_train)>5:
                    print word_vec_train
                    word_vec_train = sum(word_vec_train,[])
                    print len(word_vec_train)
                    node_ids = entity_id_finder(word_vec_train)
                    # print node_ids
                    training_data, test_data = train_data_csv(word_vec_train, node_ids, ex_ent_all)
                    print training_data, test_data
                    if training_data:
                        print "Executing Classification"
                        kg_miner_csv(training_data, file_name='training_data')
                        os.chdir('KGMiner')
                        subprocess.call('./run_test.sh')
                        os.chdir('..')
                else:
                    print "Insufficient Training Set"
                sys.exit(0)