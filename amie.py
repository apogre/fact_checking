from kb_query import all_relations_query, distance_three_query
from lpmln import amie_tsv

def get_training_data(predicate):
    entity_pairs = all_relations_query(predicate)
    return entity_pairs


if __name__ == '__main__':
    amie_training = []
    distance_three, unique_predicates = [], []
    entity_pairs = get_training_data('founders')
    entity_pairs = sum(entity_pairs,[])

    data = set([entity.split('/')[-1] for entity in entity_pairs])
    data = list(data)
    for ent in data:
        distance_three, unique_predicates = distance_three_query('dbpedia', ent, distance_three,unique_predicates)
        amie_training.extend(distance_three)

    print distance_three[:10]
    amie_tsv(amie_training, 'company_founder')
