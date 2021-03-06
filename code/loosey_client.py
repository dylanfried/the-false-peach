import OSC
from simpleOSC import *
from headless_trigger import headless_trigger
from bs4 import BeautifulSoup
import re
import sys
import time
import random

# Helper function for moving average
def update(e,c,lam=0.8):
   if c > 0: return e*lam+c*(1-lam)
   return e

# This class takes care of SEND the generated script
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
      self.act_number = 0
      self.scroll_end = False
      
      # Remember whether we've left scott's section
      self.left_actor = False
      
      # Remember what style we're currently in
      self.styles = ""
      # Remember what scene we're currently in
      self.scene = ""
      # Remember last speaking character and whether we've left it
      self.last_character = None
      self.changed_speaker = False
      
      # self.play used for keeping track of whether we actually send to loosey or not
      bs = BeautifulSoup(open(trial_config_file).read())
      play = bs.find("sender").find("play")
      if play: self.play = play.string in ["True","true","T","t","yes","Yes"]
      else: self.play = False 
      
      # Keep track of whether there's a word pause or scene pause for this chunk
      self.word_pause = None
      
      # Pull the triggers out of the config file if provided
      if triggers_file:
         trigsall = BeautifulSoup(open(triggers_file).read())
         for triggers in trigsall.findAll("triggers"):
            trigwhat = triggers['stagedir'].strip()
            trigzero = []
            if triggers.has_key("zero_out"): 
               trigzero = triggers['zero_out'].strip().split(",")
            for w in triggers.findAll("word"):
               trigwhen = float(w['pause'].strip())
               trigprio = float(w['priority'].strip())
               trigword = w.string.strip().split(" ")
               trigfan = False
               if w.has_key("fan") and int(w['fan'].strip()) == 1:
                  trigfan = True
               self.trigs.append(headless_trigger(trigwhat,trigword,trigprio,trigwhen,trigzero,trigfan))
      
      # OSC client for SEND messages to Loosey
      if self.play:
         self.sender = OSC.OSCClient()
      
      # OSC server for subscribing to messages from Loosey
      # word function used for handling OSC messages
      def word(addr, tags, stuff, source):
         #print "Word Handler", stuff,"addr",addr,"source",source
         if addr == "/scrollEnd" and stuff == ['end']:
            self.scroll_end = True
         else:
            LooseyClient.next_line[0] = " ".join(stuff)
      if self.play:
         print "Starting OSCServer",self.subscriber_ip, self.subscriber_port
         self.subscriber = OSC.OSCServer((self.subscriber_ip, self.subscriber_port))
         self.subscriber.socket.settimeout(100000)
         # Set handlers for incoming messages
         self.subscriber.addMsgHandler("/synth.word", word)
         self.subscriber.addMsgHandler("/synth.EOL", word)
         self.subscriber.addMsgHandler("/scrollEnd", word)
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
         self.subscribe("subscribe",["JIM./scrollEnd", "ANNIE", 0])
         self.subscribe("subscribe",["GREG./synth.EOL", "ANNIE", 0])
         self.subscribe("subscribe",["ANNIE./stagedir.bool", "ANNIE", -127])
         self.subscribe("subscribe",["GREG./threshold", "ANNIE", -127])
         self.subscribe("subscribe",["JIM./threshold", "ANNIE", -127])
         self.subscribe("subscribe",["LIGHT./threshold", "ANNIE", -127])
         self.subscribe("subscribe",["GREG./affect", "ANNIE", -127])
         self.subscribe("subscribe",["JIM./affect", "ANNIE", -127])
         self.subscribe("subscribe",["LIGHT./affect", "ANNIE", -127])
   
   # Method for subscribing to channels from Loosey
   # Return a 1 on success or 0 on failure
   def subscribe(self,what,value,excess=""):
      #if not self.play:
         #return 1
      #print self.actions
      # Make sure that this is one of our defined actions
      if not what in self.actions: return 0
      #print "SEND", self.actions[what], value, excess
      if not self.play:
         return 1
      # Create and send the actual message
      msg = OSC.OSCMessage()
      msg.setAddress(self.actions[what])
      msg.append(value)
      if excess: msg.append(excess)
      #print "SEND message to Loosey",self.sender_ip, self.sender_port
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

   # Method for SEND a message to Loosey
   # Return a 1 on success or 0 on failure
   def send_value(self,what,value,excess=""):
      # Make sure that this is one of our defined actions
      if not what in self.actions: return 0
      #print "SEND", self.actions[what], value, excess
      if not self.play:
         return 1
      
      # If necessary, zero out any triggers
      for trigger in self.trigs:
         #print "trigger stuff", trigger.zero_out,trigger.triggered,what,trigger.ready_to_zero
         if trigger.zero_out and trigger.triggered and what in trigger.zero_out and trigger.ready_to_zero:
            print "ZEROING OUT", trigger.stage
            # This is a trigger that requires zeroing and has
            # been triggered. Let's zero it out now.
            trigger.triggered = False
            trigger.ready_to_zero = False
            msg = OSC.OSCMessage()
            msg.setAddress(self.actions["stagedir." + trigger.stage])
            msg.append("zero")
            try: self.sender.sendto(msg, (self.sender_ip,self.sender_port))
            except AttributeError as e:
               print "Attribute Error", e
               #print "Attribute Error",e.errno,e.strerror
            except OSC.OSCClientError as e:
               print "OSC Client Error", e
            except: 
               print "Exception when trying to send",sys.exc_info()[0]
      
      # Create and send the actual message
      msg = OSC.OSCMessage()
      msg.setAddress(self.actions[what])
      msg.append(value)
      if excess: msg.append(excess)
      #print "SEND message to Loosey",self.sender_ip, self.sender_port
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
         time.sleep(0.1)
         return "EOL"
      #TODO put something in here that indicates whether we're in Loosey mode or not
      #and manages whether we actually wait for a request
      # Tell the subscriber to handle a message from Loosey
      # TODO: should this be running in parallel?
      #print "handling"
      self.subscriber.handle_request()
      #print "done handling"
      print "Get input", LooseyClient.next_line[0]
      # Return the handled request
      return LooseyClient.next_line[0]
   
   # These two methods are for pulling out the word frequency and scores
   # Mainly used for SEND out metadata across Loosey
   def word_freq(self, w):
      if w in self.freqs: return self.freqs[w]
      else: return 0
   def word_scores(self, w):
      if w in self.emotions: return self.emotions[w]
      else: return [-1,-1,-1,-1]
   
   # Method to send a script
   # The script comes in the form of a list of strings
   # where each element is a line from our script.
   # This method takes care of managing/SEND triggers
   # as well.
   def send_script(self, lines,burrito_word_count=None,act_number=None):
      if act_number and act_number in [1,2,3,4,5]:
         print "\n\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
         print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
         print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
         print "ACT NUMBER OVERRIDE | Act = %d" % act_number
         print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
         print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
         print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n\n"
         self.act_number = act_number
      print "\n\n SEND SCRIPT \n\n"
      # We only want to do beginning of show stuff if we're
      # starting at the beginning of the show
      if self.act_number == 0:
         print "BEGINNING STUFF"
         # First, send beginning text and zeroes:
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
         time.sleep(4.5)
         self.send_value("character","STYLE")
         self.send_value("line","sys.begin(show.generate(" + time.strftime("%d.%m.%y %X" ) + "))\n")
         time.sleep(2.5)
         
         # Wait for Loosey to acknowledge with EOL
         while 1:
            word = self.get_input()
            #print "Getting word",word
            if word == "EOL": 
               break
         
         # Black out video now
         self.send_value("style.video",10)
      
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
      for line_index in range(len(lines)):
         l = lines[line_index]
         # We have extra whitespace, find the next line that has something in it:
         next_line_index = line_index + 1
         last_line = True
         while next_line_index < len(lines):
            if lines[next_line_index].strip() and not re.match(".*====.*",lines[next_line_index]):
               last_line = False
               break
            next_line_index += 1
         current_word_count += len(l.split(" "))
         # Printing out word scores for scrolly thing
         if not self.play and not re.match(".*####.*",l) and not re.match(".*====.*",l) and not re.match(".*@@@@@.*",l):
            to_print = [w + ": " + str(self.word_scores(w)) for w in l.split(" ") if w]
            print ", ".join(to_print)
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
            print "SEND OUTRO"
            self.send_value("outro",2000,name_for_outro)
            time.sleep(2)
            need_outro = False
      
         # Check to see if we're in a new act
         if re.match(".*@@@@@@.*",l):
            self.act_number += 1
            print l
            # We're switching acts, so any zero out trigger should be ready to zero out
            for t in self.trigs:
               if t.triggered and not t.ready_to_zero: t.ready_to_zero = True
            if self.act_number in [3,5]:
               time.sleep(1)
            else:
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
            time.sleep(5)
            self.send_value("character","STYLE")
            self.changed_speaker = True
            time.sleep(0.001)

            # SCROLLY STUFF PRINTING
            #temp_line_index = line_index+1
            #while temp_line_index < len(lines) and not re.match(".*@@@@@@.*",lines[temp_line_index]):
            #   #print lines[temp_line_index]
            #   if re.match("^\s*\(.*\)\s*$",lines[temp_line_index]):
            #      # Stage direction, do some trigger printing
            #      for w in lines[temp_line_index].split(" "):
            #         for t in self.trigs:
            #            if w.lower().strip(" .,;:()[]{}!?") in t.words:
            #               print "TRIGGER:",t.stage,t.words
            #   if not re.match(".*####.*",lines[temp_line_index]) and not re.match(".*====.*",lines[temp_line_index]):
            #      to_print = [w + ": " + str(self.word_scores(w)) for w in lines[temp_line_index].split(" ") if w]
            #      print ", ".join(to_print)
            #   temp_line_index += 1
            #   time.sleep(0.02)
            
            grab_next_style = re.sub(".* (\d+)_([\w\.]+)_(\d+)_(\w+).*","\\1_\\2_\\3_\\4",lines[line_index+1])
            print "SEND SCROLL VALUE",self.act_number
            self.send_value("scrollStart",self.act_number)
            #print "SEND LINE", "Apply style value "+re.sub(".*name:(\w+) .*", "\\1",l)+","+",".join(grab_next_style.split("_"))
            #self.send_value("line","Apply style value "+re.sub(".*name:(\w+) .*", "\\1",l)+","+",".join(grab_next_style.split("_"))+"\n")
            # Wait for Loosey to acknowledge with EOL
            #while 1:
            #   word = self.get_input()
            #   #print "Getting word",word
            #   if word == "EOL": 
            #      current_line_count += 1
            #      break
            while not self.scroll_end and self.play:
               word = self.get_input()
            self.scroll_end = False
            if self.act_number in [3]:
               time.sleep(1)
            continue
         # Check to see if we're in a new scene
         if re.match(".*####.*",l):
            #current_word_count += 2
            # new Scene
            print l
            # Remember the scene
            self.scene = l.split(" ")[2]
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
            # We're switching scenes, so any zero out trigger should be ready to zero out
            for t in self.trigs:
               if t.triggered and not t.ready_to_zero: t.ready_to_zero = True
            # Try to get style info from title
            # Check to see if we have style info in the title
            if re.match(".*_.*",l):
               # we have style info, let's grab it
               styles_string = re.sub(".* (\d+)_([\w\.]+)_(\d+)_(\w+).*","\\1_\\2_\\3_\\4",l)
               if self.styles and re.match(".*TTS\.inear.*",self.styles):
                  # If we're doing a scott scene, sleep a little longer
                  time.sleep(1)
               self.styles = styles_string
               # send the style info again and remember
               # what this scene is
               styles = styles_string.split("_")
               # Send this style info
               # First, clear out the current styles, etc
               # Check whether we have a scene_pause for this chunk
               if not re.match(".*blackout:(\w+).*$",l) or (re.match(".*blackout:(\w+).*$",l) and re.sub(".*blackout:(\w+).*$","\\1",l) not in ["False","false","F","f","No","no"]):
                  # Don't do this sleep after dumb show
                  if self.scene != "partfourtwoB" and self.scene != "FiveTwo" and self.scene != "3pcntORIG":
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
               # Check whether we have a scene_pause for this chunk
               if not re.match(".*blackout:(\w+).*$",l) or (re.match(".*blackout:(\w+).*$",l) and re.sub(".*blackout:(\w+).*$","\\1",l) not in ["False","false","F","f","No","no"]):
                  print "BLACKOUT"
                  self.send_value("style.sound","zero")
                  time.sleep(0.001)
                  self.send_value("style.video",0)
                  time.sleep(0.001)
                  self.send_value("style.actor","zero")
                  time.sleep(0.5)
                  self.send_value("style.lights","zero")
                  # Don't do this sleep after dumb show
                  if self.scene == "partfourtwoB":
                     time.sleep(0.15)
                  elif self.scene == "FiveTwo" or self.scene == "3pcntORIG":
                     time.sleep(0.3)
                  elif self.scene in ["hamsolilddop","2bMirror","deathspeech"]:
                     time.sleep(1.2)
                  else:
                     time.sleep(0.5)
               #else:
               #   # We want to send a partial zero to lights so that we 
               #   # don't get super confused styles
               #   self.send_value("style.lights","partial_zero")
               #   time.sleep(0.3)
               print "SEND STYLES", styles_string
               # Now, actually send the new styles
               self.send_value("style.sound",styles[1])
               time.sleep(0.001)
               self.send_value("style.video",styles[0])
               time.sleep(0.001)
               self.send_value("style.actor",styles[2])
               time.sleep(0.5)
               self.send_value("style.lights",styles[3])
               time.sleep(0.01)
               self.send_value("scene.name",l.split(" ")[2])
               # Check whether we have a scene_pause for this chunk
               if not re.match(".*blackout:(\w+).*$",l) or (re.match(".*blackout:(\w+).*$",l) and re.sub(".*blackout:(\w+).*$","\\1",l) not in ["False","false","F","f","No","no"]):
                  # Don't do this sleep after dumb show
                  if self.scene == "3pcntORIG":
                     time.sleep(0.5)
                  elif self.scene != "partfourtwoB" and self.scene != "FiveTwo" and self.scene != "new_filter":
                     time.sleep(1)
            # Move on to the next line
            continue
            
         # check to see if we're at a new chunk
         elif re.match(".*=====.*",l):
            #current_word_count += len(l.split(" "))
            #print l
            # Check whether we have a word_pause for this chunk
            if re.match(".*word_pause:(\d+).*$",l):
               self.word_pause = int(re.sub(".*word_pause:(\d+).*$","\\1",l))
            else:
               self.word_pause = None
               
            # Check whether we have a scene_pause for this chunk
            if re.match(".*scene_pause:(\d+).*$",l):
               time.sleep(int(re.sub(".*scene_pause:(\d+).*$","\\1",l)))
               
            continue
         # Check to see if this is a character name
         elif re.match("^[A-Z_]+$",l.strip()): 
            #current_word_count += len(l.split(" "))
            # This is a character
            who = l.strip().upper()
            #who = re.sub("_AND_"," ",who)
            #who = re.sub("_and_"," ",who)
            # If we have multiple characters, split them up
            #who = who.split(" ")
      
            # Make sure that we're keeping track of the characters for Loosey metadata
            #for w in who:
            if not who in characters: 
               character_order += 1
               characters[who]=character_order
      
            # Not sure what this does yet
            display = 1
            
            # Send the character
            # If we're in a special Scott/computer mixed scene, and we're at the end of
            # one of Scott's sections, pause
            if self.styles and re.match(".*TTS\.mix.*",self.styles) and self.last_character and self.last_character == "HAMLET" and self.last_character != who:
               print "PAUSING FOR SCOTT"
               time.sleep(0.5)
            self.send_value("character",who)
            print "SEND WHO",who
            self.last_character = who
            self.changed_speaker = False
                  
            # Move on to the next line
            continue
            
         # Check to see if this is an ACT/SCENE title line
         elif re.match("^\s*Act\s.*",l) or re.match("^\s*Act$",l) or re.match("^\s*Scene.*",l): 
            # Don't carry singing/voice stuff over after title
            for t in self.trigs:
               if t.triggered and not t.ready_to_zero: t.ready_to_zero = True
            # Display keeps track of whether to send the word out (probably for video display)
            display = 0
            print "SEND INTRO"
            # This is the TITLE voice
            self.send_value("intro",3000)
            time.sleep(0.001)
            self.send_value("character","STAGEDIR")
            self.changed_speaker = True
            time.sleep(1.8)
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
            # Make sure not to send empty stage directions
            if re.match("^\s*\(\s*\)\s*$",l):
               continue
            # TRIGGER printing for scrolly stuff:
            if not self.play:
               for w in l.split(" "):
                  for t in self.trigs:
                     if w.lower().strip(" .,;:()[]{}!?") in t.words:
                        print "TRIGGER:",t.stage,t.words
            # Pull out the first word in the parentheses
            wwhhaatt = re.sub("^\s*\(\s*([a-zA-Z]+)[.,?!;:]*[\s)].*","\\1",l)
            # Make the line into the line except for the first word in the parentheses
            l = re.sub("^\s*\(\s*[a-zA-Z]+[.,?!;:]*\s*(.*)\)\s*","(\\1)",l)
            # Check again for empty stage directions in case we only had the label
            if re.match("^\s*\(\s*\)\s*$",l):
               continue
            
            # Zero out any trigger besides sings
            for t in self.trigs:
               if t.triggered and not t.ready_to_zero and "sings" not in t.words: t.ready_to_zero = True
            
            # Take care of fan trigger
            if wwhhaatt and self.styles and not re.match(".*TTS\.inear.*",self.styles):
               # Check to see if any "fan" triggers need to be sent now
               for t in self.trigs:
                  #print "TRIGGER THING",t.fan,t.words
                  if t.fan and re.search("[\s,;]+".join(t.words),l,re.IGNORECASE):
                     self.send_value("stagedir."+t.stage,"fan")
                     print "SENDING FAN"
                     break
            
            display = 0
            # Dont want stage directions to run over scott. 
            if self.styles and (re.match(".*TTS\.inear.*",self.styles) or re.match(".*TTS\.mix.*",self.styles)):
               print "Sleeping"
               time.sleep(1)
            # Send the stagedir
            if wwhhaatt == "dumb" or (self.scene == "dumb" and wwhhaatt == "exit"):
               #print "dumb character"
               # Special dumb character that is mute for dumb show
               self.send_value("character","DUMB")
            else:
               #print "stagedir character"
               self.send_value("character","STAGEDIR")
            self.changed_speaker = True
            self.send_value("stagedir.bool",2)
            # Special casing to not have too many parentheses in the dumb show
            if wwhhaatt == "dumb":
               stagedir_to_send = re.sub("^\s*\((.*)\)\s*$","\\1",l)
               #print "original stagedir to send", stagedir_to_send
               #print lines[line_index-1],lines[line_index+1]
               if line_index > 0 and not re.match("^\s*\(\s*dumb\s*[^\s]+.*\)\s*$",lines[line_index-1]):
                  stagedir_to_send = "(" + stagedir_to_send
               if line_index+1 < len(lines) and not re.match("^\s*\(\s*dumb\s*[^\s]+.*\)\s*$",lines[line_index+1]):
                  stagedir_to_send = stagedir_to_send + ")"
               print "Stagedir to send", stagedir_to_send
               self.send_value("stagedir",stagedir_to_send)
            else:
               print "Stagedir",l
               self.send_value("stagedir",l)
            # Pull off the parentheses for reading
            l = re.sub("^\s*\((.*)\)\s*$","\\1",l)
            self.send_value("line",l)
            trigger_label = wwhhaatt
            #print "STAGE",l
            
         # otherwise, this is a normal dialogue line
         else:
            # Don't use the line if it doesn't exist or if it is just parentheses or just whitespace
            # TODO: What happens if there's a paren in the middle of a line?
            if not l or re.match("^\s*$", l) or re.match("^\s*\(\s*$",l) or re.match("^\s*\)\s*$",l): 
               #current_word_count += len(l.split(" "))
               continue
            # If we're entering dialogue again and don't have a speaker, put one in
            if self.last_character and self.changed_speaker:
               print "Entering dialogue, SEND WHO", self.last_character
               self.send_value("character",self.last_character)
               self.changed_speaker = False
            # Send the line
            # If we're in the ham_thing scene, introduce some random pauses between lines
            if self.scene and self.scene in ['ham_thing','newgertrude']:
                random_sleep = random.random()
                sleep_value = 0
                if random_sleep < 0.4:
                    sleep_value = 0
                elif random_sleep < 0.8:
                    sleep_value = 0.3
                else:
                    sleep_value = 0.7
                #print "IN HAM_THING, PAUSE:",sleep_value
                time.sleep(sleep_value)
            self.send_value("stagedir.bool",1)
            self.send_value("line",l)
            # Now that we've actually had some dialogue, we're ready to zero out
            # the voice triggers when the time comes
            for t in self.trigs:
               if t.triggered and not t.ready_to_zero: t.ready_to_zero = True
            print "SEND LINE","%r"%l
      
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
            if trigger_label and self.styles and not re.match(".*TTS\.inear.*",self.styles):
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
                  # Send one of them
                  # For voice triggers, we have a system for zeroing them out
                  # after the next character change, stage dir, etc. Sometimes,
                  # we want to skip a character for zeroing purposes becuase the
                  # stage direction comes right before a character name
                  #if allt[0].zero_out and (line_index+1) < len(lines) and re.match("^[A-Z_]+$",lines[line_index+1].strip()):
                  #   allt[0].skip = ["character"]
                  if self.scene == "MadOph" and allt[0].words[0] == "room":
                     self.send_value("stagedir."+allt[0].stage,"room_ophelia")
                     print "SEND TRIGGER 2", allt[0].stage, "room_ophelia"
                  elif allt[0].words[0] == "exeunt" and \
                        (last_line or \
                           re.match("^\s*Act\s.*",lines[next_line_index]) or \
                           re.match("^\s*Act$",lines[next_line_index]) or \
                           re.match("^\s*Scene.*",lines[next_line_index]) or \
                           re.match(".*####.*",lines[next_line_index]) or \
                           re.match(".*@@@@@@.*",lines[next_line_index])):
                     # This is the last exeunt, we want to send "lastexeunt" so that 
                     # lights knows not to come back up
                     #self.send_value("stagedir."+allt[0].stage,"lastexeunt")
                     print "NOEXEUNT: SEND TRIGGER 2", allt[0].stage, allt[0].words[0]
                  else:
                     self.send_value("stagedir."+allt[0].stage,allt[0].words[0])
                     print "SEND TRIGGER 2", allt[0].stage, allt[0].words[0]
                  # Remember that we're triggering this in case we have to
                  # zero it out later (like for the voice triggers)
                  allt[0].triggered = True
                  allt[0].ready_to_zero = False
                  time.sleep(allt[0].pause/1000.0)
                  # Reset all of the activated triggers
                  for t in tmptrigs:
                     t.reset()
            # If we don't have a trigger_label, then we're not in a stagedir
            # Just go through and reset any triggers that aren't waiting for
            # a number of occurences
            else:
               for t in self.trigs: 
                  t.reset()
      
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
            # Do the same for the value of the max affect
            if ws[mws-1]<0: affmaxval = 0
            else: affmaxval = ws[mws-1]
            
            if ws[0] >= 0:
               # Don't update the average if this word doesn't have a real affect value
               # Keep a weighted moving average to send out
               ewma = [update(ewma[i],ws[i]) for i in range(4)]
            else:
               # Send out default with 0's
               ws = [0 for zero_out in ws]
            # Send out the max affect and value if above a threshold
            if True or (affmax != "joy" and affmaxval > 1.5) or affmaxval > 2.5:
               self.send_value("affmax",affmax)
               self.send_value("affmaxval",float(affmaxval/5.0))
               self.send_value("affvals",[normalize/5 for normalize in ws])
            self.send_value("affsmos",[normalize/5 for normalize in ewma])
            self.send_value("wordfreq",wf)
            if scene_word_count > 0:
               if current_word_count%20 == 0: print "SCENE PROGRESS", round((current_word_count+0.0)/(scene_word_count+0.0), 3)
               self.send_value("scene.progress",round((current_word_count+0.0)/(scene_word_count+0.0), 3))
               
      if self.styles and re.match(".*TTS\.inear.*",self.styles):
         # If we're doing a scott scene, sleep a little longer
         time.sleep(1)
      time.sleep(4)
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
      
      # send ending line
      time.sleep(5)
      self.send_value("character","STYLE")
      self.send_value("line","sys.exit(0)\n")
      time.sleep(6)
      self.send_value("style.video",7)
      self.send_value("style.lights","end")
      
      # Total time info
      total_line_count += current_line_count
      total_word_count += current_word_count
      print "Timing info. Seconds: {0}, words: {1}, lines: {2}\n".format(str(time.time() - total_time), str(total_word_count), str(total_line_count))
      if self.play:
         f = open("timing.txt","a")
         f.write("{0}, {1}, {2}, {3}, {4}\n".format(str(int(time.time() - total_time)), str(total_word_count), str(total_line_count), str(round((time.time() - total_time)/(total_word_count + 0.01), 3)), str(round((time.time() - total_time)/(total_line_count + 0.01), 3))))
         f.close()
