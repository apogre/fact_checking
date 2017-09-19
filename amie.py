from kb_query import positive_relations, distance_three_query, negative_relations
from lpmln import amie_tsv, amie_tsv_unique, amie_negative_tsv
import sys
import time

def get_training_data(predicate):
    # entity_pairs = positive_relations(predicate)
    entity_pairs = negative_relations(predicate)
    return entity_pairs


if __name__ == '__main__':
    # distance_three, unique_predicates = [], []
    # entity_pairs = get_training_data('founders')
    # # amie_negative_tsv(entity_pairs,'company_founder')
    # # print entity_names
    # entity_pairs = sum(entity_pairs, [])
    #
    # data = set([entity.split('/')[-1] for entity in entity_pairs])
    # data = list(data)
    # print len(data)
    # for i, ent in enumerate(data):
    #     start = time.time()
    #     end = time.time()
    #     print 'Count:' + str(i)
    #     distance_three, unique_predicates = distance_three_query('dbpedia', ent, distance_three, unique_predicates)
    #     amie_tsv(distance_three, 'company_founder')
    #     print end-start
    amie_tsv_unique('company_founder')
