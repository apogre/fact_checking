KGMiner_data = 'KGMiner/KGMiner_data'
aux_verb = ['was', 'is', 'become', 'to', 'of', 'in', 'the', 'for', 'where', 'etc']
unwanted_predicates = [u'thumbnail', u'person function', u'c',u'b',u's',u'n',u'v',u'mw', u'Caption', u'collapsible', u'd', u'q', u'signature',\
                       u'signature alt', u'species', u'voy', u'wikt', u'Guests', u'align', u'image', u'image caption',\
                       u'image size', u'logo', u'logo size',u'22-rdf-syntax-ns#type','soundRecording','rdf-schema#seeAlso',u'point',\
                       'endowment','rdf-schema#label','owl#differentFrom','description','filename','name','givenName', u'viafId',\
                       u'utcOffset','title','termPeriod',u'homepage','nick','rdf-schema#subClassOf','owl#unionOf']


rank_threshold = 0.5
kgminer_predicate_threshold = 0.4
evidence_threshold = 0
rule_threshold = 0.15
top_k = str('all_1000')
predicate = 'founders'
#
sparql_dbpedia_api = 'http://dbpedia.org/sparql'
sparql_dbpedia = 'http://localhost:8890/sparql'