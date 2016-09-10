import sparql
import csv
# e1 = select distinct ?c where{?x rdfs:label "Beckham"@en . ?x rdf:type/rdfs:subClassOf* ?c . }
# SELECT ?type ?superType WHERE 
# { 
#   # give me ?type of the resource
#   <http://dbpedia.org/resource/Thierry_Henry> rdf:type ?type .

#   # give me ?superTypes of ?type
#   OPTIONAL {
#    ?type rdfs:subClassOf ?superType .
#   }
# }
labels =['"Thierry Henry"@en','"Arsenal F.C."@en']
entities = {} 
for i,label in enumerate(labels):
	q = ('select distinct ?c where{?x rdfs:label'+ label +' . ?x rdf:type/rdfs:subClassOf* ?c . }')
	result = sparql.query('http://dbpedia.org/sparql', q)
	# print result	
	# str('entity'+i) = []
	my_list = []
	for row in result:
	# 	# print row
		values = sparql.unpack_row(row)
		my_list.append(values[0])
	# 	print values
	entities[i]= my_list
	# print entities	
	# print "==========="

# relation=[]
with open('mydata_rev_new.csv','wb') as f:
	writer = csv.writer(f)
	for i,item1 in enumerate(entities[1]):
		print i	
		for j,item2 in enumerate(entities[0]):
			q1=('SELECT ?r WHERE { ?x1 rdfs:label <'+str(item1) + '> . ?x2 rdfs:label <' + item2 +'> . ?x1 ?r ?x2}')
			# print q1
			try:
				result1 = sparql.query('http://dbpedia.org/sparql', q1)
				for row1 in result1:
					values1 = sparql.unpack_row(row1)
					# print values1
					if values1:
						print j
						print([str(item1),str(values1[0]),str(item2)])
						writer.writerow([str(item1),str(values1[0]),str(item2)])	
					# relation.append(values1[0])
			except:
				pass

# with open('mydata_1.csv','wb') as f:
# 	writer = csv.writer(f)
# 	for i,item1 in enumerate(entities[0]):
# 		print i,label	
# 		q1=('SELECT ?r WHERE { <'+str(item1) + '> ?r <' + label +'> }')
# 		# print q1
# 		try:
# 			result1 = sparql.query('http://dbpedia.org/sparql', q1)
# 			for row1 in result1:
# 				values1 = sparql.unpack_row(row1)
# 				# print values1
# 				if values1:
# 					print j
# 					print([str(item1),str(values1[0]),str(item2)])
# 					writer.writerow([str(item1),str(values1[0]),str(item2)])	
# 				# relation.append(values1[0])
# 		except:
# 			pass