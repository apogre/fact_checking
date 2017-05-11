from gensim.models import Word2Vec
import sys

def init():
    global model_wv
    if sys.argv[1:][0]=='1':
    	print "Loading Word2Vec"
    	model_wv = Word2Vec.load("/home/apradhan/en_1000_no_stem/en.model")
    global new_ambi_query
    new_ambi_query = 0
    global data_source
    # data_source = 'ug_data/all_'
    # data_source = 'main_data/'
