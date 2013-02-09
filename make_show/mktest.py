from bs4 import BeautifulSoup
import os
import sys
import re
import random

# 2bMirror.xml		52directions.xml	gertrude.xml		hamNOUN.xml		solid.xml
# 3pcntORIG.xml		MadOph.xml		gravedigger.xml		mansmemory.xml

dir = "config/TESTS/"

pins = {"2bMirror.xml":{"sound":2},
        "solid.xml":{"sound":6},
        "rogue.xml":{"sound":7},
        "MadOph.xml":{"sound":8,"video":11},
        "3pcntORIG.xml":{"sound":8,"video":1}}

#extra = open("make_show/header.txt").readlines()
#extra = [e.rstrip() for e in extra]
#for e in extra: print e

if len(sys.argv)>1: cnt = int(sys.argv[1])
else: cnt = 3

tdlist = os.listdir(dir)
tvid = ["1","2","8","10a","11","12","13"]
tsnd = ["0","1","2","3","4","5","6"]
tact = ["0","1","1","0","1","0","0"]
tlight = ["skot","theatre","emotions"]

tdlist = [l for l in tdlist if re.match("sh.*\.xml$",l) and not re.match(".*trigger.*",l)]

dlist = random.sample(tdlist,cnt)
vid = []
act = []
snd = []
light = []

for d in dlist:

   if d in pins:

      if "sound" in pins[d]: 
         snd.append(pins[d]["sound"])
      else: snd.append(random.sample(tsnd,1)[0])
      if "video" in pins[d]: 
         vid.append(pins[d]["video"])
      else: vid.append(random.sample(tvid,1)[0])
      if "actor" in pins[d]: 
         act.append(pins[d]["actor"])
      else: act.append(random.sample(tact,1)[0])
      if "light" in pins[d]: 
         light.append(pins[d]["light"])
      else: light.append(random.sample(tlight,1)[0])

   else:

      snd.append(random.sample(tsnd,1)[0])
      vid.append(random.sample(tvid,1)[0])
      act.append(random.sample(tact,1)[0])
      light.append(random.sample(tlight,1)[0])

for i in range(len(dlist)):

   l = dlist[i]
   a = str(vid[i])+"_"+str(snd[i])+"_"+str(act[i])+"_"+str(light[i])

   bs = BeautifulSoup(open(dir+l).read())

   for s in bs.findAll(["markov","mirror","filter"]):

      s["style"] = a
      print s
   
#extra = open("make_show/footer.txt").readlines()
#extra = [e.strip() for e in extra]
#for e in extra: print e

# pinning
# 3prcntorig should come first, but pulled out for now and pinned to sound 8 and video 1
# to be mirror always pinned to sound 2
# rogue.xml always pinned to sound 7
# solid.xml always pinned to sound 6
# madoph pinned to sound 8 and video 11


