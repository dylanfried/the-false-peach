import random
import re

def clean(x):

   while re.match("(.*)\ ([.,?!:;]+.*)",x):
      x = re.sub("(.*)\ ([.,?!:;]+.*)","\\1\\2",x)
   x = re.sub("(.*)[.;:,]+","\\1",x)
   return x.strip()

data = open("data/ham.txt").readlines()

pos_context1 = {}
w_context1 = {}

pos_context2 = {}
w_context2 = {}

pos_history = []
w_history = []

pos_table = {}

for d in data:

   d = d.strip()
   flds = d.split(" ")

   speaker = flds[0]
   pos = flds[0]
   w = flds[1]

   if not pos in pos_table: pos_table[pos] = []
   pos_table[pos].append( w)

   pos_history.append(pos)
   w_history.append(w)

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
      print context,w_history[2],len(w_context2[context])
      w_history = w_history[1:]

history = [data[15305].strip(),data[15305+1].strip()]
history = [d.split(" ") for d in history]

out = ""

#print history

for i in range(-15305+15622):

#   pos_history1 = history[1][0]
#
#   if i < 2: 
#
#      newmove = random.sample(pos_context[pos_history1],1)[0]
#      newmove = [newmove,random.sample(pos_table[newmove],1)[0]]

   pos_history2 = history[0][0]+" "+history[1][0]

   w_history2 = history[0][1]+" "+history[1][1]
   w_history1 = history[1][1]

   if pos_history2 in pos_context2: 

      newmove = random.sample(pos_context2[pos_history2],1)[0]
      newmove = [newmove,random.sample(pos_table[newmove],1)[0]]
      out += " "+newmove[1]
      #print newmove

      history.append(newmove)
      history = history[1:]

#   else: 

      

out = clean(out)

#print out   

