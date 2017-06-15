import csv
import global_settings
import os
import subprocess
import sys
import re


def evidence_writer(relation_ent, sent_id):
    data_source = global_settings.data_source
    entity_mapping = dict()
    maps_set = []
    count = 1
    predicate_list = global_settings.predicate_set.get(global_settings.data_source,[])
    final_list = []
    with open('lpmln_tests/'+data_source +'/groundings/'+sent_id+global_settings.data_source+'_full.db', 'wb') as csvfile:
        datawriter = csv.writer(csvfile, quoting=csv.QUOTE_NONE, delimiter=' ', skipinitialspace=True)
        for rel in relation_ent:
            if rel[2] not in entity_mapping.keys():
                if rel[2][:2] not in maps_set:
                    entity_mapping[rel[2]] = rel[2][:2]
                    maps_set.append(rel[2][:2])
                else:
                    entity_mapping[rel[2]] = str(rel[2][:2])+str(count)
                    maps_set.append(str(rel[2][:2])+str(count))
                    count = count + 1
            if rel[3] not in entity_mapping.keys():
                if rel[3][:2] not in maps_set:
                    entity_mapping[rel[3]] = rel[3][:2]
                    maps_set.append(rel[3][:2])
                else:
                    entity_mapping[rel[3]] = str(rel[3][:2])+str(count)
                    maps_set.append(str(rel[3][:2])+str(count))
                    count += 1
            rel_set = [r.replace(' ', '_') for r in rel if isinstance(r, basestring)]
            item_set = [rel_set[1]+'('+rel_set[2]+',' + rel_set[3]+').']
            print item_set
            datawriter.writerow(item_set)
    with open('lpmln_tests/'+data_source +'/'+ data_source+'_initials.db', 'wb') as csvfile:
        datawriter = csv.writer(csvfile, quoting=csv.QUOTE_NONE, delimiter=' ', skipinitialspace=True)
        for rel in relation_ent:
            rel_set = [r.replace(' ', '_') for r in rel if isinstance(r, basestring)]
            item_set = [rel_set[1]+'('+entity_mapping.get(rel[2],'').lower()+',' + entity_mapping.get(rel[3],'').lower()+').']
            datawriter.writerow(item_set)
    with open('lpmln_tests/'+data_source +'/'+ data_source+'_filter.db', 'wb') as csvfile:
        datawriter = csv.writer(csvfile, quoting=csv.QUOTE_NONE, delimiter=' ', skipinitialspace=True)
        for rel in relation_ent:
            rel_set = [r.replace(' ', '_') for r in rel if isinstance(r, basestring)]
            if rel_set[1] in predicate_list:
                item_set = [rel_set[1]+'('+entity_mapping.get(rel[2],'').lower()+',' + entity_mapping.get(rel[3],'').lower()+').']
                if item_set[0] not in final_list:
                    final_list.append(item_set[0])
                    datawriter.writerow(item_set)


def inference():
    print "Executing Classification"
    data_source = 'lpmln_tests/'+global_settings.data_source+'/'+global_settings.data_source
    # os.chdir('lpmln_tests/'+data_source)
    cmd = "lpmln2asp -i {0}.lpmln -q married -all -e {0}_filter.db -r {0}_result.txt ".format(data_source)
    print cmd
    subprocess.call(cmd, shell=True)
    text = open(data_source+'_result.txt', 'r')
    f = text.read()
    text.close()
    probs = re.findall("(\w+\(\w+\,\s\w+\)\s\d+\.\d+)",f)
    print probs
    return probs