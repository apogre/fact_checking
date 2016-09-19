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

subprocess.call(['echo "President lives in White House." | syntaxnet/demo.sh > output.txt'],shell=True)

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
NNP_list = {}
for i,sublist in enumerate(lists):
	# print sublist
	if sublist[4]=='NNP':
		word = sublist[1]
		NNP_list[i] = word
	elif sublist[7]=='ROOT':
		predicate = sublist[1]

print NNP_list
print predicate

flag = 0
for k,v in NNP_list.iteritems():
	if k != 0 or flag==0:
		print k

labels =['"David Beckham"@en','"Victoria Beckham"@en']
entities = {} 
for i,label in enumerate(labels):
	q = ('select distinct ?x where{?x rdfs:label'+ label +' }')
	result = sparql.query('http://dbpedia.org/sparql', q)
	types = {}
	for row in result:
		values = sparql.unpack_row(row)
		if not 'Category:' in values[0]:
			print values[0]
			my_list = []
			q1=('SELECT distinct ?type ?superType WHERE  { <'+str(values[0]) + '> rdf:type ?type . optional { ?type rdfs:subClassOf ?superType}}')
			result1 = sparql.query('http://dbpedia.org/sparql', q1)
			for row1 in result1:
				values1 = sparql.unpack_row(row1)
				my_list.append(values1)
			types[values[0]]= my_list
	entities[i] = types	
print "==========="
# print entities

# relation=[]
# with open('mydata_type.csv','wb') as f:
	# writer = csv.writer(f)
	# for i,item1 in enumerate(entities[1]):
		# print i	
		# for j,item2 in enumerate(entities[0]):
			# q1=('SELECT ?type ?superType WHERE  { <'+str(item1) + '> rdf:type ?type . optional { ?type rdfs:subClassOf ?superType}')
# 			# print q1
# 			try:
# 				result1 = sparql.query('http://dbpedia.org/sparql', q1)
# 				for row1 in result1:
# 					values1 = sparql.unpack_row(row1)
# 					# print values1
# 					if values1:
# 						print j
# 						print([str(item1),str(values1[0]),str(item2)])
# 						writer.writerow([str(item1),str(values1[0]),str(item2)])	
# 					# relation.append(values1[0])
# 			except:
# 				pass

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