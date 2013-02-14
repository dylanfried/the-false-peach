import OSC
from simpleOSC import *
from headless_trigger import headless_trigger
from bs4 import BeautifulSoup
import re
import sys
import time

# Helper function for moving average
def update(e,c,lam=0.8):
   if c > 0: return e*lam+c*(1-lam)
   return e

# This class takes care of sending the generated script
# via OSC. There are two important things here:
#  - We need to send stuff to Loosey
#  - We need to subscribe to Loosey (at this point to
#    monitor Loosey's rate and only send things when
#    appropriate for timing)
class LooseyClient:
   # Static variable used by subscriber callback to remember the
   # last thing that we received from Loosey
   next_line = [""]
   # Static variable to hold names of emotions
   emos = ["anger","fear","joy","sadness"]
   
   # Constructor
   # Takes care of setting up the sender and subscriber
   def __init__(self, sender_name, sender_ip, sender_port, actions, subscriber_ip, subscriber_port, triggers_file, trial_config_file):
      self.sender_name = sender_name
      self.sender_ip = sender_ip
      self.sender_port = sender_port
      self.actions = actions
      self.subscriber_ip = subscriber_ip
      self.subscriber_port = subscriber_port
      self.trigs = []
      
      # Remember last speaking character and whether we've left it
      self.last_character = None
      self.changed_speaker = False
      
      # self.play used for keeping track of whether we actually send to loosey or not
      bs = BeautifulSoup(open(trial_config_file).read())
      play = bs.find("sender").find("play")
      if play: self.play = play.string in ["True","true","T","t","yes","Yes"]
      else: self.play = False 
      
      # Keep track of whether there's a word pause for this chunk
      self.word_pause = None
      
      # Pull the triggers out of the config file if provided
      if triggers_file:
         trigsall = BeautifulSoup(open(triggers_file).read())
         for triggers in trigsall.findAll("triggers"):
            trigwhat = triggers['stagedir'].strip()
            trigwait = ""
            if triggers.has_key("wait"): 
               trigwait = triggers['wait'].strip()
            for w in triggers.findAll("word"):
               trigwhen = float(w['pause'].strip())
               trigprio = float(w['priority'].strip())
               trigword = w.string.strip().split(" ")
               self.trigs.append(headless_trigger(trigwhat,trigword,trigprio,trigwhen,trigwait))
      
      # OSC client for sending messages to Loosey
      if self.play:
         self.sender = OSC.OSCClient()
      
      # OSC server for subscribing to messages from Loosey
      # word function used for handling OSC messages
      def word(addr, tags, stuff, source):
         #print "Word Handler", stuff
         LooseyClient.next_line[0] = " ".join(stuff)
      if self.play:
         print "Starting OSCServer",self.subscriber_ip, self.subscriber_port
         self.subscriber = OSC.OSCServer((self.subscriber_ip, self.subscriber_port))
         self.subscriber.socket.settimeout(100000)
         # Set handlers for incoming messages
         self.subscriber.addMsgHandler("/synth.word", word)
         self.subscriber.addMsgHandler("/synth.EOL", word)
         self.subscriber.addDefaultHandlers()
      
      # Set up frequency and emotion vars
      freq = open("data/freq.txt").readlines()
      self.freqs = {}
      tot = 0
      for i in range(len(freq)):
         ff = freq[i].strip()
         flds = ff.split(" ")
         self.freqs[flds[1]] = float(flds[0])
         tot += self.freqs[flds[1]]
      for f in self.freqs: self.freqs[f] = round(self.freqs[f]/(tot+0.0),4)
      # Emotions
      emo = open("data/emo.txt").readlines()
      self.emotions = {}
      for i in range(len(emo)):
         flds = emo[i].split(",")
         self.emotions[flds[0]] = [round(float(f),1) for f in flds[1:]]
      
      # Subscribe to channels
      if self.play:
         self.subscribe("subscribe",["GREG./synth.EOL", "ANNIE", 0])
         self.subscribe("subscribe",["ANNIE./stagedir.bool", "ANNIE", -127])
   
   # Method for subscribing to channels from Loosey
   # Return a 1 on success or 0 on failure
   def subscribe(self,what,value,excess=""):
      #if not self.play:
         #return 1
      #print self.actions
      # Make sure that this is one of our defined actions
      if not what in self.actions: return 0
      #print "SENDING", self.actions[what], value, excess
      if not self.play:
         return 1
      # Create and send the actual message
      msg = OSC.OSCMessage()
      msg.setAddress(self.actions[what])
      msg.append(value)
      if excess: msg.append(excess)
      #print "Sending message to Loosey",self.sender_ip, self.sender_port
      try: self.sender.sendto(msg, (self.sender_ip,8110))
      except AttributeError as e:
         print "Attribute Error", e
         #print "Attribute Error",e.errno,e.strerror
      except OSC.OSCClientError as e:
         print "OSC Client Error", e
      except TypeError as e:
         print "Type Error", e
      except: 
         print "Exception when trying to send",sys.exc_info()[0]
         return 0
      # Success!
      return 1

   # Method for sending a message to Loosey
   # Return a 1 on success or 0 on failure
   def send_value(self,what,value,excess=""):
      #if self.word_pause and what == "line":
      #   words = what.split(" ")
      #   msgs = []
      #   for word in words:
      #      if word and not re.match("^\s*$",word):
      #         msg = OSC.OSCMessage()
      #         msg.setAddress(self.actions[what])
      #         msg.append(word)
      #         if excess: msg.append(excess)
      #         msgs.append(msg)
      #else:
      #   msg = OSC.OSCMessage()
      #   msg.setAddress(self.actions[what])
      #   msg.append(value)
      #   if excess: msg.append(excess)
      #   msgs = [msg]
      #
      #for msg in msgs:
      #   #print "Sending message to Loosey",self.sender_ip, self.sender_port
      #   try: self.sender.sendto(msg, (self.sender_ip,self.sender_port))
      #   except AttributeError as e:
      #      print "Attribute Error", e
      #      #print "Attribute Error",e.errno,e.strerror
      #   except OSC.OSCClientError as e:
      #      print "OSC Client Error", e
      #   except: 
      #      print "Exception when trying to send",sys.exc_info()[0]
      #      #return 0
      #   # Success!
      #   #return 1
      #return 1
      #print "In send value what: {0}, value: {1}, excess: {2}".format(what, value, excess)
      #if not self.play:
         #return 1
      #print self.actions
      # Make sure that this is one of our defined actions
      if not what in self.actions: return 0
      #print "SENDING", self.actions[what], value, excess
      if not self.play:
         return 1
      # Create and send the actual message
      msg = OSC.OSCMessage()
      msg.setAddress(self.actions[what])
      msg.append(value)
      if excess: msg.append(excess)
      #print "Sending message to Loosey",self.sender_ip, self.sender_port
      try: self.sender.sendto(msg, (self.sender_ip,self.sender_port))
      except AttributeError as e:
         print "Attribute Error", e
         #print "Attribute Error",e.errno,e.strerror
      except OSC.OSCClientError as e:
         print "OSC Client Error", e
      except: 
         print "Exception when trying to send",sys.exc_info()[0]
         return 0
      # Success!
      return 1
      
   # Method for retrieving what the subscriber has received
   def get_input(self):
      if not self.play:
         time.sleep(1)
         return "EOL"
      #TODO put something in here that indicates whether we're in Loosey mode or not
      #and manages whether we actually wait for a request
      # Tell the subscriber to handle a message from Loosey
      # TODO: should this be running in parallel?
      self.subscriber.handle_request()
      print "Get input", LooseyClient.next_line[0]
      # Return the handled request
      return LooseyClient.next_line[0]
   
   # These two methods are for pulling out the word frequency and scores
   # Mainly used for sending out metadata across Loosey
   def word_freq(self, w):
      if w in self.freqs: return self.freqs[w]
      else: return 0
   def word_scores(self, w):
      if w in self.emotions: return self.emotions[w]
      else: return [-1,-1,-1,-1]
   
   # Method to send a script
   # The script comes in the form of a list of strings
   # where each element is a line from our script.
   # This method takes care of managing/sending triggers
   # as well.
   def send_script(self, lines):
      print "\n\n SENDING SCRIPT \n\n"
      # This is a variable to keep track of a weighted moving
      # average of affect values that we send to Loosey
      ewma = [0,0,0,0]
      #if not self.play:
      #   return
      # Keep track of characters used to send as metadata to Loosey
      characters = {}
      # Keep track of the order of the characters as well
      character_order = 0
      # print "lines", lines
      # Variable to keep track of whether we need an outro from 
      # a scene. This should only be set to True if we have 
      # something with "ACT" or "SCENE" in it
      need_outro = False
      # Variable to keep track of current chunk name in case we have an outro
      # and need to send the name along
      name_for_outro = ""
      # variables to keep track of word count
      scene_word_count = -1
      current_word_count = 0
      total_word_count = 0
      # Variable used to keep track of how long a scene takes
      total_time = time.time()
      start_time = -1
      current_line_count = 0
      total_line_count = 0
      # Loop through all of the lines in the script
      for l in lines:
         current_word_count += len(l.split(" "))
         #print "percent", str(round((current_word_count+0.0)/(scene_word_count+0.0), 3))
         if not l:
            #current_word_count += 1
            continue
            
         # grab the name of the chunk to pass on to the outro if necessary
         if re.match(".*=== CHUNK \d [A-Za-z0-9]+.*",l):
            name_for_outro = re.sub(".*=== CHUNK \d ([A-Za-z0-9]+).*","\\1",l)
            
         # print "lines loop", l
         # trigger_label is used to remember whether we're in a stagedir and
         # need to go through our triggers
         trigger_label = ""
      
         # We need an outro because we're moving into a section
         # after something that had "ACT" or "SCENE"
         if need_outro:
            print "SENDING OUTRO"
            self.send_value("outro",2000,name_for_outro)
            time.sleep(2)
            need_outro = False
      
         # Check to see if we're in a new scene
         if re.match(".*####.*",l):
            #current_word_count += 2
            # new Scene
            print l
            # Print out timing information:
            if start_time != -1:
               print "Timing info. Seconds: {0}, words: {1}, lines: {2}".format(str(time.time() - start_time), str(current_word_count), str(current_line_count))
            start_time = time.time()
            total_line_count += current_line_count
            current_line_count = 0
            # Try to get word count information from title
            total_word_count += current_word_count
            current_word_count = 0
            if re.match(".*wordcount.*", l):
               scene_word_count = int(re.sub(".*wordcount:(\d+).*", "\\1",l))
            else:
               scene_word_count = -1
            # Try to get style info from title
            # Check to see if we have style info in the title
            if re.match(".*_.*",l):
               # we have style info, let's grab it
               styles_string = re.sub(".* (\d+)_([\w\.]+)_(\d+)_(\w+).*","\\1_\\2_\\3_\\4",l)
               # send the style info again and remember
               # what this scene is
               styles = styles_string.split("_")
               # Send this style info
               # First, clear out the current styles, etc
               time.sleep(2)
               self.send_value("stagedir.place","zero")
               time.sleep(0.001)
               self.send_value("stagedir.exit","zero")
               time.sleep(0.001)
               self.send_value("stagedir.entrance","zero")
               time.sleep(0.001)
               self.send_value("stagedir.sound","zero")
               time.sleep(0.001)
               self.send_value("stagedir.voice","zero")
               time.sleep(0.001)
               self.send_value("stagedir.action","zero")
               time.sleep(0.001)
               self.send_value("stagedir.title","zero")
               time.sleep(0.001)
               self.send_value("style.sound","zero")
               time.sleep(0.001)
               self.send_value("style.video",0)
               time.sleep(0.001)
               self.send_value("style.actor","zero")
               time.sleep(0.5)
               self.send_value("style.lights","zero")
               time.sleep(2)
               # Announce the new styles
               self.send_value("character",["STYLE"])
               self.changed_speaker = True
               time.sleep(0.001)
               print "SENDING LINE", "Apply style value "+",".join(styles)
               self.send_value("line","Apply style value "+",".join(styles)+"\n")
               # Wait for Loosey to acknowledge with EOL
               while 1:
                  word = self.get_input()
                  #print "Getting word",word
                  if word == "EOL": 
                     current_line_count += 1
                     break
               print "SENDING STYLES", styles_string
               # Now, actually send the new styles
               time.sleep(2)
               self.send_value("scene.name",l.split(" ")[2])
               time.sleep(0.001)
               self.send_value("style.sound",styles[1])
               time.sleep(0.001)
               self.send_value("style.video",styles[0])
               time.sleep(0.001)
               self.send_value("style.actor",styles[2])
               time.sleep(0.5)
               self.send_value("style.lights",styles[3])
               time.sleep(2)
            # Move on to the next line
            continue
            
         # check to see if we're at a new chunk
         elif re.match(".*=====.*",l):
            #current_word_count += len(l.split(" "))
            print l
            # Check whether we have a word_pause for this chunk
            if re.match(".*word_pause:(\d+).*$",l):
               self.word_pause = int(re.sub(".*word_pause:(\d+).*$","\\1",l))
            else:
               self.word_pause = None
            continue
         # Check to see if this is a character name
         elif re.match("^[A-Z_]+$",l.strip()): 
            #current_word_count += len(l.split(" "))
            # This is a character
            who = l.strip().upper()
            who = re.sub("_AND_"," ",who)
            who = re.sub("_and_"," ",who)
            who = l.strip().upper()
      
            # If we have multiple characters, split them up
            who = who.split(" ")
      
            # Make sure that we're keeping track of the characters for Loosey metadata
            for w in who:
               if not w in characters: 
                  character_order += 1
                  characters[w]=character_order
      
            # Not sure what this does yet
            display = 1
            
            # Send the character
            self.send_value("character",who)
            print "SENDING WHO",who
            self.last_character = who
            self.changed_speaker = False
      
            # Check whether any of triggers need triggering
            for t in self.trigs:
               if t.active():
                  print "SENDING TRIGGER", t.stage, t.words[0]
                  self.send_value("stagedir."+t.stage,t.words[0])
                  time.sleep(t.pause/1000.0)
                  t.reset()
                  
            # Move on to the next line
            continue
            
         # Check to see if this is an ACT/SCENE title line
         elif re.match("^\s*ACT\s.*",l.upper()) or re.match("^\s*SCENE.*",l.upper()): 
            # Display keeps track of whether to send the word out (probably for video display)
            display = 0
            print "SENDING INTRO"
            # This is the TITLE voice
            self.send_value("intro",3000)
            time.sleep(0.001)
            self.send_value("character",["TITLE"])
            self.changed_speaker = True
            time.sleep(3)
            # Send the stage directions
            self.send_value("stagedir.title",l)
            self.send_value("stagedir.bool",0)
            self.send_value("stagedir",l)
            # Also send the stage direction for reading
            self.send_value("line",l)
            print "TITLE",l
            # Need an outro before the next line
            need_outro = True
         # Check to see if this is a stage direction
         elif re.match("^\s*\(.*\)\s*$",l): 
            # Pull out the first word in the parentheses
            wwhhaatt = re.sub("^\s*\(\s*([a-zA-Z]+)\s+.*","\\1",l)
            # Make the line into the line except for the first word in the parentheses
            l = re.sub("^\s*\(\s*[a-zA-Z]+\s+(.*)","(\\1",l)
            display = 0
            # Send the stagedir
            self.send_value("character",["STAGEDIR"])
            self.changed_speaker = True
            self.send_value("stagedir.bool",2)
            self.send_value("stagedir",l)
            # Pull off the parentheses for reading
            l = re.sub("^\s*\((.*)\)\s*$","\\1",l)
            self.send_value("line",l)
            trigger_label = wwhhaatt
            print "STAGE",l
      
         # otherwise, this is a normal dialogue line
         else:
            # Don't use the line if it doesn't exist or if it is just parentheses or just whitespace
            # TODO: What happens if there's a paren in the middle of a line?
            if not l or re.match("^\s*$", l) or re.match("^\s*\(\s*$",l) or re.match("^\s*\)\s*$",l): 
               #current_word_count += len(l.split(" "))
               continue
            # If we're entering dialogue again and don't have a speaker, put one in
            if self.last_character and self.changed_speaker:
               print "Entering dialogue, SENDING WHO", self.last_character
               self.send_value("character",self.last_character)
               self.changed_speaker = False
            # Send the line
            self.send_value("stagedir.bool",1)
            self.send_value("line",l)
            print "SENDING LINE",l
      
         while 1:
            # For each word said, we're going to check whether we need
            # to trigger anything. Additionally, we will send out metadata
            word = self.get_input()
            if word == "EOL": 
               current_line_count += 1
               break
            word = word[2:]
      
            w = word.lower()
            w = re.sub("^(.*),$","\\1",w)
            w = re.sub("^(.*)\.$","\\1",w)
            w = re.sub("^(.*)\?$","\\1",w)
            w = re.sub("^(.*)\!$","\\1",w)
            w = re.sub("^(.*):$","\\1",w)
            w = re.sub("^(.*);$","\\1",w)
            ws = self.word_scores(w)
            wf = self.word_freq(w)
            #current_word_count += 1
      
            # Check to see if we've had a stagedir trigger in this line
            if trigger_label:
               tmptrigs = []
               # Loop through all the triggers and update them with
               # the current word. If they're active now, put them in
               # the list for further processing
               for t in self.trigs:
                  t.update(w)
                  if t.active(): tmptrigs.append(t)
               # If there are any triggers that are ready:
               if tmptrigs:
                  # Find the maximum priority
                  tmppriority = [t.priority for t in tmptrigs]
                  maxpriority = max(tmppriority)
                  # Grab everything with that priority
                  allt = [t for t in tmptrigs if t.priority==maxpriority]
                  print "SENDING TRIGGER 2", allt[0].stage, allt[0].words[0]
                  # Send one of them
                  self.send_value("stagedir."+allt[0].stage,allt[0].words[0])
                  time.sleep(allt[0].pause/1000.0)
                  # Reset all of the activated triggers
                  for t in tmptrigs:
                     if not t.wait: t.reset()
            # If we don't have a trigger_label, then we're not in a stagedir
            # Just go through and reset any triggers that aren't waiting for
            # a number of occurences
            else:
               for t in self.trigs: 
                  if not t.wait: t.reset()
      
            # If display, then we want to put the word out there (for video display I assume)
            # No one is using this, so taking it out
            #if display: self.send_value("word",word)

            # Now, start putting metadata together
            
            # Grab the indices of the emotions that have the max affect value
            mws = [i for i in range(4) if ws[i]==max(ws)][0]+1
            # iF the max is less than 0, then we don't have a max affect value
            if ws[mws-1]<0: affmax = "neutral"
            # Otherwise, we have a max affect 
            else: affmax = LooseyClient.emos[mws-1]
            # Send out the max affect
            self.send_value("affmax",affmax)
            # Do the same for the value of the max affect
            if ws[mws-1]<0: affmaxval = 0
            else: affmaxval = ws[mws-1]
            self.send_value("affmaxval",float(affmaxval/5.0))
            if ws[0] >= 0:
               # Don't update the average if this word doesn't have a real affect value
               # Keep a weighted moving average to send out
               ewma = [update(ewma[i],ws[i]) for i in range(4)]
            else:
               # Send out default with 0's
               ws = [0 for zero_out in ws]
            self.send_value("affvals",[normalize/5 for normalize in ws])
            self.send_value("affsmos",[normalize/5 for normalize in ewma])
            self.send_value("wordfreq",wf)
            if scene_word_count > 0:
               self.send_value("scene.progress",round((current_word_count+0.0)/(scene_word_count+0.0), 3))
      time.sleep(2)
      self.send_value("stagedir.place","zero")
      time.sleep(0.001)
      self.send_value("stagedir.exit","zero")
      time.sleep(0.001)
      self.send_value("stagedir.entrance","zero")
      time.sleep(0.001)
      self.send_value("stagedir.sound","zero")
      time.sleep(0.001)
      self.send_value("stagedir.voice","zero")
      time.sleep(0.001)
      self.send_value("stagedir.action","zero")
      time.sleep(0.001)
      self.send_value("stagedir.title","zero")
      time.sleep(0.001)
      self.send_value("style.sound","zero")
      time.sleep(0.001)
      self.send_value("style.video",0)
      time.sleep(0.001)
      self.send_value("style.actor","zero")
      time.sleep(0.5)
      self.send_value("style.lights","zero")
      
      # Total time info
      total_line_count += current_line_count
      total_word_count += current_word_count
      print "Timing info. Seconds: {0}, words: {1}, lines: {2}\n".format(str(time.time() - total_time), str(total_word_count), str(total_line_count))
      if self.play:
         f = open("timing.txt","a")
         f.write("{0}, {1}, {2}, {3}, {4}\n".format(str(int(time.time() - total_time)), str(total_word_count), str(total_line_count), str(round((time.time() - total_time)/(total_word_count + 0.01), 3)), str(round((time.time() - total_time)/(total_line_count + 0.01), 3))))
         f.close()
