# -*- coding: utf-8 -*- 

from nltk.tree import *
import dateutil.parser as dp
import sparql
import urllib2
from difflib import SequenceMatcher
from datetime import datetime
from itertools import groupby
import operator
from nltk.tag import StanfordNERTagger,StanfordPOSTagger
from nltk.parse.stanford import StanfordDependencyParser
import time, sys, re

objects = []
relation=[]
ROOT = 'ROOT'
aux_verb = ['was', 'is', 'become','to']
# SPARQL_SERVICE_URL = 'https://query.wikidata.org/sparql'
sparql_dbpedia = 'http://localhost:8890/sparql'
# sparql_dbpedia = 'https://dbpedia.org/sparql'
global date_flag
date_flag = 0
threshold_value = 0.8

stanford_parser_jar = '/home/apradhan/stanford-parser-full-2015-12-09/stanford-parser.jar'
stanford_model_jar = '/home/apradhan/stanford-parser-full-2015-12-09/stanford-parser-3.6.0-models.jar'
# stanford_parser_jar = '/home/nepal/stanford-parser-full-2015-12-09/stanford-parser.jar'
# stanford_model_jar = '/home/nepal/stanford-parser-full-2015-12-09/stanford-parser-3.6.0-models.jar'

# [list(parse.triples()) for parse in parser.raw_parse("Born in New York City on August 17, 1943, actor Robert De Niro left school at age 16 to study acting with Stella Adler.")]

st_ner = StanfordNERTagger('english.all.3class.distsim.crf.ser.gz')
st_pos = StanfordPOSTagger('english-bidirectional-distsim.tagger')
parser = StanfordDependencyParser(path_to_jar=stanford_parser_jar, path_to_models_jar=stanford_model_jar)

# export STANFORDTOOLSDIR=$HOME
# export CLASSPATH=$STANFORDTOOLSDIR/stanford-ner-2015-12-09/stanford-ner.jar:$STANFORDTOOLSDIR/stanford-postagger-full-2015-12-09:$STANFORDTOOLSDIR/stanford-parser-full-2015-12-09/stanford-parser.jar:$STANFORDTOOLSDIR/stanford-parser-full-2015-12-09/stanford-parser-3.6.0-models.jar:$STANFORDTOOLSDIR/stanford-openie/stanford-openie.jar
#
# export STANFORD_MODELS=$STANFORDTOOLSDIR/stanford-ner-2015-12-09/classifiers:$STANFORDTOOLSDIR/stanford-postagger-full-2015-12-09/models:$STANFORDTOOLSDIR/stanford-openie/stanford-openie-models.jar
# sudo /etc/init.d/virtuoso-opensource-7 start


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
    for triple in triples:
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
                triple_dict[triple[1]].append([triple[0], triple[2]])
    print "here1"
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
        print k
        q_comment = 'SELECT distinct ?uri ?comment WHERE { ?uri rdfs:comment ?comment . FILTER langMatches( lang(?comment), "EN" ).  ?comment bif:contains "'+k.split()[1]+'" .}'
        q_label = 'SELECT distinct ?uri ?label WHERE { ?uri rdfs:label ?label . ?uri rdf:type rdf:Property . FILTER langMatches( lang(?label), "EN" ). ?label bif:contains "'+k.split()[1]+'" .}'
        predicate_result = sparql.query(sparql_dbpedia, q_comment)
        p_values = [sparql.unpack_row(row) for row in predicate_result]
        if not p_values:
            predicate_result = sparql.query(sparql_dbpedia, q_label)
            p_values = [sparql.unpack_row(row) for row in predicate_result]
        pval_list.append(p_values)
    return pval_list

def resource_extractor_updated(labels):
    global new_labels
    new_labels = []
    ent_size = []
    resources = {}
    raw_resources = {}
    for i,label in enumerate(labels):
        print label
        date_labels = []
        if label[1] != 'DATE':
            my_labels = label[0].split()
            if label[1] == 'PERSON':
                if len(my_labels) == 1:
                    q_u = ('SELECT distinct ?uri ?label WHERE { ?uri rdfs:label ?label . ?uri rdf:type foaf:Person . FILTER langMatches( lang(?label), "EN" ). ?label bif:contains "' +str(my_labels[0]) +'" . }')
                else:
                    q_u = ('SELECT distinct ?uri ?label WHERE { ?uri rdfs:label ?label . ?uri rdf:type foaf:Person . FILTER langMatches( lang(?label), "EN" ). ?label bif:contains "' +str(my_labels[-1]) +'" . FILTER (CONTAINS(?label, "'+str(my_labels[0])+'"))}')
                    q_birthname = ('PREFIX dbo: <http://dbpedia.org/ontology/> SELECT distinct ?uri ?name WHERE { ?uri dbo:birthName ?name . ?uri rdf:type foaf:Person . FILTER langMatches( lang(?name), "EN" ).?name bif:contains "' +str(my_labels[-1]) +'" . FILTER (CONTAINS(?name, "'+str(my_labels[0])+'"))}')
            elif label[1] == 'LOCATION':
                if len(my_labels) == 1:
                    q_u = ('PREFIX dbo: <http://dbpedia.org/ontology/> SELECT distinct ?uri ?label WHERE { ?uri rdfs:label ?label . ?uri rdf:type dbo:Location . FILTER langMatches( lang(?label), "EN" ). ?label bif:contains "' +str(my_labels[0]) +'" . }')
                elif ',' in label[0]:
                    my_labels = label[0].split(', ')
                    a=''
                    b=''
                    for my in my_labels:
                        if len(my.split(' '))>1:
                            b = my
                        else:
                            a = my
                    q_u = ('PREFIX dbo: <http://dbpedia.org/ontology/> SELECT distinct ?uri ?label WHERE { ?uri rdfs:label ?label . ?uri rdf:type dbo:Location . FILTER langMatches( lang(?label), "EN" ). ?label bif:contains "' +str(a) +'" . FILTER (CONTAINS(?label, "'+str(b)+'"))}')
                else:
                    q_u = ('PREFIX dbo: <http://dbpedia.org/ontology/> SELECT distinct ?uri ?label WHERE { ?uri rdfs:label ?label . ?uri rdf:type dbo:Location . FILTER langMatches( lang(?label), "EN" ). ?label bif:contains "' +str(my_labels[1]) +'" . FILTER (CONTAINS(?label, "'+str(my_labels[0])+'"))}')
            else:
                if len(my_labels) == 1:
                    q_u = ('SELECT distinct ?uri ?label WHERE { ?uri rdfs:label ?label . FILTER langMatches( lang(?label), "EN" ). ?label bif:contains "' +str(my_labels[0]) +'" . }')
                else:
                    q_u = ('SELECT distinct ?uri ?label WHERE { ?uri rdfs:label ?label .  FILTER langMatches( lang(?label), "EN" ). ?label bif:contains "' +str(my_labels[1]) +'" . FILTER (CONTAINS(?label, "'+str(my_labels[0])+'"))}')

            print q_u
            result = sparql.query(sparql_dbpedia, q_u)
            values = [sparql.unpack_row(row) for row in result]
            if not values and label[1] == 'PERSON':
                result = sparql.query(sparql_dbpedia, q_birthname)
                values = [sparql.unpack_row(row) for row in result]
            raw_resources[label[0]] = [val[0].split('/')[-1] for val in values]
            new_val = [val for val in values if not 'Category:' in val[0] and not 'wikidata' in val[0]]
            values = new_val
            ent_size.append(len(values))
            label = label+(len(new_val),)
            new_labels.append(label)
            add_score = [similar(label[0],val[1]) for val in values]
            for s,score in enumerate(add_score):
                if not 'Category:' in values[0] and not 'wikidata' in values[0]:
                    values[s].append(score)
                else:
                    values.remove(values[s])
            # print values
            sorted_values = sorted(values,key=operator.itemgetter(2),reverse=True)
            resources[label[0]] = sorted_values
        else:
            date_flag = 1
            date_labels.append(label[0])
    return resources, ent_size, date_labels, raw_resources


def date_checker(dl,vo_date):
    for d in dl:
        matched_date = [vo_d for vo_d in vo_date if d.date() == vo_d[1]]
    if matched_date:
        return matched_date
    else:
        return None


def relation_processor(relations):
    # print relations
    relation_graph = {}
    entity_dict = {}
    edge_dict = {}
    for n,rel in enumerate(relations):
        id_list = []
        for m,item in enumerate(rel):
            try:
                res_key = item[0].split('/')[-1]
            except:
                res_key = str(item[0])
            if m<2:
                if res_key not in entity_dict.keys():
                    res_id = len(entity_dict)+1
                    entity_dict[res_key]={'score':item[1],'id':res_id}
                    id_list.append(res_key)
                else:
                    id_list.append(res_key)
            else:
                if res_key not in edge_dict.keys():
                    edge_dict[res_key] = [{'id':len(edge_dict)+1,'score':item[1],'join':id_list}]
                else:
                    joins = []
                    for rels in edge_dict[res_key]:
                        joins.append(rels.get('join'))
                    if id_list not in joins:
                        edge_dict[res_key].append({'id': len(edge_dict) + 1, 'score': item[1],'join':id_list})
        # print entity_dict,edge_dict
        relation_graph = {'node':entity_dict,'edge':edge_dict}
    # print relation_graph
    # sys.exit(0)
    return relation_graph


def relation_extractor_1hop(resources,verb_entity):
    global new_labels
    print new_labels
    relation = []
    new_labels = sorted(new_labels, key=operator.itemgetter(2))
    new_labels = sorted(new_labels, key=operator.itemgetter(1), reverse=True)
    for i in range(0, len(resources) - 1):
        if str(new_labels[i][0]) in resources:
            item1_v = resources[new_labels[i][0]]
            predicate_comment = {}
            for i1 in item1_v:
                # print i1
                if 'dbpedia' in i1[0]:
                    url1 = i1[0]
                    score1 = [it for it in i1 if isinstance(it, float)]
                    score1 = score1[0]
                    print url1
                for j in range(i+1, len(resources)):
                    if str(new_labels[j][0]) in resources:
                        item2_v = resources[new_labels[j][0]]
                        url2_list = [i2[0] for i2 in item2_v]
                        url2_list=list(set(url2_list))
                        # print url2_list
                        for url2 in url2_list:
                            # print url2_list
                            q_1hop='select <'+url1+'> ?rel ?v0 ?rel1 <'+url2+'> where { <'+url1+'> ?rel ?v0 . ?v0 ?rel1 <'+url2+ '> . }'
                            # print q_1hop
                            result_1 = sparql.query(sparql_dbpedia, q_1hop)
                            val_1hop = [sparql.unpack_row(row_result) for row_result in result_1]
                            if val_1hop:
                                # print url2
                                # print q_1hop
                                for val in val_1hop:
                                    print val
                            else:
                                q_2hop='select <'+url1+'> ?rel ?v0 ?rel1 ?v1 ?rel2 <'+url2+'> where { <'+url1+'> ?rel ?v0 . ?v0 ?rel1 ?v1 . ?v1 ?rel2 <'+url2+ '> . }'
                                # print q_2hop
                                result_2 = sparql.query(sparql_dbpedia, q_2hop)
                                val_2hop = [sparql.unpack_row(row_result) for row_result in result_2]
                                if val_2hop:
                                    # print url2
                                    # print q_1hop
                                    for val in val_2hop:
                                        print val

    return None


def relation_extractor_triples(resources, triples):
    relation = []
    for triple_k, triples_v in triples.iteritems():
        for triple_v in triples_v:
            item1_v = resources[triple_v[0]]
            for i1 in item1_v:
                predicate_comment = {}
                if 'dbpedia' in i1[0]:
                    url1 = i1[0]
                    score1 = [it for it in i1 if isinstance(it, float)]
                    score1 = score1[0]
                    q_all = ('SELECT ?p ?o WHERE { <' + url1 + '> ?p ?o .}')
                    result = sparql.query(sparql_dbpedia, q_all)
                    q1_values = [sparql.unpack_row(row_result) for row_result in result]
                    q1_list = [qv[1] for qv in q1_values]
                item2_v = resources.get(triple_v[1])
                if item2_v:
                    url2_list = [i2[0] for i2 in item2_v]
                    intersect = set(url2_list).intersection(q1_list)
                    for inte in intersect:
                        match = [[[url1, score1], n] for m, n in enumerate(q1_values) if n[1] == inte]
                        # print match
                        if match:
                            for ma in match:
                                # print ma
                                # sys.exit(0)
                                predicate = ma[1][0]
                                if predicate not in predicate_comment.keys():
                                    comment = comment_extractor(predicate)
                                    predicate_comment[predicate] = comment
                                else:
                                    comment = predicate_comment[predicate]
                                # print ma, comment
                                pred_score = rel_score_triple(triple_k, comment)
                                # print pred_score
                                score, score2 = rel_score_label(ma, score1, item2_v, pred_score)
                                ma.pop(1)
                                ma.append(score2)
                                ma.append([predicate, score])
                                relation.append(ma)
                else:
                    date_match = get_dates(i1, triple_v[1])
                    # print date_match
                    # sys.exit(0)
                    if date_match:
                        for dm in date_match:
                            predicate = dm[1][0]
                            if predicate not in predicate_comment.keys():
                                comment = comment_extractor(predicate)
                                predicate_comment[predicate] = comment
                            else:
                                comment = predicate_comment[predicate]
                            pred_score = rel_score_triple(triple_k, comment)
                            score = rel_score_literal(dm, score1, pred_score)
                            dm.pop(1)
                            dm.append([triple_v[1],0])
                            dm.append([predicate, 1])
                            # print dm
                            # sys.exit(0)
                            relation.append(dm)
    return relation


def relation_extractor_updated1(resources, verb_entity):
    global new_labels
    print new_labels
    relation = []
    new_labels = sorted(new_labels, key=operator.itemgetter(2))
    new_labels = sorted(new_labels, key=operator.itemgetter(1), reverse=True)
    for i in range(0, len(resources) - 1):
        if str(new_labels[i][0]) in resources:
            item1_v = resources[new_labels[i][0]]
            predicate_comment = {}
            for i1 in item1_v:
                # print i1
                if 'dbpedia' in i1[0]:
                    url1 = i1[0]
                    score1 = [it for it in i1 if isinstance(it, float)]
                    score1 = score1[0]
                    # print score1
                    q_all = ('SELECT ?p ?o WHERE { <' + url1 + '> ?p ?o .}')
                    # print q_all
                    result = sparql.query(sparql_dbpedia, q_all)
                    q1_values = [sparql.unpack_row(row_result) for row_result in result]
                    q1_list = [qv[1] for qv in q1_values]
                    # print q1_list
                for j in range(i+1, len(resources)):
                    if str(new_labels[j][0]) in resources:
                        item2_v = resources[new_labels[j][0]]
                        url2_list = [i2[0] for i2 in item2_v]
                        # print url2_list
                        intersect = set(url2_list).intersection(q1_list)
                        for inte in intersect:
                            match = [[[url1,score1],n ] for m, n in enumerate(q1_values) if n[1] == inte]
                            # print match
                            if match:
                                for ma in match:
                                    predicate = ma[1][0]
                                    if predicate not in predicate_comment.keys():
                                        comment = comment_extractor(predicate)
                                        predicate_comment[predicate] = comment
                                    else:
                                        comment = predicate_comment[predicate]
                                    # print ma, comment
                                    pred_score = rel_score_predicate(verb_entity,comment)
                                    # print pred_score
                                    score, score2 = rel_score_label(ma,score1,item2_v,pred_score)

                                    ma.pop(1)
                                    ma.append(score2)
                                    # print ma
                                    ma.append([predicate,score])
                                    # print ma
                                    # relation.append(sum(ma, []))
                                    relation.append(ma)
    return relation, len(relation)


def rel_score_predicate(verb_entity,comment):
    # print verb_entity
    # print comment
    meaning = []
    verbs = []
    for vb in verb_entity:
        verbs.extend(vb.keys())
    for com in comment:
        meaning.extend(com[0].split())
    # print meaning
    for verb in verbs:
        if verb.lower() in meaning:
            return 1
        else:
            return 0


def rel_score_triple(triple_k, comment):
    # print triples_k
    # print comment
    meaning = []
    verbs = []
    verbs.extend([vb for vb in triple_k.split()])
    for com in comment:
        meaning.extend(com[0].split())
    # print "-----"
    # print meaning
    # print verbs
    # print "-----"
    score = 0
    for verb in verbs:
        if verb.lower() in meaning and verb.lower not in aux_verb:
            score = 1
    return score


def rel_score_literal(dm, score1, pred_score):
    score = (score1+pred_score) / 2
    return score


def rel_score_label(ma,score1,item2_v,pred_score):
    scores2 = [url2 for url2 in item2_v if url2[0] == ma[1][1]]
    # print "-----"
    # print score1
    scores2 = scores2[0]
    if len(scores2)>2:
        scores2.pop(1)
    # print score1, scores2[1],pred_score
    score = (score1 + scores2[1]+pred_score) / 3
    return score, scores2


def rel_score_simple(ma,score1,item2_v):
    scores2 = [url2 for url2 in item2_v if url2[0] == ma[1][1]]
    # print "-----"
    # print scores2
    scores2 = scores2[0]
    if len(scores2)>2:
        scores2.pop(1)
    # print scores2
    score = (score1 + scores2[1]) / 2
    return score, scores2


def comment_extractor(ont):
    if "property" in ont:
        ont = ont.replace("property","ontology")
    q_c=('SELECT distinct ?c WHERE  { <'+str(ont) + '> rdfs:comment ?c }')
    q_l = ('SELECT distinct ?c WHERE  { <' + str(ont) + '> rdfs:label ?c }')
    # print q_c
    comments = sparql.query(sparql_dbpedia, q_c)
    if comments:
        comment = [sparql.unpack_row(comment) for comment in comments]
        # print q_c
        if not comment:
            comments = sparql.query(sparql_dbpedia, q_l)
            if comments:
                # print q_l
                comment = [sparql.unpack_row(comment) for comment in comments]
            else:
                comment = ''
    else:
        # print "here"
        comments = sparql.query(sparql_dbpedia, q_l)
        if comments:
            comment = [sparql.unpack_row(comment) for comment in comments]
        else:
            comment = ''
    # sys.exit(0)
    return comment


def get_dates(i1,date_ent_str):
    v = i1[0]
    dates_matched = []
    if not isinstance(date_ent_str,datetime):
        # u'1940-04-25T00:00:00'
        date_ent = datetime.strptime(date_ent_str,"%Y-%m-%dT%H:%M:%S")
    # print date_ent
    # print date_ent.date()
    if 'dbpedia' in v:
        v = v.replace('page', 'resource')
        # print v
        try:
            dq = ('SELECT distinct ?r ?o WHERE  {  ?r a owl:DatatypeProperty ; rdfs:range xsd:date . <' + str(
                v) + '> ?r ?o .}')
            resultd = sparql.query(sparql_dbpedia, dq)
            for i, row1 in enumerate(resultd):
                values1 = sparql.unpack_row(row1)
                # print values1[1],date_ent.date()
                if values1[1] == date_ent.date():
                    # print v, values1
                    dates_matched.append([i1,values1])
                else:
                    year1 = str(values1[1]).split('-')[0]
                    if year1 == str(date_ent.date().year):
                        dates_matched.append([i1, values1])
        except:
            pass
    return dates_matched


if __name__ == '__main__':
    with open('obama_sample.txt','r') as f:
        para = f.readline()
