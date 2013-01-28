import random
import re
import getopt
from bs4 import BeautifulSoup
import OSC
from simpleOSC import *
import copy

import sys
sys.path.append("code/")
from hyphenate import hyphenate_word

if len(sys.argv)>2:
   triggerconfigfile = sys.argv[2]
else:
   triggerconfigfile = ""
 
configfile = sys.argv[1]
programname = sys.argv[1]
programname = re.sub("^.*\/(.*)\.xml$","\\1",programname)

verbose = 0

def make_thresholds(x,y,m):

   what = range(m)
   val = []

   for i in what:

      right = min([j for j in range(len(x)) if i < x[j]])
      left = max([j for j in range(len(x)) if i >= x[j]])

      xleft = x[left]+0.0
      xright = x[right]+0.0
      yleft = y[left]+0.0
      yright = y[right]+0.0

      val.append( yright*(xleft-i)/(xleft-xright)+yleft*(i-xright)/(xleft-xright) )

   return val

def expand(things):

   out = []

   for t in things:

      if not "-" in t: out.append(t)
      else:
         start = int(re.sub("([0-9]+)\-.*","\\1",t))   
         end = int(re.sub(".*\-([0-9]+)","\\1",t))   
         out += [str(r) for r in range(start,end+1)]

   return out

def update(out,newmove,in_paren,nmax,insert=""):

   if insert: out += " "+insert

   if newmove[nmax-1]=="(":

      if not in_paren:

         out += " NEWLINE "+newmove[nmax-1]

   elif newmove[nmax-1]==")":

      if in_paren:

         out += " "+newmove[nmax-1]
         in_paren = 0

   elif newmove[nmax-2] == "SPEAKER" and in_paren:

      out += " ) NEWLINE "+newmove[nmax-1]
      in_paren = 0

   else: 

      if in_paren and newmove[nmax-1]=="NEWLINE":

         return (in_paren,out)

      else: out += " "+newmove[nmax-1]

   if insert: in_paren = 2
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
scene_pause = []
alternate = []
forcechar = []
firstchar = []

for trial in bs.findAll(["markov","mirror"]):

   tfirstchar = trial.find("first_character")
   if tfirstchar: tfirstchar = tfirstchar.string
   else: tfirstchar = ""
   firstchar.append(tfirstchar)

   tforcechar = trial.find("forced_character")
   if tforcechar: tforcechar = tforcechar.string
   else: tforcechar = ""
   forcechar.append(tforcechar)

   talternate = trial.find("alternate")
   if talternate: 
      talternate = talternate.string
      talternate = talternate.split(",")
   else: talternate = []
   alternate.append(talternate)

   tscene_pause = trial.find("scene_pause")
   if tscene_pause:
      tscene_pause = float(tscene_pause.string)
   else:
      tscene_pause = 0
   scene_pause.append(tscene_pause)

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
      data = [d[:5]+[float(dd) for dd in d[5:10]]+d[10:] for d in data]
   
      nmax = len(data[0])
   
      generate = trial.find("generate")
      if not generate: continue
   
      kmax = trial.find("generate").find("k")
      if kmax: kmax = int(kmax.string)
      else: kmax = 2

#      print "HERE",kmax
   
      ctype = trial.find("generate").find("type")
      if ctype: ctype = ctype.string
      else: ctype = "word"
   
      reset = trial.find("generate").find("reset")
      if reset: reset = reset.string in ["True","true","T","t","yes","Yes"]
      else: reset = True

      finishsent = trial.find("generate").find("finish_sent")
      if finishsent: finishsent = finishsent.string == "True"
      else: finishsent = False
   
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
   
      constraints = []
   
   # 1 1 2 6 Francisco vvb answer
   # 1 1 2 7 Francisco pno11 me
 
      train = trial.find("train") 
      selections = train.find("selections")

      if selections:


         for selection in selections.findAll("selection"):

            acts = selection.find("acts")
            if acts: 
               acts = acts.string
               acts = expand(acts.split(","))
            else: acts=[]
   
            scenes = selection.find("scenes")
            if scenes: 
               scenes = scenes.string
               scenes = expand(scenes.split(","))
            else: scenes=[]
   
            lines = selection.find("lines")
            if lines: 
               lines = lines.string
               lines = expand(lines.split(","))
            else: lines=[]
         
            characters = selection.find("characters")
            if characters: 
               characters = characters.string
               characters = characters.split(",")
               characters = [c.strip() for c in characters]
               characters = [re.sub(" ","_",c.upper()) for c in characters]
            else: characters=[]

            pos = selection.find("pos")
            if pos:
               pos = pos.string
               pos = pos.split(",")
               pos = [c.strip() for c in pos]
               pos = [c.upper() for c in pos]
            else: pos=[]

            constraints.append({"acts":acts,"scenes":scenes,"lines":lines,"characters":characters,"pos":pos})

      else:

         acts = train.find("acts")
         if acts:
            acts = acts.string
            acts = expand(acts.split(","))
         else: acts=[]
 
         scenes = train.find("scenes")
         if scenes:
            scenes = scenes.string
            scenes = expand(scenes.split(","))
         else: scenes=[]
 
         lines = train.find("lines")
         if lines:
            lines = lines.string
            lines = expand(lines.split(","))
         else: lines=[]
 
         characters = train.find("characters")
         if characters:
            characters = characters.string
            characters = characters.split(",")
            characters = [c.strip() for c in characters]
            characters = [re.sub(" ","_",c.upper()) for c in characters]
         else: characters=[]

         constraints.append({"acts":acts,"scenes":scenes,"lines":lines,"characters":characters})

      for m in range(len(data)):
 
         keep = []

         for c in constraints:
 
            if c["acts"] and (not data[m][0] in c["acts"]): 
               keep.append(0)
               continue
        
            if c["scenes"] and (not data[m][1] in c["scenes"]): 
               keep.append(0)
               continue

            if c["lines"] and (not data[m][2] in c["lines"]): 
               keep.append(0)
               continue

            if c["characters"] and (not data[m][4].upper() in c["characters"]): 
               keep.append(0)
               continue

            if 'pos' in c and c['pos']:
               if data[m][nmax-2]=="SPEAKER" or data[m][nmax-2].upper() in c['pos'] or data[m][nmax-1]=="NEWLINE" and not data[m][nmax-1] in [")","("]: keep.append(1)
               else: keep.append(0)
            else: keep.append(1)

         if keep and max(keep)==0: continue
   
         trial_data.append(data[m])
#         print data[m]
      
         for i in range(kmax):
      
            if len(trial_data) > i:
      
               for j in range(nmax-2,nmax):
      
                  indie = " ".join([a[j] for a in trial_data[(-1-i-1):-1]])
      
                  if not indie in contexts[i][j]: contexts[i][j][indie] = []
                  contexts[i][j][indie].append(trial_data[-1])
    
#      for kk in contexts[1][nmax-1].keys():
#         print kk," ".join([c[nmax-1] for c in contexts[1][nmax-1][kk]])
    
      k = kmax
   
      if cnt == 0 or reset: cursor = trial_data[:k]
      cnt += 1

      in_paren = 0
      minicursor = []

      for newmove in cursor:
         
         insert = ""
         if minicursor and minicursor[-1][nmax-1]=="(" and in_paren<2: insert=newmove[nmax-2]
         (in_paren,out) = update(out,newmove,in_paren,nmax,insert)
         minicursor.append(newmove)

#      out = out + " ".join([h[nmax-1] for h in cursor])
#      ptest = " ".join([h[nmax-1] for h in cursor])
#      if re.match(".*\(.*",ptest):
#         if not re.match(".*\(.*\).*",ptest):
#            in_paren = 1
#         else: in_paren = 0

      ramp = generate.find("ramp")
      if ramp:

         vals = []
         xlines = []

         emotion = ramp['emotion']
         emolist = ["anger","fear","joy","sadness","freq"]
         emoi = [e for e in range(len(emolist)) if emotion==emolist[e]]
         if emoi: emoi = emoi[0]+5
         else: sys.exit()

         for point in ramp.findAll("point"):

            vals.append(float(point["value"]))
            xlines.append(float(point["line"]))

         thresholds = make_thresholds(xlines,vals,length)
   
      for i in range(length):

         if ctype == "word":
   
            indie = " ".join([a[nmax-1] for a in cursor])

            if indie in contexts[k-1][nmax-1].keys(): 
               newmove = random.sample(contexts[k-1][nmax-1][indie],1)[0]
            else:
               indie = " ".join([a[nmax-1] for a in cursor[1:]])

               if indie in contexts[k-2][nmax-1].keys(): 
                  newmove = random.sample(contexts[k-1][nmax-1][indie],1)[0]
               else:
                  break
 
            insert ="" 
            if cursor[-1][nmax-1]=="(" and in_paren<2: insert=newmove[nmax-2]
            (in_paren,out) = update(out,newmove,in_paren,nmax,insert)
     
            cursor.append(newmove)
            cursor = cursor[1:]
   
         if ctype == "pos":
   
            indie = " ".join([a[nmax-2] for a in cursor])
            if not indie in contexts[k-1][nmax-2].keys(): break
            newmove = random.sample(contexts[k-1][nmax-2][indie],1)[0]
   
            insert ="" 
            if cursor[-1][nmax-1]=="(": insert=newmove[nmax-2]
            (in_paren,out) = update(out,newmove,in_paren,nmax,insert)
     
            cursor.append(newmove)
            cursor = cursor[1:]

         level = -1

         if ctype == "threshold":

            lk = k

            newmove = []

            while lk > 0 and not newmove:

               indie = " ".join([a[nmax-1] for a in cursor[k-lk:]])

               if indie in contexts[lk-1][nmax-1].keys():
  
                  tc = [t for t in contexts[lk-1][nmax-1][indie] if thresholds[i]<0 or t[emoi] > thresholds[i] or t[nmax-1]=="NEWLINE"]
  
                  if tc: 
                     level = 1
                     newmove = random.sample(tc,1)[0]
                  else: 
                     lk -= 1
                     continue
               else:
                  lk -= 1
                  continue

            if not newmove:

               lk = k

               while lk > 0 and not newmove:
   
                  indie = " ".join([a[nmax-2] for a in cursor[k-lk:]])
   
                  if indie in contexts[lk-1][nmax-2].keys():

                     tc = [t for t in contexts[lk-1][nmax-2][indie] if thresholds[i]<0 or t[emoi] > thresholds[i] or t[nmax-1]=="NEWLINE"]
    
                     if tc: 
                        newmove = random.sample(tc,1)[0]
                        level = 1
                     else:
                        lk -= 1
                        continue
                  else:
                     lk -= 1
                     continue

            if not newmove:

               level = 3
               tc = [t for t in trial_data if t[emoi]>thresholds[i] or t[nmax-1]=="NEWLINE"]
               newmove = random.sample(tc,1)[0]

            (in_paren,out) = update(out,newmove,in_paren,nmax)
         
            cursor.append(newmove)
            cursor = cursor[1:]
            in_paren = False

      if not finishsent: continue
#      while (in_paren or (not re.match(".*[.?!]\s*$",out))) and (not ctype=="threshold"):
      while (in_paren or (not re.match(".*[.?!]\s*$",out))):

         if ctype == "word":
  
            indie = " ".join([a[nmax-1] for a in cursor])
            if not indie in contexts[k-1][nmax-1].keys(): break
            newmove = random.sample(contexts[k-1][nmax-1][indie],1)[0]
  
            insert ="" 
            if cursor[-1][nmax-1]=="(": insert=newmove[nmax-2]
            (in_paren,out) = update(out,newmove,in_paren,nmax,insert)

            cursor.append(newmove)
            cursor = cursor[1:]
  
         if ctype == "pos":
  
            indie = " ".join([a[nmax-2] for a in cursor])
            if not indie in contexts[k-1][nmax-2].keys(): break
            newmove = random.sample(contexts[k-1][nmax-2][indie],1)[0]
  
            insert ="" 
            if cursor[-1][nmax-1]=="(": insert=newmove[nmax-2]
            (in_paren,out) = update(out,newmove,in_paren,nmax,insert)

            cursor.append(newmove)
            cursor = cursor[1:]

         if ctype == "threshold":

            lk = k

            newmove = []

            while lk > 0 and not newmove:

               indie = " ".join([a[nmax-1] for a in cursor[k-lk:]])

               if indie in contexts[lk-1][nmax-1].keys():

                  tc = contexts[lk-1][nmax-1][indie]

                  if tc:
                     level = 1
                     newmove = random.sample(tc,1)[0]
                  else:
                     lk -= 1
                     continue
               else:
                  lk -= 1
                  continue

            if not newmove:

               lk = k

               while lk > 0 and not newmove:

                  indie = " ".join([a[nmax-2] for a in cursor[k-lk:]])

                  if indie in contexts[lk-1][nmax-2].keys():

                     tc = contexts[lk-1][nmax-2][indie]

                     if tc:
                        newmove = random.sample(tc,1)[0]
                        level = 1
                     else:
                        lk -= 1
                        continue
                  else:
                     lk -= 1
                     continue

            if not newmove:

               level = 3
               tc = trial_data
               newmove = random.sample(tc,1)[0]

            insert ="" 
            if cursor[-1][nmax-1]=="(": insert=newmove[nmax-2]
            (in_paren,out) = update(out,newmove,in_paren,nmax,insert)

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

      trainconstraints = []

      train = trial.find("train")
      selections = train.find("selections")

      if selections:

         for selection in selections.findAll("selection"):
  
            acts = selection.find("acts")
            if acts:
               acts = acts.string
               acts = expand(acts.split(","))
            else: acts=[]
  
            scenes = selection.find("scenes")
            if scenes:
               scenes = scenes.string
               scenes = expand(scenes.split(","))
            else: scenes=[]
  
            lines = selection.find("lines")
            if lines:
               lines = lines.string
               lines = expand(lines.split(","))
            else: lines=[]
  
            characters = selection.find("characters")
            if characters:
               characters = characters.string
               characters = characters.split(",")
               characters = [c.strip() for c in characters]
               characters = [re.sub(" ","_",c.upper()) for c in characters]
            else: characters=[]

            pos = selection.find("pos")
            if pos:
               pos = pos.string
               pos = pos.split(",")
               pos = [c.strip() for c in pos]
               pos = [c.upper() for c in pos]
            else: pos=[]


            trainconstraints.append({"acts":acts,"scenes":scenes,"lines":lines,"characters":characters,"pos":pos})

      else:

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
            characters = [c.strip() for c in characters]
            characters = [re.sub(" ","_",c.upper()) for c in characters]
         else: characters=[]

         trainconstraints.append({"acts":acts,"scenes":scenes,"lines":lines,"characters":characters})

      context = {}

      for m in range(len(data)):

         keep = []

         for c in trainconstraints:

            if c["acts"] and (not data[m][0] in c["acts"]):
               keep.append(0)
               continue

            if c["scenes"] and (not data[m][1] in c["scenes"]):
               keep.append(0)
               continue

            if c["lines"] and (not data[m][2] in c["lines"]):
               keep.append(0)
               continue

            if c["characters"] and (not data[m][4].upper() in c["characters"]):
               keep.append(0)
               continue

            if 'pos' in c and c['pos']:
               if data[m][nmax-2].upper() in c['pos']: keep.append(1)
               else: keep.append(0)
            else: keep.append(1)

         if keep and max(keep)==0: continue

         w = data[m][nmax-1]
         p = data[m][nmax-2]
         if not p in context: context[p] = []
         context[p].append(w)

      if not context: continue

      constraints = []
 
      generate = trial.find("generate")

      selections = generate.find("selections")
      if selections: 

         for selection in selections.findAll("selection"):

            acts = selection.find("acts")
            if acts:
               acts = acts.string
               acts = expand(acts.split(","))
            else: acts=[]
        
            scenes = selection.find("scenes")
            if scenes:
               scenes = scenes.string
               scenes = expand(scenes.split(","))
            else: scenes=[]
     
            lines = selection.find("lines")
            if lines:
               lines = lines.string
               lines = expand(lines.split(","))
            else: lines=[]
     
            characters = selection.find("characters")
            if characters:
               characters = characters.string
               characters = characters.split(",")
               characters = [c.strip() for c in characters]
               characters = [re.sub(" ","_",c.upper()) for c in characters]
            else: characters=[]

            pos = selection.find("pos")
            if pos:
               pos = pos.string
               pos = pos.split(",")
               pos = [c.strip() for c in pos]
               pos = [c.upper() for c in pos]
            else: pos=[]


            if acts or scenes or lines or characters:

               constraints.append({"acts":acts,"scenes":scenes,"lines":lines,"characters":characters,"pos":pos})

      else:

         acts = train.find("acts")
         if acts:
            acts = acts.string
            acts = expand(acts.split(","))
         else: acts=[]

         scenes = train.find("scenes")
         if scenes:
            scenes = scenes.string
            scenes = expand(scenes.split(","))
         else: scenes=[]

         lines = train.find("lines")
         if lines:
            lines = lines.string
            lines = expand(lines.split(","))
         else: lines=[]

         characters = train.find("characters")
         if characters:
            characters = characters.string
            characters = characters.split(",")
            characters = [c.strip() for c in characters]
            characters = [re.sub(" ","_",c.upper()) for c in characters]
         else: characters=[]

         if acts or scenes or lines or characters:

            constraints.append({"acts":acts,"scenes":scenes,"lines":lines,"characters":characters})

      if not constraints: continue

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
out = re.sub("(oh oh )+"," oh oh ",out)
out = re.sub("(ho ho )+"," ho ho ",out)
out = re.sub("(nonny nonny )+"," nonny nonny ",out)
out = re.sub("(a-down a-down )+"," nonny nonny ",out)
out = re.sub("( NEWLINE)+"," NEWLINE",out)
out = out.split("NEWLINE")
lines = [clean(o.strip()) for o in out]
for l in lines: print l

# communication

class actant():

   def __init__(self,name,ip,port,actions):

      self.name = name
      self.ip = ip
      self.port = port
      self.actions = actions
      self.client = OSC.OSCClient()

   def send_value(self,what,value,excess=""):

      if not what in self.actions: return 1

#      print self.ip,self.port,what,self.actions[what], value
      msg = OSC.OSCMessage()
      msg.setAddress(self.actions[what])
      msg.append(value)
      if excess: msg.append(excess)
      try: self.client.sendto(msg, (self.ip,self.port))
      except: return 0

      return 1

class datum(object):

   def __init__(self,ip,port):

      self.ip = ip
      self.port = port

   def get_input(self): return None

class voice_source(datum):

   global next_line
   next_line = [""]

   def __init__(self,ip,port):

      super(voice_source,self).__init__(ip,port)
      self.server = OSC.OSCServer((self.ip,self.port))
      self.server.socket.settimeout(100000)

      def word(addr, tags, stuff, source):
         global next_line
         next_line[0] = stuff[0]

      self.server.addMsgHandler("/synth.word", word)
      self.server.addDefaultHandlers()

   def get_input(self):

      global next_line
      self.server.handle_request()

      return next_line[0]

rec = bs.find("receiver")

who = rec.find("name")
if who:
   who = who.string.encode('utf-8','ignore')
else: 
   for o in out: print o

ip = rec.find("ip")
if ip:
   ip = ip.string.encode('utf-8','ignore')
else: 
   for o in out: print o

port = rec.find("port")
if port:
   port = int(port.string)
else: 
   for o in out: print o

actions = {}

for action in rec.findAll("action"):

   source = action.find("source")
   if source:
      source = source.string.encode('utf-8','ignore')
   else: source=""

   target = action.find("target")
   if target:
      target = target.string.encode('utf-8','ignore')
   else: target=""

   if source and target: actions[source] = target


receiver = actant(who,ip,port,actions)

emo = open("data/emo.txt").readlines()
emotions = {}

for i in range(len(emo)):

   flds = emo[i].split(",")
   emotions[flds[0]] = [round(float(f),1) for f in flds[1:]]

freq = open("data/freq.txt").readlines()
freqs = {}
tot = 0

for i in range(len(freq)):

   ff = freq[i].strip()
   flds = ff.split(" ")
   freqs[flds[1]] = float(flds[0])
   tot += freqs[flds[1]]

for f in freqs: freqs[f] = round(1000.0*freqs[f]/(tot+0.0),2)

def syll_count(w):
   return len(hyphenate_word(w))

def word_freq(w):
   if w in freqs: return freqs[w]
   else: return 0

def word_score(w,n=3):
   if w in emotions: return emotions[w][n]
   else: return -1

def word_scores(w):
   if w in emotions: return emotions[w]
   else: return [-1,-1,-1,-1]

ewma = [0,0,0,0]

def update(e,c,lam=0.8):
   if c > 0: return e*lam+c*(1-lam)
   return e

who = ""
c = 0
characters = {}

sender = bs.find("sender")

if not sender: 
   print "Drat"
   sys.exit()

play = sender.find("play")
if play: play = play.string in ["True","true","T","t","yes","Yes"]
else: play = False
if not play: sys.exit()

print "Playing..."

trigs = {}

if triggerconfigfile:

   trigsall = BeautifulSoup(open(triggerconfigfile).read())

   for triggers in trigsall.findAll("triggers"):

      trigwhat = triggers['stagedir'].strip()
      trigs[trigwhat] = {}

      for w in triggers.findAll("word"):

         trigwhen = float(w['pause'].strip())
         trigword = w.string.strip()
         trigs[trigwhat][trigword.lower()] = trigwhen

my_port = sender.find("port")
if my_port: my_port = int(my_port.string)
else: sys.exit()

my_ip = sender.find("ip")
if my_ip: my_ip = my_ip.string 
else: sys.exit()

voice = voice_source(my_ip,my_port)
   
emos = ["anger","fear","joy","sadness"]

tkn = -1
need_outro=0

for l in lines:

   in_stagedir_trigger = 0
   trigger_label = ""

   if need_outro:

      if not re.match("^\s*ACT.*",l.upper()) or re.match("^\s*SCENE.*",l.upper()): 

         receiver.send_value("outro",3000,trialname)
         time.sleep(3)
         need_outro=0

   if re.match(".*====.*",l):
 
      tkn += 1
      print "===== Next scene ====== " 
      time.sleep(scene_pause[tkn])
      trialname = l.split(" ")[3]
      continue

   elif re.match("^[A-Z_]+$",l.strip()): 

      if not who and forcechar[tkn]: who = forcechar[tkn]
      elif alternate[tkn]:
         who = alternate[tkn][0]
         alternate[tkn] = alternate[tkn][1:]+[alternate[tkn][0]]
      else:
         who = l
      if not who in characters: 
         c += 1
         characters[who]=c
      continue

   elif re.match("^\s*ACT.*",l.upper()) or re.match("^\s*SCENE.*",l.upper()): 

      receiver.send_value("character","TITLE")
#      receiver.send_value("character","STAGEDIR")

      display = 0
      receiver.send_value("intro",3000)
      time.sleep(3)
      receiver.send_value("stagedir.title",l)
      receiver.send_value("stagedir.bool",0)
      receiver.send_value("stagedir",l)
      receiver.send_value("line",l)
      need_outro=1
      print l

   elif re.match("^\s*\(.*\)\s*$",l): 

      wwhhaatt = re.sub("^\s*\(\s*([a-zA-Z]+)\s+.*","\\1",l)
      l = re.sub("^\s*\(\s*[a-zA-Z]+\s+(.*)","(\\1",l)
      display = 0
      receiver.send_value("character","STAGEDIR")
      receiver.send_value("stagedir.bool",2)
#      receiver.send_value("stagedir."+wwhhaatt,l)
      receiver.send_value("stagedir",l)
      l = re.sub("^\s*\((.*)\)\s*$","\\1",l)
      receiver.send_value("line",l)
      trigger_label = wwhhaatt
      print l

   else: 

      if not who:

         if firstchar[tkn]: who = firstchar[tkn].upper()
         if forcechar[tkn]: who = forcechar[tkn].upper()
         if alternate[tkn]: 
            who = alternate[tkn][0].upper()
            alternate[tkn] = alternate[tkn][1:]+[alternate[tkn][0]]

         if not who: who = "HAMLET"

         if not who in characters:
            c += 1
            characters[who]=c

         print who

      display = 1
      receiver.send_value("character",who)
      receiver.send_value("stagedir.bool",1)
      receiver.send_value("line",l)
      print l

   while 1:

      word = voice.get_input()

      if word == "EOL": break
      print word

      w = word.lower()
      w = re.sub("^(.*),$","\\1",w)
      w = re.sub("^(.*)\.$","\\1",w)
      w = re.sub("^(.*)\?$","\\1",w)
      w = re.sub("^(.*)\!$","\\1",w)
      w = re.sub("^(.*):$","\\1",w)
      w = re.sub("^(.*);$","\\1",w)
      ws = word_scores(w)
      wf = word_freq(w)

      if trigger_label:

         print "TRIG",trigger_label

         tfound = 0
         for label in trigs.keys():

            if w in trigs[label]: 
               tfound = 1
               break

         if tfound:
 
            print "SENDING", label, w
            receiver.send_value("stagedir."+label,w)
            time.sleep(trigs[label][w]/1000.0)
         else: 
            print "NOT FOUND",w

#      print "TRIG",trigger_label
#      if trigger_label and trigger_label in trigs:
#
#         if w in trigs[trigger_label]: 
# 
#            print "SENDING", trigger_label, w
#            receiver.send_value("stagedir."+trigger_label,w)
#            time.sleep(trigs[trigger_label][w]/1000.0)
#
      mws = [i for i in range(4) if ws[i]==max(ws)][0]+1

      if display: receiver.send_value("word",word)

      if ws[mws-1]<0: affmax = ""
      else: affmax = emos[mws-1]
      receiver.send_value("affmax",affmax)

      if ws[mws-1]<0: affmaxval = 0
      else: affmaxval = ws[mws-1]
      receiver.send_value("affmaxval",affmaxval)

      if ws[0] < 0: continue

      ewma = [update(ewma[i],ws[i]) for i in range(4)]

      receiver.send_value("affvals",ws)
      receiver.send_value("affsmos",ewma)
      receiver.send_value("wordfreq",wf)
      receiver.send_value("smallpacket",[word,emos[mws-1],ws[mws-1]])
      if who: receiver.send_value("bigpacket",ws+ewma+[mws]+[ws[mws-1]]+[wf]+[characters[who]])

