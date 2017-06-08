# -*- coding: utf-8 -*- 

from nltk.tree import *
import dateutil.parser as dp
import sparql
from difflib import SequenceMatcher
from datetime import datetime
from itertools import groupby,product
import operator
from nltk.tag import StanfordNERTagger,StanfordPOSTagger
from nltk.parse.stanford import StanfordDependencyParser
import time, sys, re, csv
import pandas
from nltk.corpus import wordnet as wn
from ftfy.badness import sequence_weirdness
import os
import global_settings
import numpy as np

aux_verb = ['was', 'is', 'become','to','of', 'in', 'the']
sparql_dbpedia = 'http://localhost:8890/sparql'
sparql_dbpedia_on = 'https://dbpedia.org/sparql'
# sparql_dbpedia = 'https://dbpedia.org/sparql'
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

if stanford_setup:
    stanford_parser_jar = str(os.environ['HOME'])+'/stanford-parser-full-2015-12-09/stanford-parser.jar'
    stanford_model_jar = str(os.environ['HOME'])+'/stanford-parser-full-2015-12-09/stanford-parser-3.6.0-models.jar'

    st_ner = StanfordNERTagger('english.all.3class.distsim.crf.ser.gz')
    st_pos = StanfordPOSTagger('english-bidirectional-distsim.tagger')
    parser = StanfordDependencyParser(path_to_jar=stanford_parser_jar, path_to_models_jar=stanford_model_jar)


def get_nodes_updated(netagged_words):
    ent = []
    for tag, chunk in groupby(netagged_words, lambda x:x[1]):
        # print tag
        if tag != "O":
            tuple1 =(" ".join(w for w, t in chunk),tag)
            ent.append(tuple1)
    return ent


def verb_entity_matcher(parsed_tree):
    # print parsed_tree
    verb_ent = []
    for tree in parsed_tree:
        # print tree
        verb_entity = {}
        # print "----"
        be_tree = be_verb(tree[0])
        # print be_tree
        if be_tree:
            verb_ent.append([be_tree])
        for nodes in tree[0]:
            # print nodes
            if re.search('VB',nodes[0][1]) and re.search('NN',nodes[2][1]):
                if nodes[0][0] not in verb_entity.keys():
                    verb_entity[nodes[0][0]]=[nodes[2][0]]
                else:
                    verb_entity[nodes[0][0]].append(nodes[2][0])
        if verb_entity:
            verb_ent.append([verb_entity])
    # sys.exit(0)
    return verb_ent


def svo_finder(ent,triples):
    triple_dict = {}
    entity_set = [x[0] for x in ent]
    # print ent
    # print entity_set
    # print "----"
    for triple in triples:
        # print triple
        # sys.exit(0)
        for ent in entity_set:
            if not isinstance(ent, datetime):
                if ent in triple[2] and triple[1] not in aux_verb:
                    triple[2] = ent
        for trip in triple:
            try:
                date_ent = dp.parse(trip,default=datetime(2017, 1, 1))
                print date_ent
                if triple[0] in entity_set and date_ent in entity_set:
                    if triple[1] not in triple_dict.keys():
                        triple_dict[triple[1]] = [[triple[0],date_ent]]
                    else:
                        triple_dict[triple[1]].append([triple[0], date_ent])
                    # print triple_dict
            except:
                pass
        if triple[0] in entity_set and triple[2] in entity_set:
            if triple[1] not in triple_dict.keys():
                triple_dict[triple[1]] = [[triple[0], triple[2]]]
            else:
                triple_list = [item for sublist in triple_dict[triple[1]] for item in sublist]
                # print triple_list
                if triple[0] in triple_list and triple[2] in triple_list:
                    pass
                else: 
                    triple_dict[triple[1]].append([triple[0], triple[2]])
        # print triple_dict
    return triple_dict


def be_verb(tree):
    be_tree = {}
    be_noun = ''
    b_verb = ''
    for n,nodes in enumerate(tree):
        if re.search('NN', nodes[0][1]) and re.search('VB', nodes[2][1]):
            be_noun = nodes[0][0]
            b_verb = nodes[2][0]
            if b_verb not in be_tree.keys():
                be_tree[b_verb] = [be_noun]
            else:
                be_tree[str(b_verb)+str(n)]=[be_noun]
        if be_noun in nodes[0] and re.search('JJ', nodes[2][1]):
            adj = nodes[2][0]
            if b_verb not in be_tree.keys():
                be_tree[b_verb] = [adj+' '+be_noun]
            else:
                if be_noun not in nodes[0]:
                    be_tree[str(b_verb)+str(n)]=[adj+' '+be_noun]
                else:
                    be_tree[str(b_verb)] = [adj + ' ' + be_noun]
    return be_tree


def get_verb(postagged_words):
    verb = []
    for tag in postagged_words:
        if "VB" in tag[1]:
            verb.append(tag)
    return verb


def similar(a,b):
    return SequenceMatcher(None,a,b).ratio()


def compare(word1, word2):
    # print word2, word1
    wierdness2 = sequence_weirdness(unicode(word2))
    if wierdness2 == 0:
        wierdness1 = sequence_weirdness(unicode(word1))
        if wierdness1 == 0:
            # print word1, word2
            ss1 = sum([wn.synsets(word) for word in word1.split() if word not in aux_verb],[])
            ss2 = sum([wn.synsets(word) for word in word2.split() if word not in aux_verb],[])
            # print ss1, ss2
            # ss1 = sum(ss1,[])
            # ss2 = sum(ss2,[])
            # print ss1, ss2
            try:
                return max(s1.path_similarity(s2) for (s1, s2) in product(ss1, ss2))
            except:
                # print "exception"
                return 0.0


def date_parser(docs):
    dates = []
    for doc in docs:
        try:
            dates.append([dp.parse(doc, fuzzy=True,default=datetime(2017, 1, 1))])
        except:
            dates.append('')
    return dates


def location_update(parse):
    new_loc = ''
    for i,p in enumerate(parse):
        if p[1] == 'LOCATION':
            if parse[i+1][0] == ',' or parse[i+1][1] == 'LOCATION':
                new_loc = p[0]+' '+parse[i+1][0]
                if parse[i+2][1] == 'LOCATION' or parse[i+2][0] == ',':
                    new_loc = new_loc+' '+parse[i+2][0]
                    if parse[i+3][1]=='LOCATION':
                        new_loc = new_loc+' '+parse[i+3][0]
                        ent = new_loc.split(',')
                        st = [','.join(e.rstrip() for e in ent)]
                        return st


def st_tagger(sentence_list):
    ne_s = st_ner.tag_sents(sentence_list)
    pos_s = st_pos.tag_sents(sentence_list)
    dep_s = [[list(parse.triples()) for parse in dep_parse] for dep_parse in parser.parse_sents(sentence_list)]
    return ne_s, pos_s, dep_s


entities = {} 
new_labels = []


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


def get_labels(labels):
    global new_labels
    new_labels = []
    for i,label in enumerate(labels):
        if label[1] != 'DATE':
            new_labels.append(label)


def date_checker(dl,vo_date):
    for d in dl:
        matched_date = [vo_d for vo_d in vo_date if d.date() == vo_d[1]]
    if matched_date:
        return matched_date
    else:
        return None


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
    print query
    print query_back
    try:
        result = sparql.query(sparql_endpoint, query)
        q1_values = [sparql.unpack_row(row_result) for row_result in result]
    except:
        q1_values = []
        pass
    if q1_values:
        for vals in q1_values:
            try:
                val_score = predicate_confidence(vals[0], triple_k)
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
            val_score = predicate_confidence(vals[0], triple_k)
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
    print query_back
    print query
    try:
        result = sparql.query(sparql_endpoint, query)
        q1_values = [sparql.unpack_row(row_result) for row_result in result]
    except:
        q1_values = []
    if q1_values:
        for vals in q1_values:
            try:
                val_score = predicate_confidence(vals[0], triple_k)
                val_score1 = predicate_confidence(vals[2], triple_k)
                val_score2 = predicate_confidence(vals[4], triple_k)
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
                val_score = predicate_confidence(vals[0], triple_k)
                val_score1 = predicate_confidence(vals[2], triple_k)
                val_score2 = predicate_confidence(vals[4], triple_k)
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
    print query
    print query_back
    try:
        result = sparql.query(sparql_endpoint, query)
        q1_values = [sparql.unpack_row(row_result) for row_result in result]
    except:
        q1_values = []
        pass
    if q1_values:
        for vals in q1_values:
            try:
                val_score = predicate_confidence(vals[0], triple_k)
                val_score1 = predicate_confidence(vals[2],triple_k)
            except:
                val_score = 0
                val_score1 = 0
            relations.append((kb, vals[0], vals[1], label[0], val_score))
            relations.append((kb, vals[2], label[1], vals[1], val_score1))
    try:
        result_back = sparql.query(sparql_endpoint, query_back)
        q1_values_back = [sparql.unpack_row(row_result) for row_result in result_back]
    except:
        q1_values_back = []
    if q1_values_back:
        for vals in q1_values_back:
            try:
                val_score = predicate_confidence(vals[0], triple_k)
                val_score1 = predicate_confidence(vals[2], triple_k)
            except:
                val_score = 0
                val_score1 = 0
            relations.append((kb, vals[0], vals[1], label[1], val_score))
            relations.append((kb, vals[2], label[0], vals[1], val_score1))
    return relations


def predicate_confidence(rel, triple_k):
    score = []
    for r in rel.split():
        if r not in aux_verb:
            score.extend([global_settings.model_wv_g.similarity(r, trip) for trip in triple_k.split() if trip not in aux_verb])
    return round(np.mean(score),3)


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
