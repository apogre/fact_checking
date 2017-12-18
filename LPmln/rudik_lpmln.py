import re

fname = "company_founder/rudik_rules_1000/prop_founders_pos.txt"
with open("company_founder/rudik_rules_1000/founders_pos_lpmln.txt", "w") as text_file:
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
			con = con.replace("<(C,D)", "C>D")
			print con
			if "null" not in con:
				text_file.write("founders(A,B) :- "+str(con))