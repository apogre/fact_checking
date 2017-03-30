import sparql
import fact_check
import operator

entity_type_threshold=0.5
sparql_dbpedia = 'http://localhost:8890/sparql'
sparql_dbpedia_on = 'https://dbpedia.org/sparql'


def entity_type_extractor(resources, triples, ent_dict):
    print resources
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
        print len(sorted_values)
        type_set_ranked[k] = sorted_values
        threshold_sorted = [vals for vals in sorted_values if vals[1] >= entity_type_threshold]
        print len(threshold_sorted)
        threshold_ranked[k] = threshold_sorted
    return type_set_ranked, threshold_ranked


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
