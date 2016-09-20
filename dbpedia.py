import sparql
import csv
import subprocess
import csv
import os

# e1 = select distinct ?c where{?x rdfs:label "Beckham"@en . }
# SELECT ?type ?superType WHERE 
# { 
#   # give me ?type of the resource
#   <http://dbpedia.org/resource/Thierry_Henry> rdf:type ?type .

#   # give me ?superTypes of ?type
#   OPTIONAL {
#    ?type rdfs:subClassOf ?superType .
#   }
# }
os.chdir('../models/syntaxnet/')

# subprocess.call(['echo "David Beckham and Victoria Beckham are married." | syntaxnet/demo.sh > output.txt'],shell=True)

filename='output.txt'

def readata(filename):
    file=open(filename,'r')
    lines=file.readlines()
    lines=lines[:-1]
    data=csv.reader(lines,delimiter='\t')
#make a list of lists
    lol=list(data)
    return  lol
#find the verb which is ROOT of the sentence

lists=readata(filename)
mylabels = []
prev_type = ''
for i,sublist in enumerate(lists):
	# print sublist
	if sublist[4]=='NNP':
		if prev_type == 'NNP':
			word = word+' '+sublist[1]
		else:
			prev_type = sublist[4] 
			word = sublist[1]
	elif sublist[7]=='ROOT':
		predicate = sublist[1]
		prev_type=''
	else:
		prev_type=''
		# print word
		mylabels.append('"'+word+'"'+'@en')

labels =  set(mylabels)
labels = list(labels)
print "predicate=>"+predicate

entities = {} 
resources = {}

for i,label in enumerate(labels):
	resource_list = []
	print label
	print "==========="
	q = ('select distinct ?x where{?x rdfs:label'+ label +' }')
	result = sparql.query('http://dbpedia.org/sparql', q)
	types = {}
	for row in result:
		values = sparql.unpack_row(row)
		if not 'Category:' in values[0]:
			print values[0]
			resource_list.append(values[0])
			my_list = []
			q1=('SELECT distinct ?type ?superType WHERE  { <'+str(values[0]) + '> rdf:type ?type . optional { ?type rdfs:subClassOf ?superType}}')
			result1 = sparql.query('http://dbpedia.org/sparql', q1)
			for row1 in result1:
				values1 = sparql.unpack_row(row1)
				my_list.append(values1)
			types[values[0]]= my_list
	entities[i] = types
	resources[label] = resource_list	
print "==========="
# print entities
print resources

# relation=[]
# with open('mydata_type.csv','wb') as f:
# 	writer = csv.writer(f)
for item1 in resources[labels[0]]:
	for item2 in resources[labels[1]]:
		q1=('SELECT ?r WHERE  { <'+str(item1) + '> ?r <' +str(item2)+'>}')
		print q1
		try:
			result1 = sparql.query('http://dbpedia.org/sparql', q1)
			for row1 in result1:
				values1 = sparql.unpack_row(row1)
				# print values1
				if values1:
					print "relation========="
					print([str(item1),str(values1[0]),str(item2)])
					# writer.writerow([str(item1),str(values1[0]),str(item2)])	
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