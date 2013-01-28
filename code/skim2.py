import re
import os
import copy
from bs4 import BeautifulSoup
#from hyphenate import hyphenate_word
import csv
import getopt
import sys
from nltk.corpus import wordnet as wn

temo = open("data/emo.txt").readlines()
temo = [e.strip() for e in temo]
temo = [e.split(",") for e in temo]
emo = {}
for e in temo:
   emo[e[0]] = [float(e[1]),float(e[2]),float(e[3]),float(e[4])]

tfreq = open("data/freq.txt").readlines()
tfreq = [t.strip() for t in tfreq]
tfreq = [t.split(" ") for t in tfreq]
freq = {}
for t in tfreq:
   t[1] = re.sub("(.*)\W+$","\\1",t[1])
   t[1] = t[1].lower()
   freq[t[1]] = float(t[0])

ofile = open("data/ham_unspooled2.txt","w")
bs = BeautifulSoup(open("data/ham.xml").read())

bs = bs.find("body")
act = "0"
scene = "0"
lineno = "0"

for s in bs.findAll(["head","stage","sp"]):

   if s.name == "sp":

      g = s.find("speaker")
      sp = g.string
      sp = sp.encode('utf-8')
      sp = re.sub(" ","_",sp)

      ofile.write(act+" "+scene+" "+lineno+" -1 "+sp+" -1 -1 -1 -1 -1 NEWLINE NEWLINE\n")
      ofile.write(act+" "+scene+" "+lineno+" -1 "+sp+" -1 -1 -1 -1 -1 SPEAKER "+sp.upper()+"\n")
      ofile.write(act+" "+scene+" "+lineno+" -1 "+sp+" -1 -1 -1 -1 -1 NEWLINE NEWLINE\n")
    
      for l in s.findAll(["l","ab"]):

         lineno = l["n"].strip()
         lineno = lineno.encode('utf-8','ignore')
   
         for w in l.findAll("w"):

            wordno = w["ord"].strip()
            wordno = wordno.encode('utf-8','ignore')
  
            ww = w.string.encode('utf-8','ignore')
            ww = re.sub("\s+"," ",ww)
            ww = ww.strip()

            tst = ww
            tst = tst.lower()
            tst = re.sub("(.*)\W+$","\\1",tst)

            if tst in emo:

               affs = " ".join([str(e) for e in emo[tst]])
               fffs = str(freq[tst])

            elif not tst:

               affs = "-1 -1 -1 -1"
               fffs = "-1"

            else:

               affs = "0 0 0 0"
               fffs = "0"

            if ww:

               ofile.write(act+" "+scene+" "+lineno+" "+wordno+" "+sp+" "+\
                        affs+" "+fffs+" "+w["pos"].encode("utf-8")+" "+ww+"\n")

#         ofile.write(act+" "+scene+" "+lineno+" -1 "+sp+" NEWLINE NEWLINE\n")

   elif s.name == "stage":

      l = s.string.encode("utf-8","ignore")

      wwhhaatt = s['type']

      l = re.sub("\s+"," ",l)

      l = re.sub("\."," .",l)
      l = re.sub("\;"," ;",l)
      l = re.sub("\:"," :",l)
      l = re.sub("\,"," ,",l)
      l = re.sub("\?"," ?",l)
      l = re.sub("\!"," !",l)

      ofile.write(act+" "+scene+" "+lineno+" -1 "+"Stage -1 -1 -1 -1 -1 ( (\n")
  
      for w in l.split(" "):

         ofile.write(act+" "+scene+" "+lineno+" -1 "+"Stage -1 -1 -1 -1 -1 "+wwhhaatt+" "+w+"\n")

      ofile.write(act+" "+scene+" "+lineno+" -1 "+"Stage -1 -1 -1 -1 -1 ) )\n")
      ofile.write(act+" "+scene+" "+lineno+" -1 "+"Stage -1 -1 -1 -1 -1 NEWLINE NEWLINE\n")

   elif s.name == "head":

      l = s.string.encode("utf-8","ignore")

      l = re.sub("\s+"," ",l)

      l = re.sub("\."," .",l)
      l = re.sub("\;"," ;",l)
      l = re.sub("\:"," :",l)
      l = re.sub("\,"," ,",l)
      l = re.sub("\?"," ?",l)
      l = re.sub("\!"," !",l)

      if "Act" in l: 

         act = re.sub(".*Act\s*([0-9]).*","\\1",l)
         scene = "1"
         lineno = "1"

      if "Scene" in l: scene = re.sub(".*Scene\s*([0-9]).*","\\1",l)

      for w in l.split(" "):

         ofile.write(act+" "+scene+" "+lineno+" -1 "+"Stage -1 -1 -1 -1 -1 Title "+w+"\n")

      ofile.write(act+" "+scene+" "+lineno+" -1 "+"Stage -1 -1 -1 -1 -1 NEWLINE NEWLINE\n")


ofile.close() 
