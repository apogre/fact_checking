# -*- coding: utf-8 -*- 

from nltk.tree import *
import dateutil.parser as dp
import sparql
import urllib2
from difflib import SequenceMatcher
import datetime
from itertools import groupby
import operator
from nltk.tag import StanfordNERTagger,StanfordPOSTagger
from nltk.parse.stanford import StanfordDependencyParser
import time, sys

objects = []
relation=[]
ROOT = 'ROOT'
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

target_predicate = {'born':['birthName','birthPlace','birthDate'],'married':['spouse']}

# export STANFORDTOOLSDIR=$HOME
# export CLASSPATH=$STANFORDTOOLSDIR/stanford-ner-2015-12-09/stanford-ner.jar:$STANFORDTOOLSDIR/stanford-postagger-full-2015-12-09:$STANFORDTOOLSDIR/stanford-parser-full-2015-12-09/stanford-parser.jar:$STANFORDTOOLSDIR/stanford-parser-full-2015-12-09/stanford-parser-3.6.0-models.jar
#
# export STANFORD_MODELS=$STANFORDTOOLSDIR/stanford-ner-2015-12-09/classifiers:$STANFORDTOOLSDIR/stanford-postagger-full-2015-12-09/models
# sudo /etc/init.d/virtuoso-opensource-7 start

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

def date_parser(docs):
    dates = []
    for doc in docs:
        try:
            dates.append([dp.parse(doc,fuzzy=True)])
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


def resource_extractor_updated(labels):
    global new_labels
    new_labels = []
    ent_size = []
    resources = {}
    raw_resources = {}
    for i,label in enumerate(labels):
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

            # print q_u
            result = sparql.query(sparql_dbpedia, q_u)
            values = [sparql.unpack_row(row) for row in result]
            if not values and label[1] == 'PERSON':
                result = sparql.query(sparql_dbpedia, q_birthname)
                values = [sparql.unpack_row(row) for row in result]
            # print values
            raw_resources[label[0]] = [val[0].split('/')[-1] for val in values]
            # print raw_resources
            # sys.exit(0)
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
            # print("--- %s res score seconds ---" % (time.time() - res_query1))
            # print "=============================================="
        else:
            date_flag = 1
            # print '++++++++++++++='
            # print label
            date_labels.append(label[0])
    return resources, ent_size, date_labels, raw_resources

def redirect_link(o_link):
    try:
        link = urllib2.urlopen(o_link)
        url1 = link.geturl()
        r_link = url1.replace('page','resource')
    except:
        r_link = o_link
    return r_link

def date_checker(dl,vo_date):
    for d in dl:
        matched_date = [vo_d for vo_d in vo_date if d.date() == vo_d[1]]
    if matched_date:
        return matched_date
    else:
        return None

def relation_processor(relations):
    pro_rels = []
    for rel in relations:
        pro_rel = [r.split('/')[-1] if isinstance(r,basestring) else r for r in rel]
        pro_rels.append(pro_rel)
    return pro_rels

def target_predicate_processor(resources,vb,date_labels):
    rel_dict = {}
    global new_labels
    new_labels = sorted(new_labels,key=operator.itemgetter(2))
    # print new_labels
    new_labels.sort(key=lambda x: len(x[1]))
    # new_labels = sorted(new_labels,key=len(operator.itemgetter(1)),reverse=True)
    # print new_labels
    # print vb
    # for v in vb:
    predicates = [target_predicate.get(v[0].lower()) for v in vb]
    predicates = [pred for pred in predicates if pred is not None]
    # print predicates
    for i in range(0,len(resources)-1):
        if str(new_labels[i][0]) in resources:
            item1_v = resources[new_labels[i][0]]
            for i1 in item1_v:
                if 'dbpedia' in i1[0]:
                    # url1 = redirect_link(i1[0])
                    url1 = i1[0]
                    # print url1
                    # q_all = ('SELECT ?p ?o WHERE {?s ?p ?o . FILTER ( ?s = <'+ url1 + '> )}')
                    q_all = ('SELECT ?p ?o WHERE { <'+ url1 + '> ?p ?o .}')
                    # print q_all
                    result = sparql.query(sparql_dbpedia, q_all)
                    q1_values = [sparql.unpack_row(row_result) for row_result in result]
                    # print q1_values
                    verb_ont = []
                    for predicate in predicates:
                        verb_ont = [q1_val for q1_val in q1_values if q1_val[0].split('/')[-1] in predicate]
                    # print verb_ont
                    # sys.exit(0)
                    if verb_ont:
                        if date_labels:
                            vo_date = [vo for vo in verb_ont if type(vo[1]) is datetime.date]
                            for dl in date_labels:
                                matched_date = date_checker(dl,vo_date)
                        else:
                            matched_date = None
                        for j in range(i+1,len(resources)):
                            if str(new_labels[j][0]) in resources:
                                item2_v = resources[new_labels[j][0]]
                                # print "item2============="
                                # print item2_v
                                new_time=time.time()
                                url2_list = [i2[0] for i2 in item2_v]
                                # print url2_list
                                # print verb_ont
                                vo_list = [vo[1] for vo in verb_ont]
                                # print vo_list
                                intersect = set(url2_list).intersection(vo_list)
                                for inte in intersect:
                                    match = [[url1,j,inte] for i, j in enumerate(verb_ont) if j[1] == inte]
                                if intersect and match:
                                    # print("--- %s url2 seconds ---" % (time.time() - new_time))
                                    return match, matched_date
                    else:
                        return None, None

def relation_extractor_updated1(resources):
    global new_labels
    print new_labels
    relation = []
    new_labels = sorted(new_labels, key=operator.itemgetter(2))
    new_labels = sorted(new_labels, key=operator.itemgetter(1), reverse=True)
    for i in range(0, len(resources) - 1):
        if str(new_labels[i][0]) in resources:
            item1_v = resources[new_labels[i][0]]
            for i1 in item1_v:
                if 'dbpedia' in i1[0]:
                    url1 = i1[0]
                    score1 = i1[2]
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
                            match = [[n, [url1]] for m, n in enumerate(q1_values) if n[1] == inte]
                            # print match
                            if match:
                                for ma in match:
                                    # print ">>>>>"
                                    # print ma
                                    scores2 = [url2[2] for url2 in item2_v if url2[0] == ma[0][1]]
                                    # print scores2
                                    score = (score1+scores2[0])/2
                                    ma.append([score])
                                    # print ma
                                    relation.append(sum(ma, []))
    return relation , len(relation)
 
def relation_extractor_updated(resources):
    global new_labels
    rel_count = 0
    relation = []
    new_labels = sorted(new_labels,key=operator.itemgetter(2))
    new_labels = sorted(new_labels,key=operator.itemgetter(1),reverse=True)
    print new_labels
    all_output=[]
    ext_output=[]
    rel_dict = {}
    loc_flag = 0
    for i in range(0,len(resources)-1):
        if str(new_labels[i][0]) in resources:
            item1_v = resources[new_labels[i][0]]
            for i1 in item1_v:
                if 'dbpedia' in i1[0]:
                    # url1 = redirect_link(i1[0])
                    url1 = i1[0]
                    # print url1
                    # q_all = ('SELECT ?p ?o WHERE {?s ?p ?o . FILTER ( ?s = <'+ url1 + '> )}')
                    q_all = ('SELECT ?p ?o WHERE { <'+ url1 + '> ?p ?o .}')
                    # print q_all
                    result = sparql.query(sparql_dbpedia, q_all)
                    q1_values = [sparql.unpack_row(row_result) for row_result in result]
                    # print q1_values
                    q1_list = [qv[1] for qv in q1_values]
                    print q1_list
                    # print len(set(q1_list))
                    # sys.exit(0)
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
                        url2_list = [i2[0] for i2 in item2_v]
                        print url2_list
                        intersect = set(url2_list).intersection(q1_list)
                        print intersect
                        for inte in intersect:
                            match = [[j,[url1]] for i, j in enumerate(q1_values) if j[1] == inte]
                            match = match[0]
                            print match
                            print sum(match,[])
                        sys.exit(0)
                        for i2 in item2_v:
                            # print i2
                            if i2[2]>threshold:
                                if 'dbpedia' in i2[0]:
                                    # url2 = redirect_link(i2[0])
                                    url2 = i2[0]
                                    # print url2PREFIX dbo: <http://dbpedia.org/ontology/> SELECT distinct ?uri ?label WHERE { ?uri rdfs:label ?label . ?uri rdf:type dbo:Location . FILTER langMatches( lang(?label), "EN" ). ?label bif:contains "Hawaii" . }

                                    if loc_flag == 1:
                                        loc_detail = []
                                        # q_loc = ('SELECT ?p ?o WHERE {?s ?p ?o . FILTER ( ?s = <'+ url2 + '> )}')
                                        q_loc = ('SELECT ?p ?o WHERE { <'+ url2 + '> ?p ?o .}')
                                        result_loc = sparql.query(sparql_dbpedia, q_loc)
                                        q1_loc = [sparql.unpack_row(row_result_loc) for row_result_loc in result_loc]
                                        # print q1_loc
                                        search = ['http://dbpedia.org/ontology/capital','http://dbpedia.org/ontology/country','http://dbpedia.org/ontology/isPartOf']
                                        for s in search:
                                            match = [e for e in q1_loc if e[0] == s]
                                                # print e[0]
                                            # print match
                                            if match:
                                                for m in match:
                                                    m.append(url2)
                                                    loc_detail.append(m)
                                        # print loc_detail
                                        # sys.exit(0)
                                    # print q1_values
                                    output = [val for val in q1_values if url2 in val]
                                    # print output
                                    if output:
                                        # print "here"
                                        # print output
                                        for o in output:
                                            o.append(url1)
                                        all_output.append(output)
                                        # print all_output
                                        break
                                    else:
                                        if loc_flag==1:
                                            if loc_detail:
                                                # print loc_detail
                                                for loc_d in loc_detail:
                                                    output_ext = [val for val in q1_values if loc_d[1] in val]
                                                    for o_c,oe in enumerate(output_ext):
                                                        ext_output.append([url1,oe,loc_d,url2])
                                        loc_flag = 0
                                # print ext_output
                            else:
                                break
                if all_output:
                    break
    if ext_output:
        # print ext_output
        for ext in ext_output:
            if 'ontology' in ext[1][0]:
                # print ext[1][0]
                comment = comment_extractor(ext[1][0])
                if comment:
                    ext[1].append(comment[0])
            # print ext
            if 'ext' not in rel_dict:
                rel_dict['ext'] = [ext]
            else:
                rel_dict['ext'].append(ext)
                # print ext[0],ext[1][0],comment,ext[3]
    if all_output or ext_output:
        if all_output:
            for out in all_output[0]:
                if 'ontology' in out[0]:    
                    comment = comment_extractor(out[0])
                    relation.append([(out[2]),(str(out[0])),comment,(out[1])]) 
            if relation:
                rel_dict['relation'] = relation
        return rel_dict, rel_count
    return None, rel_count

def comment_extractor(ont):
    q_c=('SELECT distinct ?c WHERE  { <'+str(ont) + '> rdfs:comment ?c }')
    comments = sparql.query(sparql_dbpedia, q_c)
    if comments:
        comment = [sparql.unpack_row(comment) for comment in comments]
    else:
        comment = ''
    return comment

def entity_sorter(labels):
    pass


def relation_extractor(resources):
    global new_labels
    print "====Relations===="
    my_item1 = []
    my_item2 = []
    rel_count = 0
    relation = []
    new_labels = sorted(new_labels,key=operator.itemgetter(2))
    new_labels = sorted(new_labels,key=operator.itemgetter(1),reverse=True)
    print new_labels
    print "here"
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