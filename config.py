KGMiner_data = 'KGMiner/KGMiner_data'
aux_verb = ['was', 'is', 'become', 'to', 'of', 'in', 'the', 'for', 'where', 'etc']
unwanted_predicates = [u'thumbnail', u'person function', u'c',u'b',u's',u'n',u'v',u'mw', u'Caption', u'collapsible', u'd', u'q', u'signature',\
                       u'signature alt', u'species', u'voy', u'wikt', u'Guests', u'align', u'image', u'image caption',\
                       u'image size', u'logo', u'logo size']

# rule_predicates = ['birth_name','birth_year','commons', 'designer', 'display', 'employer', 'foundation_place','founded_by', 'founders',\
#                    'founding_year','key_person', 'parents', 'key_people', 'known_for', 'long_name', 'name','occupation','owner', 'owning_company'
#                    ,'parents','relatives', 'relative','short_name','spouse' 'subsid',  'trading_name']

# rule_predicates = ['activeYearsStartYear','activeYearsEndYear','birthYear','birthPlace','child','deathPlace','deathYear','parent','predecessor','partner','placeOfBurial','relation','relative','spouse','successor']
#spouse
# rule_predicates = ['birthPlace','child','deathPlace','spouse','parent','partner','placeOfBurial','restingPlace','relation','relative',]

rule_predicates = ['birthPlace','child','deathPlace','spouse','parent','partner','placeOfBurial','restingPlace','relation','relative',]

rank_threshold = 0.5
kgminer_predicate_threshold = 0.4
evidence_threshold = 0
rule_threshold = 0.15
top_k = str(5)
#
# sparql_dbpedia_local_v = 'http://10.218.105.56:8890/sparql'
# sparql_dbpedia_on_v = 'http://10.218.105.56:8890/sparql'
# sparql_dbpedia_v = 'http://10.218.105.56:8890/sparql'
sparql_dbpedia_local = 'http://dbpedia.org/sparql'
sparql_dbpedia_on = 'http://dbpedia.org/sparql'
sparql_dbpedia = 'http://dbpedia.org/sparql'
sparql_wikidata = 'https://query.wikidata.org/sparql'
