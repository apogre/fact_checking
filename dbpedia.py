import sparql
# e1 = 
labels =['"Beckham"@en','"LA Galaxy"@en'] 
for label in labels:
	q = ('select distinct ?c where{?x rdfs:label'+ label +' . ?x rdf:type/rdfs:subClassOf* ?c . }')

	result = sparql.query('http://dbpedia.org/sparql', q)

	for row in result:
		# print row
		values = sparql.unpack_row(row)
		print values
	print "==========="