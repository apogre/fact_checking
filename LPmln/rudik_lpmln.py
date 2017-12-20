import re
set_up = "controlled"
predicate = "keyPerson"
polarity = "_pos"
fname = "company_keyPerson/"+ set_up + "/rudik_rules_all1000/" + predicate + polarity + "_all.txt"
with open("company_keyPerson/" + set_up + "/rudik_rules_all1000/" + predicate + polarity + "_lpmln.txt", "w") as text_file:
	with open(fname) as f:
		content = f.readlines()
		for con in content:
			con = re.sub(r'http://dbpedia.org/ontology/', "",con)
			con = re.sub(r'subject',"A",con)
			con = re.sub("object","B",con)
			con = re.sub("v0","C",con)
			con = re.sub("v1","D",con)
			con = re.sub("&",",",con)
			con = con.replace('!=(C,D)', 'C!=D')
			con = con.replace("!=(D,C)", "C!=D")
			con = con.replace(">(C,D)", "C>D")
			con = con.replace("<(C,D)", "C<D")
			if "null" not in con:
				if polarity == "_neg":
					text_file.write("not_"+predicate+"(A,B) :- "+str(con))
				else:
					text_file.write(predicate+"(A,B) :- "+str(con))