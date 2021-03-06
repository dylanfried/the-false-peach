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
scene_lines = []

# Get going with the scene config file
bs = BeautifulSoup(open(sceneconfigfile).read())
#bs = bs.find("trial", recursive=False)
if not bs.find("scene"):
   # put in the scene tag
   bs = BeautifulSoup("<scene>" + bs.__str__() + "</scene>")
# Grab all the immediate children
for scene in bs.findAll("scene"):
   # Reset the scene line container and word count
   scene_lines = []
   scene_word_count = 0
   for trial in scene.findAll(["markov","mirror","skip","filter","sm_filter"]):
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
         scene_lines.append("=================== CHUNK 1 " + trialname + " ================")
         trial_data = util.get_lines(data, trial.find("train"))
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
               # Check to see if we're forcing a single character
               forced_character = trial.find("forced_character")
               if forced_character:
                  line['speaker'] = forced_character.string
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
            elif re.match("^"+pattern+".*",u['line']):
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
            scene_lines.append(u['speaker'].upper())
            # increment scene_word_count
            scene_word_count += 1
            scene_lines.append(u['line'])
            # increment word count
            scene_word_count += len(scene_lines[-1])
         continue
      elif trial.name == "skip":
         print "skip not yet implemented"
         continue
      elif trial.name == "mirror":
         print "Mirror"
         POS_training_text = util.get_lines(data, trial.find('generate'))
         #print "POS_training Text", POS_training_text
         POS_order_ramp.append({"order":10, "word_number": 1})
         POS_emotion_ramp = []
         word_training_text = util.get_lines(data, trial.find('train'))
         word_order_ramp.append({"order":0, "word_number": 1})
         word_emotion_ramp = []
         # Trial length should just be length of POS training text
         trial_length = len(POS_training_text)
      elif trial.name == "markov":
         print "Markov"
         POS_training_text = util.get_lines(data, trial.find('train'))
         POS_order_ramp.append({"order":-1, "word_number": 1})
         POS_emotion_ramp = []
         word_training_text = util.get_lines(data, trial.find('train'))
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
      # Check to see if we're forcing a single character
      forced_character = trial.find("forced_character")
      if forced_character: forced_character = forced_character.string
      else: forced_character = None
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
      chunk['forced_character'] = forced_character
      chunks = []
      chunks.append(chunk)
      
      gen = Generator(chunks)
      if scene_lines:
         scene_lines += gen.generate()
      else:
         scene_lines = gen.generate()
      # increment word count
      scene_word_count += len(scene_lines[-1])
   # Put scene information in:
   if "name" in scene.attrs and "style" in scene.attrs:
      out.append("################# SCENE " + scene["name"]  + " " + scene["style"] + " wordcount:" + str(sum([len(script_line.split(" ")) for script_line in scene_lines])) + " #################")
   else:
      out.append("################# SCENE wordcount:" + str(sum([len(script_line.split(" ")) for script_line in scene_lines])) + " #################")
   out += scene_lines
  
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
