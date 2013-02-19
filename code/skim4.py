##### Makes a new brute.txt called out_test.txt, which can be checked and
##### renamed brute.txt.
import re
import os
import copy
from bs4 import BeautifulSoup
import csv
import getopt
import sys

# Setup a dictionary of emotional data. Each key is a word and the value is a 
# list of emotion values for each of the four emotions anger, fear joy sadness
# in that order.
temo = open("data/emo.txt").readlines()
temo = [e.strip() for e in temo]
temo = [e.split(",") for e in temo]
emo = {}
for e in temo:
   emo[e[0]] = [float(e[1]),float(e[2]),float(e[3]),float(e[4])]

# Setup a dictionary of frequency data. Keys = word, Values = # of occurences.
tfreq = open("data/freq.txt").readlines()
tfreq = [t.strip() for t in tfreq]
tfreq = [t.split(" ") for t in tfreq]
freq = {}
for t in tfreq:
   t[1] = re.sub("(.*)\W+$","\\1",t[1])
   t[1] = t[1].lower()
   freq[t[1]] = float(t[0])

# Specify IN/OUT files. 
ofile = open("data/out_test.txt","w")
bs = BeautifulSoup(open("data/ham.xml").read())

bs = bs.find("body")
act = "0"
scene = "0"
lineno = "0"
last_line = "-1"
last_speaker = ""
# Main loop for writing text to the out file. 
# Notes on ham.xml:
# - Acts and scenes are the outside div statements. Within each scene there are
# - "head", "stage", and "sp" for headers, stage directions and speeches. 
for acts in bs.findAll("div", recursive = False):
   for scenes in acts.findAll("div", recursive = False):
      for s in scenes.findAll(["head","stage","sp"], recursive = False):
         if s.name == "sp":
            scene_length = len(s.findAll("ab"))
            scene_index = 0
            
            g = s.find("speaker")
            sp = g.string
            sp = sp.encode('utf-8')
            sp = re.sub(" ","_",sp)
            # Within each speech we can have "l"or "ab" lines of
            # poetry or prose and "stage" in line stage directions. 
            for l in s.findAll(["l","ab","stage"]):
               scene_index += 1
               # If the line is a stage direction we force the opening and  closing
               # parens and add the stage directions.
               if l.name == "stage":
                  t = l.string.encode("utf-8","ignore")
                  wwhhaatt = l['type']
                  # Formatting substitutions.
                  t = re.sub("\s+"," ",t)
                  t = re.sub("\."," .",t)
                  t = re.sub("\;"," ;",t)
                  t = re.sub("\:"," :",t)
                  t = re.sub("\,"," ,",t)
                  t = re.sub("\?"," ?",t)
                  t = re.sub("\!"," !",t)
                  # Open parens
                  ofile.write(act+" "+scene+" "+lineno+" -1 "+"Stage -1 -1 -1 -1 -1 -1 ( (\n")
                  # Text of the stage direction
                  for w in t.split(" "):
              
                     ofile.write(act+" "+scene+" "+lineno+" -1 "+"Stage -1 -1 -1 -1 -1 -1 "+wwhhaatt+" "+w+"\n")
                  # Close parens and NEWLINE.
                  ofile.write(act+" "+scene+" "+lineno+" -1 "+"Stage -1 -1 -1 -1 -1 -1 ) )\n")
                  ofile.write(act+" "+scene+" "+lineno+" -1 "+"Stage -1 -1 -1 -1 -1 -1 NEWLINE NEWLINE\n")
                  continue
               # If l is not a "stage then we want treat it as a line of text.
               # Set the line number lineno from the "n" attribute in the line
               lineno = l["n"].strip()
               lineno = lineno.encode('utf-8','ignore')
               
               # If it is a new line but with the same speaker 
               # - we do not want to add a newline because it will be separated from the previous line 
               #   by the newline of the previous line.
               # If it is a new speaker regardless of if it is a new line.
               # - we add the new speaker and a newline.
               # If it is the same line but with  speaker
               # - we want a newline but no new character 
               if lineno != last_line:
                  tmp = int(last_line)
                  tmp += 1
                  tmp = str(tmp)
                  tmp = tmp.encode('utf-8','ignore')
                  if last_speaker != sp:
                     ofile.write(act+" "+scene+" "+tmp+" -1 "+sp+" -1 -1 -1 -1 -1 -1 SPEAKER "+sp.upper()+"\n")
                     ofile.write(act+" "+scene+" "+tmp+" -1 "+sp+" -1 -1 -1 -1 -1 -1 NEWLINE NEWLINE\n")
               else:
                  if last_speaker == sp:
                     ofile.write(act+" "+scene+" "+lineno+" -1 "+sp+" -1 -1 -1 -1 -1 -1 NEWLINE NEWLINE\n")
                  else:
                     ofile.write(act+" "+scene+" "+lineno+" -1 "+sp+" -1 -1 -1 -1 -1 -1 SPEAKER "+sp.upper()+"\n")
                     ofile.write(act+" "+scene+" "+lineno+" -1 "+sp+" -1 -1 -1 -1 -1 -1 NEWLINE NEWLINE\n")
               # Processing for each word in a line of text.
               for w in l.findAll("w"):
                  # Word number. 
                  wordno = w["ord"].strip()
                  wordno = wordno.encode('utf-8','ignore')
                  
                  # The word string. 
                  ww = w.string.encode('utf-8','ignore')
                  ww = re.sub("\s+"," ",ww)
                  ww = ww.strip()
                  
                  tst = ww
                  tst = tst.lower()
                  tst = re.sub("(.*)\W+$","\\1",tst)
                  
                  # If it is a word we add a string of the emotion values for 
                  # the word. Otherwise we add the string of "-1"'s or "0"'s
                  if tst in emo:
                     affs = " ".join([str(e) for e in emo[tst]])
                     fffs = str(freq[tst])
                  elif not tst:
                     affs = "-1 -1 -1 -1"
                     fffs = "-1"
                  else:
                     affs = "0 0 0 0"
                     fffs = "0"
                  # Write the new word to the out file. 
                  if ww: 
                     print act, scene, lineno
                     ofile.write(act+" "+scene+" "+lineno+" "+wordno+" "+sp+" "+\
                              affs+" "+fffs+" "+l.name+" "+w["pos"].encode("utf-8")+" "+ww+"\n")
               # We don't want to add newline on "ab" lines. 
               if l.name != "ab" or scene_index == scene_length:
                  ofile.write(act+" "+scene+" "+lineno+" -1 "+sp+" -1 -1 -1 -1 -1 -1 NEWLINE NEWLINE\n")

               # Reset variables.
               last_speaker = sp
               last_line = lineno
               
         elif s.name == "stage":
            # If the line is a stage direction we force the opening and  closing
            # parens and add the stage directions.
            l = s.string.encode("utf-8","ignore")
            wwhhaatt = s['type']
         
            l = re.sub("\s+"," ",l)
         
            l = re.sub("\."," .",l)
            l = re.sub("\;"," ;",l)
            l = re.sub("\:"," :",l)
            l = re.sub("\,"," ,",l)
            l = re.sub("\?"," ?",l)
            l = re.sub("\!"," !",l)
         
            ofile.write(act+" "+scene+" "+lineno+" -1 "+"Stage -1 -1 -1 -1 -1 -1 ( (\n")
         
            for w in l.split(" "):
         
               ofile.write(act+" "+scene+" "+lineno+" -1 "+"Stage -1 -1 -1 -1 -1 -1 "+wwhhaatt+" "+w+"\n")
         
            ofile.write(act+" "+scene+" "+lineno+" -1 "+"Stage -1 -1 -1 -1 -1 -1 ) )\n")
            ofile.write(act+" "+scene+" "+lineno+" -1 "+"Stage -1 -1 -1 -1 -1 -1 NEWLINE NEWLINE\n")
      
      
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
      
               ofile.write(act+" "+scene+" "+lineno+" -1 "+"Stage -1 -1 -1 -1 -1 -1 Title "+w+"\n")
      
            ofile.write(act+" "+scene+" "+lineno+" -1 "+"Stage -1 -1 -1 -1 -1 -1 NEWLINE NEWLINE\n")
           

ofile.close() 
