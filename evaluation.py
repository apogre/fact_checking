import json, sys
import os
import global_settings

# data_source = global_settings.data_source
data_source = 'main_data/'
# data_source = 'ug_final/'
# data_source = 'ug_data/all_'


def precision_recall_entities(n, resources):
    # global test_count
    # print n, resources
    # print expected_outputs_entities
    expected_entities = expected_outputs_entities.get(str(n),{})
    p_list=[]
    r_list=[]
    entity_matched = {}
    # print expected_entities
    # sys.exit(0)
    for res_key, res_val in expected_entities.iteritems():
        expected_ent = res_val
        # print str(res_key)+" Expected: "+ str(res_val)
        retrieved_ent = resources.get(res_key)
        # print "retrieved "+str(retrieved_ent)
        if retrieved_ent:
            correct_results = []
            for ents in retrieved_ent:
                # print ents, expected_ent
                retrieved_entity = ents[0].split('/')[-1]
                if retrieved_entity==expected_ent[0]:
                    correct_results=[retrieved_entity]
                    correct_resource = ents
            # correct_results = [ent for ent in expected_ent if ent in retrieved_ent]
            if correct_results:
                cr = float(len(correct_results))
                # print cr
                entity_matched[res_key]=[correct_resource]
                # print cr, len(ex_out), len(unique_rel)
                precision = cr / float(len(retrieved_ent))
                recall = cr / float(len(expected_ent))
                print res_key + " >>", "Precision: " + str(precision), "Recall: " + str(recall)
                p_list.append(round(precision,3))
                r_list.append(round(recall,2))
        else:
            p_list.append(0)
            r_list.append(0)
    return p_list, r_list, entity_matched


def precision_recall_ent_match(n,relations):
    ex_ent_all = []
    expected_ents = expected_outputs_entities.get(str(n),{})
    # print expected_ents
    for ke,ve in expected_ents.iteritems():
        ex_ent_all.extend(ve)
    retrieved_ents = relations['node'].keys()
    true_pos = [e_ent for e_ent in ex_ent_all if e_ent in retrieved_ents]
    return true_pos, retrieved_ents, ex_ent_all


def precision_recall_relations(n, relations):
    subgraph = relations.get('edge')
    retrived_rels = []
    true_pos = []
    ex_rels = []
    for s_key,s_val in subgraph.iteritems():
        for rels in s_val:
            retrived_rel = [s_key]
            retrived_rel.extend(rels['join'])
            retrived_rels.append(retrived_rel)
    # print retrived_rels
    ex_dict = expected_outputs_relations.get(str(n),{})
    # print ex_dict
    if ex_dict:
        for r_key,r_val in ex_dict.iteritems():
            r_val.append(r_key)
            ex_rels.append(r_val)

        for ret_rel in retrived_rels:
            for ex_rel in ex_rels:
                try:
                    if set(ret_rel) == set(ex_rel):
                        true_pos.append(ret_rel)
                except:
                    pass
    return true_pos,retrived_rels,ex_rels


def precision_recall(true_pos,true_false_pos,ex_rels):
    true_pos_len = float(len(true_pos))
    true_false_pos_len = float(len(true_false_pos))
    print "Retrieved: " + str(true_false_pos)
    print "Expected: " + str(ex_rels)
    print "True Positive: " + str(true_pos)
    precision = true_pos_len / true_false_pos_len
    if ex_rels:
        recall = true_pos_len / float(len(ex_rels))
    else:
        recall = 0
    return round(precision, 2), round(recall, 2)

if os.path.isfile(data_source+'entity_annotations.json'):
    with open(data_source+'entity_annotations.json') as json_data:
        expected_outputs_entities = json.load(json_data)


if os.path.isfile(data_source+'relation_annotations.json'):
    with open(data_source+'relation_annotations.json') as json_data:
        expected_outputs_relations = json.load(json_data)

