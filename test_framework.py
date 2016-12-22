import fact_check
from nltk import word_tokenize
import sys
import time

aux_verb = ['was','is','become']

sentence_list= []
count = 0

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

def validator(relation,vb,true_flag=0):
    if relation:
        for rel in relation.get('relation',[]):
            print rel
            for v in vb:
                # print v
                # print relation[2]
                if v[0] not in aux_verb:
                    for r in rel[2]:
                        if v[0].lower() in r[0].split():
                            print "The statement is True"
                            true_flag = 1
    if true_flag == 0:
        print "The statement is False with direct relation"
        print "=============================================="
        if relation:
            for ext in relation.get('ext',[]):
                # print ext
                for v in vb:
                    if v[0] not in aux_verb:
                        if len(ext[1])>2:
                            for e in ext[1][2]:
                                # print v[0].lower(),e 
                                if v[0].lower() in e.split():
                                    print ext
                                    print "True by one loop"


def fact_checker(sentence_list):
    ne_s,pos_s = fact_check.st_tagger(sentence_list)
    # print ne_s
    # print pos_s
    print("--- %s seconds ---" % (time.time() - start_time))
    print "================================================"
    for n,ne in enumerate(ne_s):
        print n
        true_flag = 0
        new_time = time.time()
        ent =  fact_check.get_nodes_updated(ne)
        # print ent
        new_loc = location_update(ne)
        # print new_loc
        if new_loc:
            new_ent = (new_loc[0],'LOCATION')
            ent.append(new_ent)
        # print ent
        vb = fact_check.get_verb(pos_s[n])
        print vb
        resources, ent_size = fact_check.resource_extractor_updated(ent)
        # print resources
        relation = fact_check.target_predicate_processor(resources,vb)
        # relation, rel_count = fact_check.relation_extractor_updated(resources)
        # print vb  
        # print "here================="                  
        if relation:
            print relation
            print "The statement in True"
        else:
            print "The statement is False with direct relation"
        # validator(relation,vb)
        # sys.exit(0)
        # if relation:
        #     for rel in relation.get('relation',[]):
        #         print rel
        #         for v in vb:
        #             # print v
        #             # print relation[2]
        #             if v[0] not in aux_verb:
        #                 for r in rel[2]:
        #                     if v[0].lower() in r[0].split():
        #                         print "The statement is True"
        #                         true_flag = 1
        # if true_flag == 0:
        #     print "The statement is False with direct relation"
        #     print "=============================================="
        #     if relation:
        #         for ext in relation.get('ext',[]):
        #             # print ext
        #             for v in vb:
        #                 if v[0] not in aux_verb:
        #                     if len(ext[1])>2:
        #                         for e in ext[1][2]:
        #                             # print v[0].lower(),e 
        #                             if v[0].lower() in e.split():
        #                                 print ext
        #                                 print "True by one loop"

        print("--- %s seconds ---" % (time.time() - new_time))
        print "=============================================="
                

with open('simple.txt','r') as f:
    all_time = time.time()
    sentences = f.readlines()
    for i,sentence in enumerate(sentences):
        i = i+1
        count = count+1
        new_labels = []
        start_time = time.time()
        sent = word_tokenize(sentence)
        if i%20 != 0:
            sentence_list.append(sent)
            if i == len(sentences):
                print sentence_list
                fact_checker(sentence_list)
        else:
            print sentence_list
            fact_checker(sentence_list)
            sentence_list = []
            sentence_list.append(sent)
    print("--- %s full time in seconds ---" % (time.time() - all_time))
    print "================================================"