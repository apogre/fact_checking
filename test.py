import csv


data_set = '/media/apradhan/DATA/person/'

persons = {}

with open(data_set+'all_person.txt') as tsv:
    reader = csv.reader(tsv, delimiter='\t')
    for row in reader:
        print row
        if row[0] not in persons.keys():
            persons[row[0]] = 1
        else:
            persons[row[0]] += 1

with open('person_data.csv', 'wb') as f:
    writer = csv.writer(f)
    for row in persons.iteritems():
        writer.writerow(row)

^.*null.*\n