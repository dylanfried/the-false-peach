import re
import getopt
import random
from bs4 import BeautifulSoup

from generator import Generator

import sys
sys.path.append("code/")
import util
from loosey_client import LooseyClient

# Grab the config files
if len(sys.argv)>2:
   trialconfigfile = sys.argv[2]
else:
   trialconfigfile = ""

if len(sys.argv)>3:
   triggerconfigfile = sys.argv[3]
else:
   triggerconfigfile = ""
 
if len(sys.argv)>4:
   act_number = int(sys.argv[4])
else:
   act_number = 0
sceneconfigfile = sys.argv[1]
programname = sys.argv[1]
programname = re.sub("^.*\/(.*)\.xml$","\\1",programname)

# hold all of the script generated to then send to loosey
out = []

# Get going with the scene config file
text = open(sceneconfigfile).read()
print "text",text
out = text.split("\n")
  
print "Script generated:","\n".join(out)

# Get total count:
burrito_word_count = 0
for l in re.findall(".*wordcount.*",text):
   burrito_word_count += int(re.sub(".*wordcount:(\d+).*","\\1",l))

print burrito_word_count

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
loosey.send_script(out,burrito_word_count=burrito_word_count,act_number=act_number)
