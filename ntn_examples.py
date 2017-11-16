import csv
import numpy as np
import pickle
import pandas as pd
from kb_query import get_all_entity, distance_one_query, get_all_person
from lpmln import amie_tsv
import sys
import random
#
# rule_predicates = ["gender","nationality",
# "profession",
# "deathPlace",
# "birthPlace",
# "residence",
# "almaMater",
# "deathCause",
# "religion",
# "parent",
# "child",
# "ethnicity",
# "spouse"]

# gender
# nationality
# profession
# place_of_death
# place_of_birth
# location
# institution
# cause_of_death
# religion
# parents
# children
# ethnicity
# spouse

#
# related_pred = ["parent", "child", "spouse"]
# related_person = []
# train_data = []
#
# with open('person.txt') as f:
#     old_person = f.readlines()
# old_person = [x.strip() for x in old_person]
#
# with open('related_person.txt') as f:
#     old_person_1 = f.readlines()
# old_person_1 = [x.strip() for x in old_person_1]
#
# with open('related_person_1.txt') as f:
#     old_person_2 = f.readlines()
# old_person_2 = [x.strip() for x in old_person_2]
#
# with open('related_person_2.txt') as f:
#     old_person_3 = f.readlines()
# old_person_3 = [x.strip() for x in old_person_3]
#
# with open('related_person_3.txt') as f:
#     person = f.readlines()
# person = [x.strip() for x in person]
# for i, per in enumerate(person):
#     if i < 200:
#         train_data.extend(get_all_person(per))
# print len(train_data)
#
#
# # sys.exit(0)
word_set = []
entity_set = []
relation_set = []
filtered_evidence = []


#
#
# print "========"
# # for i, entities in enumerate(all_entity):
# #     print 'count:' + str(i)
# #     distance_three = []
# #     for entity in entities:
# #         print entity
# #         if isinstance(entity, basestring):
# #             if '/' in entity:
# #                 entity = entity.split('/')[-1]
# #                 if entity not in entity_set:
# #                     distance_three = distance_one_query('dbpedia', entity, distance_three)
# #     if distance_three:
# #         for evidence in distance_three:
# #             if evidence[1] in rule_predicates:
# #                 filtered_evidence.append(evidence)
# #         entity_set.append(entity)
#
# for i, entities in enumerate(train_data):
#     url = entities[0].split('/')[-1]
#     entity_set.append(url)
#     entities.pop(0)
#     for j, entity in enumerate(entities):
#         if entity:
#             if isinstance(entity, basestring):
#                 if '/' in entity:
#                     entity = entity.split('/')[-1]
#                 filtered_evidence.append([url, rule_predicates[j], entity])
#                 if rule_predicates[j] in related_pred:
#                     if entity not in related_person and entity not in person and entity not in old_person and entity\
#                             not in old_person_1 and entity not in old_person_2 and entity not in old_person_3:
#                         related_person.append(entity)
#                 entity_set.append(entity)
# # print filtered_evidence
# # print len(filtered_evidence)
# print related_person
#
#
#
#
# amie_tsv(filtered_evidence, data_source='person')
#
# with open('related_person_4.txt', 'wb') as personwriter:
#     for per in related_person:
#         try:
#             personwriter.write(per + '\n')
#         except:
#             print per

# print len(filtered_evidence)

# word_count_set = []


data

# df = pd.read_csv(data_set+'all_person.txt', sep='/t')
# df['split'] = np.random.randn(df.shape[0], 1)
#
#
# msk = np.random.rand(len(df)) <= 0.7
#
#
# train = df[msk]
# test = df[~msk]
#
# del train['split']
# del test['split']
#
# train.to_csv(data_set+'train_1_comb.txt', sep='\t', header=False, index=False)
# test.to_csv(data_set+'test_comb.txt', sep='\t', header=False, index=False)

# df = pd.read_csv(data_set+'train_1_comb.txt', sep='/t')
# df['split'] = np.random.randn(df.shape[0], 1)
#
# msk = np.random.rand(len(df)) <= 0.7
# #
# train = df[msk]
# dev = df[~msk]
#
# del train['split']
# del dev['split']
#
# train.to_csv(data_set+'train_comb.txt', sep='\t', header=False, index=False)
#
# dev.to_csv(data_set+'dev_comb.txt', sep='\t', header=False, index=False)

# def relation_counter(data):
#     relation_set = []
#     with open(data_set+data+'.txt') as tsv:
#         reader = csv.reader(tsv, delimiter='\t')
#         for row in reader:
#             relation_set.append(row[1])
#         relation_set_full = relation_set
#
#     relation_count_dict = {i:relation_set_full.count(i) for i in set(relation_set_full)}
#     print relation_count_dict
#
# rel_data = ['train_comb', 'test_comb', 'dev_comb']
# for data in rel_data:
#     relation_counter(data)


rel_dict = dict()

with open(data_set+'test_comb.txt') as tsv:
    reader = csv.reader(tsv, delimiter='\t')
    for row in reader:
        print row
        if row[1] not in rel_dict.keys():
            rel_dict[row[1]] = {'e1':[row[0]], 'e2':[row[2]]}
        else:
            rel_dict[row[1]]['e1'].append(row[0])
            rel_dict[row[1]]['e2'].append(row[2])


suffle_rel = []
for rel in rel_dict.keys():
    e1 = rel_dict[rel]['e1']
    e2 = rel_dict[rel]['e2']
    e3 = random.sample(e2, len(e2))
    for i, ent in enumerate(e1):
        if e3[i] != e2[i]:
            suffle_rel.append([ent, rel, e3[i], -1])
            suffle_rel.append([ent, rel, e2[i], 1])

amie_tsv(suffle_rel, data_source='person')

