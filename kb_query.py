# -*- coding: utf-8 -*- 

import sparql
from config import sparql_dbpedia, unwanted_predicates
import sys
import json
from resource_writer import json_serial
import itertools


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


def positive_relations(predicate):
    query = 'select distinct ?a where {?a <http://dbpedia.org/property/' + predicate + '> ?b. ?b rdf:type \
    <http://dbpedia.org/ontology/Person> . ?a rdf:type <http://dbpedia.org/ontology/Company> .}'
    sparql_endpoint = sparql_dbpedia
    print query
    try:
        result = sparql.query(sparql_endpoint, query)
        q1_values = [sparql.unpack_row(row_result) for row_result in result]
    except:
        q1_values = []
    return q1_values


def negative_relations(predicate):
    query = "SELECT DISTINCT ?subject <notfounders> ?object WHERE { ?object <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> \
    <http://dbpedia.org/ontology/Person>. ?subject <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> \
    <http://dbpedia.org/ontology/Company>. {{?subject ?targetRelation ?realObject.} UNION  \
    {?realSubject ?targetRelation ?object.}} ?subject ?otherRelation ?object. \
    FILTER (?targetRelation = <http://dbpedia.org/property/"+predicate+">) \
    FILTER (?otherRelation != <http://dbpedia.org/property/"+predicate+">) \
    FILTER NOT EXISTS {?subject <http://dbpedia.org/property/"+predicate+"> ?object.} }"
    sparql_endpoint = sparql_dbpedia
    print query
    try:
        result = sparql.query(sparql_endpoint, query)
        q1_values = [sparql.unpack_row(row_result) for row_result in result]
    except:
        q1_values = []
    return q1_values


def distance_one_query(kb, id1, distance_one):
    print "Distance One Query"
    if kb == 'dbpedia':
        sparql_endpoint = sparql_dbpedia
        query = (prefixes_dbpedia + ' SELECT distinct ?p ?id2 WHERE { <http://dbpedia.org/resource/' + id1 + '> ?p ?id2\
         . ' + suffixes_dbpedia_0 + ' FILTER (!regex(str(?pl), "Wikipage","i")) . FILTER (!regex(str(?pl), \
         "abstract","i")) . }')
        query_back = (prefixes_dbpedia + ' SELECT distinct ?p ?id2 WHERE { ?id2 ?p <http://dbpedia.org/resource/' + id1\
                      + '> . ' + suffixes_dbpedia_0 + ' FILTER (!regex(str(?pl), "Wikipage","i")) . \
                      FILTER (!regex(str(?pl), "abstract","i")) .  }')

    print query
    print query_back
    try:
        result = sparql.query(sparql_endpoint, query)
        q1_values = [sparql.unpack_row(row_result) for row_result in result]
    except:
        q1_values = []
        pass
    if q1_values:
        print len(q1_values)
        for vals in q1_values:
            vals_0 = vals[0].split('/')[-1]
            if vals_0 not in unwanted_predicates:
                if isinstance(vals[1], basestring):
                #     distance_one.append([id1, vals_0, vals[1]])
                # else:
                    if '/' in vals[1]:
                        distance_one.append([id1, vals_0, vals[1].split('/')[-1]])
    try:
        result_back = sparql.query(sparql_endpoint, query_back)
        q1_values_back = [sparql.unpack_row(row_result) for row_result in result_back]
    except:
        q1_values_back = []
    print len(q1_values_back)
    for vals in q1_values_back:
        vals_0 = vals[0].split('/')[-1]
        if vals_0 not in unwanted_predicates:
            if isinstance(vals[1], basestring):
            #     distance_one.append([vals[1], vals_0, id1])
            # else:
                if '/' in vals[1]:
                    distance_one.append([vals[1].split('/')[-1], vals_0, id1])
    return distance_one


def distance_one_query_local(kb, id1, distance_one):
    print "Distance One Query Local"
    if kb == 'dbpedia':
        sparql_endpoint = sparql_dbpedia_v
        query = (' SELECT distinct ?p ?id2 WHERE { <http://dbpedia.org/resource/'+id1+'> ?p  ?id2 . }')
        query_back = (' SELECT distinct ?p ?id2 WHERE { ?id2 ?p <http://dbpedia.org/resource/'+id1+'> .}')
    print query
    print query_back
    try:
        result = sparql.query(sparql_endpoint, query)
        q1_values = [sparql.unpack_row(row_result) for row_result in result]
    except:
        q1_values = []
        pass
    if q1_values:
        print len(q1_values)
        for vals in q1_values:
            vals_0 = vals[0].split('/')[-1]
            if vals_0 not in unwanted_predicates:
                if not isinstance(vals[1], basestring):
                    distance_one.append([id1, vals_0, vals[1]])
                else:
                    distance_one.append([id1, vals_0, vals[1].split('/')[-1]])
    try:
        result_back = sparql.query(sparql_endpoint, query_back)
        q1_values_back = [sparql.unpack_row(row_result) for row_result in result_back]
    except:
        q1_values_back = []
    print len(q1_values_back)
    for vals in q1_values_back:
        vals_0 = vals[0].split('/')[-1]
        if vals_0 not in unwanted_predicates:
            if not isinstance(vals[1], basestring):
                distance_one.append([vals[1], vals_0, id1])
            else:
                distance_one.append([vals[1].split('/')[-1], vals_0, id1])
    return distance_one



def distance_two_query(kb, id1, distance_two, unique_predicates):
    print "Distance Two Query"
    if kb == 'wikidata':
        sparql_endpoint = sparql_wikidata
        query = (prefixes_wikidata+' SELECT distinct ?propLabel ?id2Label WHERE { entity:'+id1+' ?p ?id2 . '+ suffixes_wikidata_0 \
                 + ' }')
        query_back = (prefixes_wikidata + ' SELECT distinct ?propLabel ?id2Label WHERE { ?id2 ?p entity:'+id1 + ' . ' + \
                      suffixes_wikidata_0)
    if kb == 'dbpedia':
        sparql_endpoint = sparql_dbpedia
        # if ',' in id1:
        query = (prefixes_dbpedia + ' SELECT distinct ?pl ?id2 ?pl1 ?id3 WHERE { <http://dbpedia.org/resource/' + \
                 id1 + '> ?p ?id2 . ?id2 ?p1 ?id3 . ' + suffixes_dbpedia_0 + ' ?p1 rdfs:label ?pl1 . \
                 FILTER langMatches( lang(?pl1), "EN" ) . }')
        query_back = (prefixes_dbpedia + ' SELECT distinct ?pl ?id2 ?pl1 ?id3 WHERE { ?id3 ?p1 ?id2 . ?id2 ?p <http://dbpedia.org/resource/' + id1 + '> . ' + suffixes_dbpedia_0 + ' ?p1 rdfs:label ?pl1 .\
        FILTER langMatches( lang(?pl1), "EN" ) . }')
        # else:
        #     query = (prefixes_dbpedia+' SELECT distinct ?pl ?id2 WHERE { entity:'+id1+' ?p  ?id2 . ' + suffixes_dbpedia_0 + \
        #              ' FILTER (!regex(str(?pl), "Wikipage","i")) . FILTER (!regex(str(?pl), "abstract","i")) . }')
        #     query_back = (prefixes_dbpedia+' SELECT distinct ?pl ?id2 WHERE { ?id2 ?p entity:'+id1+' . ' + suffixes_dbpedia_0\
        #                   + ' FILTER (!regex(str(?pl), "Wikipage","i")) . FILTER (!regex(str(?pl), "abstract","i")) .  }')
    print query
    print query_back
    try:
        result = sparql.query(sparql_endpoint, query)
        q1_values = [sparql.unpack_row(row_result) for row_result in result]
    except:
        q1_values = []
        pass
    if q1_values:
        print len(q1_values)
        for vals in q1_values:
            if vals[0] not in unique_predicates:
                unique_predicates.append(vals[0])
            if vals[0] not in unwanted_predicates:
                vals_0 = vals[0].replace(' ', '_')
                if not isinstance(vals[1], basestring):
                    distance_two.append([id1, vals_0, vals[1]])
                else:
                    distance_two.append([id1, vals_0, vals[1].split('/')[-1].replace(' ', '_')])
            if vals[2] not in unique_predicates:
                unique_predicates.append(vals[2])
            if vals[2] not in unwanted_predicates:
                vals_2 = vals[2].replace(' ', '_')
                if not isinstance(vals[3], basestring) and not isinstance(vals[1], basestring):
                    distance_two.append([vals[1], vals_2, vals[3]])
                elif isinstance(vals[3], basestring) and not isinstance(vals[1], basestring):
                    distance_two.append([vals[1], vals_2, vals[3].split('/')[-1].replace(' ', '_')])
                elif not isinstance(vals[3], basestring) and isinstance(vals[1], basestring):
                    distance_two.append([vals[1].split('/')[-1].replace(' ', '_'), vals_2, vals[3]])
                else:
                    distance_two.append([vals[1].split('/')[-1].replace(' ', '_'), vals_2, vals[3].split('/')[-1].replace(' ', '_')])
    try:
        result_back = sparql.query(sparql_endpoint, query_back)
        q1_values_back = [sparql.unpack_row(row_result) for row_result in result_back]
    except:
        q1_values_back = []
    print len(q1_values_back)
    for vals in q1_values_back:
        if vals[0] not in unique_predicates:
            unique_predicates.append(vals[0])
        if vals[0] not in unwanted_predicates:
            vals_0 = vals[0].replace(' ', '_')
            if not isinstance(vals[1], basestring):
                distance_two.append([vals[1], vals_0, id1])
            else:
                distance_two.append([vals[1].split('/')[-1].replace(' ', '_'), vals_0, id1])
        if vals[2] not in unique_predicates:
            unique_predicates.append(vals[2])
        if vals[2] not in unwanted_predicates:
            vals_2 = vals[2].replace(' ', '_')
            if not isinstance(vals[3], basestring) and not isinstance(vals[1], basestring):
                distance_two.append([vals[3], vals_2, vals[1]])
            elif not isinstance(vals[3], basestring) and isinstance(vals[1], basestring):
                distance_two.append([vals[3], vals_2, vals[1].split('/')[-1].replace(' ', '_')])
            elif not isinstance(vals[1], basestring) and isinstance(vals[3], basestring):
                distance_two.append([vals[3].split('/')[-1].replace(' ', '_'), vals_2, vals[1]])
            else:
                distance_two.append(
                    [vals[3].split('/')[-1].replace(' ', '_'), vals_2, vals[1].split('/')[-1].replace(' ', '_')])
    return distance_two, unique_predicates


def distance_three_query(kb, id1, distance_two):
    if kb == 'dbpedia':
        sparql_endpoint = sparql_dbpedia

        query = ' SELECT distinct ?p ?id2 ?p1 ?id3 ?p2 ?id4 WHERE { <http://dbpedia.org/resource/'+ \
                id1 + '> ?p ?id2 . ?id2 ?p1 ?id3 . ?id3 ?p2 ?id4 . }'

        query_back = ' SELECT distinct ?p ?id2 ?p1 ?id3 ?p2 ?id4 WHERE { ?id4 ?p2 ?id3 . ?id3 ?p1 \
        ?id2 . ?id2 ?p <http://dbpedia.org/resource/' + id1 + '> .  }'

    print query
    print query_back
    # try:
    result = sparql.query(sparql_endpoint, query)
    q1_values = [sparql.unpack_row(row_result) for row_result in result]
    # except:
    #     q1_values = []
    #     pass
    print len(q1_values)
    sys.exit(0)
    if q1_values:
        for vals in q1_values:
            if vals[0] not in unwanted_predicates:
                vals_0 = vals[0]
                if not isinstance(vals[1], basestring):
                    distance_two.append([id1, vals_0, vals[1]])
                else:
                    distance_two.append([id1, vals_0, vals[1].split('/')[-1].replace(' ', '_')])
            if vals[2] not in unwanted_predicates:
                vals_2 = vals[2]
                if not isinstance(vals[3], basestring) and not isinstance(vals[1], basestring):
                    distance_two.append([vals[1], vals_2, vals[3]])
                elif isinstance(vals[3], basestring) and not isinstance(vals[1], basestring):
                    distance_two.append([vals[1], vals_2, vals[3].split('/')[-1].replace(' ', '_')])
                elif not isinstance(vals[3], basestring) and isinstance(vals[1], basestring):
                    distance_two.append([vals[1].split('/')[-1].replace(' ', '_'), vals_2, vals[3]])
                else:
                    distance_two.append([vals[1].split('/')[-1].replace(' ', '_'), vals_2, vals[3].split('/')[-1].replace(' ', '_')])
            if vals[4] not in unwanted_predicates:
                vals_4 = vals[4]
                if not isinstance(vals[3], basestring) and not isinstance(vals[5], basestring):
                    distance_two.append([vals[3], vals_4, vals[5]])
                elif isinstance(vals[5], basestring) and not isinstance(vals[3], basestring):
                    distance_two.append([vals[3], vals_4, vals[5].split('/')[-1].replace(' ', '_')])
                elif not isinstance(vals[5], basestring) and isinstance(vals[3], basestring):
                    distance_two.append([vals[3].split('/')[-1].replace(' ', '_'), vals_4, vals[5]])
                else:
                    distance_two.append([vals[3].split('/')[-1].replace(' ', '_'), vals_4, vals[5].split('/')[-1].replace(' ', '_')])
    try:
        result_back = sparql.query(sparql_endpoint, query_back)
        q1_values_back = [sparql.unpack_row(row_result) for row_result in result_back]
    except:
        q1_values_back = []
    print len(q1_values_back)
    for vals in q1_values_back:
        if vals[0] not in unwanted_predicates:
            vals_0 = vals[0]
            if not isinstance(vals[1], basestring):
                distance_two.append([vals[1], vals_0, id1])
            else:
                distance_two.append([vals[1].split('/')[-1].replace(' ', '_'), vals_0, id1])
        if vals[2] not in unwanted_predicates:
            vals_2 = vals[2]
            if not isinstance(vals[3], basestring) and not isinstance(vals[1], basestring):
                distance_two.append([vals[3], vals_2, vals[1]])
            elif not isinstance(vals[3], basestring) and isinstance(vals[1], basestring):
                distance_two.append([vals[3], vals_2, vals[1].split('/')[-1].replace(' ', '_')])
            elif not isinstance(vals[1], basestring) and isinstance(vals[3], basestring):
                distance_two.append([vals[3].split('/')[-1].replace(' ', '_'), vals_2, vals[1]])
            else:
                distance_two.append(
                    [vals[3].split('/')[-1].replace(' ', '_'), vals_2, vals[1].split('/')[-1].replace(' ', '_')])
        if vals[4] not in unwanted_predicates:
            vals_4 = vals[4]
            if not isinstance(vals[3], basestring) and not isinstance(vals[5], basestring):
                distance_two.append([vals[5], vals_4, vals[3]])
            elif not isinstance(vals[3], basestring) and isinstance(vals[5], basestring):
                distance_two.append([vals[5], vals_4, vals[3].split('/')[-1].replace(' ', '_')])
            elif not isinstance(vals[5], basestring) and isinstance(vals[3], basestring):
                distance_two.append([vals[5].split('/')[-1].replace(' ', '_'), vals_4, vals[3]])
            else:
                distance_two.append(
                    [vals[5].split('/')[-1].replace(' ', '_'), vals_4, vals[3].split('/')[-1].replace(' ', '_')])
    return distance_two


def dbpedia_wikidata_equivalent(dbpedia_url):
    query = 'PREFIX owl:<http://www.w3.org/2002/07/owl#> PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#> SELECT \
    ?WikidataProp WHERE { <'+dbpedia_url+'>  owl:sameAs ?WikidataProp . FILTER (CONTAINS \
    (str(?WikidataProp) , "wikidata.org")) .} '
    result = sparql.query(sparql_dbpedia, query)
    resources = [sparql.unpack_row(row_result) for row_result in result]
    return resources


def dbpedia_wikidata_mapping():
    resource_dict = dict()
    query = "PREFIX owl:<http://www.w3.org/2002/07/owl#> PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#> SELECT \
    ?itemLabel ?WikidataProp WHERE { ?DBpediaProp  owl:equivalentProperty  ?WikidataProp . FILTER ( \
    CONTAINS ( str(?WikidataProp) , 'wikidata')) . ?DBpediaProp  rdfs:label  ?itemLabel . FILTER (lang(?itemLabel) \
    = 'en') .} ORDER BY  ?DBpediaProp"
    result = sparql.query(sparql_dbpedia, query)
    resources = [sparql.unpack_row(row_result) for row_result in result]
    for resource in resources:
        resource_dict[resource[1].split('/')[-1]] = resource[0]
    with open('LPmln/predicate_dict.json', 'w') as fp:
        json.dump(resource_dict, fp, default=json_serial)


def get_leaf_nodes(type_values):
    leaf, root = [x[0] for x in type_values], [x[1] for x in type_values]
    leaves = [le for le in leaf if le not in root]
    # leaves = leaf+root
    return leaves


def resource_extractor(entity):
    db_resource = dict()
    wiki_resource = dict()
    resource_ids = dict()
    result = []
    query = 'PREFIX dbo: <http://dbpedia.org/ontology/> SELECT distinct ?uri ?label WHERE { ?uri rdfs:label ?label . \
    FILTER langMatches( lang(?label), "EN" ) . ?label bif:contains "' + entity + '" . }'
    print query
    try:
        result = sparql.query(sparql_dbpedia, query)
    except:
        pass
    if result:
        resources = [sparql.unpack_row(row_result) for row_result in result]
    	for resource in resources:
            if 'wikidata' in resource[0]:
            	if resource[1] not in wiki_resource.keys():
                    wiki_resource[resource[1]] = [resource[0]]
            	else:
                    if resource[0] not in sum(wiki_resource.values(), []):
                    	wiki_resource[resource[1]].append(resource[0])
            else:
            	if resource[1] not in db_resource.keys() and 'Category' not in resource[0]:
               	    db_resource[resource[1]] = [resource[0]]
            	else:
                    if resource[0] not in sum(db_resource.values(), []):
                    	db_resource.get(resource[1], []).append(resource[0])
    	resource_ids['dbpedia_id'] = db_resource.get(entity)[0].split('/')[-1]
    	resource_ids['wikidata_id'] = wiki_resource.get(entity)[0].split('/')[-1]
    return resource_ids


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

    print q_ts
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
    for triples_k, triples_v in triple_dict.iteritems():
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
                                                            '} '
                        else:
                            q_pp = 'SELECT distinct ?p WHERE { ?url1 rdf:type <http://dbpedia.org/ontology/'+it1+'> . \
                            ?url2 rdf:type <http://dbpedia.org/ontology/'+it2+'> . ?url1 ?p ?url2 . \
                            FILTER(STRSTARTS(STR(?p), "http://dbpedia.org/")).}'
                        # try:
                        if q_pp:
                            result = sparql.query(sparql_dbpedia_on, q_pp)
                            pred_values = [sparql.unpack_row(row_result) for row_result in result]
                            if pred_values:
                                pred_vals = [val[0].replace('http://dbpedia.org/','') for val in pred_values]
                                predicate_list.extend(pred_vals)
                        # except Exception as e:
                        #     print e
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


def get_all_entity(predicate):
    # q_ts = 'PREFIX dbo:  <http://dbpedia.org/ontology/> select distinct ?url1 ?url2 where { ?url1 rdf:type dbo:Person .\
    #  ?url1 dbo:' + predicate + ' ?url2  .} '
    q_ts = 'PREFIX dbo:  <http://dbpedia.org/ontology/> select distinct ?url1 where { ?url1 rdf:type dbo:Person .} '
    print q_ts
    result = sparql.query(sparql_dbpedia, q_ts, timeout=30000)
    training_set = [sparql.unpack_row(row_result) for row_result in result]
    print len(training_set)
    print training_set[:2]
    return training_set
    sys.exit(0)


def get_all_person(pers):
    per = '<http://dbpedia.org/resource/'+pers+'>'
    q_ts = 'PREFIX foaf:  <http://xmlns.com/foaf/0.1/> PREFIX dbo:  <http://dbpedia.org/ontology/> \
    PREFIX dbp: <http://dbpedia.org/property/> select '+per+'  ?url2 ?url3 ?url4 ?url5 ?url6 ?url7 ?url8 ?url9 ?url10 ?url11\
     ?url12 ?url13 ?url14 where  { ' +per+'  dbo:birthPlace ?url6 .  '+per+'  foaf:gender ?url2 . optional { '+per+' \
      dbp:nationality ?url3} . optional { '+per+'  dbo:deathPlace ?url5 }. \
      optional {   '+per+'  dbo:profession ?url4 }. optional { '+per+'  dbo:residence ?url7} . optional { '+per+'  dbo:almaMater \
      ?url8 }. optional { '+per+'  dbo:deathCause ?url9 }. optional { '+per+'  dbo:religion ?url10 } .  optional { '+per+'  dbo:parent ?url11} \
      . optional { '+per+'  dbo:child ?url12} . optional { '+per+'  dbo:ethnicity ?url13} .  optional { '+per+' dbo:spouse ?url14} .  }'
    # print q_ts
    result = sparql.query(sparql_dbpedia, q_ts)
    training_set = [sparql.unpack_row(row_result) for row_result in result]
    print training_set
    return training_set


if __name__ == '__main__':
    with open('obama_sample.txt','r') as f:
        para = f.readline()
