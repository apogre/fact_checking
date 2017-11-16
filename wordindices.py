import csv
import pickle
import numpy as np

data_set = '../'

entity_set = []
relation_set = []
word_set = []

with open(data_set+'all_data.tsv') as tsv:
    reader = csv.reader(tsv, delimiter='\t')
    for row in reader:
        entity_set.extend([row[0], row[2]])
        relation_set.append(row[1])
        row_0 = row[0].split('_')
        row_2 = row[2].split('_')
        word_set.extend(row_0)
        word_set.extend(row_2)
    word_set_full = word_set
    word_set = list(set(word_set))
    entity_set_full = entity_set
    entity_set = list(set(entity_set))
    relation_set_full = relation_set
    relation_set = list(set(relation_set))

relation_count_dict = {i:relation_set_full.count(i) for i in set(relation_set_full)}
print relation_count_dict

entity_count_dict = {i:entity_set_full.count(i) for i in set(entity_set_full)}
word_count_dict = {i:word_set_full.count(i) for i in set(word_set_full)}


with open('entity_count.csv', 'wb') as f:
    writer = csv.writer(f)
    for row in entity_count_dict.iteritems():
        writer.writerow(row)

with open('word_count.csv', 'wb') as f:
    writer = csv.writer(f)
    for row in word_count_dict.iteritems():
        writer.writerow(row)

with open(data_set+'entities.txt', 'w') as txtwriter:
    for item in entity_set:
        txtwriter.write(item+'\n')

with open(data_set+'relations.txt', 'w') as txtwriter:
    for item in relation_set:
        txtwriter.write(item+'\n')

word_dict = {k: v for v, k in enumerate(word_set)}
word_indices = []

for i, row in enumerate(entity_set):
    row_0 = row.split('_')
    index_0 = []
    for word in row_0:
        index_0.append(word_dict[word])
    word_indices.append(index_0)

word_index = dict()

np_entity_words = np.array([np.array(ent) for ent in word_indices])
word_index['word_indices'] = np_entity_words
word_index['num_words'] = len(word_set)
pickle.dump(word_index, open(data_set+'wordIndices.p','wb'))