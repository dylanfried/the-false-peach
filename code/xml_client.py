import re
import getopt
import random
from bs4 import BeautifulSoup

from generator import Generator

import sys
sys.path.append("code/")
import util
from loosey_client import LooseyClient

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
   word_pause = None
   
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
   trialname = ""
   if trial.has_key("style"): style = trial["style"]
   name_tag = trial.find("name")
   if name_tag: trialname += name_tag.string
   trialname += " " + style
   # Check to see if there's a word pause set
   word_pause = trial.find("word_pause")
   if word_pause: trialname += " word_pause:" + word_pause.string
   
   if trial.name == "sm_filter":
      print "sm_filter not yet implemented"
      continue
      #lines = get_lines(data, trial.find('train'))
   elif trial.name == "filter":
      print "Filter"
      out.append("=================== Filter chunk ================")
      trial_data = get_lines(data, trial.find("train"))
      #get the pattern
      pattern = trial.find("generate").find("pattern")
      if pattern: pattern = pattern.string
      else: pattern = ""
      
      #get the length (number of lines to be output) from the xml.
      length = trial.find("generate").find("length")
      if length: length = int(length.string)
      else: length = 0
      
      # list lines in the training text
      # Go through the trial data and break it up into a list of dictionaries
      # where each dictionary has the speaker info and the line spoken
      # This is useful so that we can put speaker information in our filter
      # chunks
      universe = []
      line = {"speaker": "", "line":""}
      for d in trial_data:
         if d[4] != line["speaker"] or d[-1] == "NEWLINE":
            universe.append(line)
            line = {"speaker": d[4], "line":""}
         if d[-1] != "NEWLINE":
            line["line"] += d[-1] + " "
      universe.append(line)
            
      trial_lines = []
      
      # SUPER HACK
      # Loop through all of the lines and check to see if they match the pattern given
      # If they do, keep them
      # Also, this makes sure that we end each line with end of line punctuation
      # We do this by:
      #  - If the line that matches the pattern has any end of line punctuation (?,!,.,;),
      #    then we take the line up to the last of these punctuation marks
      #  - Otherwise, we keep looking onto subsequent lines for punctuation marks
      no_punctuation = False
      for i in range(len(universe)):
         u = universe[i]
         if no_punctuation:
            # Make sure that we haven't switched speakers
            if u['speaker'] != universe[i-1]['speaker']:
               # stop looking for punctuation
               no_punctuation = False
               continue
            # The last line matched the pattern, but didn't have punctuation
            # continue to look for punctuation here
            if re.match("^.*[.!;?].*$", u['line']):
               # We have a punctuation mark in this line, cut
               # off everything after the first punctuation mark
               u['line'] = re.sub("(^.*[.?;!]).*$","\\1",u['line'])
               no_punctuation = False
            trial_lines[-1]['line'] += " " + u['line']
            #trial_lines.append(u)
         # We don't have a previously matching line without punctuation.
         # Check to see if this line matches the pattern
         elif re.match("^"+pattern+".*",u['line'],re.IGNORECASE):
            # Make sure that we end each line with punctuation
            if re.match("^.*[.!;?].*$", u['line']):
               # We have a punctuation mark in this line, cut
               # off everything after the last punctuation mark
               u['line'] = re.sub("(^.*[.?;!])[^.?;!]*$","\\1",u['line'])
            else:
               # We don't have a punctuation mark in this line,
               # continue on to the next line
               no_punctuation = True
            trial_lines.append(u)

      # It's possiblet that there are still some lines without endline punctuation here
      # This could happen because some lines end and change speaker without endline
      # punctuation. Also, make sure that no line is too long.
      trial_lines = [t for t in trial_lines if re.match("^.*[.!;?].*$", t['line']) and len(t['line'].split(" ")) < 30]

      if length and length <= len(trial_lines): 
            trial_lines = random.sample(trial_lines,length)
      
      for u in trial_lines:
         # Formatting stuff left over from Mark
         u['line'] = re.sub(" NEWLINE \)"," )",u['line'])
         u['line'] = re.sub("(oh oh )+"," oh oh ",u['line'])
         u['line'] = re.sub("(ho ho )+"," ho ho ",u['line'])
         u['line'] = re.sub("(nonny nonny )+"," nonny nonny ",u['line'])
         u['line'] = re.sub("(a-down a-down )+"," nonny nonny ",u['line'])
         u['line'] = re.sub("( NEWLINE)+"," NEWLINE",u['line'])
         out.append(u['speaker'].upper())
         out.append(u['line'])
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
      # Check to see if we have an emotion threshold constraint to add
      type_tag = trial.find("generate").find("type")
      if type_tag and type_tag.string == "threshold":
         # Need to create the emotion ramp filter
         ramp_tag = trial.find("generate").find("ramp")
         emotion_list = ["anger","fear","joy","sadness","freq"]
         if ramp_tag and ramp_tag.has_key("emotion") and ramp_tag["emotion"] in emotion_list:
            # Grab the points and interpolate between them to create
            # the emotional ramp to pass in to the generator
            # Keep two arrays to keep track of the value and line
            values = []
            line_numbers = []
            for point in ramp_tag.findAll("point"):
               values.append(float(point['value']))
               line_numbers.append(float(point['line']))
            thresholds = util.interpolate(line_numbers, values, trial_length)
            # Now, let's put this in the correct format for the generator
            emotion_ramp = {}
            emotion_ramp['emotion'] = ramp_tag['emotion']
            emotion_ramp['ramp_list'] = []
            # Loop through the points and add them to the ramp list
            for i in range(len(thresholds)):
               emotion_ramp['ramp_list'].append({'emotion_level':thresholds[i],'word_number':i})
            word_emotion_ramp.append(emotion_ramp)
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
   # Check to see if we have the reset config flag
   # It dictates what to do when you run out of possible words:
   #  - If True: Reset cursor at beginning
   #  - If False or not provided: backoff order all the way to 0 and randomly sample
   reset = trial.find("generate").find("reset")
   if reset: reset = reset.string == "True"
   else: reset = False
   chunk['finish_sentence'] = finish_sentence
   chunk['chunk_name'] = trialname
   chunk['POS_training_text'] = POS_training_text
   chunk['POS_order_ramp'] = POS_order_ramp
   chunk['POS_emotion_ramp'] = POS_emotion_ramp
   chunk['word_training_text'] = word_training_text
   chunk['word_order_ramp'] = word_order_ramp
   chunk['word_emotion_ramp'] = word_emotion_ramp
   chunk['trial_length'] = trial_length
   chunk['word_pause'] = word_pause
   chunk['reset'] = reset
   chunks = []
   chunks.append(chunk)
   
   gen = Generator(chunks)
   if out:
      out += gen.generate()
   else:
      out = gen.generate()
  
print "Script generated:","\n".join(out)

# Now that we have our output, let's use the Sender to send it
bs = BeautifulSoup(open(trialconfigfile).read())
rec = bs.find("receiver")
# Grab sender info
who = rec.find("name")
if who:
   who = who.string.encode('utf-8','ignore')
else: 
   for o in out: print o
sender_ip = rec.find("ip")
if sender_ip:
   sender_ip = sender_ip.string.encode('utf-8','ignore')
else: 
   for o in out: print o
sender_port = rec.find("port")
if sender_port:
   sender_port = int(sender_port.string)
else: 
   for o in out: print o
# Put actions together
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
# Grab subscriber info
sender = bs.find("sender")
my_port = sender.find("port")
if my_port: my_port = int(my_port.string)
else: sys.exit()
my_ip = sender.find("ip")
if my_ip: my_ip = my_ip.string 
else: sys.exit()
# Create Loosey Client
loosey = LooseyClient(who, sender_ip, sender_port, actions, my_ip, my_port, triggerconfigfile, trialconfigfile)
# Send script!
loosey.send_script(out)
