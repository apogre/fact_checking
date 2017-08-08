KGMiner_data = 'KGMiner/KGMiner_data'
aux_verb = ['was', 'is', 'become', 'to', 'of', 'in', 'the', 'for', 'where', 'etc']
unwanted_predicates = [u'thumbnail', u'person function', u'c',u'b',u's',u'n',u'v',u'mw', u'Caption', u'collapsible', u'd', u'q', u'signature',\
                       u'signature alt', u'species', u'voy', u'wikt', u'Guests', u'align', u'image', u'image caption',\
                       u'image size', u'logo', u'logo size']

rule_predicates = ['founders', 'name', 'subsid', 'key_people', 'known_for', 'birth_place', \
                   'foundation_place']

rank_threshold = 0.5
kgminer_predicate_threshold = 0.4
evidence_threshold = 0
rule_threshold = 0.15

sparql_dbpedia_local = 'http://localhost:8890/sparql'
sparql_dbpedia_on = 'http://localhost:8890/sparql'
sparql_dbpedia = 'http://localhost:8890/sparql'
sparql_wikidata = 'https://query.wikidata.org/sparql'
