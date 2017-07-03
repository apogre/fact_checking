from nltk.tag import StanfordNERTagger,StanfordPOSTagger
# from nltk.parse.stanford import StanfordDependencyParser
import os, sys
from itertools import groupby,product
from StanfordOpenIEPython.main import stanford_ie
from datetime import datetime
from config import aux_verb
# stanford_parser_jar = str(os.environ['HOME'])+'/stanford-parser-full-2015-12-09/stanford-parser.jar'
stanford_model_jar = str(os.environ['STANFORDTOOLSDIR'])+'/stanford-parser-full-2015-12-09/stanford-parser-3.6.0-models.jar'

st_ner = StanfordNERTagger('english.all.3class.distsim.crf.ser.gz')
# st_pos = StanfordPOSTagger('english-bidirectional-distsim.tagger')
# parser = StanfordDependencyParser(path_to_jar=stanford_parser_jar, path_to_models_jar=stanford_model_jar)


def svo_finder(ent, triples):
    triple_dict = {}
    entity_set = [x[0] for x in ent]
    for triple in triples:
        if triple[0] in entity_set and triple[2] in entity_set:
            if triple[1] not in triple_dict.keys():
                triple_dict[triple[1]] = [[triple[0], triple[2]]]
            else:
                triple_list = [item for sublist in triple_dict[triple[1]] for item in sublist]
                if triple[0] in triple_list and triple[2] in triple_list:
                    pass
                else:
                    triple_dict[triple[1]].append([triple[0], triple[2]])
    return triple_dict


def sentence_tagger(sentence_list):
    named_entities = st_ner.tag_sents(sentence_list)
    # POS_tagger = st_pos.tag_sents(sentence_list)
    # dependency_tagger = [[list(parse.triples()) for parse in dep_parse] for dep_parse in parser.parse_sents(sentence_list)]
    return named_entities


def get_nodes(tagged_words):
    ent = []
    for tag, chunk in groupby(tagged_words, lambda x:x[1]):
        # print tag
        if tag != "O":
            tuple1 =(" ".join(w for w, t in chunk),tag)
            ent.append(tuple1)
    return ent


def triples_extractor(sentence, named_entities, new_triple_flag=0):
    try:
        os.remove('sentences.txt')
    except:
        pass
    with open('sentences.txt', 'a') as text:
        text.write(sentence)
    triples_raw = stanford_ie("sentences.txt", verbose=False)
    triples = [[trip.lstrip() for trip in triple] for triple in triples_raw]
    triple_dict = svo_finder(named_entities, triples)
    return triple_dict
