import fact_check
from nltk import word_tokenize
import sys
import time
import operator

test_count = 0

aux_verb = ['was', 'is', 'become']

expected_outputs_entities = {2: {
    u'Barack Obama': [u'Barack_Obama', u'Presidency_of_Barack_Obama', u'Illinois_Senate_career_of_Barack_Obama',
                      u'Early_life_and_career_of_Barack_Obama', u'United_States_Senate_career_of_Barack_Obama'],
    u'Hawaii': [u'Hawaii']}, 0: {u'Alfredo James Pacino': [u'Al_Pacino'],
                                 u'New York City': [u'New_York', u'New_York_City']},
    11: {u'Scarlett Johansson': [u'Scarlett_Johansson'],
         u'New York City': [u'New_York', u'New_York_City']},
    10: {u'Michael Douglas': [u'Michael_Douglas'], u'Kirk Douglas': [u'Kirk_Douglas'],
         u'New Jersey': [u'New_Brunswick,_New_Jersey']},
    9: {u'Michael Cera': [u'Michael_Cera'], u'Brampton': [u'Brampton'],
        u'Ontario': [u'Ontario'], u'Canada': [u'Canada']},
    8: {u'Johansson': [u'Scarlett_Johansson'], u'Ryan Reynolds': [u'Ryan_Reynolds'],
        u'British Columbia': [u'British_Columbia'], u'Canada': [u'Canada']},
    7: {u'Johansson': [u'Scarlett_Johansson'], u'Ryan Reynolds': [u'Ryan_Reynolds']},
    6: {u'Jack Black': [u'Jack_Black'],
        u'Santa Monica, California': [u'Santa_Monica,_California'],
        u'Santa Monica': [u'Santa_Monica,_California'],
        u'California': [u'Santa_Monica,_California', u'California']},
    5: {u'Danny DeVito': [u'Danny_DeVito'],
        u'New Jersey': [u'Neptune_Township,_New_Jersey', u'New_Jersey']},
    4: {u'Megyn Kelly': [u'Megyn_Kelly'], u'Syracuse, New York': [u'Syracuse,_New_York'],
        u'Syracuse': [u'Syracuse,_New_York'], u'New York': [u'Syracuse,_New_York']},
    3: {u'Robert De Niro': [u'Robert_De_Niro'], u'Stella Adler': [u'Stella_Adler'],
        u'New York City': [u'New_York_City', u'New_York']}, 1: {
        u'Barack Obama': [u'Barack_Obama', u'Presidency_of_Barack_Obama', u'Illinois_Senate_career_of_Barack_Obama',
                          u'Early_life_and_career_of_Barack_Obama', u'United_States_Senate_career_of_Barack_Obama'],
        u'Michelle Obama': [u'Michelle_Obama']}}

expected_outputs_relations = {
    0: [[u'birthPlace', u'New_York', u'Al_Pacino'], [u'birthDate', u'April 25, 1940', u'Al_Pacino']],
    2: [[u'birthPlace', u'Hawaii', u'Barack_Obama']],
    1: [[u'spouse', u'Barack_Obama', u'Michelle_Obama']],
    3: [[u'birthPlace', u'New_York_City', u'Robert_De_Niro'], [u'birthDate', u'August 17, 1943', u'Robert_De_Niro']],
    5: [[u'birthPlace', u'Neptune_Township,_New_Jersey', u'Danny_DeVito'], [u'birthDate', u'1944', u'Danny_DeVito']],
    6: [[u'birthPlace', u'Santa_Monica,_California', u'Jack_Black'], [u'birthDate', u'August 28, 1969', u'Jack_Black']],
    8: [[u'spouse', u'Scarlett_Johansson', u'Ryan_Reynolds']],
    7: [[u'spouse', u'Scarlett_Johansson', u'Ryan_Reynolds']],
    4: [[u'birthPlace', u'Syracuse,_New_York', u'Megyn_Kelly'], [u'birthDate', u'1970', u'Megyn_Kelly']],
    9: [[u'birthPlace', u'Brampton', u'Michael_Cera'], [u'birthPlace', u'Ontario', u'Michael_Cera'],
        [u'birthDate', u'June 7, 1988', u'Michael_Cera']],
    10: [[u'birthPlace', u'New_Brunswick,_New_Jersey', u'Michael_Douglas'], [u'birthDate', u'1944', u'Michael_Douglas'],
         [u'parent', u'Kirk_Douglas', u'Michael_Douglas'], [u'child', u'Michael_Douglas', u'Kirk_Douglas']],
    11: [[u'birthPlace', u'New_York_City', u'Scarlett_Johansson'],
         [u'birthDate', u'November 22, 1984', u'Scarlett_Johansson']]}


def validator_entitymap(relation, vb, true_flag=0):
    if relation:
        for rel in relation.get('relation', []):
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
            for ext in relation.get('ext', []):
                # print ext
                for v in vb:
                    if v[0] not in aux_verb:
                        if len(ext[1]) > 2:
                            for e in ext[1][2]:
                                # print v[0].lower(),e 
                                if v[0].lower() in e.split():
                                    print ext
                                    print "True by one loop"
                                    pass


def validator_verbpredicate(relation, dates):
    if relation:
        print relation
        print dates, "The statement is True"
    else:
        print "The statement is False with direct relation"
    print "=============================================="

def precision_recall_entity_match(ent_out_ret,ent_ex_all):
    tp_set = []
    ent_ret_k = []
    tp_set_new = 0
    # print ent_out_ret
    # print ent_ex_all
    for e,ent_ret in enumerate(ent_out_ret):
        for en in ent_ret:
            # print en
            if isinstance(en, basestring):
                ent_ret_k.append(en)
                if en in ent_ex_all:
                    tp_set.append(en)
        tp_set = list(set(tp_set))
        if e == 0:
            tp_set_old = len(tp_set)
        else:
            tp_set_new = len(tp_set)
        # print tp_set_new,tp_set_old
        if tp_set_old != tp_set_new:
            print "---------------------------------------"
            print "Top " + str(e + 1) + " Precision & Recall:"
            ent_ret_k = list(set(ent_ret_k))
            print "True Positive: "+str(tp_set)
            print "Retrieved Entites: "+str(ent_ret_k)
            print "Expected Output: "+str(ent_ex_all)
            print "Precision: "+str(float(len(tp_set))/float(len(ent_ret_k))),"Recall: "+str(float(len(tp_set))/float(len(ent_ex_all)))
            if e > 0:
                tp_set_old = tp_set_new
        else:
            pass


def precision_recall_relations(n, relations):
    # print relations
    global test_count
    ex_ent_all = []
    unique_rel_raw = [list(x) for x in set(tuple(x) for x in relations)]
    unique_rel = sorted(unique_rel_raw, key=operator.itemgetter(3),reverse=True)
    ent_outputs_ret = [corr[1:4] for corr in unique_rel]
    # print ent_outputs_ret
    expected_ent_outs = expected_outputs_entities[n+test_count]
    for ke,ve in expected_ent_outs.iteritems():
        ex_ent_all.extend(ve)
    # print ex_ent_all
    precision_recall_entity_match(ent_outputs_ret, ex_ent_all)
    print "-----------------------------------------"
    print "Retrieved Relations: " + str(unique_rel)
    ex_out = expected_outputs_relations[n+test_count]
    print "Expected Outputs: " + str(ex_out)
    correct_results = [rel for rel in unique_rel if rel[0:3] in ex_out]
    # if len(ent_outputs)>1:
    #     end_outputs = [item for sublist in ent_outputs for item in sublist]
    # print ent_outputs
    # print "Matched Outputs: " + str(correct_results)
    cr = float(len(correct_results))
    # print cr, len(ex_out), len(unique_rel)
    unique_rel_len = float(len(unique_rel))
    if unique_rel_len < 1:
        unique_rel_len = 1
    precision = cr / unique_rel_len
    recall = cr / float(len(ex_out))
    return precision, recall


def precision_recall_entities(n, raw_resources):
    global test_count
    expected_entities = expected_outputs_entities[n + test_count]
    # print expected_entities
    # print raw_resources
    for res_key, res_val in expected_entities.iteritems():
        expected_ent = res_val
        # print res_key
        retrieved_ent = raw_resources[res_key]
        correct_results = [ent for ent in expected_ent if ent in retrieved_ent]
        cr = float(len(correct_results))
        # print cr, len(ex_out), len(unique_rel)
        precision = cr / float(len(retrieved_ent))
        recall = cr / float(len(expected_ent))
        print res_key + " >>", "Precision: " + str(precision), "Recall: " + str(recall)


def fact_checker(sentence_lis):
    # print sentence_lis
    dates = fact_check.date_parser(sentence_lis)
    sentence_list = [word_tokenize(sent) for sent in sentence_lis]
    ne_s, pos_s, dep_s = fact_check.st_tagger(sentence_list)
    start_time = time.time()
    for i in range(0, 1):
        for n, ne in enumerate(ne_s):
            print n, sentence_lis[n],'\n'
            ent = fact_check.get_nodes_updated(ne)
            new_loc = fact_check.location_update(ne)
            if new_loc:
                new_ent = (new_loc[0], 'LOCATION')
                ent.append(new_ent)
            if dates[n]:
                date_string = (dates[n], 'DATE')
                ent.append(date_string)
            vb = fact_check.get_verb(pos_s[n])
            print ent
            res_time = time.time()
            resources, ent_size, date_labels, raw_resources = fact_check.resource_extractor_updated(ent)
            # print raw_resources
            # print resources
            # sys.exit(0)
            # print ent_size
            # sys.exit(0)
            # relation_verb, matched_date = fact_check.target_predicate_processor(resources,vb, date_labels)
            # relation_ent, rel_count = fact_check.relation_extractor_updated(resources)
            relation_ent, rel_count = fact_check.relation_extractor_updated1(resources)
            # print relation_ent
            print "Precision & Recall for Resource Extractor"
            print "-----------------------------------------"
            precision_recall_entities(n, raw_resources)
            # print '\n'
            relations = fact_check.relation_processor(relation_ent)
            precision, recall = precision_recall_relations(n, relations)
            print "------------------------------------------"
            print "Precision & Recall for Relations"
            print "--------------------------------"
            print "Relations: Precision: " + str(round(precision, 2)), "Recall: " + str(round(recall, 2))
            execution_time = time.time() - res_time
            print "Execution Time: " + str(round(execution_time, 2))
            print "================================================="
    ex_time = time.time() - start_time
    print "Total Execution Time: " + str(round(ex_time, 2))


with open('sample.txt', 'r') as f:
    sentence_list = []
    sentences = f.readlines()
    for i, sentence in enumerate(sentences, start=1):
        if i % 20 != 0:
            sentence_list.append(sentence)
            if i == len(sentences):
                fact_checker(sentence_list)
        else:
            fact_checker(sentence_list)
            sentence_list = []
            sentence_list.append(sentence)
