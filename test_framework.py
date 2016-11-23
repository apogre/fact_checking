from nltk.tag import StanfordNERTagger,StanfordPOSTagger
import fact_check

st_ner = StanfordNERTagger('english.all.3class.distsim.crf.ser.gz')
st_pos = StanfordPOSTagger('english-bidirectional-distsim.tagger')
aux_verb = ['was','is']
true_flag = 0

with open('sample.txt','r') as f:
    sentences = f.readlines()
    for i,sentence in enumerate(sentences):
        new_labels = []
        print sentence
        sent = sentence.replace('.','').split()
        ne = st_ner.tag(sent)
        # print ne
        pos = st_pos.tag(sent)
        # print pos
        ent =  fact_check.get_nodes_updated(ne)
        # print ent
        vb = fact_check.get_verb(pos)
        # print vb
        # updated_labels = []
        # for en in ent:
        #     if 'University' in en[0] or 'College' in en[0] or 'School' in en[0]:
        #         label1 = str(en[0])+' alumni'
        #         tup2 = (label1,en[1])
        #         # print tup2
        #         updated_labels.append(tup2)
        # ent.extend(updated_labels)
        # try:
        #     date = date_parser(doc)
        #     tup1 = (date,'DATE')
        #     ent.append(tup1)
        #     date_flag = 1
        # except:
        #     pass
        print "====Entities===="
        # print ent
        for e in ent:
            if e[1] == 'LOCATION' and ',' in e[0]:
                loc_label = e[0].split(',')
                for loc in loc_label:
                    ent.append((loc,'LOCATION'))
        print ent
        print vb
        resources, ent_size = fact_check.resource_extractor_updated(ent)
        print "====Resources Count===="
        # print resources
        print ent_size
        relation, rel_count = fact_check.relation_extractor(resources)
        print "no. of iterations: " + str(rel_count)
        print relation
        if relation:
            for v in vb:
                # print v
                # print relation[2]
                if v[0] not in aux_verb:
                    for rel in relation[2]:
                        if v[0] in rel[0].split():
                            print "The statement is True"
                            true_flag = 1
        if true_flag == 0:
            print "The statement is False"

            # print date_flag
            # now_current = datetime.datetime.now()
            # relation_extractor(resources)
            # total_time = datetime.datetime.now() - now_current
            # print total_time
            # if date_flag == 1:
            #     date_extractor(date,resources)
            #     date_flag = 0
            # objects.extend(ent)
        # except:
        #     pass