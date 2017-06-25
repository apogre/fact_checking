from gensim.models import KeyedVectors
import sys

data_source = 'president_spouse'
KGMiner_data = 'KGMiner/KGMiner_data/'
aux_verb = ['was', 'is', 'become']
rank_threshold = 0.5
kgminer_predicate_threshold = 0.5
# global model_wv
# global model_wv_g

if sys.argv[1:][0] == '2':
    print "Loading Word2Vec"
    model_wv_g = KeyedVectors.load_word2vec_format("/home/apradhan/Google_Vectors/GoogleNews-vectors-negative300.bin", \
                                               binary=True)
else:
    model_wv_g = None

if sys.argv[1:][0] == '1':
    print "Loading Word2Vec DBpedia"
    model_wv = Word2Vec.load("/home/apradhan/en_1000_no_stem/en.model")
else:
    model_wv = None

# global new_ambi_query
# global predicate_set
# new_ambi_query = 0
# global nodes_id
# global edge_id
# data_source = 'ug_data/all_'
# data_source = 'dataset/state_capital/'
# data_source = 'dataset/country_capital/'
