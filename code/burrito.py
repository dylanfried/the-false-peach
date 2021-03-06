from bs4 import BeautifulSoup
import sys
sys.path.append("code/")
import util
from transition_logic import TransitionLogic
from random_transition import RandomTransition
from scene import Scene
from loosey_client import LooseyClient
from generator import Generator
from pinning_table import PinningTable
from markov import Markov
import re
import random
import os
import copy
import uuid

# This class will take care of making a show!
class Burrito:
   def __init__(self,show_file,pinnings_file,trial_file,triggers_file, transition_logic):
      self.sequences = BeautifulSoup(open(show_file).read()).findAll("sequence")
      # Let's go through and find all the prescribed scenes so that we make sure
      # not to sample them in the random sequences
      self.prescribed_scenes = []
      for sequence in self.sequences:
         if "random" not in sequence.attrs or sequence["random"] not in ["True","true","t","T","yes","Yes"]:
            for scene in sequence.findAll("scene"):
               self.prescribed_scenes.append(scene.string)
      self.triggers_file = triggers_file
      self.trial_file = trial_file
      
      # Transition logic object
      self.transition_logic = transition_logic
      
      # Pinnings object initialization
      self.pinning_table = PinningTable(pinnings_file)
      
      # Keep track of the generated scenes
      self.scenes = []
      
      # Grab all the Loosey info out of the trial file
      # and prepare the Loosey Client
      bs = BeautifulSoup(open(self.trial_file).read())
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
      self.loosey = LooseyClient(who, sender_ip, sender_port, actions, my_ip, my_port, self.triggers_file, self.trial_file)
      
   def create_script(self):
      for sequence in self.sequences:
         # First, let's put in a "scene" that is the sequence title
         if "name" in sequence.attrs and sequence["name"]:
            act_name = sequence["name"]
         else:
            act_name = "default"
         act_title = "@@@@@@@@@@@@@@@ Act name:" + act_name + " @@@@@@@@@@@@@@@@"
         added_title = False
         # This can either be a prescribed sequence of scenes
         # or a set of random scenes
         if "random" in sequence.attrs and sequence["random"] in ["True","true","t","T","yes","Yes"]:
            # if no length tag is specified we want to do output a script with 
            # every chunk in that is specified but in a random order.
            # else we we check the length...
            if not sequence.find("length"):
               # This is a random sequence of scenes
               length = len(sequence.findAll("scene_choice"))
               iterations = 0
               scene_choices = []
               if sequence.find("scene_choices"):
                  # Specific scene choices given
                  for scene_choice in sequence.findAll("scene_choice"):
                     scene_choices.append(scene_choice.string)
               else:
                   print "Error: Need length parameter or a scene choice."
               while length > iterations:
                  # Get next scene as a function of past feature
                  # vectors and available scene choices
                  next_scene = self.transition_logic.next_scene([s.feature_vector for s in self.scenes], scene_choices)
                  if added_title:
                     self.scenes.append(self.create_scene(next_scene))
                  else:
                     self.scenes.append(self.create_scene(next_scene))
                     self.scenes[-1].script = [act_title] + self.scenes[-1].script
                     added_title = True
                  iterations += 1
            else:
               # This is a random sequence of scenes
               length = int(sequence.find("length").string)
               words_generated = 0
               iterations = 0
               scene_choices = []
               if sequence.find("scene_choices"):
                  # Specific scene choices given
                  for scene_choice in sequence.findAll("scene_choice"):
                     if scene_choice not in self.prescribed_scenes:
                        scene_choices.append(scene_choice.string)
               else:
                  # Grab all the scenes from the SHOW dir
                  scene_choices = [l for l in os.listdir("config/SHOW/") if re.match(".*\.xml$",l) and not re.match(".*trigger.*",l) and l not in self.prescribed_scenes]
               # keep going until we get enough stuff
               while words_generated < length:
                  # Don't go too long
                  if iterations > 50: break
                  # Get next scene as a function of past feature
                  # vectors and available scene choices
                  next_scene = self.transition_logic.next_scene([s.feature_vector for s in self.scenes], scene_choices)
                  if added_title:
                     self.scenes.append(self.create_scene(next_scene))
                  else:
                     self.scenes.append(self.create_scene(next_scene))
                     self.scenes[-1].script = [act_title] + self.scenes[-1].script
                     added_title = True
                  words_generated += self.scenes[-1].length
                  iterations += 1
         else:
            # This is a prescribed sequence
            for scene in sequence.findAll("scene"):
               if added_title:
                  self.scenes.append(self.create_scene(scene.string))
               else:
                  self.scenes.append(self.create_scene(scene.string))
                  self.scenes[-1].script = [act_title] + self.scenes[-1].script
                  added_title = True
      # Print out script
      for s in self.scenes:
         print "\n".join(s.script)
      # Print out summary of burrito:
      print "\n----------------------"
      print "Burrito summary"
      print "Total word count:", sum([s.length for s in self.scenes])
      print "\n".join([(s.script[0] if re.match(".*########.*",s.script[0]) else s.script[0] + "\n" + s.script[1]) for s in self.scenes])
      print "----------------------"
            
   def send_script(self):
      # Loop through the scenes and create the script in its entirety
      out = []
      for scene in self.scenes:
         out += scene.script
      self.loosey.send_script(out,burrito_word_count=sum([s.length for s in self.scenes]))
   
   # Method for generating a single scene
   # Returns a scene object
   def create_scene(self, scene_name):
      # Special handling for play within a play:
      # We want to replace the text with the text from another scene
      playwithin = False
      if scene_name == "playwithin.xml":
         playwithin = True
         scene_choices = [l for l in os.listdir("config/SHOW/") if re.match(".*\.xml$",l) and not re.match(".*trigger.*",l) and l not in self.prescribed_scenes]
         scene_name = self.transition_logic.next_scene([s.feature_vector for s in self.scenes], scene_choices)
      # Get going with the scene config file
      bs = BeautifulSoup(open("config/SHOW/" + scene_name).read())
      scene_name = re.sub("^(.*)\.xml$", "\\1", scene_name)
      if not bs.find("scene"):
         # put in the scene tag
         bs = BeautifulSoup("<scene>" + bs.__str__() + "</scene>")
      scene = bs.find("scene")
      scene["name"] = scene_name
      scene["style"] = self.pinning_table.generate_style(scene_name)
      scene['strategy'] = ""
      # Reset the scene line container and word count
      scene_lines = []
      # Remember characters across chunks within a scene
      current_characters = []
      if scene.find('characters_on_stage'):
         current_characters = scene.find('characters_on_stage').string.split(",")
      if scene_name == "hamsolilddop" and os.path.exists('data/hamsolilddop.txt'):
         # This takes too long to generate, just grab file
         scene_lines += [line.strip() for line in open('data/hamsolilddop.txt')]
         scene['strategy'] = "ddop"
      else:
         for trial in scene.findAll(["markov","mirror","skip","filter","sm_filter","letter_markov","ddop","straightdo","read_xml","rhythm_filter","new_filter"]):
            if not scene['strategy']:
               scene['strategy'] = trial.name
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
               #print datafile
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
            # Check to see if there's a scene pause set
            scene_pause = trial.find("scene_pause")
            if scene_pause: trialname += " scene_pause:" + scene_pause.string
            
            if trial.name == "sm_filter":
               print "sm_filter not yet implemented"
               continue
               #lines = get_lines(data, trial.find('train'))
            elif trial.name == "read_xml":
               scene_lines.append("=================== CHUNK 1 " + trialname + " ================")
               file_to_read = trial.find("xml_file")
               if file_to_read:
                  file_to_read = file_to_read.string
               else:
                  print "No XML file specified"
                  continue
               
               #file_to_read = BeautifulSoup(open(file_to_read).read())
               file_to_read = open(file_to_read).readlines()
               for line in file_to_read:
                  scene_lines.append(line.rstrip())
               continue
            elif trial.name == "letter_markov":
               scene_lines.append("=================== CHUNK 1 " + trialname + " ================")
               trial_data = util.get_lines(data, trial.find("train"))
               
               # Let's break up this text into letters for markoving
               markov_data = []
               stagedir = None
               for word in trial_data:
                  if word[-1] == "NEWLINE" or word[-2] == "SPEAKER":
                     # If we've been tracking a stagedir, it's over now
                     if stagedir:
                        # Don't let stage dirs be too long
                        if len(stagedir[-1]) < 22:
                           markov_data.append(stagedir)
                        stagedir = None
                     # want to keep words and speakers intact
                     #word[-1] = " " + word[-1] + " "
                     markov_data.append(word)
                  elif word[4] == "Stage":
                     # Keep stage dirs intact
                     if not stagedir:
                        stagedir = word
                     else:
                        stagedir[-1] += " " + word[-1]
                  else:
                     # break everything else up character by character
                     for letter in list(word[-1]):
                        new_letter = word[:]
                        new_letter[-1] = letter
                        markov_data.append(new_letter)
                     new_space = word[:]
                     # Maybe we don't want spaces after the last word?
                     new_space[-1] = " "
                     markov_data.append(new_space)
   
               if trial.find("generate").find("k"):
                  letter_markov_order = int(trial.find("generate").find("k").string)
               else:
                  letter_markov_order = 2
               
               letter_markov = Markov(markov_data, letter_markov_order, 12, False)
               letter_markov.initialize()
               
               text = ""
               length = trial.find("generate").find("length")
               if length: length = int(length.string)
               else: length = 0
               markov_letter_line_length = 0
               for i in range(length):
                  temp = letter_markov.generateNext(letter_markov_order,[])[-1]
                  if temp == "NEWLINE":
                     markov_letter_line_length = 0
                  elif markov_letter_line_length > 22:
                     text += "NEWLINE"
                     markov_letter_line_length = 0
                  elif temp == " ":
                     markov_letter_line_length += 1
                  text += temp
               
               for l in text.split("NEWLINE"):
                  # Formatting stuff left over from Mark
                  l = re.sub(" NEWLINE \)"," )",l)
                  l = re.sub("(oh oh )+"," oh oh ",l)
                  l = re.sub("(ho ho )+"," ho ho ",l)
                  l = re.sub("(nonny nonny )+"," nonny nonny ",l)
                  l = re.sub("(a-down a-down )+"," nonny nonny ",l)
                  l = re.sub("( NEWLINE)+"," NEWLINE",l)
                  # Get rid of quotation marks
                  l = re.sub("\"\s*","",l)
                  # Get rid of spaces before punctuation
                  l = re.sub("\s*([,.?!:;)])","\\1",l)
                  scene_lines.append(l)
               
               continue
            elif trial.name == "ddop":
               scene_lines.append("=================== CHUNK 1 " + trialname + " ================")
               acts = []
               scenes = []
               lines = []
               arg_name = []
               if trial.find("selections"):
                  for selection in trial.findAll("selection"):
                     arg_name += ["-a","-s","-l"]
                     arg_val=[]
                     if selection.find("acts"): 
                        arg_val.append(selection.find("acts").string)
                     else:
                        arg_val.append("")
                     if selection.find("scenes"): 
                        arg_val.append(selection.find("scenes").string)
                     else:
                        arg_val.append("")
                     if selection.find("lines"): 
                        arg_val.append(selection.find("lines").string)
                     else:
                        arg_val.append("")
               opts = []
               for i in range(len(arg_name)):
                  if arg_val[i]:
                     tup = arg_name[i], arg_val[i]
                     opts.append(tup)
               acts = []
               scenes = []
               lines = []
               characters = []
               for o, a in opts:
                  if o == "-a":
                     if "-" in a:
                        a = a.split("-")
                        acts += range(int(a[0]),int(a[1])+1)
                     else: acts += [int(a)]
                     #if len(acts)>1: break
                  elif o == "-s":
                     if "-" in a:
                        a = a.split("-")
                        scenes = range(int(a[0]),int(a[1])+1)
                     else: scenes = [int(a)]
                     #if len(scenes)>1: break
                  elif o == "-l":
                     if "-" in a:
                        a = a.split("-")
                        lines = range(int(a[0]),int(a[1])+1)
                     else: lines = [int(a)]
                  else:
                     assert False, "unhandled option"
               if trial.find("characters"):
                  characters = trial.find("characters").string.split(",")
               def clean(x):
               
                  while re.match("(.*)\ ([-.,?!:;)]+.*)",x):
                     x = re.sub("(.*)\ ([-.,?!:;)]+.*)","\\1\\2",x)
               
                  while re.match("(.*)\( (.*)",x):
                     x = re.sub("(.*)\( (.*)","\\1 (\\2",x)
               
                  return x.strip()
               
               x = open("data/ndata2.txt").readlines()
               #x = [d.strip() for d in x]
               #x = [d.split(" ") for d in x]
               #x = util.get_lines(x, trial.find("train"))
               
               #print x
               
               ACT = [int(a.split(" ")[0]) for a in x]
               SCENE = [int(a.split(" ")[1]) for a in x]
               LINE = [int(a.split(" ")[2]) for a in x]
               c = [a.split(" ")[3] for a in x]
               p = [a.split(" ")[4] for a in x]
               w = [a.split(" ")[5].strip() for a in x]
               
               #ACT = [int(a[0]) for a in x]
               #SCENE = [int(a[1]) for a in x]
               #LINE = [int(a[2]) for a in x]
               #c = [a[3] for a in x]
               #p = [a[4] for a in x]
               #w = [a[5].strip() for a in x]
               
               counts = {}
               history = []
               speaker = ""
               
               for i in range(len(c)):
               
                  if c[i] == speaker:
               
                     history.append(p[i])
                  
                     if len(history) == 4: history = history[1:]
               
                     if len(history)==3:    
                  
                        if not c[i] in counts: counts[c[i]] = {}
               
                        k = " ".join(history)  
                        if not k in counts[c[i]]: counts[c[i]][k] = 0
                        counts[c[i]][k] += 1
               
                  else: history = [p[i]]
                  speaker = c[i]
               
               for speaker in counts:
                  ss = sum(counts[speaker].values())
                  bbf = counts[speaker].values()
                  for kk in counts[speaker]: 
                     counts[speaker][kk] = sum([xxx for xxx in bbf if xxx < counts[speaker][kk]])/(ss+0.0)
               history = []
               whistory = []
               speaker = ""
               spoke = ""
               pspoke = ""
               
               for i in range(len(c)):
   
                  if acts and not ACT[i] in acts: continue
                  if scenes and not SCENE[i] in scenes: continue
                  if lines and not LINE[i] in lines: continue
                  #print "character check", characters, c[i].upper()
                  if characters and not c[i].upper() in characters: continue
               
                  if c[i] == speaker:
               
                     history.append(p[i])
                     whistory.append(w[i])
               
                     if len(history) == 4: 
               
                        history = history[1:]
                        whistory = whistory[1:]
               
                     if len(history)==3:
               
                        k = " ".join(history)
                        bbbb = 1
                        if re.match("^\W (.*)$",k): bbbb=0
                        kk = " ".join(whistory)
                        kk = re.sub("^\W (.*)$","\\1",kk)
                        kk = re.sub("^(.*) \W$","\\1",kk)
               
                        if k in counts[c[i]].keys() and counts[c[i]][k] > 0.92: 
               
                           if not spoke and not pspoke == c[i]: 
               
                              scene_lines.append(c[i].upper())
                              spoke = 1
                              pspoke = c[i]
               
                           tmpaa = clean(kk)
                           #print tmpaa[0].capitalize()+tmpaa[1:]
                           line = tmpaa[0].capitalize()+tmpaa[1:]
                           # Formatting stuff left over from Mark
                           line = re.sub(" NEWLINE \)"," )",line)
                           line = re.sub("(oh oh )+"," oh oh ",line)
                           line = re.sub("(ho ho )+"," ho ho ",line)
                           line = re.sub("(nonny nonny )+"," nonny nonny ",line)
                           line = re.sub("(a-down a-down )+"," nonny nonny ",line)
                           line = re.sub("( NEWLINE)+"," NEWLINE",line)
                           # Get rid of quotation marks
                           line = re.sub("\"\s*","",line)
                           # Get rid of spaces before punctuation
                           line = re.sub("\s*([,.?!:;)])","\\1",line)
                           # if there's a stage direction, put it in
                           scene_lines.append(line)
               
                  else: 
               
                     history = [p[i]]
                     whistory = [w[i]]
                     spoke = ""
               
                  speaker = c[i]
               continue
            elif trial.name == "straightdo":
               scene_lines.append("=================== CHUNK 1 " + trialname + " ================")
               x = open("data/ndata4.txt").readlines()
               
               # Check to see if we have a character spec
               if trial.find("characters"):
                  character_constraints = trial.find("characters").string.split(",")
                  character_constraints = [character_constraint.upper() for character_constraint in character_constraints]
                  # Make sure that we only use data from x if it's from the correct character
                  x = [line for line in x if line.split(" ")[3].upper() in character_constraints]
               
               ACT = [int(a.split(" ")[0]) for a in x]
               SCENE = [int(a.split(" ")[1]) for a in x]
               LINE = [int(a.split(" ")[2]) for a in x]
               c = [a.split(" ")[3] for a in x]
               p = [a.split(" ")[4] for a in x]
               w = [re.sub("\\\\n","\n",a.split(" ")[5].strip()) for a in x]
               
               start = random.sample(range(len(p)),1)[0]
               while SCENE[start-1]==SCENE[start]: start -= 1
               while LINE[start-1]==LINE[start]: start -= 1
               
               N = 1000
               
               if trial.find("length") and trial.find("length").string:
                  N = int(trial.find("length").string)
               
               act = 0
               mark_scene = 0
            
               opts = []
               arg_names=["-a","-s"]
               arg_val=[]
               if trial.find("acts"):
                  arg_val.append(trial.find("acts").string)
               else:
                  arg_val.append("")
                  
               if trial.find("scenes"):
                  arg_val.append(trial.find("scenes").string)
               else:
                  arg_val.append("")
                  
               for i in range(len(arg_names)):
                  if arg_val[i]:
                     tup = arg_names[i], arg_val[i]
                     opts.append(tup)
               for o, a in opts:
            
                  if o == "-a":
                     act = int(a)
                  elif o == "-s":
                     mark_scene = int(a)
                  elif o == "-n":
                     N = int(n)
                  else:
                      assert False, "unhandled option"
               
               if act and not mark_scene: mark_scene = 1
               if act and mark_scene:
            
                  start = min([i for i in range(len(p)) if act==ACT[i] and mark_scene==SCENE[i]])
            
               
               def clean(x):
               
                  x = re.sub("^\W+ (.*)$","\\1",x,re.S,re.MULTILINE)
                  x = re.sub("^\W+(.*)$","\\1",x,re.S,re.MULTILINE)
               
                  while re.match("(.*)\n (.*)",x,re.S):
                     x = re.sub("(.*)\n (.*)","\\1\n\\2",x,re.S)
               
                  while re.match("(.*) ([-.,?!:;)]+.*)",x,re.S):
                     x = re.sub("(.*) ([-.,?!:;)]+.*)","\\1\\2",x,re.S)
               
                  while re.match("(.*)\( (.*)",x,re.S):
                     x = re.sub("(.*)\( (.*)","\\1 (\\2",x,re.S)
               
                  x = re.sub('"','',x)
                  x = re.sub("(.*)\n$","\\1",x)
                  return x
               
               COUNTER = start
               pstart = p[COUNTER]
               wstart = w[COUNTER]
               cstart = c[COUNTER]
               tailspeaker = cstart
               
               COUNTER += 1
               pcurrent = [pstart,p[COUNTER]]
               wcurrent = [wstart,w[COUNTER]]
               ccurrent = [cstart,c[COUNTER]]
               
               out = " ".join(wcurrent)
               cout = " ".join(ccurrent)
               for ii in range(N):
               
                  COUNTER += 1
                  ppatt = [pcurrent[0],pcurrent[1],p[COUNTER]]
                  wpatt = [wcurrent[0],wcurrent[1],w[COUNTER]]
                  pcurrent = [pcurrent[1],p[COUNTER]]
                  wcurrent = [wcurrent[1],w[COUNTER]]
                  ccurrent = [ccurrent[1],c[COUNTER]]
               
                  out += " "+wcurrent[1]
                  cout += " "+ccurrent[1]
               
                  pcnt = [[w[i-2],w[i-1],w[i]] for i in range(3,len(w)) if p[i] == ppatt[2] and 
                              p[i-1]==ppatt[1] and p[i-2]==ppatt[0]]
                  ccnt = [[c[i-2],c[i-1],c[i]] for i in range(3,len(w)) if p[i] == ppatt[2] and 
                              p[i-1]==ppatt[1] and p[i-2]==ppatt[0]]
                  icnt = [[i-2,i-1,i] for i in range(3,len(w)) if p[i] == ppatt[2] and 
                              p[i-1]==ppatt[1] and p[i-2]==ppatt[0]]
               
                  iii = int(len(pcnt)**0.5-7.0)
                  if range(iii) and len(out.split(" "))>5: 
                     WORDS = out.split(" ")
                     CHARS = cout.split(" ")
               
                     RWORDS = WORDS[0]
                     RCHARS = CHARS[0]
               
                     for i in range(1,len(WORDS)):
               
                        if RCHARS == CHARS[i]: RWORDS += " "+WORDS[i]
                        else:
               
                           #char = RCHARS.upper()+"\n"
                           #line = clean(RWORDS)+"\n\n
                           scene_lines.append(RCHARS.upper())
                           scene_lines.append(clean(RWORDS))
   
                           RCHARS = CHARS[i]
                           RWORDS = WORDS[i]
                     #char = RCHARS.upper()+"\n"
                     #line = clean(RWORDS)+"\n\n"
                     scene_lines.append(RCHARS.upper())
                     scene_lines.append(clean(RWORDS))
                     
               
                     cccc = random.sample(range(len(pcnt)),iii)
               
                     ppcnt =[" ".join(aaa) for aaa in [pcnt[aaaa] for aaaa in cccc]]
                     cpcnt =[" ".join(aaa) for aaa in [ccnt[aaaa] for aaaa in cccc]]
                     COUNTER =[icnt[aaaa] for aaaa in cccc][-1][-1]
                     last_character = ""
                     for kk in range(len(ppcnt[:-1])): 
               
                        char = cpcnt[:-1][kk].split(" ")[0].upper()
                        atmp = re.sub("^\W+ (.*)$","\\1",ppcnt[:-1][kk])
                        atmp = re.sub("^(.*) \W+$","\\1",atmp)
                        atmp = clean(atmp)
                        line = atmp[0].capitalize()+atmp[1:]
                        
                        # Formatting stuff left over from Mark
                        line = re.sub(" NEWLINE \)"," )",line)
                        line = re.sub("(oh oh )+"," oh oh ",line)
                        line = re.sub("(ho ho )+"," ho ho ",line)
                        line = re.sub("(nonny nonny )+"," nonny nonny ",line)
                        line = re.sub("(a-down a-down )+"," nonny nonny ",line)
                        line = re.sub("( NEWLINE)+"," NEWLINE",line)
                        # Get rid of quotation marks
                        line = re.sub("\"\s*","",line)
                        # Get rid of spaces before punctuation
                        line = re.sub("\s*([,.?!:;)])","\\1",line)
                        # if there's a stage direction, put it in
                        if last_character != char:
                           scene_lines.append(char)
                        scene_lines.append(line)
                        last_character = char
               
                     out = ppcnt[-1]
                     cout = cpcnt[-1]
                     tailspeaker = cout
                     wcurrent = ppcnt[-1].split(" ")[1:]
                     ccurrent = cpcnt[-1].split(" ")[1:]
   
               continue
            elif trial.name == "rhythm_filter":
               #print "Filter"
               scene_lines.append("=================== CHUNK 1 " + trialname + " ================")
               trial_data = util.get_lines(data, trial.find("train"))
               
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
               line = {"speaker": "", "line":"","length":0,"uuid":uuid.uuid4()}
               for i in range(len(trial_data)):
                  d = trial_data[i]
                  if d[4] != line["speaker"] or d[-1] == "NEWLINE":
                     # If the last line was a stage dir, we want to remember what type
                     if i > 1 and trial_data[i-2][4] == "Stage":
                        line['pos'] = trial_data[i-2][-2]
                     if line['line']:
                        universe.append(line)
                     line = {"speaker": d[4], "line":"","length":0,"uuid":uuid.uuid4()}
                     # Check to see if we're forcing a single character (but don't overwrite stage directions)
                     forced_character = trial.find("forced_character")
                     if forced_character and line['speaker'] != "Stage":
                        line['speaker'] = forced_character.string
                  if d[-1] != "NEWLINE":
                     line["line"] += d[-1] + " "
                     if d[-1] not in [",",".","?",":",";","!"]:
                        line['length'] += 1
               if line['line']:
                  universe.append(line)
               
               #print universe
               
               # We want to chain together filters
               # Use all of the two word lines, then transition to a filter and play the filter from longest to shortest
               # at which point we pull out all of the n-length lines (where n is the length of the shortest line in the
               # filter). Do this for a while.
               potential_patterns = []
               current_length = 0
               # Make sure not to repeat patterns
               past_patterns = []
               line_length = 2
               number_of_length_lines = 10
               raw_scene_lines = []
               
               # Manually add the first line
               for u in universe:
                  if re.match("^\s*Who\'s\s*there\s*\?\s*$",u['line']):
                     raw_scene_lines.append(u)
                     break
               
               while 1:
                  # First, grab all of the line_length-length lines that we haven't already had and that start
                  # with an uppercase letter. Additionally, don't include any lines with dashes in them (because
                  # it's hard for the audience to get a sense of the number of words)
                  length_lines = [l for l in universe if l['uuid'] not in [r['uuid'] for r in raw_scene_lines] and l['length'] == line_length and l["line"].split(" ")[0].istitle() and re.match("^.*[.;?!]\s*$", l["line"]) and not re.match("^.*-.*$",l["line"])]
                  if len(length_lines) == 0:
                     break
                  if len(length_lines) > number_of_length_lines:
                     length_lines = random.sample(length_lines, number_of_length_lines)
                  else:
                     random.shuffle(length_lines)
                  raw_scene_lines += length_lines
                  
                  if length and len(raw_scene_lines) >= length:
                     break
                  
                  # Grab the next pattern
                  trial_lines = []
                  # Remember lines to remove after looping (mostly
                  # these will be lines that did not yield results
                  # as patterns and we want to ensure that the last
                  # short-word line is always the pattern for the 
                  # next section)
                  to_remove = []
                  for raw_scene_line in reversed(raw_scene_lines):
                     # Keep trying until we get one that yields results
                     pattern = raw_scene_line['line'].split(" ")[0] + " "
                     # Don't repeat patterns
                     if pattern.lower() in past_patterns:
                        # Cut this line out of the short-word lines
                        to_remove.append(raw_scene_line['uuid'])
                        continue
                     trial_lines = []
                     # Loop through all of the lines and check to see if they match the pattern given
                     # If they do, keep them
                     # Also, this makes sure that we end each line with end of line punctuation
                     # We do this by:
                     #  - If the line that matches the pattern has any end of line punctuation (?,!,.,;),
                     #    then we take the line up to the last of these punctuation marks
                     #  - Otherwise, we keep looking onto subsequent lines for punctuation marks
                     no_punctuation = False
                     for i in range(len(universe)):
                        u = copy.copy(universe[i])
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
                        elif re.match("^"+pattern+".*",u['line'],re.IGNORECASE) and not u['line'].isupper():
                           # Check to see whether the last line was a stage dir
                           # and include it if it was (Don't want titles, just stagedirs)
                           if i > 1 and universe[i-2]["speaker"] == "Stage" and re.match("^\s*\(.*\)\s*$",universe[i-2]['line']):
                              # This re.sub expression is used to insert the type of stage dir at the beginning of the stage dir
                              u['stage_direction'] = re.sub("\s*\((.*)\)\s*", "( " + universe[i-2]['pos'] + " \\1)", universe[i-2]["line"])
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
                     # It's possible that there are still some lines without endline punctuation here
                     # This could happen because some lines end and change speaker without endline
                     # punctuation. Also, make sure that no line is too long.
                     trial_lines = [t for t in trial_lines if re.match("^.*[.!;?].*$", t['line']) and len(t['line'].split(" ")) < 18 and t['uuid'] not in [r['uuid'] for r in raw_scene_lines]]
                     
                     if trial_lines:
                        # Found a pattern that yields results
                        break
                     else:
                        # Cut out the last line in the short-word lines
                        # to make sure that the last short-word lines is 
                        # always the next pattern
                        to_remove.append(raw_scene_line['uuid'])
                  
                  # Go through and remove lines that should be removed
                  raw_scene_lines = [raw_scene_line for raw_scene_line in raw_scene_lines if raw_scene_line['uuid'] not in to_remove]
                  
                  if not trial_lines:
                     # ran out of viable patterns...
                     break
                  
                  # Recount the line lengths because of the punctuation splitting that we do above
                  for t in trial_lines:
                     t['length'] = 0
                     for w in t['line'].split(" "):
                        if w not in [",",".","?",":",";","!"]:
                           t['length'] += 1
                  # Make sure that we don't have too many of any one filter
                  if len(trial_lines) > 17:
                     trial_lines = random.sample(trial_lines, 17)
                  # Sort the lines based on length
                  trial_lines.sort(key=lambda line: line['length'])
                  trial_lines.reverse()
                  past_patterns.append(pattern.lower())
                  current_length += len(trial_lines)
                  raw_scene_lines += trial_lines
                  # Set line length for next section
                  line_length = trial_lines[-1]['length']
                  
               for u in raw_scene_lines:
                  # Formatting stuff left over from Mark
                  temp_line = u['line']
                  temp_line = re.sub(" NEWLINE \)"," )",temp_line)
                  temp_line = re.sub("(oh oh )+"," oh oh ",temp_line)
                  temp_line = re.sub("(ho ho )+"," ho ho ",temp_line)
                  temp_line = re.sub("(nonny nonny )+"," nonny nonny ",temp_line)
                  temp_line = re.sub("(a-down a-down )+"," nonny nonny ",temp_line)
                  temp_line = re.sub("( NEWLINE)+"," NEWLINE",temp_line)
                  # Get rid of quotation marks
                  temp_line = re.sub("\"\s*","",temp_line)
                  # Get rid of spaces before punctuation
                  temp_line = re.sub("\s*([,.?!:;)])","\\1",temp_line)
                  # if there's a stage direction and it's short enough, put it in
                  if "stage_direction" in u and u["stage_direction"] and len(u['stage_direction']) < 22:
                     u['stage_direction'] = re.sub("\s*([,.?!:;)])","\\1",u['stage_direction'])
                     #scene_lines.append(u['stage_direction'])
                  scene_lines.append(u['speaker'].upper())
                  scene_lines.append(temp_line)
                  
               continue
            elif trial.name == "new_filter":
               #print "Filter"
               scene_lines.append("=================== CHUNK 1 " + trialname + " ================")
               trial_data = util.get_lines(data, trial.find("train"))
               
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
               line = {"speaker": "", "line":"","length":0,"uuid":uuid.uuid4()}
               for i in range(len(trial_data)):
                  d = trial_data[i]
                  if d[4] != line["speaker"] or d[-1] == "NEWLINE":
                     # If the last line was a stage dir, we want to remember what type
                     if i > 1 and trial_data[i-2][4] == "Stage":
                        line['pos'] = trial_data[i-2][-2]
                     if line['line']:
                        universe.append(line)
                     line = {"speaker": d[4], "line":"","length":0,"uuid":uuid.uuid4()}
                     # Check to see if we're forcing a single character (but don't overwrite stage directions)
                     forced_character = trial.find("forced_character")
                     if forced_character and line['speaker'] != "Stage":
                        line['speaker'] = forced_character.string
                  if d[-1] != "NEWLINE":
                     line["line"] += d[-1] + " "
                     if d[-1] not in [",",".","?",":",";","!"]:
                        line['length'] += 1
               if line['line']:
                  universe.append(line)
               
               #print universe
               
               # First, grab all of the lines matching the pattern:
               trial_lines = []
               patterns = []
               for pattern in trial.find("generate").findAll("pattern"):
                  patterns.append(pattern.string)
               pattern = random.sample(patterns,1)[0]
               no_punctuation = False
               for i in range(len(universe)):
                  u = copy.copy(universe[i])
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
                  elif re.match("^"+pattern+".*",u['line'],re.IGNORECASE) and not u['line'].isupper():
                     # Check to see whether the last line was a stage dir
                     # and include it if it was (Don't want titles, just stagedirs)
                     if i > 1 and universe[i-2]["speaker"] == "Stage" and re.match("^\s*\(.*\)\s*$",universe[i-2]['line']):
                        # This re.sub expression is used to insert the type of stage dir at the beginning of the stage dir
                        u['stage_direction'] = re.sub("\s*\((.*)\)\s*", "( " + universe[i-2]['pos'] + " \\1)", universe[i-2]["line"])
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
               # It's possible that there are still some lines without endline punctuation here
               # This could happen because some lines end and change speaker without endline
               # punctuation. Also, make sure that no line is too long.
               trial_lines = [t for t in trial_lines if re.match("^.*[.!;?].*$", t['line']) and len(t['line'].split(" ")) < 18]
               # Recount the line lengths because of the punctuation splitting that we do above
               for t in trial_lines:
                  t['length'] = 0
                  for w in t['line'].split(" "):
                     if w not in [",",".","?",":",";","!"]:
                        t['length'] += 1
               # limit the number of lines to sample
               if length and len(trial_lines) > length:
                  trial_lines = random.sample(trial_lines,length)
               # Sort the lines based on length
               trial_lines.sort(key=lambda line: len(line['line']))
               trial_lines.reverse()
               length_lines = [l for l in universe if l['uuid'] not in [r['uuid'] for r in trial_lines] and l['length'] == 2 and l["line"].split(" ")[0].istitle() and re.match("^.*[.;?!]\s*$", l["line"]) and not re.match("^.*-.*$",l["line"])]
               random.shuffle(length_lines)
               length_lines.sort(key=lambda line: len(line['line']))
               length_lines.reverse()
               trial_lines += length_lines
               length_lines = [l for l in universe if l['uuid'] not in [r['uuid'] for r in trial_lines] and l['length'] == 1 and l["line"].split(" ")[0].istitle() and re.match("^.*[.;?!]\s*$", l["line"]) and not re.match("^.*-.*$",l["line"])]
               random.shuffle(length_lines)
               length_lines.sort(key=lambda line: len(line['line']))
               length_lines.reverse()
               # Make sure that we end with "Ha!"
               length_lines.sort(key=lambda line: line['line'] == "Ha ! " and line['speaker'] == "Hamlet")
               trial_lines += length_lines
               raw_scene_lines = trial_lines
                  
               for u in raw_scene_lines:
                  # Formatting stuff left over from Mark
                  temp_line = u['line']
                  temp_line = re.sub(" NEWLINE \)"," )",temp_line)
                  temp_line = re.sub("(oh oh )+"," oh oh ",temp_line)
                  temp_line = re.sub("(ho ho )+"," ho ho ",temp_line)
                  temp_line = re.sub("(nonny nonny )+"," nonny nonny ",temp_line)
                  temp_line = re.sub("(a-down a-down )+"," nonny nonny ",temp_line)
                  temp_line = re.sub("( NEWLINE)+"," NEWLINE",temp_line)
                  # Get rid of quotation marks
                  temp_line = re.sub("\"\s*","",temp_line)
                  # Get rid of spaces before punctuation
                  temp_line = re.sub("\s*([,.?!:;)])","\\1",temp_line)
                  # if there's a stage direction and it's short enough, put it in
                  if "stage_direction" in u and u["stage_direction"] and len(u['stage_direction']) < 22:
                     u['stage_direction'] = re.sub("\s*([,.?!:;)])","\\1",u['stage_direction'])
                     #scene_lines.append(u['stage_direction'])
                  scene_lines.append(u['speaker'].upper())
                  scene_lines.append(temp_line)
                  
               continue
            elif trial.name == "filter":
               #print "Filter"
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
               for i in range(len(trial_data)):
                  d = trial_data[i]
                  if d[4] != line["speaker"] or d[-1] == "NEWLINE":
                     # If the last line was a stage dir, we want to remember what type
                     if i > 1 and trial_data[i-2][4] == "Stage":
                        line['pos'] = trial_data[i-2][-2]
                     if line['line']:
                        universe.append(line)
                     line = {"speaker": d[4], "line":""}
                     # Check to see if we're forcing a single character (but don't overwrite stage directions)
                     forced_character = trial.find("forced_character")
                     if forced_character and line['speaker'] != "Stage":
                        line['speaker'] = forced_character.string
                  if d[-1] != "NEWLINE":
                     line["line"] += d[-1] + " "
               if line['line']:
                  universe.append(line)
               
               #print universe
               
               # We want to chain together filters
               # Keep going until we get a filter that has no results
               potential_patterns = []
               current_length = 0
               # Make sure not to repeat patterns
               past_patterns = []
               while 1:
                  past_patterns.append(pattern.lower())
                  trial_lines = []
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
                        # Check to see whether the last line was a stage dir
                        # and include it if it was (Don't want titles, just stagedirs)
                        if i > 1 and universe[i-2]["speaker"] == "Stage" and re.match("^\s*\(.*\)\s*$",universe[i-2]['line']):
                           # This re.sub expression is used to insert the type of stage dir at the beginning of the stage dir
                           u['stage_direction'] = re.sub("\s*\((.*)\)\s*", "( " + universe[i-2]['pos'] + " \\1)", universe[i-2]["line"])
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
                  trial_lines = [t for t in trial_lines if re.match("^.*[.!;?].*$", t['line']) and len(t['line'].split(" ")) < 22]
            
                  # Check if we've hit a pattern without any results
                  found_new_pattern = False
                  if not trial_lines:
                     while len(potential_patterns) > 0:
                        potential_pattern = potential_patterns.pop(0)
                        if potential_pattern.lower() not in past_patterns and potential_pattern.lower() != pattern.lower() and pattern.split(" ")[0].lower() != potential_pattern.lower() and re.match("[A-Za-z]",potential_pattern):
                           pattern = potential_pattern + " "
                           found_new_pattern = True
                           break
                     if found_new_pattern:
                        continue
                     else:
                        break
                  #else:
                     # Put in what word it is to be read by the stagedir voice
                     #scene_lines.append("( pattern " + re.sub("\s*([,.?!:;)])","\\1",pattern) + ")")
            
                  # Make sure that no one section is too long:
                  #if len(trial_lines) > 15:
                  #   trial_lines = random.sample(trial_lines, random.randint(8,15))
                  
                  current_length += len(trial_lines)
                  
                  #print "length", length, "current_length", current_length,"trial length",len(trial_lines)
                  #if length and length <= current_length:
                  #   if len(trial_lines) - (current_length - length) < 5:
                  #      trial_lines = random.sample(trial_lines,min(5,len(trial_lines)))
                  #   else:
                  #      trial_lines = random.sample(trial_lines,len(trial_lines) - (current_length - length))
                  #else:
                     # Make sure that the lines are still in a random order
                  if length and length < len(trial_lines):
                     trial_lines = random.sample(trial_lines, length)
                  else:
                     random.shuffle(trial_lines)
                  
                  # Set up the next pattern:
                  potential_patterns = trial_lines[-1]['line'].split(" ")
                  # Uncomment this line to try with the last word chaining instead of second word chaining
                  # potential_patterns.reverse()
                  # Remember whether we've found a new pattern:
                  found_new_pattern = False
                  #for potential_pattern in potential_patterns:
                  while len(potential_patterns) > 0:
                     potential_pattern = potential_patterns.pop(0)
                     if potential_pattern.lower() not in past_patterns and potential_pattern.lower() != pattern.lower() and pattern.split(" ")[0].lower() != potential_pattern.lower() and re.match("[A-Za-z]",potential_pattern):
                        pattern = potential_pattern + " "
                        found_new_pattern = True
                        break
                  
                  for u in trial_lines:
                     # Formatting stuff left over from Mark
                     temp_line = u['line']
                     temp_line = re.sub(" NEWLINE \)"," )",temp_line)
                     temp_line = re.sub("(oh oh )+"," oh oh ",temp_line)
                     temp_line = re.sub("(ho ho )+"," ho ho ",temp_line)
                     temp_line = re.sub("(nonny nonny )+"," nonny nonny ",temp_line)
                     temp_line = re.sub("(a-down a-down )+"," nonny nonny ",temp_line)
                     temp_line = re.sub("( NEWLINE)+"," NEWLINE",temp_line)
                     # Get rid of quotation marks
                     temp_line = re.sub("\"\s*","",temp_line)
                     # Get rid of spaces before punctuation
                     temp_line = re.sub("\s*([,.?!:;)])","\\1",temp_line)
                     # if there's a stage direction and it's short enough, put it in
                     if "stage_direction" in u and u["stage_direction"] and len(u['stage_direction']) < 22:
                        u['stage_direction'] = re.sub("\s*([,.?!:;)])","\\1",u['stage_direction'])
                        #scene_lines.append(u['stage_direction'])
                     scene_lines.append(u['speaker'].upper())
                     scene_lines.append(temp_line)
                  
                  if True or not found_new_pattern or (length and current_length >= length):
                     break
               continue
            elif trial.name == "skip":
               print "skip not yet implemented"
               continue
            elif trial.name == "mirror":
               #print "Mirror"
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
               #print "Markov"
               POS_training_text = util.get_lines(data, trial.find('train'))
               POS_order_ramp.append({"order":-1, "word_number": 1})
               POS_emotion_ramp = []
               word_training_text = util.get_lines(data, trial.find('train'))
               word_order_ramp.append({"order":int(trial.find("generate").find("k").string), "word_number": 1})
               if trial.find("generate").find("order_ramp"):
                  for point in trial.find("generate").find("order_ramp").find_all("point"):
                     word_order_ramp.append({"order":int(point['order']),"word_number":int(point['word'])})
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
            # Check to see if we want one_word_lines
            one_word_line = trial.find("one_word_line")
            if one_word_line: one_word_line = one_word_line.string == "True"
            else: one_word_line = None
            if "semantic_logic" in scene.attrs and scene['semantic_logic'] in ["True","true","Yes","yes","t","y","1"]:
               chunk['semantic_logic'] = True
            else:
               chunk['semantic_logic'] = False
            max_line_length = trial.find("max_line_length")
            if max_line_length: 
               chunk['max_line_length'] = int(max_line_length.string)
            chunk['one_word_line'] = one_word_line
            chunk['chunk_type'] = trial.name
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
            
            gen = Generator(chunks,current_characters)
            if scene_lines:
               scene_lines += gen.generate()
            else:
               scene_lines = gen.generate()
            current_characters = gen.current_characters
      
      # Put in some transition/chaining stuff between chunks
      #if scene['strategy'] == "markov" and self.scenes and self.scenes[-1].strategy == "markov":
      #   # we have two markov scenes in a row, let's transition nicely between them
      #   # Grab the first word of this scene and the last word of the last scene and transition between them:
      #   first_word = ""
      #   first_word_counter = 0
      #   while not first_word or not re.match("[A-Za-z]+",first_word):
      #      #print scene_lines[1]
      #      first_word = scene_lines[1].split(" ")[first_word_counter]
      #      first_word_counter += 1
      #   first_word = re.sub("^([A-Za-z]+).*$","\\1",first_word)
      #   last_word = ""
      #   last_word_counter = -1
      #   last_line_counter = -1
      #   while not last_word or not re.match("^[A-Za-z]+[.,?!;]*",last_word):
      #      if len(self.scenes[-1].script[last_line_counter].split(" ")) < last_word_counter*-1:
      #         last_word_counter = -1
      #         last_line_counter -= 1
      #         continue
      #      last_word = self.scenes[-1].script[last_line_counter].split(" ")[last_word_counter]
      #      last_word_counter -= 1
      #   last_word = re.sub("^([A-Za-z]+).*$","\\1",last_word)
      #   #print last_word,first_word
      #   
      #   # Now, let's look for places where these two words coexist
      #   first_word_occurences = [i for i, x in enumerate(data) if x[-1] == first_word]
      #   last_word_occurences = [i for i, x in enumerate(data) if x[-1] == last_word]
      #   #print first_word_occurences, last_word_occurences
      #   
      #   # Find the closest occurences:
      #   first_word_occurence = -1
      #   last_word_occurence = -1
      #   for l in last_word_occurences:
      #      for f in first_word_occurences:
      #         if f > l and (first_word_occurence == -1 or first_word_occurence - last_word_occurence > f - l):
      #            first_word_occurence = f
      #            last_word_occurence = l
      #   # If we found good occurences, make a transition:
      #   # print "f and l", first_word_occurence, last_word_occurence
      #   if first_word_occurence and last_word_occurence and first_word_occurence != -1 and last_word_occurence != -1:
      #      new_text = ""
      #      for i in range(last_word_occurence,first_word_occurence):
      #         if data[i][-2] in ["NEWLINE","n1"]:
      #         #if data[i][-2] in ["NEWLINE","vvb","vbz","pn31|vbz","vmb","vvi","vvg","vvn","vmb"]:
      #         #if data[i][4] in ["Stage"]:
      #            new_text += " " + data[i][-1]
      #      print new_text
      #      scene_lines = new_text.split("NEWLINE") + scene_lines
      # Put scene information in:
      out = []
      # Check to see if there's a blackout parameter
      #blackout = scene.find("blackout")
      if "blackout" in scene.attrs and scene["blackout"]: 
         blackout = " blackout:" + scene["blackout"] + " "
      else:
         blackout = ""
      
      #blackout = ""
      
      if playwithin:
         out.append("################# SCENE playwithin " + self.pinning_table.generate_style("playwithin") + " wordcount:" + str(sum([len(script_line.split(" ")) for script_line in scene_lines])) + " strategy:" + scene['strategy'] + blackout + " #################")
      elif "name" in scene.attrs and "style" in scene.attrs:
         out.append("################# SCENE " + scene["name"]  + " " + scene["style"] + " wordcount:" + str(sum([len(script_line.split(" ")) for script_line in scene_lines])) + " strategy:" + scene['strategy'] + blackout + " #################")
      else:
         out.append("################# SCENE wordcount:" + str(sum([len(script_line.split(" ")) for script_line in scene_lines])) + " strategy:" + scene['strategy'] + blackout + " #################")
      out += scene_lines
      to_return = Scene(out)
      if playwithin:
         to_return.name = scene["name"]
         to_return.feature_vector["name"] = scene["name"]
      return to_return
   
def main(argv):
   # Grab the config files
   if len(argv) != 5:
      print "4 args required (show file, pinnings file, trial file, triggers file)"
      return
   burrito = Burrito(argv[1],argv[2],argv[3],argv[4], RandomTransition())
   burrito.create_script()
   burrito.send_script()
   
if __name__ == "__main__":
   main(sys.argv)
