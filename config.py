KGMiner_data = 'KGMiner/KGMiner_data'
aux_verb = ['was', 'is', 'become', 'to', 'of', 'in', 'the', 'for', 'where', 'etc']
unwanted_predicates = [u'thumbnail', u'person function', u'c',u'b',u's',u'n',u'v',u'mw', u'Caption', u'collapsible', u'd', u'q', u'signature',\
                       u'signature alt', u'species', u'voy', u'wikt', u'Guests', u'align', u'image', u'image caption',\
                       u'image size', u'logo', u'logo size']

rule_predicates = ['birth_name', 'birth_place','commons' ,'display','foundation_place','founded_by', 'founders',\
                   'key_person', 'key_people', 'known_for', 'long_name', 'name','occupation','owner', 'owning_company',\
                   'publisher','relatives', 'relative','short_name', 'subsid',  'trading_name']

rank_threshold = 0.5
kgminer_predicate_threshold = 0.4
evidence_threshold = 0
rule_threshold = 0.15

sparql_dbpedia_local = 'http://10.218.108.227:8890/sparql'
sparql_dbpedia_on = 'http://10.218.108.227:8890/sparql'
sparql_dbpedia = 'http://10.218.108.227:8890/sparql'
# sparql_dbpedia_local = 'http://dbpedia.org/sparql'
# sparql_dbpedia_on = 'http://dbpedia.org/sparql'
# sparql_dbpedia = 'http://dbpedia.org/sparql'
sparql_wikidata = 'https://query.wikidata.org/sparql'
