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
                  self.scenes.append(self.create_scene(next_scene))
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
                  self.scenes.append(self.create_scene(next_scene))
                  words_generated += self.scenes[-1].length
                  iterations += 1
         else:
            # This is a prescribed sequence
            for scene in sequence.findAll("scene"):
               self.scenes.append(self.create_scene(scene.string))
      # Print out script
      for s in self.scenes:
         print "\n".join(s.script)
            
   def send_script(self):
      # Loop through the scenes and create the script in its entirety
      out = []
      for scene in self.scenes:
         out += scene.script
      self.loosey.send_script(out)
   
   # Method for generating a single scene
   # Returns a scene object
   def create_scene(self, scene_name):
      # Get going with the scene config file
      bs = BeautifulSoup(open("config/SHOW/" + scene_name).read())
      scene_name = re.sub("^(.*)\.xml$", "\\1", scene_name)
      if not bs.find("scene"):
         # put in the scene tag
         bs = BeautifulSoup("<scene>" + bs.__str__() + "</scene>")
         
      scene = bs.find("scene")
      scene["name"] = scene_name
      scene["style"] = self.pinning_table.generate_style(scene_name)

      # Reset the scene line container and word count
      scene_lines = []
      for trial in scene.findAll(["markov","mirror","skip","filter","sm_filter","letter_markov","ddop","straightdo","read_xml"]):
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
                     if len(stagedir[-1]) < 17:
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
            
            letter_markov = Markov(markov_data, 2, 11, False)
            letter_markov.initialize()
            
            text = ""
            for i in range(500):
               text += letter_markov.generateNext(2,[])[-1]
            
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
            acts = []
            scenes = []
            lines = []
            
            arg_name=["-a","-s","-l"]
            arg_val=[]
            arg_val.append(trial.find("acts").string)
            arg_val.append(trial.find("scenes").string)
            arg_val.append(trial.find("lines").string)
            opts = []
            for i in range(len(arg_name)):
               if arg_val[i]:
                  tup = arg_name[i], arg_val[i]
                  opts.append(tup)
            print "OPTS: ", opts
            for o, a in opts:
               print o,a
               if o == "-a":
                  if "-" in a:
                     a = a.split("-")
                     acts = range(int(a[0]),int(a[1])+1)
                  else: acts = [int(a)]
                  if len(acts)>1: break
               elif o == "-s":
                  if "-" in a:
                     a = a.split("-")
                     scenes = range(int(a[0]),int(a[1])+1)
                  else: scenes = [int(a)]
                  if len(scenes)>1: break
               elif o == "-l":
                  if "-" in a:
                     a = a.split("-")
                     lines = range(int(a[0]),int(a[1])+1)
                  else: lines = [int(a)]
               else:
                   assert False, "unhandled option"
            def clean(x):
            
               while re.match("(.*)\ ([-.,?!:;)]+.*)",x):
                  x = re.sub("(.*)\ ([-.,?!:;)]+.*)","\\1\\2",x)
            
               while re.match("(.*)\( (.*)",x):
                  x = re.sub("(.*)\( (.*)","\\1 (\\2",x)
            
               return x.strip()
            
            x = open("code/ndata2.txt").readlines()
            
            ACT = [int(a.split(" ")[0]) for a in x]
            #print "ACT", ACT
            SCENE = [int(a.split(" ")[1]) for a in x]
            #print "SCENE", SCENE
            LINE = [int(a.split(" ")[2]) for a in x]
            #print "LINE", LINE
            c = [a.split(" ")[3] for a in x]
            p = [a.split(" ")[4] for a in x]
            w = [a.split(" ")[5].strip() for a in x]
            
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
            
            #   print ss, max(counts[speaker].values()), len(counts[speaker])
            #   print counts[speaker].keys()
            
               bbf = counts[speaker].values()
            
               for kk in counts[speaker]: 
                  
                  counts[speaker][kk] = sum([xxx for xxx in bbf if xxx < counts[speaker][kk]])/(ss+0.0)
            
               #print min(counts[speaker].values()),max(counts[speaker].values())
            
            history = []
            whistory = []
            speaker = ""
            spoke = ""
            pspoke = ""
            
            for i in range(len(c)):

               if acts and not ACT[i] in acts: continue
               if scenes and not SCENE[i] in scenes: continue
               if lines and not LINE[i] in lines: continue
            
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
            
                     if counts[c[i]][k] > 0.92: 
            
                        if not spoke and not pspoke == c[i]: 
            
                           print "\n"+c[i].upper()
                           scene_lines.append(c[i].upper())
                           spoke = 1
                           pspoke = c[i]
            
                        tmpaa = clean(kk)
                        print tmpaa[0].capitalize()+tmpaa[1:]
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
            x = open("code/ndata4.txt").readlines()
            
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
            
            act = 0
            mark_scene = 0
         
            opts = []
            arg_names=["-a","-s"]
            arg_val=[]
            arg_val.append(trial.find("acts").string)
            arg_val.append(trial.find("scenes").string)
            for i in range(len(arg_names)):
               if arg_val[i]:
                  tup = arg_names[i], arg_val[i]
                  opts.append(tup)
            print "OPTS", opts
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
                        #line = clean(RWORDS)+"\n\n"

                        RCHARS = CHARS[i]
                        RWORDS = WORDS[i]
                  #char = RCHARS.upper()+"\n"
                  #line = clean(RWORDS)+"\n\n"
                  
            
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
            trial_lines = [t for t in trial_lines if re.match("^.*[.!;?].*$", t['line']) and len(t['line'].split(" ")) < 17]
      
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
               # Get rid of quotation marks
               u['line'] = re.sub("\"\s*","",u['line'])
               # Get rid of spaces before punctuation
               u['line'] = re.sub("\s*([,.?!:;)])","\\1",u['line'])
               # if there's a stage direction and it's short enough, put it in
               if "stage_direction" in u and u["stage_direction"] and len(u['stage_direction']) < 17:
                  u['stage_direction'] = re.sub("\s*([,.?!:;)])","\\1",u['stage_direction'])
                  scene_lines.append(u['stage_direction'])
               scene_lines.append(u['speaker'].upper())
               scene_lines.append(u['line'])
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
      # Put scene information in:
      out = []
      if "name" in scene.attrs and "style" in scene.attrs:
         out.append("################# SCENE " + scene["name"]  + " " + scene["style"] + " wordcount:" + str(sum([len(script_line.split(" ")) for script_line in scene_lines])) + " #################")
      else:
         out.append("################# SCENE wordcount:" + str(sum([len(script_line.split(" ")) for script_line in scene_lines])) + " #################")
      out += scene_lines
      return Scene(out)
   
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
