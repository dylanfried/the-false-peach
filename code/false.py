import random
import re
import getopt
import sys
from bs4 import BeautifulSoup

configfile = sys.argv[1]

verbose = 0

def expand(things):

   out = []

   for t in things:

      if not "-" in t: out.append(t)
      else:
         start = int(re.sub("([0-9]+)\-.*","\\1",t))   
         end = int(re.sub(".*\-([0-9]+)","\\1",t))   
         out += [str(r) for r in range(start,end+1)]

   return out

def update(out,newmove,in_paren,nmax):

   if newmove[nmax-1]=="(":

      if not in_paren:

         out += " "+newmove[nmax-1]
         in_paren = 1

   elif newmove[nmax-1]==")":

      if in_paren:

         out += " "+newmove[nmax-1]
         in_paren = 0

   elif newmove[nmax-2] == "SPEAKER" and in_paren:

      out += " ) NEWLINE "+newmove[nmax-1]
      in_paren = 0

   else: out += " "+newmove[nmax-1]

   return (in_paren,out)

def clean(x):

   while re.match("(.*)\ ([.,?!:;)]+.*)",x):
      x = re.sub("(.*)\ ([.,?!:;)]+.*)","\\1\\2",x)

   while re.match("(.*)\( (.*)",x):
      x = re.sub("(.*)\( (.*)","\\1 (\\2",x)

   return x.strip()


cnt = 0

bs = BeautifulSoup(open(configfile).read())
out = ""

for trial in bs.findAll(["markov","mirror"]):

   if trial.name == "markov":

      trialname = trial.find("name")
      if trialname: 
         trialname = trialname.string.encode('utf-8','ignore')
      else: trialname = ""
   
      if not out:
         if trialname:
            out =  "================ MARKOV "+str(cnt+1)+" "+trialname+" ================ NEWLINE "
         else:
            out =  "================ MARKOV "+str(cnt+1)+" ================ NEWLINE "
      else:
         if trialname:
            out = out + " NEWLINE ================ MARKOV "+str(cnt+1)+" "+trialname+" ================ NEWLINE "
         else:
            out = out + " NEWLINE ================ MARKOV "+str(cnt+1)+" ================ NEWLINE "
   
      datafile = trial.find("file")
      if datafile: 
         datafile = datafile.string
      else: continue
   
      data = open(datafile).readlines()
      data = [d.strip() for d in data]
      data = [d.split(" ") for d in data]
   
      nmax = len(data[0])
   
      generate = trial.find("generate")
      if not generate: continue
   
      kmax = trial.find("generate").find("k")
      if kmax: kmax = int(kmax.string)
      else: kmax = 2
   
      ctype = trial.find("generate").find("type")
      if ctype: ctype = ctype.string
      else: ctype = "word"
   
      reset = trial.find("generate").find("reset")
      if reset: reset = reset.string in ["True","true","T","t","yes","Yes"]
      else: reset = True
   
      length = trial.find("generate").find("length")
      if length: length = int(length.string)
      else: length = 0
   
      contexts = []
      trial_data = []
   
      for i in range(kmax): 
   
         contexts.append([])
   
         for j in range(nmax):
      
            contexts[i].append({})
      
      history = []
   
      acts = []
      scenes = []
      lines = []
      characters = []
   
   # 1 1 2 6 Francisco vvb answer
   # 1 1 2 7 Francisco pno11 me
   
      acts = trial.find("acts")
      if acts: 
         acts = acts.string
         acts = expand(acts.split(","))
      else: acts=[]
   
      scenes = trial.find("scenes")
      if scenes: 
         scenes = scenes.string
         scenes = expand(scenes.split(","))
      else: scenes=[]
   
      lines = trial.find("lines")
      if lines: 
         lines = lines.string
         lines = expand(lines.split(","))
      else: lines=[]
   
      characters = trial.find("characters")
      if characters: 
         characters = characters.string
         characters = characters.split(",")
         characters = [re.sub(" ","_",c.upper()) for c in characters]
      else: characters=[]
   
      for m in range(len(data)):
   
         if acts and (not data[m][0] in acts): continue
         if scenes and (not data[m][1] in scenes): continue
         if lines and (not data[m][2] in lines): continue
         if characters and (not data[m][4].upper() in characters): continue
   
         trial_data.append(data[m])
      
         for i in range(kmax):
      
            if m > i:
      
               for j in range(nmax):
      
                  indie = " ".join([a[j] for a in data[(m-i-1):m]])
      
                  if not indie in contexts[i][j]: contexts[i][j][indie] = []
                  contexts[i][j][indie].append(data[m])
    
   #   for kk in contexts[0][nmax-1].keys():
   #      print kk," ".join([c[nmax-1] for c in contexts[0][nmax-1][kk]])
    
      k = kmax
   
      if cnt == 0 or reset: cursor = trial_data[:k]
      cnt += 1
   
      out = out + " ".join([h[nmax-1] for h in cursor])
      in_paren = 0
   
      for i in range(length):
   
         if ctype == "word":
   
            indie = " ".join([a[nmax-1] for a in cursor])
            if not indie in contexts[k-1][nmax-1].keys(): break
            newmove = random.sample(contexts[k-1][nmax-1][indie],1)[0]
   
            (in_paren,out) = update(out,newmove,in_paren,nmax)
      
            cursor.append(newmove)
            cursor = cursor[1:]
   
         if ctype == "pos":
   
            indie = " ".join([a[nmax-2] for a in cursor])
            if not indie in contexts[k-1][nmax-2].keys(): break
            newmove = random.sample(contexts[k-1][nmax-2][indie],1)[0]
   
            (in_paren,out) = update(out,newmove,in_paren,nmax)
     
            cursor.append(newmove)
            cursor = cursor[1:]

   if trial.name == "mirror": 

      trialname = trial.find("name")
      if trialname:
         trialname = trialname.string.encode('utf-8','ignore')
      else: trialname = ""

      if not out:
         if trialname:
            out =  "================ MIRROR "+str(cnt+1)+" "+trialname+" ================ NEWLINE "
         else:
            out =  "================ MIRROR "+str(cnt+1)+" ================ NEWLINE "
      else:
         if trialname:
            out = out + " NEWLINE ================ MIRROR "+str(cnt+1)+" "+trialname+" ================ NEWLINE "
         else:
            out = out + " NEWLINE ================ MIRROR "+str(cnt+1)+" ================ NEWLINE "

      datafile = trial.find("file")
      if datafile:
         datafile = datafile.string
      else: continue

      data = open(datafile).readlines()
      data = [d.strip() for d in data]
      data = [d.split(" ") for d in data]

      nmax = len(data[0])
  
      generate = trial.find("generate")
      if not generate: continue

      length = trial.find("generate").find("length")
      if length: length = int(length.string)
      else: length = 0

      trainacts = []
      trainscenes = []
      trainlines = []
      traincharacters = []
  
      trainacts = trial.find("acts")
      if trainacts:
         trainacts = trainacts.string
         trainacts = expand(trainacts.split(","))
      else: trainacts=[]
  
      trainscenes = trial.find("scenes")
      if trainscenes:
         trainscenes = trainscenes.string
         trainscenes = expand(trainscenes.split(","))
      else: trainscenes=[]
  
      trainlines = trial.find("lines")
      if trainlines:
         trainlines = trainlines.string
         trainlines = expand(trainlines.split(","))
      else: trainlines=[]
  
      traincharacters = trial.find("characters")
      if traincharacters:
         traincharacters = traincharacters.string
         traincharacters = traincharacters.split(",")
         traincharacters = [re.sub(" ","_",c.upper()) for c in traincharacters]
      else: traincharacters=[]

      context = {}

      for m in range(len(data)):

         if trainacts and (not data[m][0] in trainacts): continue
         if trainscenes and (not data[m][1] in trainscenes): continue
         if trainlines and (not data[m][2] in trainlines): continue
         if traincharacters and (not data[m][4].upper() in traincharacters): continue

         w = data[m][nmax-1]
         p = data[m][nmax-2]
         if not p in context: context[p] = []
         context[p].append(w)

      if not context: continue

      acts = []
      scenes = []
      lines = []
      characters = []
  
      acts = trial.find("acts")
      if acts:
         acts = acts.string
         acts = expand(acts.split(","))
      else: acts=[]
  
      scenes = trial.find("scenes")
      if scenes:
         scenes = scenes.string
         scenes = expand(scenes.split(","))
      else: scenes=[]
  
      lines = trial.find("lines")
      if lines:
         lines = lines.string
         lines = expand(lines.split(","))
      else: lines=[]
  
      characters = trial.find("characters")
      if characters:
         characters = characters.string
         characters = characters.split(",")
         characters = [re.sub(" ","_",c.upper()) for c in characters]
      else: characters=[]

      for m in range(len(data)):

         if acts and (not data[m][0] in acts): continue
         if scenes and (not data[m][1] in scenes): continue
         if lines and (not data[m][2] in lines): continue
         if characters and (not data[m][4].upper() in characters): continue

         w = data[m][nmax-1]
         p = data[m][nmax-2]

         if p in context: 
            out += " "+random.sample(context[p],1)[0]

      cnt += 1
   
out = re.sub(" NEWLINE \)"," )",out)
out = out.split("NEWLINE")
out = [clean(o.strip()) for o in out]
for o in out: print o
   
