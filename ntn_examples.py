import csv
import numpy as np
import pickle
import pandas as pd
from kb_query import get_all_entity, distance_one_query, get_all_person
from lpmln import amie_tsv
import sys
import random

rule_predicates = ["nationality",
"profession",
"deathPlace",
"birthPlace",
"location",
"institution",
"deathCause",
"religion",
"parent",
"child",
"ethnicity",
"spouse"]


train_set_full = []
for rel in rule_predicates:
    all_entity = get_all_entity(rel)
    train_set_full.append(all_entity)
print len(train_set_full)

sys.exit(0)

# sys.exit(0)
word_set = []
entity_set = []
relation_set = []
filtered_evidence = []


data_set = '/media/apradhan/DATA/company_founder/'


print "========"
# for i, entities in enumerate(all_entity):
#     print 'count:' + str(i)
#     distance_three = []
#     for entity in entities:
#         print entity
#         if isinstance(entity, basestring):
#             if '/' in entity:
#                 entity = entity.split('/')[-1]
#                 if entity not in entity_set:
#                     distance_three = distance_one_query('dbpedia', entity, distance_three)
#     if distance_three:
#         for evidence in distance_three:
#             if evidence[1] in rule_predicates:
#                 filtered_evidence.append(evidence)
#         entity_set.append(entity)

for i, entities in enumerate(all_entity):
    print 'count:' + str(i)
    url = entities[0].split('/')[-1]
    entity_set.append(url)
    entities.pop(0)
    for j, entity in enumerate(entities):
        if entity:
            if isinstance(entity, basestring):
                if '/' in entity:
                    entity = entity.split('/')[-1]
                filtered_evidence.append([url, rule_predicates[j], entity])
                entity_set.append(entity)
print filtered_evidence
print len(filtered_evidence)


# amie_tsv(filtered_evidence, data_source='company_founder')

# print len(filtered_evidence)
# with open(data_set+'founders_unique_ntn.tsv') as tsv:
#     reader = csv.reader(tsv, delimiter='\t')
#     for row in reader:
#         row[0] = row[0].replace(' ', '_')
#         row[2] = row[2].replace(' ', '_')
#         entity_set.extend([row[0], row[2]])
#         relation_set.append(row[1])
#         row_0 = row[0].split('_')
#         row_2 = row[2].split('_')
#         word_set.extend(row_0)
#         word_set.extend(row_2)
#     word_set_full = word_set
#     word_set = list(set(word_set))
#     entity_set = list(set(entity_set))
#     relation_set = list(set(relation_set))
#
# # print entity_set
# # print word_set
# #
# word_dict = {k: v for v, k in enumerate(word_set)}
#
# word_count_dict = {i:word_set_full.count(i) for i in set(word_set_full)}
#
# word_indices = []
#
# for i, row in enumerate(entity_set):
#     row_0 = row.split('_')
#     index_0 = []
#     for word in row_0:
#         if word_count_dict[word] > 5:
#             index_0.append(word_dict[word])
#         else:
#             entity_set.pop(i)
#     if index_0:
#         word_indices.append(index_0)
#
#
# word_count_set = []
#
# with open(data_set+'founders_unique_ntn.tsv') as tsv:
#     reader = csv.reader(tsv, delimiter='\t')
#     for row in reader:
#         row_0 = row[0].replace(' ', '_')
#         row_2 = row[2].replace(' ', '_')
#         if row_0 in entity_set and row_2 in entity_set:
#             word_count_set.append(row)
#
# amie_tsv(word_count_set, data_source='company_founder')
#
# with open(data_set+'founders_ntn_filter.tsv') as tsv:
#     reader = csv.reader(tsv, delimiter='\t')
#     for row in reader:
#         entity_set.extend([row[0], row[2]])
#         relation_set.append(row[1])
#         row_0 = row[0].split('_')
#         row_2 = row[2].split('_')
#         word_set.extend(row_0)
#         word_set.extend(row_2)
#     word_set_full = word_set
#     word_set = list(set(word_set))
#     entity_set_full = entity_set
#     entity_set = list(set(entity_set))
#     relation_set_full = relation_set
#     relation_set = list(set(relation_set))
#
# word_count_dict = {i:word_set_full.count(i) for i in set(word_set_full)}
# entity_count_dict = {i:entity_set_full.count(i) for i in set(entity_set_full)}
# relation_count_dict = {i:relation_set_full.count(i) for i in set(relation_set_full)}
#
# print relation_count_dict
#
# with open(data_set+'entity.txt', 'w') as txtwriter:
#     for item in entity_set:
#         txtwriter.write(item+'\n')
#
# with open(data_set+'relation.txt', 'w') as txtwriter:
#     for item in relation_set:
#         txtwriter.write(item+'\n')
#
# word_dict = {k: v for v, k in enumerate(word_set)}
# word_indices = []
#
# for i, row in enumerate(entity_set):
#     row_0 = row.split('_')
#     index_0 = []
#     for word in row_0:
#         index_0.append(word_dict[word])
#     word_indices.append(index_0)
#
# word_index = dict()
#
# np_entity_words = np.array([np.array(ent) for ent in word_indices])
# word_index['word_indices'] = np_entity_words
# word_index['num_words'] = len(word_set)
# pickle.dump(word_index, open(data_set+'fc_wordIndices.p','wb'))
#
# df = pd.read_csv(data_set+'founders_ntn_filter.tsv', sep='/t')
# df['split'] = np.random.randn(df.shape[0], 1)
#
#
# msk = np.random.rand(len(df)) <= 0.8
#
#
# train = df[msk]
# test = df[~msk]
#
# del train['split']
# del test['split']
#
# train.to_csv(data_set+'train_1.txt', sep='\t', header=False, index=False)
# test.to_csv(data_set+'test.txt', sep='\t', header=False, index=False)

# df = pd.read_csv(data_set+'train_1.txt', sep='/t')
# df['split'] = np.random.randn(df.shape[0], 1)
#
# msk = np.random.rand(len(df)) <= 0.8
# #
# train = df[msk]
# dev = df[~msk]
#
# del train['split']
# del dev['split']
#
# train.to_csv(data_set+'train.txt', sep='\t', header=False, index=False)
#
# dev.to_csv(data_set+'dev.txt', sep='\t', header=False, index=False)

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
# rel_data = ['train', 'test', 'dev']
# for data in rel_data:
#     relation_counter(data)


# rel_dict = dict()
#
# with open(data_set+'test.txt') as tsv:
#     reader = csv.reader(tsv, delimiter='\t')
#     for row in reader:
#         print row
#         if row[1] not in rel_dict.keys():
#             rel_dict[row[1]] = {'e1':[row[0]], 'e2':[row[2]]}
#         else:
#             rel_dict[row[1]]['e1'].append(row[0])
#             rel_dict[row[1]]['e2'].append(row[2])
#
#
# suffle_rel = []
# for rel in rel_dict.keys():
#     e1 = rel_dict[rel]['e1']
#     e2 = rel_dict[rel]['e2']
#     e3 = random.sample(e2, len(e2))
#     for i, ent in enumerate(e1):
#         if e3[i] != e2[i]:
#             suffle_rel.append([ent, rel, e3[i], -1])
#             suffle_rel.append([ent, rel, e2[i], 1])
#
# amie_tsv(suffle_rel, data_source='company_founder')

