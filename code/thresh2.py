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

configfile = sys.argv[1]

verbose = 0
global threshold
global affect
threshold = 0

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

def oupdate(out,newmove,in_paren,nmax):

   if newmove[nmax-1]=="(": pass

   elif newmove[nmax-1]==")": pass

   elif newmove[nmax-2] == "SPEAKER": pass

   elif newmove[nmax-2] == "NEWLINE": pass

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

play = bs.find("play")
if play: play = play.string in ["True","true","T","t","yes","Yes"]
else: play = False
if play:
   
   class actant():
   
      def __init__(self,name,ip,port,actions):
   
         self.name = name
         self.ip = ip
         self.port = port
         self.actions = actions
         self.client = OSC.OSCClient()
   
      def send_value(self,what,value):
   
         if not what in actions: return 1
   
   #      print self.ip,self.port,what,self.actions[what], value
         msg = OSC.OSCMessage()
         msg.setAddress(self.actions[what])
         msg.append(value)
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
      global threshold
      global affect
      threshold = 0
      affect = ""
      next_line = [""]
   
      def __init__(self,ip,port):
   
         self.emos = ["anger","fear","joy","sadness"]
         super(voice_source,self).__init__(ip,port)
         self.server = OSC.OSCServer((self.ip,self.port))
         self.server.socket.settimeout(100000)
   
         def word(addr, tags, stuff, source):
            global affect
            global threshold
            global next_line
            next_line[0] = stuff[0]
   
         def thresh(addr,tags,stuff,source):
            global affect
            global threshold
            global next_line
            threshold = stuff[0]
            next_line[0] = ""
            print "setting threshold",affect,threshold

         def aff(addr,tags,stuff,source):
            global affect
            global threshold
            global next_line
            affect = stuff[0] + 5
            next_line[0] = ""

            print "setting affect",affect,emos[affect-5]
   
         self.server.addMsgHandler("/synth.word", word)
         self.server.addMsgHandler("/threshold", thresh)
         self.server.addMsgHandler("/affect", aff)
         self.server.addDefaultHandlers()
   
      def get_input(self):
   
         global next_line
         global threshold
         global affect
         self.server.handle_request()
         print affect,threshold
   
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
   
   scene_pause = rec.find("scene_pause")
   if scene_pause:
      scene_pause = float(scene_pause.string)
   else:
      scene_pause = 0
   
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
   
   sender = bs.find("sender")
   
   if not sender: 
      print "Drat"
      sys.exit()
   
   my_port = sender.find("port")
   if my_port: my_port = int(my_port.string)
   else: sys.exit()
   
   my_ip = sender.find("ip")
   if my_ip: my_ip = my_ip.string 
   else: sys.exit()
   
   voice = voice_source(my_ip,my_port)
      
   emos = ["anger","fear","joy","sadness"]

out = ""

for trial in bs.findAll(["markov","mirror"]):

   if trial.name == "markov":

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

            constraints.append({"acts":acts,"scenes":scenes,"lines":lines,"characters":characters})

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

            keep.append(1)

         if keep and max(keep)==0: continue
   
         trial_data.append(data[m])
         print data[m]
      
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
   
      out = ""
      in_paren = 0

      ramp = generate.find("ramp")
      if ramp:

         vals = []
         xlines = []

         emotion = ramp['emotion']
         emolist = ["anger","fear","joy","sadness","freq"]
         aff = [e for e in range(len(emolist)) if emotion==emolist[e]]
         if aff: affect = aff[0]+5
         else: affect=0

         for point in ramp.findAll("point"):

            vals.append(float(point["value"]))
            xlines.append(float(point["line"]))

         thresholds = make_thresholds(xlines,vals,length)

      cursor = trial_data[:k]
      out = ""
   
      while(1):
  
         ctype = "livethreshold" 
         if ctype == "livethreshold":

            # hack 1
            dc = 1
            dwho = "HAMLET"
            dcharacters = {}
            dcharacters[dwho] = dc
            display = 1
            # hack 1

            lk = k

            newmove = []

            while lk > 0 and not newmove:

               indie = " ".join([a[nmax-1] for a in cursor[k-lk:]])

               if indie in contexts[lk-1][nmax-1].keys():

                  tc = [t for t in trial_data if threshold < 0 or t[affect]>threshold or t[nmax-1]=="NEWLINE"]

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

                     tc = [t for t in trial_data if threshold < 0 or t[affect]>threshold or t[nmax-1]=="NEWLINE"]

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
               tc = [t for t in trial_data if threshold < 0 or t[affect]>threshold or t[nmax-1]=="NEWLINE"]
               newmove = random.sample(tc,1)[0]

            if newmove[nmax-1] == "NEWLINE" and out:

               l = clean(out)

               if re.match("^[A-Z]+$",l.strip()): 

                  dwho = l
                  if not dwho in dcharacters: 
                     dc += 1
                     dcharacters[dwho]=dc
                  continue

               elif re.match("^\s*ACT.*",l) or re.match("^\s*SCENE.*",l): 

                  display = 0
                  receiver.send_value("character","STAGEDIR")
                  receiver.send_value("line",l)
                  print l

               elif re.match("^\s*\(.*\)\s*$",l): 

                  display = 0
                  receiver.send_value("character","STAGEDIR")
                  receiver.send_value("line",l)
                  receiver.send_value("stagedir",l)
                  print l

               else: 

                  display = 1
                  receiver.send_value("character",dwho)
                  receiver.send_value("line",l)
                  print l

               while 1:

                  word = voice.get_input()
                  if not word: continue

                  if word == "EOL": 
                     out = ""
                     break
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
                  receiver.send_value("bigpacket",ws+ewma+[mws]+[ws[mws-1]]+[wf]+[dcharacters[dwho]])

            else:

               (in_paren,out) = oupdate(out,newmove,in_paren,nmax)

            cursor.append(newmove)
            cursor = cursor[1:]

