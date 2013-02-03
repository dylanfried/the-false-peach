import re
import getopt
from bs4 import BeautifulSoup

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
# Grab all the immediate children
for trial in bs.findAll(recursive=False):
   # Match the strategy name to a set of parameters to pass on to
   # the generator
   # We're going to fill in these variables:
   POS_training_text = []
   POS_order_ramp = []
   POS_emotion_ramp = []
   word_training_text = []
   word_order_ramp = []
   word_emotion_ramp = []
   
   if trial.name == "sm_filter":
      
   elif: trial.name == "filter":
      
   elif: trial.name == "skip":
      
   elif: trial.name == "mirror":
      
   elif: trial.name == "markov":
      
   else:
      print "Bad trial type ", trial.name
      
   # We've got the params, format the data and send it to the
   # generator
   chunk = {}
   chunk['POS_training_text'] = POS_training_text
   chunk['POS_order_ramp'] = POS_order_ramp
   chunk['POS_emotion_ramp'] = POS_emotion_ramp
   chunk['word_training_text'] = word_training_text
   chunk['word_order_ramp'] = word_order_ramp
   chunk['word_emotion_ramp'] = word_emotion_ramp
   chunks = []
   chunks.append(chunk)
   gen = Generator(chunks)
   out += gen.generate()

print "Script generated:"
print out

# Now that we have our output, let's use the Sender to send it
