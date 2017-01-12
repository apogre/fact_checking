import fact_check
from nltk import word_tokenize
import sys
import time

aux_verb = ['was','is','become']

expected_outputs_entities = {2:{u'Barack Obama': [u'Barack_Obama', u'Presidency_of_Barack_Obama', u'Illinois_Senate_career_of_Barack_Obama', u'Early_life_and_career_of_Barack_Obama', u'United_States_Senate_career_of_Barack_Obama'], u'Hawaii': [u'Hawaii']},0:{u'Alfredo James Pacino': [u'Al_Pacino'], u'New York City': [u'New_York', u'New_York_City']},11:{u'Scarlett Johansson':[u'Scarlett_Johansson'],u'New York City': [u'New_York', u'New_York_City']},10:{u'Michael Douglas':[u'Michael_Douglas'],u'Kirk Douglas':[u'Kirk_Douglas'],u'New Jersey':[u'New_Brunswick,_New_Jersey']},9:{u'Michael Cera':[u'Michael_Cera'],u'Brampton':[u'Brampton'],u'Ontario':[u'Ontario'],u'Canada':[u'Canada']},8:{u'Johansson':[u'Scarlett_Johansson'],u'Ryan Reynolds':[u'Ryan_Reynolds'],u'British Columbia':[u'British_Columbia'],u'Canada':[u'Canada']},7:{u'Johansson':[u'Scarlett_Johansson'],u'Ryan Reynolds':[u'Ryan_Reynolds']},6:{u'Jack Black':[u'Jack Black'],u'Santa Monica, California':[u'Santa_Monica,_California'],u'Santa Monica':[u'Santa_Monica,_California'],u'California':[u'Santa_Monica,_California',u'California']},5:{u'Danny DeVito':[u'Danny_DeVito'],u'New Jersey':[u'Neptune_Township,_New_Jersey',u'New_Jersey']},4:{u'Megyn Kelly':[u'Megyn_Kelly'],u'Syracuse, New York':[u'Syracuse,_New_York'],u'Syracuse':[ u'Syracuse,_New_York'],u'New York':[ u'Syracuse,_New_York']},3:{u'Robert De Niro':[u'Robert_De_Niro'],u'Stella Adler':[u'Stella_Adler'],u'New York City':[u'New_York_City',u'New_York']},1:{u'Barack Obama': [u'Barack_Obama', u'Presidency_of_Barack_Obama', u'Illinois_Senate_career_of_Barack_Obama', u'Early_life_and_career_of_Barack_Obama', u'United_States_Senate_career_of_Barack_Obama'],u'Michelle Obama':[u'Michelle_Obama']}}

expected_outputs_relations = {0:[[u'birthPlace', u'New_York', u'Al_Pacino']], 2:[[u'birthPlace', u'Hawaii', u'Barack_Obama']],
                              1:[[u'spouse', u'Barack_Obama', u'Michelle_Obama']], 3:[[u'birthPlace', u'New_York_City', u'Robert_De_Niro']],
                              5:[[u'birthPlace', u'Neptune_Township,_New_Jersey', u'Danny_DeVito']], 6:[[u'birthPlace', u'Santa_Monica,_California', u'Jack_Black']],
                              11:[[u'birthPlace', u'New_York_City', u'Scarlett_Johansson']], 9:[[u'birthPlace', u'Brampton', u'Michael_Cera'],[u'birthPlace', u'Ontario', u'Michael_Cera']],
                              8:[[u'spouse', u'Scarlett_Johansson', u'Ryan_Reynolds']], 7:[[u'spouse', u'Scarlett_Johansson', u'Ryan_Reynolds']],
                              4:[[u'birthPlace', u'Syracuse,_New_York', u'Megyn_Kelly']], 10:[[u'birthPlace', u'New_Brunswick,_New_Jersey', u'Michael_Douglas'],[u'child', u'Michael_Douglas', u'Kirk_Douglas']]}

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

def precision_recall_relations(n, relations):
    unique_rel = [list(x) for x in set(tuple(x) for x in relations)]
    print "Retrieved Relations: " +str(unique_rel)
    ex_out = expected_outputs_relations[n]
    print "Expected Outputs: "+str(ex_out)
    correct_results = [rel for rel in unique_rel if rel in ex_out]
    cr = float(len(correct_results))
    # print cr, len(ex_out), len(unique_rel)
    precision = cr/float(len(unique_rel))
    recall = cr/float(len(ex_out))
    return precision, recall

def precision_recall_entities(n, raw_resources):
    expected_entities = expected_outputs_entities[n]
    # print expected_entities
    # print raw_resources
    for res_key,res_val in expected_entities.iteritems():
        expected_ent = res_val
        # print res_key
        retrieved_ent = raw_resources[res_key]
        correct_results = [ent for ent in expected_ent if ent in retrieved_ent]
        cr = float(len(correct_results))
        # print cr, len(ex_out), len(unique_rel)
        precision = cr/float(len(retrieved_ent))
        recall = cr/float(len(expected_ent))
        print res_key+" >>", "Precision: "+str(precision), "Recall: "+str(recall)

def fact_checker(sentence_lis):
    # print sentence_lis
    dates = fact_check.date_parser(sentence_lis)
    sentence_list = [word_tokenize(sent) for sent in sentence_lis]
    ne_s,pos_s,dep_s = fact_check.st_tagger(sentence_list)
    start_time = time.time()
    for i in range(0,1):
        for n,ne in enumerate(ne_s):
            print n, sentence_lis[n]
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
            resources, ent_size, date_labels, raw_resources = fact_check.resource_extractor_updated(ent)
            # print raw_resources
            # print ent_size
            # sys.exit(0)
            # relation_verb, matched_date = fact_check.target_predicate_processor(resources,vb, date_labels)
            # relation_ent, rel_count = fact_check.relation_extractor_updated(resources)
            relation_ent, rel_count = fact_check.relation_extractor_updated1(resources)
            relations = fact_check.relation_processor(relation_ent)
            precision, recall = precision_recall_relations(n, relations)
            print "Precision & Recall"
            print "------------------"
            precision_recall_entities(n,raw_resources)
            print "Relations: Precision: "+str(round(precision,2)), "Recall: "+str(round(recall,2))
            execution_time = time.time() - res_time
            print "Execution Time: "+str(round(execution_time,2))
            print "================================================="
    ex_time = time.time() - start_time
    print "Total Execution Time: "+str(round(ex_time,2))

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