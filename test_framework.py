import fact_check
from nltk import word_tokenize
import sys
import time

aux_verb = ['was','is','become']

expected_outputs = {0:[[u'birthPlace', u'New_York', u'Al_Pacino']],2:[[u'birthPlace', u'Hawaii', u'Barack_Obama']],
                    1:[[u'spouse', u'Barack_Obama', u'Michelle_Obama']],3:[[u'birthPlace', u'New_York_City', u'Robert_De_Niro']],
                    5:[[u'birthPlace', u'Neptune_Township,_New_Jersey', u'Danny_DeVito']],6:[[u'birthPlace', u'Santa_Monica,_California', u'Jack_Black']],
                    11:[[u'birthPlace', u'New_York_City', u'Scarlett_Johansson']],9:[[u'birthPlace', u'Brampton', u'Michael_Cera']],
                    8:[[u'spouse', u'Scarlett_Johansson', u'Ryan_Reynolds']],7:[[u'spouse', u'Scarlett_Johansson', u'Ryan_Reynolds']],
                    4:[[u'birthPlace', u'Syracuse,_New_York', u'Megyn_Kelly']],10:[[u'birthPlace', u'New_Brunswick,_New_Jersey', u'Michael_Douglas']]}

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

def validator_entitymap(relation,vb,true_flag=0):
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
        # print "=============================================="
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
                                    pass

def validator_verbpredicate(relation,dates):
    if relation:
        print relation
        print dates, "The statement is True"
    else:
        print "The statement is False with direct relation"
    print "=============================================="

def precision_recall(n,relations):
    unique_rel = [list(x) for x in set(tuple(x) for x in relations)]
    # print unique_rel
    ex_out = expected_outputs[n]
    # print ex_out
    correct_results = [rel for rel in unique_rel if rel in ex_out]
    cr = float(len(correct_results))
    # print cr, len(ex_out), len(unique_rel)
    precision = cr/float(len(unique_rel))
    recall = cr/float(len(ex_out))
    return precision, recall



def fact_checker(sentence_lis):
    print sentence_lis
    dates = fact_check.date_parser(sentence_lis)
    sentence_list = [word_tokenize(sent) for sent in sentence_lis]
    ne_s,pos_s = fact_check.st_tagger(sentence_list)
    for i in range(0,1):
        for n,ne in enumerate(ne_s):
            ent = fact_check.get_nodes_updated(ne)
            new_loc = location_update(ne)
            if new_loc:
                new_ent = (new_loc[0],'LOCATION')
                ent.append(new_ent)
            if dates[n]:
                date_string = (dates[n],'DATE')
                ent.append(date_string)
            vb = fact_check.get_verb(pos_s[n])
            res_time = time.time()
            # print ent
            resources, ent_size, date_labels = fact_check.resource_extractor_updated(ent)
            # print resources
            # sys.exit(0)
            # relation_verb, matched_date = fact_check.target_predicate_processor(resources,vb, date_labels)
            # relation_ent, rel_count = fact_check.relation_extractor_updated(resources)
            relation_ent, rel_count = fact_check.relation_extractor_updated1(resources)
            relations = fact_check.relation_processor(relation_ent)
            precision, recall = precision_recall(n,relations)
            print "Precision: "+str(precision), "Recall: "+str(recall)
            execution_time = time.time() - res_time
            print "Execution Time: "+str(round(execution_time,2))
            print "================================================="
            # sys.exit(0)
            # validator_verbpredicate(relation_verb, matched_date)
            # print("--- %s rel seconds ---" % (time.time() - res_time))
            # print vb
            # print "here================="                  
            
            # validator_entitymap(relation_ent,vb)
            # tt = time.time() - new_time
            # print n+1, tt
            # if i>0:
            #     if time_stat[n] > tt:
            #         time_stat[n] = tt
            # else:
            #     time_stat.append(tt)

            # print("--- %s seconds ---" % (time.time() - new_time))
            # print "=============================================="
        # print("--- %s query seconds ---" % (time.time() - query_time))
        # print "================================================"
        # print time_stat
                
with open('sample.txt','r') as f:
    sentence_list = []
    sentences = f.readlines()
    for i,sentence in enumerate(sentences,start=1):
        if i%20 != 0:
            sentence_list.append(sentence)
            if i == len(sentences):
                fact_checker(sentence_list)
        else:
            fact_checker(sentence_list)
            sentence_list = []
            sentence_list.append(sentence)