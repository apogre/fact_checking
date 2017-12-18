import re

con = "associatedMusicalArtist(B,C) , !=(C,D) , recordLabel(D,A),0.000000"

con.replace('!=(C,D)', 'C!=D')

print con