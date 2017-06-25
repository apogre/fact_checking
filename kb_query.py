# -*- coding: utf-8 -*- 

from nltk.tree import *
import dateutil.parser as dp
import sparql
from difflib import SequenceMatcher

import operator

import time, sys, re, csv
import pandas
from nltk.corpus import wordnet as wn
import os

aux_verb = ['was', 'is', 'become','to','of', 'in', 'the']
# sparql_dbpedia = 'http://localhost:8890/sparql'
sparql_dbpedia_on = 'https://dbpedia.org/sparql'
sparql_dbpedia = 'https://dbpedia.org/sparql'
sparql_wikidata = 'https://query.wikidata.org/sparql'

global date_flag
date_flag = 0
threshold_value = 0.8
stanford_setup = True

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
    query = 'SELECT distinct ?label WHERE { <http://dbpedia.org/ontology/' + entity_type + '> rdfs:label ?label . \
    FILTER langMatches( lang(?label), "EN" ) . }'
    result = sparql.query(sparql_dbpedia, query)
    type_values = [sparql.unpack_row(row_result) for row_result in result]
    return type_values


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
                        WHERE {{entity:'+key+' dbo:type ?t } UNION { entity:'+key+' rdf:type ?t }. ?t rdfs:subClassOf \
                        ?t1 . FILTER(STRSTARTS(STR(?t), "http://dbpedia.org/ontology") || STRSTARTS(STR(?t), \
                        "http://dbpedia.org/resource")).}'
                        result = sparql.query(sparql_dbpedia, q_type)
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


def get_kgminer_predicates(type_set, triple_dict, resource_ids):
    for triples_k,triples_v in triple_dict.iteritems():
        predicate_list = []
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
                                                            . FILTER(STRSTARTS(STR(?p), "http://dbpedia.org/ontology")). }'
                        else:
                            q_pp = 'SELECT distinct ?p WHERE { ?url1 rdf:type <http://dbpedia.org/ontology/'+it1+'> . \
                            ?url2 rdf:type <http://dbpedia.org/ontology/'+it2+'> . ?url1 ?p ?url2 . \
                            FILTER(STRSTARTS(STR(?p), "http://dbpedia.org/ontology")).}'
                        try:
                            if q_pp:
                                result = sparql.query(sparql_dbpedia_on, q_pp)
                                pred_values = [sparql.unpack_row(row_result) for row_result in result]
                                if pred_values:
                                    pred_vals = [val[0].split('/')[-1] for val in pred_values]
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


def entity_threshold(resources):
    limit_entity ={}
    for label, entities in resources.iteritems():
        ent_coded = []
        for i,ent in enumerate(entities):
            if i < 20:
                ent_code = ent[0].split('/')[-1]
                ent_coded.append(ent_code)
            else:
                break
        limit_entity[label] = ent_coded
    return limit_entity


def relation_processor(relations):
    predicate_set = []
    relation_graph = {}
    for item in relations:
        if item[1] not in predicate_set:
            predicate_set.append(item[1])
        if item[0] not in relation_graph.keys():
            relation_graph[item[0]] = [{'predicate':item[1], 'entity1':item[2], 'entity2':item[3], 'score':item[4]}]
        else:
            relation_graph[item[0]].extend([{'predicate': item[1], 'entity1': item[2], 'entity2': item[3],\
                                            'score': item[4]}])
    return relation_graph, predicate_set


def relation_extractor_0hop(kb, id1, id2, label, relations, triple_k):
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
            try:
                val_score = word2vec_score(vals[0], triple_k)
            except:
                val_score = 0
            relations.append((kb, vals[0], label[0], label[1], val_score))
    try:
        result_back = sparql.query(sparql_endpoint, query_back)
        q1_values_back = [sparql.unpack_row(row_result) for row_result in result_back]
    except:
        q1_values_back = []
    for vals in q1_values_back:
        try:
            val_score = word2vec_score(vals[0], triple_k)
        except:
            val_score = 0
        relations.append((kb, vals[0], label[1], label[0], val_score))
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
            try:
                val_score = word2vec_score(vals[0], triple_k)
                val_score1 = word2vec_score(vals[2], triple_k)
                val_score2 = word2vec_score(vals[4], triple_k)
            except:
                val_score = 0
                val_score1 = 0
                val_score2 = 0
            relations.append((kb, vals[0], vals[1], label[0], val_score))
            relations.append((kb, vals[2], vals[3], vals[1], val_score1))
            relations.append((kb, vals[4], label[1], vals[3], val_score2))
    try:
        result_back = sparql.query(sparql_endpoint, query_back)
        q1_values_back = [sparql.unpack_row(row_result) for row_result in result_back]
    except:
        q1_values_back = []
    if q1_values_back:
        for vals in q1_values_back:
            try:
                val_score = word2vec_score(vals[0], triple_k)
                val_score1 = word2vec_score(vals[2], triple_k)
                val_score2 = word2vec_score(vals[4], triple_k)
            except:
                val_score = 0
                val_score1 = 0
                val_score2 = 0
            relations.append((kb, vals[0], vals[1], label[1], val_score))
            relations.append((kb, vals[2], vals[3], vals[1], val_score1))
            relations.append((kb, vals[4], label[0], vals[3], val_score2))
    return relations


def relation_extractor_1hop(kb, id1, id2, label, relations, triple_k):
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
            try:
                val_score = word2vec_score(vals[0], triple_k)
                val_score1 = word2vec_score(vals[2], triple_k)
            except:
                val_score = 0
                val_score1 = 0
            # print vals
            relations.append((kb, vals[0], vals[1], label[0], val_score))
            relations.append((kb, vals[2], label[1], vals[1], val_score1))
    # print query_back
    try:
        result_back = sparql.query(sparql_endpoint, query_back)
        q1_values_back = [sparql.unpack_row(row_result) for row_result in result_back]
    except:
        q1_values_back = []
    if q1_values_back:
        for vals in q1_values_back:
            try:
                val_score = word2vec_score(vals[0], triple_k)
                val_score1 = word2vec_score(vals[2], triple_k)
            except:
                val_score = 0
                val_score1 = 0
            # print vals
            relations.append((kb, vals[0], vals[1], label[1], val_score))
            relations.append((kb, vals[2], label[0], vals[1], val_score1))
    return relations




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


def get_dates(i1,date_ent_str):
    v = i1[0]
    dates_matched = []
    if not isinstance(date_ent_str,datetime):
        # u'1940-04-25T00:00:00'
        date_ent = datetime.strptime(date_ent_str,"%Y-%m-%dT%H:%M:%S")
    # print date_ent
    # sys.exit(0)
    # print date_ent.date()
    if 'dbpedia' in v:
        v = v.replace('page', 'resource')
        # print v
        try:
            dq = ('SELECT distinct ?r ?o WHERE  {  ?r a owl:DatatypeProperty ; rdfs:range xsd:date . <' + str(
                v) + '> ?r ?o .}')
            # print dq
            resultd = sparql.query(sparql_dbpedia, dq)
            for i, row1 in enumerate(resultd):
                values1 = sparql.unpack_row(row1)
                # print values1[1],date_ent.date()
                # sys.exit(0)
                if values1[1] == date_ent.date():
                    # print v, values1
                    dates_matched.append([i1,values1])
                else:
                    year1 = str(values1[1]).split('-')[0]
                    if year1 == str(date_ent.date().year):
                        dates_matched.append([i1, values1])
        except:
            pass
    # print dates_matched
    return dates_matched


if __name__ == '__main__':
    with open('obama_sample.txt','r') as f:
        para = f.readline()
