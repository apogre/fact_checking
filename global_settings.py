from gensim.models import Word2Vec
import sys

def init():
    global model_wv
    global model_wv_g
    if sys.argv[1:][0] == '1':
        print "Loading Word2Vec DBpedia"
        model_wv = Word2Vec.load("/home/apradhan/en_1000_no_stem/en.model")
    if sys.argv[1:][0] == '2':
        print "Loading Word2Vec"
        model_wv_g = Word2Vec.load_word2vec_format("/home/apradhan/Google_Vectors/GoogleNews-vectors-negative300.bin",binary=True)
    global new_ambi_query
    new_ambi_query = 0
    global data_source
    global nodes_id
    global edge_id
    # data_source = 'ug_data/all_'
    data_source = 'president_spouse'
    # data_source = 'dataset/state_capital/'
    # data_source = 'dataset/country_capital/'
