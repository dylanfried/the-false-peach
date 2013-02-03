import re
import getopt
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
            if data[m][nmax-2]=="SPEAKER" or data[m][nmax-2].upper() in c['pos'] or data[m][nmax-1]=="NEWLINE" and not data[m][nmax-1] in [")","("]: keep.append(1)
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
out = ""

# Get going with the scene config file
bs = BeautifulSoup(open(sceneconfigfile).read())
bs = bs.find("trial", recursive=False)
# Grab all the immediate children
for trial in bs.findAll(recursive=False):
   print "Trial type:", trial.name
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
   
   if trial.name == "sm_filter":
      print "sm_filter not yet implemented"
      continue
      #lines = get_lines(data, trial.find('train'))
   elif trial.name == "filter":
      print "filter not yet implemented"
      continue
   elif trial.name == "skip":
      print "skip not yet implemented"
      continue
   elif trial.name == "mirror":
      print "Mirror"
      POS_training_text = get_lines(data, trial.find('train'))
      POS_order_ramp.append({"order":10, "word_number": 1})
      POS_emotion_ramp = []
      word_training_text = get_lines(data, trial.find('generate'))
      word_order_ramp.append({"order":0, "word_number": 1})
      word_emotion_ramp = []
      # Trial length should just be length of POS training text
      trial_length = len(POS_training_text)
   elif trial.name == "markov":
      print "Markov"
      POS_training_text = get_lines(data, trial.find('train'))
      POS_order_ramp.append({"order":0, "word_number": 1})
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
   out += gen.generate()

print "Script generated:"
print out

# Now that we have our output, let's use the Sender to send it
