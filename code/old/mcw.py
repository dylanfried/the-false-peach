import random
import re
import getopt
import sys

opts, args = getopt.getopt(sys.argv[1:], "w")

word = 0
for o, a in opts:
   if o == "-w": word = 1

def clean(x):

   while re.match("(.*)\ ([.,?!:;]+.*)",x):
      x = re.sub("(.*)\ ([.,?!:;]+.*)","\\1\\2",x)
   x = re.sub("(.*)[.;:,]+","\\1",x)
   return x.strip()

data = open("data/ham_unspooled.txt").readlines()
#data = [data[i] for i in range(15305,15622)]

pos_context1 = {}
w_context1 = {}
posw_context1 = {}

pos_context2 = {}
w_context2 = {}
posw_context2 = {}

pos_history = []
w_history = []
posw_history = []

pos_table = {}

for d in data:

   d = d.strip()
   flds = d.split(" ")

   speaker = flds[0]
   pos = flds[1]
   w = flds[2]

   if not pos in pos_table: pos_table[pos] = []
   pos_table[pos].append(w)

   pos_history.append(pos)
   w_history.append(w)
   posw_history.append([pos,w])

   if len(pos_history) > 2: 

      context = pos_history[1]
      if not context in pos_context1: pos_context1[context] = []
      pos_context1[context].append(pos_history[2])

      context = pos_history[0]+" "+pos_history[1]
      if not context in pos_context2: pos_context2[context] = []

      pos_context2[context].append(pos_history[2])
      pos_history = pos_history[1:]

   if len(w_history) > 2: 

      context = w_history[1]
      if not context in w_context1: w_context1[context] = []
      w_context1[context].append(w_history[2])

      context = w_history[0]+" "+w_history[1]
      if not context in w_context2: w_context2[context] = []

      w_context2[context].append(w_history[2])
      w_history = w_history[1:]

   if len(posw_history) > 2:

      context = " ".join(posw_history[1])
      if not context in posw_context1: posw_context1[context] = []
      posw_context1[context].append(posw_history[2])

      context = " ".join(posw_history[0])+" "+" ".join(posw_history[1])
      if not context in posw_context2: posw_context2[context] = []

      posw_context2[context].append(posw_history[2])
      posw_history = posw_history[1:]

history = [data[0].strip(),data[1].strip()]
history = [d.split(" ") for d in history]

out = " ".join([h[2] for h in history])

for i in range(1000):

   pos_history1 = history[1][0]
   w_history1 = history[1][1]

   pos_history2 = history[0][0]+" "+history[1][0]
   w_history2 = history[0][1]+" "+history[1][1]

   if not word:

      if pos_history2 in pos_context2: 
   
         newmove = random.sample(pos_context2[pos_history2],1)[0]
         newmove = [newmove,random.sample(pos_table[newmove],1)[0]]
         if newmove[1]=="NEWLINE": newmove[1] = "\n"
         out += " "+newmove[1]
#         print newmove
   
         history.append(newmove)
         history = history[1:]

   else:

      if w_history2 in w_context2:

         newmove = random.sample(w_context2[w_history2],1)[0]
         newmove = [random.sample([p for p in pos_table if newmove in pos_table[p]],1)[0],newmove]
         if newmove[1]=="NEWLINE": newmove[1] = "\n"
         out += " "+newmove[1]
#         print newmove, len(w_context2[w_history2])

         history.append(newmove)
         history = history[1:]

out = clean(out)

print word
print out   

