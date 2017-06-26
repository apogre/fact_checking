from gensim.models import Word2Vec
import sys

data_source = 'president_spouse'
KGMiner_data = 'KGMiner/KGMiner_data/'
aux_verb = ['was', 'is', 'become','to','of', 'in', 'the']
rank_threshold = 0.5
kgminer_predicate_threshold = 0.4

# sparql_dbpedia = 'http://localhost:8890/sparql'
sparql_dbpedia_on = 'https://dbpedia.org/sparql'
sparql_dbpedia = 'https://dbpedia.org/sparql'
sparql_wikidata = 'https://query.wikidata.org/sparql'


if sys.argv[1:][0] == '2':
    print "Loading Word2Vec"
    model_wv_g = Word2Vec.load_word2vec_format("/home/apradhan/Google_Vectors/GoogleNews-vectors-negative300.bin", \
                                               binary=True)
else:
    model_wv_g = None

if sys.argv[1:][0] == '1':
    print "Loading Word2Vec DBpedia"
    model_wv = Word2Vec.load("/home/apradhan/en_1000_no_stem/en.model")
else:
    model_wv = None

# data_source = 'ug_data/all_'
# data_source = 'dataset/state_capital/'
# data_source = 'dataset/country_capital/'
