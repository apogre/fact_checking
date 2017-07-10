# -*- coding: utf-8 -*- 

import sparql
from config import sparql_dbpedia, sparql_dbpedia_on, sparql_wikidata, sparql_dbpedia_local
import sys

prefixes_dbpedia = "PREFIX entity: <http://dbpedia.org/resource/>"
prefixes_wikidata = "PREFIX entity: <http://www.wikidata.org/entity/>"

suffixes_wikidata = '?prop wikibase:directClaim ?p . ?prop1 wikibase:directClaim ?q . SERVICE wikibase:label \
                    {bd:serviceParam wikibase:language "en" . }'
suffixes_wikidata_2 = '?prop wikibase:directClaim ?p . ?prop1 wikibase:directClaim ?r . ?prop2 wikibase:directClaim ?q . \
                        SERVICE wikibase:label {bd:serviceParam wikibase:language "en" . }'

suffixes_wikidata_0 = '?prop wikibase:directClaim ?p . SERVICE wikibase:label {bd:serviceParam wikibase:language "en" .}'

suffixes_dbpedia = '?v rdfs:label ?vl . ?p rdfs:label ?pl . ?q rdfs:label ?ql . FILTER langMatches( lang(?ql), "EN" ) .\
                   FILTER langMatches( lang(?pl), "EN" ) . FILTER langMatches( lang(?vl), "EN" ) . '
suffixes_dbpedia_2 = 'FILTER langMatches( lang(?rl), "EN" ) . ?v rdfs:label ?vl .  FILTER langMatches(lang(?vl1), "EN")\
. ?p rdfs:label ?pl . ?q rdfs:label ?ql . ?r rdfs:label ?rl . ?v1 rdfs:label ?vl1 . FILTER langMatches(lang(?ql), "EN")\
 . FILTER langMatches(lang(?pl), "EN") . FILTER langMatches(lang(?vl), "EN") .'
suffixes_dbpedia_0 = '?p rdfs:label ?pl . FILTER langMatches( lang(?pl), "EN" ) .'


def get_leaf_nodes(type_values):
    leaf, root = [x[0] for x in type_values], [x[1] for x in type_values]
    leaves = [le for le in leaf if le not in root]
    # leaves = leaf+root
    return leaves


def get_description(entity_type):
    query = 'SELECT distinct ?label WHERE { <http://dbpedia.org/' + entity_type + '> rdfs:comment ?label . \
        FILTER langMatches( lang(?label), "EN" ) . }'
    result = sparql.query(sparql_dbpedia, query)
    type_comment = [sparql.unpack_row(row_result) for row_result in result]
    query = 'SELECT distinct ?label WHERE { <http://dbpedia.org/' + entity_type + '> rdfs:label ?label . \
    FILTER langMatches( lang(?label), "EN" ) . }'
    result = sparql.query(sparql_dbpedia, query)
    type_label = [sparql.unpack_row(row_result) for row_result in result]
    return type_comment, type_label


def kgminer_training_data(poi, q_part):
    q_ts = 'PREFIX dbo: <http://dbpedia.org/ontology/> select distinct ?url1 ?url2 where { \
    { ?url2 <http://dbpedia.org/' + poi + '> ?url1 } . ' + q_part + \
           ' FILTER(?url1 != ?url2).} '
    result = sparql.query(sparql_dbpedia, q_ts)
    training_set = [sparql.unpack_row(row_result) for row_result in result]
    if not training_set:
        q_ts = 'PREFIX dbo: <http://dbpedia.org/ontology/> select distinct ?url1 ?url2 where { \
        {?url1 <http://dbpedia.org/' + poi + '> ?url2} . ' + q_part + \
               ' FILTER(?url1 != ?url2).} '
        result = sparql.query(sparql_dbpedia, q_ts)
        training_set = [sparql.unpack_row(row_result) for row_result in result]
    print q_ts
    return training_set


def or_query_prep(resource_type_set_ranked, ontology_threshold_ranked, triple_v):
    q_part_base = '{ ?url1 rdf:type <http://dbpedia.org/ontology/'
    q_part_base_res = 'UNION { ?url1 dbo:type <http://dbpedia.org/ontology/'
    q_part = ''
    for v in triple_v:
        q_part_res = ''
        ont_types = ontology_threshold_ranked.get(v, [])
        res_types = resource_type_set_ranked.get(v, [])
        for i, val in enumerate(ont_types):
            if i == (len(ont_types)-1):
                q_part = q_part + q_part_base + val + '>} '
            else:
                q_part = q_part + q_part_base + val + '>} UNION '
        if res_types:
            for j,res_val in enumerate(res_types):
                if j == (len(res_types)-1):
                    q_part_res = q_part_res + q_part_base_res + res_val + '>}  .'
                else:
                    q_part_res = q_part_res + q_part_base_res + res_val + '>} UNION '
        else:
            q_part_res = ' .'
        q_part += q_part_res
        q_part_base = ' { ?url2 rdf:type <http://dbpedia.org/ontology/'
        q_part_base_res = 'UNION { ?url2 dbo:type <http://dbpedia.org/ontology/'
    return q_part


def get_entity_type(resources, triples):
    type_set_ontology = {}
    type_set_resource = {}
    type_set_ontology_full = {}
    type_set_resource_full = {}
    for triple_k, triples_v in triples.iteritems():
        for triple_v in triples_v:
            for ent in triple_v:
                item1_v = resources.get(ent, None)
                type_list_ontology = []
                type_list_resource = []
                type_list_ontology_full = []
                type_list_resource_full = []
                if item1_v:
                    key = item1_v.get('dbpedia_id', None)
                    if key not in type_set_ontology.keys():
                        q_type = prefixes_dbpedia+' PREFIX dbo: <http://dbpedia.org/ontology/> SELECT distinct ?t ?t1 \
                        WHERE {{<http://dbpedia.org/resource/'+key+'> dbo:type ?t } UNION {\
                         <http://dbpedia.org/resource/'+key+'> rdf:type ?t }. ?t rdfs:subClassOf ?t1 . \
                         FILTER(STRSTARTS(STR(?t), "http://dbpedia.org/ontology") || STRSTARTS(STR(?t), \
                         "http://dbpedia.org/resource")).}'
                        result = sparql.query(sparql_dbpedia, q_type)
                        type_values = [sparql.unpack_row(row_result) for row_result in result]
                        if not type_values:
                            result = sparql.query(sparql_dbpedia_local, q_type)
                            type_values = [sparql.unpack_row(row_result) for row_result in result]
                        leaves = get_leaf_nodes(type_values)
                        type_ontology = [val.split('/')[-1] for val in leaves if 'ontology' in val]
                        type_resource = [val.split('/')[-1] for val in leaves if 'resource' in val]
                        type_list_ontology.extend(type_ontology)
                        type_list_resource.extend(type_resource)
                        type_set_ontology[ent] = list(set(type_list_ontology))
                        type_set_resource[ent] = list(set(type_list_resource))

                        # type_ontology = [x[0] for x in type_values]
                        type_ontology_full = [val[0].split('/')[-1] for val in type_values if 'ontology' in val[0]]
                        type_resource_full = [val[0].split('/')[-1] for val in type_values if 'resource' in val[0]]
                        type_list_ontology_full.extend(type_ontology_full)
                        type_list_resource_full.extend(type_resource_full)
                        # print type_list_ontology
                        type_set_ontology_full[ent] = list(set(type_list_ontology_full))
                        type_set_resource_full[ent] = list(set(type_list_resource_full))
    return type_set_ontology, type_set_resource, type_set_ontology_full, type_set_resource_full


def get_kgminer_predicates(type_set, triple_dict):
    predicate_list = []
    for triples_k,triples_v in triple_dict.iteritems():
        sort_list = dict()
        for triple_v in triples_v:
            item1_v = type_set.get(triple_v[0], [])
            item2_v = type_set.get(triple_v[1], [])
            if item1_v and item2_v: 
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
                                q_pp = 'SELECT distinct ?p WHERE { ?url1 rdf:type <http://dbpedia.org/ontology/'+it1+'>\
                                 . ?url2 rdf:type <http://dbpedia.org/ontology/' + it2 + '> . {?url1 ?p ?url2 } UNION {?url2 ?p ?url1 } \
                                                            . FILTER(STRSTARTS(STR(?p), "http://dbpedia.org/")).' \
                                                            '}'
                        else:
                            q_pp = 'SELECT distinct ?p WHERE { ?url1 rdf:type <http://dbpedia.org/ontology/'+it1+'> . \
                            ?url2 rdf:type <http://dbpedia.org/ontology/'+it2+'> . ?url1 ?p ?url2 . \
                            FILTER(STRSTARTS(STR(?p), "http://dbpedia.org/")).}'
                        print q_pp
                        try:
                            if q_pp:
                                result = sparql.query(sparql_dbpedia_on, q_pp)
                                pred_values = [sparql.unpack_row(row_result) for row_result in result]
                                if pred_values:
                                    pred_vals = [val[0].replace('/')[-1] for val in pred_values]
                                    predicate_list.extend(pred_vals)
                        except:
                            pass
    return list(set(predicate_list))


def predicate_finder(triple_dict):
    pval_list=[]
    for k in triple_dict.keys():
        q_comment = 'SELECT distinct ?uri ?comment WHERE { ?uri rdfs:comment ?comment . \
        FILTER langMatches( lang(?comment), "EN" ).  ?comment bif:contains "'+k.split()[1]+'" .}'
        q_label = 'SELECT distinct ?uri ?label WHERE { ?uri rdfs:label ?label . ?uri rdf:type rdf:Property . \
        FILTER langMatches( lang(?label), "EN" ). ?label bif:contains "'+k.split()[1]+'" .}'
        predicate_result = sparql.query(sparql_dbpedia, q_comment)
        p_values = [sparql.unpack_row(row) for row in predicate_result]
        if not p_values:
            predicate_result = sparql.query(sparql_dbpedia, q_label)
            p_values = [sparql.unpack_row(row) for row in predicate_result]
        pval_list.append(p_values)
    return pval_list


def relation_extractor_0hop(kb, id1, id2, label, relations):
    if kb == 'wikidata':
        sparql_endpoint = sparql_wikidata
        query = (prefixes_wikidata+' SELECT distinct ?propLabel WHERE { entity:'+id1+' ?p entity:'+id2+' . '+\
                 suffixes_wikidata_0+'}')
        query_back = (prefixes_wikidata + ' SELECT distinct ?propLabel WHERE { entity:' +id2+ ' ?p entity:'+id1 + ' . '\
                      +suffixes_wikidata_0+ '}')
    if kb == 'dbpedia':
        sparql_endpoint = sparql_dbpedia
        if ',' in id1 or ',' in id2:
            query = (prefixes_dbpedia + ' SELECT distinct ?pl WHERE { <http://dbpedia.org/resource/' + id1 + '> ?p \
             <http://dbpedia.org/resource/' + id2 + '> . ' + suffixes_dbpedia_0 + '}')
            query_back = (prefixes_dbpedia + ' SELECT distinct ?pl WHERE {<http://dbpedia.org/resource/' + id2 + '> ?p \
            <http://dbpedia.org/resource/' + id1 + '> . ' + suffixes_dbpedia_0 + '}')
        else:
            query = (prefixes_dbpedia+' SELECT distinct ?pl WHERE { entity:'+id1+' ?p  entity:'+id2+' . ' +\
                     suffixes_dbpedia_0+'}')
            query_back = (prefixes_dbpedia+' SELECT distinct ?pl WHERE {entity:'+id2+' ?p entity:'+id1+' . '\
                          +suffixes_dbpedia_0+ '}')
    # print query
    # print query_back
    try:
        result = sparql.query(sparql_endpoint, query)
        q1_values = [sparql.unpack_row(row_result) for row_result in result]
    except:
        q1_values = []
        pass
    if q1_values:
        for vals in q1_values:
            relations.append((kb, vals[0], label[0], label[1]))
    try:
        result_back = sparql.query(sparql_endpoint, query_back)
        q1_values_back = [sparql.unpack_row(row_result) for row_result in result_back]
    except:
        q1_values_back = []
    for vals in q1_values_back:
        relations.append((kb, vals[0], label[1], label[0]))
    return relations


def relation_extractor_2hop(kb, id1, id2, label, relations, triple_k):
    if kb == 'wikidata':
        sparql_endpoint = sparql_wikidata

        query = (prefixes_wikidata+' SELECT distinct ?propLabel ?vLabel ?prop1Label ?v1Label ?prop2Label WHERE { \
        entity:'+id1+' ?p ?v . ?v ?r ?v1 . ?v1 ?q entity:'+id2+' .  FILTER(entity:'+id1+' != ?v1) . \
        FILTER(entity:'+id1+' != ?v) . FILTER(entity:'+id2+' != ?v) . FILTER(entity:'+id2+' != ?v1) . '+\
                 suffixes_wikidata_2+'}')

        query_back = (prefixes_wikidata + ' SELECT distinct ?propLabel ?vLabel ?prop1Label ?v1Label ?prop2Label WHERE \
        { entity:' + id2 + ' ?p ?v . ?v ?r ?v1 . ?v1 ?q entity:' + id1 + ' . FILTER(entity:'+id2+' != ?v1) . \
        FILTER(entity:'+id1+' != ?v) . FILTER(entity:'+id1+' != ?v1) . FILTER(entity:'+id2+' != ?v) . '+\
                      suffixes_wikidata_2 + '}')
    if kb == 'dbpedia':
        sparql_endpoint = sparql_dbpedia

        query = (prefixes_dbpedia+' SELECT distinct ?pl ?vl ?rl ?vl1 ?ql WHERE { <http://dbpedia.org/resource/'+id1+'> \
        ?p ?v . ?v ?r ?v1 . ?v1 ?q <http://dbpedia.org/resource/'+id2+'> . FILTER(<http://dbpedia.org/resource/'+id1+'>\
         != ?v1) . FILTER(<http://dbpedia.org/resource/'+id2+'> != ?v) . FILTER(<http://dbpedia.org/resource/'+id1+'> \
         != ?v). FILTER(<http://dbpedia.org/resource/'+id2+'> != ?v1).' + suffixes_dbpedia_2+'}')

        query_back = (prefixes_dbpedia+' SELECT distinct ?pl ?vl ?rl ?vl1 ?ql WHERE {\
        <http://dbpedia.org/resource/'+id2+'> ?p ?v . ?v ?r ?v1 . ?v1 ?q <http://dbpedia.org/resource/'+id1+'> . \
        FILTER(<http://dbpedia.org/resource/'+id2+'> != ?v1). FILTER(<http://dbpedia.org/resource/'+id2+'> != ?v) . \
        FILTER(<http://dbpedia.org/resource/'+id1+'> != ?v) . FILTER(<http://dbpedia.org/resource/'+id1+'> != ?v1) .'+\
                      suffixes_dbpedia_2+ '}')
    # print query_back
    # print query
    try:
        result = sparql.query(sparql_endpoint, query)
        q1_values = [sparql.unpack_row(row_result) for row_result in result]
    except:
        q1_values = []
    if q1_values:
        for vals in q1_values:
            relations.append((kb, vals[0], vals[1], label[0]))
            relations.append((kb, vals[2], vals[3], vals[1]))
            relations.append((kb, vals[4], label[1], vals[3]))
    try:
        result_back = sparql.query(sparql_endpoint, query_back)
        q1_values_back = [sparql.unpack_row(row_result) for row_result in result_back]
    except:
        q1_values_back = []
    if q1_values_back:
        for vals in q1_values_back:
            relations.append((kb, vals[0], vals[1], label[1]))
            relations.append((kb, vals[2], vals[3], vals[1]))
            relations.append((kb, vals[4], label[0], vals[3]))
    return relations


def relation_extractor_1hop(kb, id1, id2, label, relations):
    if kb == 'wikidata':
        sparql_endpoint = sparql_wikidata
        query = (prefixes_wikidata+' SELECT distinct ?propLabel ?vLabel ?prop1Label WHERE { entity:'+id1+' ?p ?v . \
        ?v ?q entity:'+id2+' . FILTER(entity:'+id1+' != ?v) . FILTER(entity:'+id2+' != ?v) . '+suffixes_wikidata+'}')

        query_back = (prefixes_wikidata + ' SELECT distinct ?propLabel ?vLabel ?prop1Label WHERE { entity:' + id2 + ' \
        ?p ?v . ?v ?q entity:' + id1 + ' .  FILTER(entity:'+id1+' != ?v) .  FILTER(entity:'+id2+' != ?v) . ' +\
                      suffixes_wikidata + '}')
    if kb == 'dbpedia':
        sparql_endpoint = sparql_dbpedia
        query = (prefixes_dbpedia+' SELECT distinct ?pl ?vl ?ql WHERE { <http://dbpedia.org/resource/'+id1+'> ?p ?v . \
        ?v ?q <http://dbpedia.org/resource/'+id2+'> . FILTER(<http://dbpedia.org/resource/'+id1+'> != ?v) . \
        FILTER(<http://dbpedia.org/resource/'+id2+'> != ?v) .' + suffixes_dbpedia+'}')
        query_back = (prefixes_dbpedia+' SELECT distinct ?pl ?vl ?ql WHERE {<http://dbpedia.org/resource/'+id2+'> ?p ?v\
         . ?v ?q <http://dbpedia.org/resource/'+id1+'> . FILTER(<http://dbpedia.org/resource/'+id1+'> != ?v) . \
         FILTER(<http://dbpedia.org/resource/'+id2+'> != ?v) .' + suffixes_dbpedia+ '}')
    # print sparql_endpoint
    # print query
    try:
        result = sparql.query(sparql_endpoint, query)
        q1_values = [sparql.unpack_row(row_result) for row_result in result]
    except:
        q1_values = []
        pass
    if q1_values:
        for vals in q1_values:
            relations.append([kb, vals[0], vals[1], label[0]])
            relations.append([kb, vals[2], label[1], vals[1]])
    # print query_back
    try:
        result_back = sparql.query(sparql_endpoint, query_back)
        q1_values_back = [sparql.unpack_row(row_result) for row_result in result_back]
    except:
        q1_values_back = []
    if q1_values_back:
        for vals in q1_values_back:
            relations.append([kb, vals[0], vals[1], label[1]])
            relations.append([kb, vals[2], label[0], vals[1]])
    return relations


if __name__ == '__main__':
    with open('obama_sample.txt','r') as f:
        para = f.readline()
