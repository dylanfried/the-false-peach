import re
import getopt
import random
from bs4 import BeautifulSoup

from generator import Generator

import sys
sys.path.append("code/")

# This is a client that takes burrito.xml files and interacts
# with the generator to generate a script and the sender to
# send the script. Essentially, it is a translation from discreet
# strategies to the continuous parameter space
# It takes up to three arguments:
#  - The scene config file
#  - The trial config file
#  - The trigger config file

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

      characters = xml_constraints.find("characters")
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
            if data[m][-2]=="SPEAKER" or data[m][-2].upper() in c['pos'] or data[m][-1]=="NEWLINE" and not data[m][-1] in [")","("]: keep.append(1)
            else: keep.append(0)
         else: keep.append(1)

      if keep and max(keep)==0: continue

      trial_data.append(data[m])
   return trial_data

# Helper function
def expand(things):

   out = []

   for t in things:

      if not "-" in t: out.append(t)
      else:
         start = int(re.sub("([0-9]+)\-.*","\\1",t))   
         end = int(re.sub(".*\-([0-9]+)","\\1",t))   
         out += [str(r) for r in range(start,end+1)]

   return out


# Grab the config files
if len(sys.argv)>2:
   trialconfigfile = sys.argv[2]
else:
   trialconfigfile = ""

if len(sys.argv)>3:
   triggerconfigfile = sys.argv[3]
else:
   triggerconfigfile = ""
 
sceneconfigfile = sys.argv[1]
programname = sys.argv[1]
programname = re.sub("^.*\/(.*)\.xml$","\\1",programname)

# hold all of the script generated to then send to loosey
out = []

# Get going with the scene config file
bs = BeautifulSoup(open(sceneconfigfile).read())
#bs = bs.find("trial", recursive=False)
# Grab all the immediate children
for trial in bs.findAll(["markov","mirror","skip","filter","sm_filter"]):
   #print "Trial type:", trial.name
   # Match the strategy name to a set of parameters to pass on to
   # the generator
   # We're going to fill in these variables:
   trial_length = 0
   POS_training_text = []
   POS_order_ramp = []
   POS_emotion_ramp = []
   word_training_text = []
   word_order_ramp = []
   word_emotion_ramp = []
   
   # Grab the data file
   datafile = trial.find("file")
   if datafile:
      datafile = datafile.string
      print datafile
   else: 
      print "No data file"
      continue
   
   # Grab the data from the data file
   data = open(datafile).readlines()
   data = [d.strip() for d in data]
   data = [d.split(" ") for d in data]
   # Make sure the numbers are numbers
   data = [d[:5]+[float(dd) for dd in d[5:10]]+d[10:] for d in data]
   
   #Grab the style from the xml
   style = ""
   if trial.has_key("style"): style = trial["style"]
   trialname = style
   
   if trial.name == "sm_filter":
      print "sm_filter not yet implemented"
      continue
      #lines = get_lines(data, trial.find('train'))
   elif trial.name == "filter":
      print "Filter"
      
      trial_data = get_lines(data, trial.find("train").find("selections").find("selection").find("acts"))
      #get the pattern
      pattern = trial.find("generate").find("pattern")
      if pattern: pattern = pattern.string
      else: pattern = ""
      
      #get the length (number of lines to be output) from the xml.
      length = trial.find("generate").find("length")
      if length: length = int(length.string)
      else: length = 0
      
      # list lines in the training text
      universe = " ".join([d[-1] for d in trial_data])
      universe = re.sub("NEWLINE","\n",universe)
      universe = [u.strip() for u in universe.split("\n")]
      trial_lines = []
      
      for u in universe:
         if re.match("^"+pattern+".*",u,re.IGNORECASE): trial_lines.append(u)

      if length: trial_lines = random.sample(trial_lines,length)
      
      for u in trial_lines:
         # Formatting stuff left over from Mark
         u = re.sub(" NEWLINE \)"," )",u)
         u = re.sub("(oh oh )+"," oh oh ",u)
         u = re.sub("(ho ho )+"," ho ho ",u)
         u = re.sub("(nonny nonny )+"," nonny nonny ",u)
         u = re.sub("(a-down a-down )+"," nonny nonny ",u)
         u = re.sub("( NEWLINE)+"," NEWLINE",u)
         if not out: out.append(u)
         else: out.append(u)
      continue
   elif trial.name == "skip":
      print "skip not yet implemented"
      continue
   elif trial.name == "mirror":
      print "Mirror"
      POS_training_text = get_lines(data, trial.find('generate'))
      #print "POS_training Text", POS_training_text
      POS_order_ramp.append({"order":10, "word_number": 1})
      POS_emotion_ramp = []
      word_training_text = get_lines(data, trial.find('train'))
      word_order_ramp.append({"order":0, "word_number": 1})
      word_emotion_ramp = []
      # Trial length should just be length of POS training text
      trial_length = len(POS_training_text)
   elif trial.name == "markov":
      print "Markov"
      POS_training_text = get_lines(data, trial.find('train'))
      POS_order_ramp.append({"order":-1, "word_number": 1})
      POS_emotion_ramp = []
      word_training_text = get_lines(data, trial.find('train'))
      word_order_ramp.append({"order":int(trial.find("generate").find("k").string), "word_number": 1})
      word_emotion_ramp = []
      trial_length = int(trial.find("generate").find("length").string)
   else:
      print "Bad trial type:",trial.name
      continue
      
   # We've got the params, format the data and send it to the
   # generator
   chunk = {}
   # Check to see if we have the finish_sent config flag
   finish_sentence = trial.find("generate").find("finish_sent")
   if finish_sentence: finish_sentence = finish_sentence.string == "True"
   else: finish_sentence = False
   chunk['finish_sentence'] = finish_sentence
   chunk['chunk_name'] = trialname
   chunk['POS_training_text'] = POS_training_text
   chunk['POS_order_ramp'] = POS_order_ramp
   chunk['POS_emotion_ramp'] = POS_emotion_ramp
   chunk['word_training_text'] = word_training_text
   chunk['word_order_ramp'] = word_order_ramp
   chunk['word_emotion_ramp'] = word_emotion_ramp
   chunk['trial_length'] = trial_length
   chunks = []
   chunks.append(chunk)
   
   gen = Generator(chunks)
   if out:
      out += gen.generate()
   else:
      out = gen.generate()
  
print "Script generated:","\n".join(out)

# Now that we have our output, let's use the Sender to send it
