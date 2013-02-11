import re
# This file houses useful functions that may be used in many
# places

# Function for making a smooth curve
# For instance, this is used to make a smooth
# line for thresholding emotional values
# Params:
#  - x: x points
#  - y: corresponding y points
#  - m: maximum x-value to go out to
# Returns: An array of length m with, where the index is
#          the x value and the value is the y value
def interpolate(x,y,m):
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
   

# Helper function for expanding number ranges (eg, 20-24)
def expand(things):
   out = []
   for t in things:
      if not "-" in t: out.append(t)
      else:
         start = int(re.sub("([0-9]+)\-.*","\\1",t))   
         end = int(re.sub(".*\-([0-9]+)","\\1",t))   
         out += [str(r) for r in range(start,end+1)]
   return out

# Helper function for pulling lines of the play out based
# on XML constraints in a trial
def get_lines(data, xml_constraints):
   trial_data = []
   constraints = []
   selections = xml_constraints.find("selections")

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
         
         words = selection.find("words")
         if words: 
            words = words.string
            words = expand(words.split(","))
         else: words=[]
      
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

         constraints.append({"acts":acts,"scenes":scenes,"lines":lines,"words":words,"characters":characters,"pos":pos})

   else:
      # Only a single constraint
      acts = xml_constraints.find("acts")
      if acts:
         acts = acts.string
         acts = expand(acts.split(","))
      else: acts=[]

      scenes = xml_constraints.find("scenes")
      if scenes:
         scenes = scenes.string
         scenes = expand(scenes.split(","))
      else: scenes=[]

      lines = xml_constraints.find("lines")
      if lines:
         lines = lines.string
         lines = expand(lines.split(","))
      else: lines=[]
      
      words = xml_constraints.find("words")
      if words: 
         words = words.string
         words = expand(words.split(","))
      else: words=[]

      characters = xml_constraints.find("characters")
      if characters:
         characters = characters.string
         characters = characters.split(",")
         characters = [c.strip() for c in characters]
         characters = [re.sub(" ","_",c.upper()) for c in characters]
      else: characters=[]

      constraints.append({"acts":acts,"scenes":scenes,"lines":lines,"words":words,"characters":characters})

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
            
         if c["words"] and (not data[m][3] in c["words"]): 
            keep.append(0)
            continue

         if c["characters"] and (not data[m][4].upper() in c["characters"]): 
            keep.append(0)
            continue

         if 'pos' in c and c['pos']:
            if data[m][-2]=="SPEAKER" or data[m][-2].upper() in c['pos'] or data[m][-1]=="NEWLINE" and not data[m][-1] in [")","("]: keep.append(1)
            else: keep.append(0)
         else: keep.append(1)

      if keep and max(keep)==0: continue

      trial_data.append(data[m])
   return trial_data
