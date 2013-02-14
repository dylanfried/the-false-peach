##### Line 

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

ofile = open("data/out_test.txt","w")
bs = BeautifulSoup(open("data/ham.xml").read())

bs = bs.find("body")
act = "0"
scene = "0"
lineno = "0"


same_line = False
last_line = "-1"
last_speaker = ""
for acts in bs.findAll("div", recursive = False):
   for scenes in acts.findAll("div", recursive = False):
      for s in scenes.findAll(["head","stage","sp"], recursive = False):
         if s.name == "sp":
            #scene_length = len(s.findAll(["ab","l"]))
            #scene_index = 0
            
            g = s.find("speaker")
            sp = g.string
            sp = sp.encode('utf-8')
            sp = re.sub(" ","_",sp)
               
            for l in s.findAll(["l","ab","stage"]):
               if l.name == "stage":
                  ofile.write(act+" "+scene+" "+last_line+" -1 "+last_speaker+" -1 -1 -1 -1 -1 NEWLINE NEWLINE\n")
                  t = l.string.encode("utf-8","ignore")
                  wwhhaatt = l['type']
              
                  t = re.sub("\s+"," ",t)
              
                  t = re.sub("\."," .",t)
                  t = re.sub("\;"," ;",t)
                  t = re.sub("\:"," :",t)
                  t = re.sub("\,"," ,",t)
                  t = re.sub("\?"," ?",t)
                  t = re.sub("\!"," !",t)
              
                  ofile.write(act+" "+scene+" "+lineno+" -1 "+"Stage -1 -1 -1 -1 -1 ( (\n")
              
                  for w in t.split(" "):
              
                     ofile.write(act+" "+scene+" "+lineno+" -1 "+"Stage -1 -1 -1 -1 -1 "+wwhhaatt+" "+w+"\n")
              
                  ofile.write(act+" "+scene+" "+lineno+" -1 "+"Stage -1 -1 -1 -1 -1 ) )\n")
                  ofile.write(act+" "+scene+" "+lineno+" -1 "+"Stage -1 -1 -1 -1 -1 NEWLINE NEWLINE\n")
                  last_speaker = "Stage"
                  continue
      
               lineno = l["n"].strip()
               lineno = lineno.encode('utf-8','ignore')
               
               if lineno == last_line:
                  same_line = True
               #if the sameline flag is set then we add the previous lineno
               if not same_line:
                  tmp = int(last_line)
                  tmp += 1
                  tmp = str(tmp)
                  tmp = tmp.encode('utf-8','ignore')
                  #if the sameline flag is set then we add the previous lineno
                  if last_speaker != sp:
                     if last_speaker != "Stage":
                        ofile.write(act+" "+scene+" "+last_line+" -1 "+last_speaker+" -1 -1 -1 -1 -1 NEWLINE NEWLINE\n")
                     ofile.write(act+" "+scene+" "+tmp+" -1 "+sp+" -1 -1 -1 -1 -1 SPEAKER "+sp.upper()+"\n")
                     ofile.write(act+" "+scene+" "+tmp+" -1 "+sp+" -1 -1 -1 -1 -1 NEWLINE NEWLINE\n")
               else:
                  if last_speaker == sp:
                     pass
                     #ofile.write(act+" "+scene+" "+lineno+" -1 "+sp+" -1 -1 -1 -1 -1 NEWLINE NEWLINE\n")
                  else:
                     if last_speaker != "Stage":
                        ofile.write(act+" "+scene+" "+last_line+" -1 "+last_speaker+" -1 -1 -1 -1 -1 NEWLINE NEWLINE\n")
                     ofile.write(act+" "+scene+" "+lineno+" -1 "+sp+" -1 -1 -1 -1 -1 SPEAKER "+sp.upper()+"\n")
                     ofile.write(act+" "+scene+" "+lineno+" -1 "+sp+" -1 -1 -1 -1 -1 NEWLINE NEWLINE\n")
                  same_line = False
         
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
               last_line = lineno
               #print "scene Index", scene_index
               #print "scene Length", scene_length
              #if l.name != "ab":
              #   ofile.write(act+" "+scene+" "+lineno+" -1 "+sp+" -1 -1 -1 -1 -1 NEWLINE NEWLINE\n")

               #last_line = lineno
               last_speaker = sp
      
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
            last_speaker = "Stage"
      
      
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
