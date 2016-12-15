# -*- coding: utf-8 -*- 

import nltk
from nltk.tree import *
import cPickle as pickle
import csv
import sys
import dateutil.parser as dp
import sparql
import urllib2
import json
from difflib import SequenceMatcher
import datetime
from string import digits
from itertools import groupby
import operator
from nltk.tag import StanfordNERTagger,StanfordPOSTagger


objects = []
relation=[]
ROOT = 'ROOT'
# SPARQL_SERVICE_URL = 'https://query.wikidata.org/sparql'
sparql_dbpedia = 'http://localhost:8890/sparql'
# sparql_dbpedia = 'https://dbpedia.org/sparql'
global date_flag
date_flag = 0
threshold_value = 0.8

st_ner = StanfordNERTagger('english.all.3class.distsim.crf.ser.gz')
st_pos = StanfordPOSTagger('english-bidirectional-distsim.tagger')

# export STANFORDTOOLSDIR=$HOME
# export CLASSPATH=$STANFORDTOOLSDIR/stanford-ner-2015-12-09/stanford-ner.jar:$STANFORDTOOLSDIR/stanford-postagger-full-2015-12-09
# export STANFORD_MODELS=$STANFORDTOOLSDIR/stanford-ner-2015-12-09/classifiers:$STANFORDTOOLSDIR/stanford-postagger-full-2015-12-09/models

# grammar = r"""
#         NP: {<DT>?<JJ.*>*<NN.*>+}
#             {}
#     """
# cp = nltk.RegexpParser(grammar)
# select ?p ?o where {
#   ?p a owl:DatatypeProperty ;
#      rdfs:range xsd:date .
#  <http://dbpedia.org/resource/Barack_Obama> ?p ?o .
# }
# SELECT distinct ?uri ?label
# WHERE {
#    ?uri rdfs:label ?label .
#    FILTER regex(str(?label), "Barack Hussein Obama", "i")
# }
# q_u = ('SELECT distinct ?uri ?label WHERE { ?uri rdfs:label ?label . ?uri rdf:type foaf:'+ str(label[1].title()) + ' . FILTER (regex(str(?label),"'+ str(label[0]) +'", "i") && langMatches(lang(?label),"EN") )} limit 100')

def get_nodes_updated(netagged_words):
    ent = []
    for tag, chunk in groupby(netagged_words, lambda x:x[1]):
        # print tag
        if tag != "O":
            tuple1 =(" ".join(w for w, t in chunk),tag)
            ent.append(tuple1)
    return ent

def get_verb(postagged_words):
    verb = []
    for tag in postagged_words:
        if "VB" in tag[1]:
            verb.append(tag)
    return verb

def similar(a,b):
    return SequenceMatcher(None,a,b).ratio()

def date_parser(doc):
    return dp.parse(doc,fuzzy=True)


def st_tagger(sentence_list):
    ne_s = st_ner.tag_sents(sentence_list)
    pos_s = st_pos.tag_sents(sentence_list)
    return ne_s, pos_s


entities = {} 
new_labels = []


def resource_extractor_updated(labels):
    # print labels
    global new_labels
    new_labels = []
    ent_size = []
    resources = {}
    for i,label in enumerate(labels):
        resource_list = []
        score_list = {}
        if label[1] != 'DATE':
            # print label[0]
            my_labels = label[0].split()
            if label[1] == 'PERSON':
                if len(my_labels) == 1:
                    q_u = ('SELECT distinct ?uri ?label WHERE { ?uri rdfs:label ?label . ?uri rdf:type foaf:Person . FILTER langMatches( lang(?label), "EN" ). ?label bif:contains "' +str(my_labels[0]) +'" . }')
                else:
                    q_u = ('SELECT distinct ?uri ?label WHERE { ?uri rdfs:label ?label . ?uri rdf:type foaf:Person . FILTER langMatches( lang(?label), "EN" ). ?label bif:contains "' +str(my_labels[-1]) +'" . FILTER (CONTAINS(?label, "'+str(my_labels[0])+'"))}')
            elif label[1] == 'LOCATION':
                if len(my_labels) == 1:
                    q_u = ('PREFIX dbo: <http://dbpedia.org/ontology/> SELECT distinct ?uri ?label WHERE { ?uri rdfs:label ?label . ?uri rdf:type dbo:Location . FILTER langMatches( lang(?label), "EN" ). ?label bif:contains "' +str(my_labels[0]) +'" . }')
                elif ',' in label[0]:
                    print label[0]
                    my_labels = label[0].split(', ')
                    q_u = ('PREFIX dbo: <http://dbpedia.org/ontology/> SELECT distinct ?uri ?label WHERE { ?uri rdfs:label ?label . ?uri rdf:type dbo:Location . FILTER langMatches( lang(?label), "EN" ). ?label bif:contains "' +str(my_labels[0]) +'" . FILTER (CONTAINS(?label, "'+str(my_labels[1])+'"))}')
                else:
                    q_u = ('PREFIX dbo: <http://dbpedia.org/ontology/> SELECT distinct ?uri ?label WHERE { ?uri rdfs:label ?label . ?uri rdf:type dbo:Location . FILTER langMatches( lang(?label), "EN" ). ?label bif:contains "' +str(my_labels[1]) +'" . FILTER (CONTAINS(?label, "'+str(my_labels[0])+'"))}')
            else:
                if len(my_labels) == 1:
                    q_u = ('SELECT distinct ?uri ?label WHERE { ?uri rdfs:label ?label . FILTER langMatches( lang(?label), "EN" ). ?label bif:contains "' +str(my_labels[0]) +'" . }')
                else:
                    q_u = ('SELECT distinct ?uri ?label WHERE { ?uri rdfs:label ?label .  FILTER langMatches( lang(?label), "EN" ). ?label bif:contains "' +str(my_labels[1]) +'" . FILTER (CONTAINS(?label, "'+str(my_labels[0])+'"))}')

            # print q_u
            # sys.exit()
            result = sparql.query(sparql_dbpedia, q_u)
            link_list = []
            # print result
            # types = {}
            # print 'here'
            
            values = [sparql.unpack_row(row) for row in result]
            # print values
            new_val = [val for val in values if not 'Category:' in val[0] and not 'wikidata' in val[0]]
            values = new_val
            ent_size.append(len(values))
            label = label+(len(new_val),)
            new_labels.append(label)

            add_score = [similar(label[0],val[1]) for val in values]
            # print add_score

            for s,score in enumerate(add_score):
                if not 'Category:' in values[0] and not 'wikidata' in values[0]:
                    values[s].append(score)
                else:
                    values.remove(values[s])
            # print values

            sorted_values = sorted(values,key=operator.itemgetter(2),reverse=True)
            # print "=====================sorted"
            # print sorted_values
            # resources.append(sorted_values)
            # sys.exit()
                # if not 'Category:' in values[0] and not 'wikidata' in values[0]:
                #     r_link = redirect_link(values[0])
                #     if r_link not in link_list:
                #         try:
                #             # q_type=('SELECT distinct ?type WHERE  { <'+str(r_link.encode('utf-8')) + '> rdf:type ?type }')
                #             # result_type = sparql.query(sparql_dbpedia, q_type)
                #             link_list.append(r_link)
                #             type_list = []
                #             # print q_type
                #             # for row_type in result_type:
                #                 # types1 = sparql.unpack_row(row_type)
                #                 # print types1
                #                 # mytype =  types1[0].split('/')[-1]
                #                 # types = str(mytype).translate(None,digits)
                #                 # print types
                #                 # if '#' in types:
                #                 #     types = types.split('#')[-1]
                #                 # type_list.append(types)
                #             # type_list = list(set(type_list))
                #             # if 'Q' in type_list:
                #             #     type_list.remove('Q')
                #             # print type_list
                #             score = similar(values[1],label[0])
                #             print score
                #             # values.append(type_list)
                #             if score in score_list:
                #                 score_list[score].append(values)
                #             else:
                #                 score_list[score] = [values]
                #         except:
                #             pass
            # q = ('select distinct ?x where{?x rdfs:label "'+ label[0] +'"@en }')
            # result = sparql.query('http://localhost:8890/sparql', q)
            # for row in result:
            #     values = sparql.unpack_row(row)
            #     if not 'Category:' in values[0] or 'alumni' in values[0]:
            #         # print values[0]
            #         # resource_list.append(values[0])
            #         q1=('SELECT distinct ?type WHERE  { <'+str(values[0].encode()) + '> rdf:type ?type }')
            #         print q1
            #         result1 = sparql.query('http://localhost:8890/sparql', q1)
            #         type_list = []
            #         for row1 in result1:
            #             values1 = sparql.unpack_row(row1)
            #             mytype =  values1[0].split('/')[-1]
            #             types = str(mytype).translate(None,digits)
            #             if '#' in types:
            #                 types = types.split('#')[-1]
            #             type_list.append(types)
            #         main_value = [values[0],label[0],type_list]
            #         if 1.0 in score_list:
            #             score_list[1.0].append(main_value)
            #         else:
            #             score_list[1.0] = [main_value]
            resources[label[0]] = sorted_values
    return resources, ent_size

def redirect_link(o_link):
    try:
        link = urllib2.urlopen(o_link)
        url1 = link.geturl()
        r_link = url1.replace('page','resource')
    except:
        r_link = o_link
    return r_link

def relation_extractor_updated(resources):
    # print resources
    # sys.exit(0)
    global new_labels
    rel_count = 0
    relation = []
    new_labels = sorted(new_labels,key=operator.itemgetter(2))
    print new_labels
    all_output=[]
    loc_flag = 0
    for i in range(0,len(resources)-1):
        if str(new_labels[i][0]) in resources:
            item1_v = resources[new_labels[i][0]]
            for i1 in item1_v:
                if 'dbpedia' in i1[0]:
                    url1 = redirect_link(i1[0])
                    q_all = ('SELECT ?p ?o WHERE {?s ?p ?o . FILTER ( ?s = <'+ url1 + '> )}')
                    # print q_all
                    result = sparql.query(sparql_dbpedia, q_all)
                    q1_values = [sparql.unpack_row(row_result) for row_result in result]
                    # print q1_values
                    # print url1
                for j in range(i+1,len(resources)):
                    if str(new_labels[j][0]) in resources:
                        item2_v = resources[new_labels[j][0]]
                        # print item2_v
                        if new_labels[j][1]=='PERSON':
                            threshold = 0.5
                        if new_labels[j][1]=='LOCATION':
                            loc_flag = 1
                            threshold = 0.9
                        else:
                            threshold = 0.9
                        # print threshold
                        for i2 in item2_v:
                            # print i2
                            if i2[2]>threshold:
                                if 'dbpedia' in i2[0]:
                                    url2 = redirect_link(i2[0])
                                    # print url2
                                    if loc_flag == 1:
                                        loc_detail = []
                                        q_loc = ('SELECT ?p ?o WHERE {?s ?p ?o . FILTER ( ?s = <'+ url2 + '> )}')
                                        result_loc = sparql.query(sparql_dbpedia, q_loc)
                                        q1_loc = [sparql.unpack_row(row_result_loc) for row_result_loc in result_loc]
                                        # print q1_loc
                                        search = ['http://dbpedia.org/ontology/capital','http://dbpedia.org/ontology/country']
                                        for s in search:
                                            match = [e for e in q1_loc if e[0] == s]
                                                # print e[0]
                                            match.append(url2)
                                            loc_detail.append(match)
                                            # print loc_detail
                                        # sys.exit(0)
                                        loc_flag = 0
                                    # print q1_values
                                    output = [val for val in q1_values if url2 in val]
                                    # print output
                                    if output:
                                        # print output
                                        for o in output:
                                            o.append(url1)
                                        all_output.append(output)
                                        # print all_output
                                        break
                                    else:
                                        if loc_detail:
                                            for loc_d in loc_detail:
                                                output_ext = [val for val in q1_values if loc_d[0][1] in val]
                                            print url1,output_ext,url2
                                            # print url1,loc_detail


                            else:
                                break
                # print output
                if all_output:
                    # print "ereeee"
                    break
    # print all_output
    # sys.exit(0)
    if all_output:
        for out in all_output[0]:
            # print out
            # sys.exit(0)
            if 'ontology' in out[0]:
                # print out
                # print "relations============"
                q_c=('SELECT distinct ?c WHERE  { <'+str(out[0]) + '> rdfs:comment ?c }')
                # print q_c
                comments = sparql.query(sparql_dbpedia, q_c)
                if comments:
                    comment = [sparql.unpack_row(comment) for comment in comments]
                else:
                    comment = ''
                relation.append([(out[2]),(str(out[0])),comment,(out[1])]) 
                # print([str(url1),str(values1[0]),str(url2)])
        if relation:
            return relation, rel_count
    return None, rel_count

def relation_extractor(resources):
    global new_labels
    print "====Relations===="
    my_item1 = []
    my_item2 = []
    rel_count = 0
    relation = []
    new_labels = sorted(new_labels,key=operator.itemgetter(2))
    print new_labels
    for i in range(0,len(resources)-1):
        if str(new_labels[i][0]) in resources:
            item1_v = resources[new_labels[i][0]]
            for i1 in item1_v:
                if 'dbpedia' in i1[0]:
                    url1 = redirect_link(i1[0])
                    # print url1
                for j in range(i+1,len(resources)):
                    if str(new_labels[j][0]) in resources:
                        item2_v = resources[new_labels[j][0]]
                        for i2 in item2_v:
                            if 'dbpedia' in i2[0]:
                                url2 = redirect_link(i2[0])
                            try:
                                q1=('SELECT ?r WHERE  { <'+str(url1) + '> ?r <' +str(url2)+'>}')
                                # print q1
            #                     # if 'wikidata' in item1 and 'wikidata' in item2:
            #                     #     print q1
            #                     #     result1 = doSparqlQuery(q1)
            #                     #     data = result1['results']['bindings'][0]
            #                     #     print([str(item1),str(data['r']['value']),str(item2)])
            #                     #     print '\n'
            #                     #     rel =  data['r']['value'].split('/')
            #                     #     relation.append(rel[-1])
            #                     # if url1 not in my_item1 and url2 not in my_item2:
                                if 'dbpedia' in url1 and 'dbpedia' in url2:
                                    # print i1[2],i2[2]
                                    # if i1[2]>threshold_value and i2[2] > threshold_value:
                                        # if url1 not in my_item1:
                                    result1 = sparql.query(sparql_dbpedia, q1)
                                    # print q1
                                    rel_count+=1
                                    # print "urls============"
                                    # print url1
                                    # print url2
                                    
            #                         my_item2.append(url2)
                                    if result1:
                                        for row1 in result1:
                                            values1 = sparql.unpack_row(row1)
                                            # print values1
                                            if 'ontology' in values1[0]:
                                                # print "relations============"
                                                q_c=('SELECT distinct ?c WHERE  { <'+str(values1[0]) + '> rdfs:comment ?c }')
                                                comments = sparql.query(sparql_dbpedia, q_c)
                                                if comments:
                                                    comment = [sparql.unpack_row(comment) for comment in comments]
                                                else:
                                                    comment = ''
                                                relation.append([(str(url1),i1[2]),(str(values1[0])),comment,(str(url2),i2[2])]) 
                                                # print([str(url1),str(values1[0]),str(url2)])
                                        if relation:
                                            return relation, rel_count
                #                                 print '\n'
                #                                 rel =  values1[0].split('/')
                #                                 relation.append(rel[-1])
                #                         # print relation
                #                                     # writer.writerow([str(item1),str(values1[0]),str(item2)])  
                #                                 # relation.append(values1[0])
                                        # else:
                                            # break
                            except:
                                    pass
                        # my_item1.append(url1) 
    return None, rel_count

def date_extractor(date,resources):
    # print resources
    for key,val in resources.iteritems():
        for v in val:
            # print v
            if 'dbpedia' in v:
                link = urllib2.urlopen(v)
                v = link.geturl()
                v = v.replace('page','resource')
                dq=('SELECT distinct ?r ?o WHERE  {  ?r a owl:DatatypeProperty ; rdfs:range xsd:date . <'+str(v) + '> ?r ?o .}')
                resultd = sparql.query(sparql_dbpedia, dq)
                # print resultd
                for i,row1 in enumerate(resultd):
                    # print i
                    values1 = sparql.unpack_row(row1)
                    
                    if values1[1] == date.date():
                        print v,values1
                    # resources[key].extend(values1)


if __name__ == '__main__':
    with open('obama_sample.txt','r') as f:
        para = f.readline()
        for i,row in enumerate(para.split('.')):
            # try:
            if row:
                doc = row
                print doc
                tree = st.tag(doc.split())
                print tree
                ent =  get_nodes_updated(tree)
                # print ent
                # sys.exit()
                updated_labels = []
                for en in ent:
                    if 'University' in en[0] or 'College' in en[0] or 'School' in en[0]:
                        label1 = str(en[0])+' alumni'
                        tup2 = (label1,en[1])
                        # print tup2
                        updated_labels.append(tup2)
                ent.extend(updated_labels)

                try:
                    date = date_parser(doc)
                    tup1 = (date,'DATE')
                    ent.append(tup1)
                    date_flag = 1
                except:
                    pass
                print "====Entities===="
                # print ent
                for e in ent:
                    if e[1] == 'LOCATION' and ',' in e[0]:
                        loc_label = e[0].split(',')
                        for loc in loc_label:
                            ent.append((loc,'LOCATION'))
                        # ent.remove(e)
                print ent
                # sys.exit()
                resources = resource_extractor_updated(ent)
                print "====Resources===="
                # print resources
                relation_extractor(resources)
                print date_flag
                now_current = datetime.datetime.now()
                relation_extractor(resources)
                total_time = datetime.datetime.now() - now_current
                print total_time
                if date_flag == 1:
                    date_extractor(date,resources)
                    date_flag = 0
                objects.extend(ent)
            # except:
            #     pass