import fact_check
from nltk import word_tokenize
import sys
import time
import operator, json
import collections, csv
import pprint, os
from StanfordOpenIEPython.main import stanford_ie

aux_verb = ['was', 'is', 'become']
precision_recall_stats = collections.OrderedDict()


def precision_recall_ent_match(n,relations):
    ex_ent_all = []
    expected_ents = expected_outputs_entities[str(n)]
    for ke,ve in expected_ents.iteritems():
        ex_ent_all.extend(ve)
    retrieved_ents = relations['node'].keys()
    true_pos = [e_ent for e_ent in ex_ent_all if e_ent in retrieved_ents]
    return true_pos, retrieved_ents, ex_ent_all


def precision_recall_relations1(n,relations):
    subgraph = relations.get('edge')
    retrived_rels = []
    for s_key,s_val in subgraph.iteritems():
        for rels in s_val:
            retrived_rel = [s_key]
            retrived_rel.extend(rels['join'])
            retrived_rels.append(retrived_rel)
    ex_rels = []
    ex_dict = expected_outputs_relations[str(n)]
    for r_key,r_val in ex_dict.iteritems():
        r_val.append(r_key)
        ex_rels.append(r_val)
    true_pos = []
    for ret_rel in retrived_rels:
        for ex_rel in ex_rels:
            if set(ret_rel) == set(ex_rel):
                true_pos.append(ret_rel)
    return true_pos,retrived_rels,ex_rels


def precision_recall(true_pos,true_false_pos,ex_rels):
    true_pos_len = float(len(true_pos))
    true_false_pos_len = float(len(true_false_pos))
    print "Retrieved: " + str(true_false_pos)
    print "Expected: " + str(ex_rels)
    print "True Positive: " + str(true_pos)
    precision = true_pos_len / true_false_pos_len
    recall = true_pos_len / float(len(ex_rels))
    return round(precision, 2), round(recall, 2)


def precision_recall_entities(n, raw_resources):
    global test_count
    expected_entities = expected_outputs_entities[str(n)]
    p_list=[]
    r_list=[]
    for res_key, res_val in expected_entities.iteritems():
        expected_ent = res_val
        # print res_val
        retrieved_ent = raw_resources.get(res_key)
        if retrieved_ent:
            correct_results = [ent for ent in expected_ent if ent in retrieved_ent]
            cr = float(len(correct_results))
            # print cr, len(ex_out), len(unique_rel)
            precision = cr / float(len(retrieved_ent))
            recall = cr / float(len(expected_ent))
            print res_key + " >>", "Precision: " + str(precision), "Recall: " + str(recall)
            p_list.append((precision,2))
            r_list.append(round(recall,2))
        else:
            p_list.append(0)
            r_list.append(0)
    return p_list,r_list


def fact_checker(sentence_lis, id_list):
    dates = fact_check.date_parser(sentence_lis)
    sentence_list = [word_tokenize(sent) for sent in sentence_lis]
    ne_s, pos_s, dep_s = fact_check.st_tagger(sentence_list)
    # print dep_s
    verb_entity = fact_check.verb_entity_matcher(dep_s)

    # print verb_entity
    triples = stanford_ie("sentences.txt", verbose=False)
    print triples
    # print verb_entity
    start_time = time.time()
    for i in range(0, 1):
        for n, ne in enumerate(ne_s):
            sent_id = id_list[n]
            print sent_id, sentence_lis[n],'\n'
            ent = fact_check.get_nodes_updated(ne)
            # print ent
            new_loc = fact_check.location_update(ne)
            if new_loc:
                new_ent = (new_loc[0], 'LOCATION')
                ent.append(new_ent)
            if dates[n]:
                date_string = (dates[n][0], 'DATE')
                ent.append(date_string)
            vb = fact_check.get_verb(pos_s[n])
            print ent
            # sys.exit(0)
            res_time = time.time()
            resources, ent_size, date_labels, raw_resources = fact_check.resource_extractor_updated(ent)
            triple_dict = fact_check.svo_finder(ent,triples)
            print triple_dict
            relation_ent = fact_check.relation_extractor_triples(resources, triple_dict)
            # sys.exit(0)
            # relation_ent, rel_count = fact_check.relation_extractor_updated1(resources, verb_entity[n], triple_dict)
            print "Precision & Recall for Resource Extractor"
            print "-----------------------------------------"
            precision_ent, recall_ent = precision_recall_entities(sent_id, raw_resources)
            # print '\n'
            relations = fact_check.relation_processor(relation_ent)
            print "Relation Graph"
            print "--------------"
            # print relations
            # sys.exit(0)
            if relations:
                pprint.pprint(relations)
                # sys.exit(0)
                true_pos_rel, retrived_rels, ex_rels = precision_recall_relations1(sent_id, relations)
                true_pos_ent, retrieved_ents, ex_ent_all = precision_recall_ent_match(sent_id, relations)
                print '\n'
                print "Precision & Recall for Entities"
                print "--------------------------------"
                precision_ent_out, recall_ent_out = precision_recall(true_pos_ent, retrieved_ents, ex_ent_all)
                print "Entity Match: Precision: " + str(precision_ent_out), "Recall: " + str(recall_ent_out)
                print "------------------------------------------"
                print "Precision & Recall for Relations"
                print "--------------------------------"
                precision_rel, recall_rel = precision_recall(true_pos_rel, retrived_rels, ex_rels)

                print "Relations: Precision: " + str(precision_rel), "Recall: " + str(recall_rel)

                precision_recall_stats[sent_id] = [precision_rel,recall_rel,precision_ent_out,recall_ent_out]
            else:
                precision_recall_stats[sent_id] = [0,0,0,0]
            execution_time = time.time() - res_time
            print "Execution Time: " + str(round(execution_time, 2))
            print "================================================="
    ex_time = time.time() - start_time
    print "Total Execution Time: " + str(round(ex_time, 2))
    # print precision_recall_stats
    print "{:<8} {:<10} {:<10} {:<10} {:<10} ".format('S.N.', 'p_rel', 'r_rel', 'p_ent', 'r_ent')
    vals_sum=0
    for k1,v1 in precision_recall_stats.iteritems():
        vals = v1
        p_r,r_r,p_eo,r_eo = vals
        print "{:<8} {:<10} {:<10} {:<10} {:<10}".format(k1, p_r, r_r,p_eo, r_eo)
        if k1 == 1:
            vals1 = vals
        else:
            vals_sum = map(operator.add,vals1,vals)
            # print vals,vals1,vals_avg
            vals1 = vals_sum
    num_sent = len(sentence_list)
    if vals_sum>0:
        vals_avg = [round((x/num_sent),2) for x in vals_sum]
        print "average",vals_avg


with open('entity_annotations.json') as json_data:
    expected_outputs_entities = json.load(json_data)


with open('relation_annotations.json') as json_data:
    expected_outputs_relations = json.load(json_data)


with open('sentences1.csv') as f:
    reader = csv.DictReader(f)
    sentences_list = []
    id_list = []
    try:
        os.remove('sentences.txt')
    except:
        pass
    with open('sentences.txt','a') as text:
        for i,row in enumerate(reader):
            sentence = row['sentence']
            text.write(sentence+'\n')
            sentences_list.append(row['sentence'])
            id_list.append(row['id'])
    fact_checker(sentences_list,id_list)
        # if i % 20 != 0:
        #     sentence_list.append(sentence)
        #     if i == len(sentences):
        #         fact_checker(sentence_list)
        # else:
        #     fact_checker(sentence_list)
        #     sentence_list = []
        #     sentence_list.append(sentence)
