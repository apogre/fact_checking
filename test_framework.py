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

def fact_checker(sentence_list):
    ne_s,pos_s = fact_check.st_tagger(sentence_list)
    # print ne_s
    # print pos_s
    print("--- %s seconds ---" % (time.time() - start_time))
    print "================================================"
    for n,ne in enumerate(ne_s):
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
        resources, ent_size = fact_check.resource_extractor_updated(ent)
        # print resources
        relation, rel_count = fact_check.relation_extractor_updated(resources)
        print vb                    
        print relation
        if relation:
            for rel in relation['relation']:
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

        print("--- %s seconds ---" % (time.time() - new_time))
        print "=============================================="
                

with open('simple.txt','r') as f:
    sentences = f.readlines()
    # print len(sentences)
    for i,sentence in enumerate(sentences):
        i = i+1
        # print i
        count = count+1
        new_labels = []
        # print sentence
        start_time = time.time()
        sent = word_tokenize(sentence)
        # print sent
        # print i
        # print len(sentences),i
        if i%5 != 0:
            # print i
            # print sent
            sentence_list.append(sent)
            if i == len(sentences):
                print sentence_list
                fact_checker(sentence_list)
        else:
            # print 'here'
            # sys.exit(0)
            # print tokens
            print sentence_list
            fact_checker(sentence_list)
            sentence_list = []
            sentence_list.append(sent)
            # sys.exit(0)
            # ne_s,pos_s = fact_check.st_tagger(sentence_list)
            # print("--- %s seconds ---" % (time.time() - start_time))
            # print "================================================"
            
            # count = 0
            # # sys.exit(0)
            # for n,ne in enumerate(ne_s):
            #     # print ne 
            #     new_time = time.time()
            #     ent =  fact_check.get_nodes_updated(ne)
            #     # print ent
            #     vb = fact_check.get_verb(pos_s[n])
            #     # print vb
            #     # updated_labels = []
            #     # for en in ent:
            #     #     if 'University' in en[0] or 'College' in en[0] or 'School' in en[0]:
            #     #         label1 = str(en[0])+' alumni'
            #     #         tup2 = (label1,en[1])
            #     #         # print tup2
            #     #         updated_labels.append(tup2)
            #     # ent.extend(updated_labels)
            #     # try:
            #     #     date = date_parser(doc)
            #     #     tup1 = (date,'DATE')
            #     #     ent.append(tup1)
            #     #     date_flag = 1
            #     # except:
            #     #     pass
            #     # print "====Entities===="
            #     # print ent
            #     # for e in ent:
            #     #     if e[1] == 'LOCATION' and ',' in e[0]:
            #     #         loc_label = e[0].split(',')
            #     #         for loc in loc_label:
            #     #             ent.append((loc,'LOCATION'))
            #     # print ent
            #     # print vb
            #     # print("--- %s seconds ---" % (time.time() - start_time))
            #     resources, ent_size = fact_check.resource_extractor_updated(ent)
            #     # print "====Resources Count===="
            #     # print resources
            #     # print ent_size
            #     relation, rel_count = fact_check.relation_extractor_updated(resources)
            #     print vb
            #     # print "no. of iterations: " + str(rel_count)
            #     print relation
            #     if relation:
            #         for rel in relation:
            #             for v in vb:
            #                 # print v
            #                 # print relation[2]
            #                 if v[0] not in aux_verb:
            #                     for r in rel[2]:
            #                         if v[0].lower() in r[0].split():
            #                             print "The statement is True"
            #                             true_flag = 1
            #     if true_flag == 0:
            #         print "The statement is False"
            #     print("--- %s seconds ---" % (time.time() - new_time))
            #     print "=============================================="
            #         # print date_flag
            #         # now_current = datetime.datetime.now()
            #         # relation_extractor(resources)
            #         # total_time = datetime.datetime.now() - now_current
            #         # print total_time
            #         # if date_flag == 1:
            #         #     date_extractor(date,resources)
            #         #     date_flag = 0
            #         # objects.extend(ent)
            #     # except:
            #     #     pass
# print sentence_list