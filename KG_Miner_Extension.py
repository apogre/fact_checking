import sparql
import fact_check
import operator
import csv

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
    print entity_set
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

def test_set(training_data, file_name):
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


                # print type_set
#         # print type_set_ranked
#         # print threshold_ranked
#         # sys.exit(0)
#         # predicate_list = fact_check.possible_predicate_type(threshold_ranked,triple_dict)
#         # predicate_list = predicate_list_json["data1"]
#         # print predicate_list
#         # print len(predicate_list)
#         # sys.exit(0)
#         # predicate_ranked = fact_check.predicate_ranker(predicate_list,triple_dict)
#         # print predicate_ranked
#         # prob_value = fact_check.KG_implementation(predicate_ranked)
#         print relation_ent
#         # sys.exit(0)


#     predicate_list = fact_check.predicate_finder(triple_dict)
#     print predicate_list
#     entity_set = fact_check.entity_threshold(resources)
#     print entity_set
#     id_set = fact_check.entity_id_finder(entity_set)
#     print id_set
#     data_size = fact_check.test_set(id_set)
#     # fact_check.csv_processor(data_size)
