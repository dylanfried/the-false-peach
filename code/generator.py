from markov import Markov
import re
# This class will take care of generating a scene. Essentially, 
# given a list where each element in the list is a set of parameters, 
# this class will take care of instantiating the Markov objects and 
# generating the scene (where the scene is the text generated from each 
# of the elements of the parameter list).
class Generator:
   # The constructor takes a list where each element represents a chunk and each chunk takes
   # the following form:
   #  {"chunk_length" : 100,
   #   "chunk_type": "markov"/"mirror"/etc
   #   "finish_sentence" : True/False // Defaults to False
   #   "POS_training_text": [lines],
   #   "POS_order_ramp":    [{"order": 3, "word_number": 1},
   #                         {"order": 1, "word_number": 100}],
   #   "POS_emotion_ramp":  [{"emotion" : "fear, "ramp_list" : [{"emotion_level": 3.0, "word_number":1},
   #                                                            {"emotion_level":2.0,"word_number":10}]},
   #                         {"emotion" : "anger, "ramp_list" : [{"emotion_level": 3.0, "word_number":1}
   #                                                             {"emotion_level":2.0,"word_number":10}]},
   #                         {"emotion" : "joy, "ramp_list" : [{"emotion_level": 3.0, "word_number":1},
   #                                                           {"emotion_level":2.0,"word_number":10}]}],
   #   "word_training_text": [lines],
   #   "word_order_ramp":    [{"order": 3, "word_number": 1}],
   #   "word_emotion_ramp":  [{"emotion" : "sadness, "ramp_list" : [{"emotion_level": 3.0, "word_number":1},
   #                                                             {"emotion_level":2.0,"word_number":10}]},
   #                          {"emotion" : "anger, "ramp_list" : [{"emotion_level": 3.0, "word_number":1}
   #                                                              {"emotion_level":2.0,"word_number":10}]},
   #                          {"emotion" : "joy, "ramp_list" : [{"emotion_level": 3.0, "word_number":1},
   #                                                            {"emotion_level":2.0,"word_number":10}]}],
   #   "word_pause": None/3,
   #   "reset" : True/False,
   #   "forced_character": "HAMLET"/None,
   #   "semantic_logic":True/False}
   def __init__(self, chunks,start_characters=[]):
      self.chunks = chunks
      # Variable to keep track of whether we're inside parentheses in text
      # generation
      self.in_paren = False
      # We always want the type of stage direction at the beginning
      # of each stage direction
      # grab_stagedir will be set if the last word was an open
      # paren and we need to grab the stagedir from the next word
      self.grab_stagedir = False
      # Also, remember the last stagedir label in case we have to split up stage directions
      self.last_stagedir_label = None
      # Variable to keep track of words as we generate them
      self.output = []
      # Variable to keep track of whether we have a first character for 
      # dialogue in a given chunk
      self.first_character = False
      # Variable to keep track of how many words in a row we have
      # without a NEWLINE. This is used as we generate text to make
      # sure that no line gets too long.
      self.line_length = 0
      # Keep track of the number of words in this line that are prose
      # so that we know whether to count the current line as prose or 
      # poetry
      self.current_line_prose = 0
      # Variable to keep track of whether the current chunk has a forced character
      self.forced_character = None
      # Keep track of who the current speaker is
      self.current_speaker = None
      # Keep track of how many times in a row this speaker has been chosen
      self.current_speaker_count = 0
      # Keep track of how many words the current character has said
      self.current_speaker_line_count = 0
      # List of major characters
      self.major_characters = ['HAMLET','GERTRUDE','GHOST','KING','HORATIO','OPHELIA']
      # Dictionary mapping all character names to the correct characters
      self.characters = {"HAMLET"  : ["HAMLET"],
                         "GERTRUDE": ["GERTRUDE"],
                         "QUEEN":["GERTRUDE"],
                         "GHOST": ["GHOST"],
                         "KING": ["KING"],
                         "HORATIO": ["HORATIO"],
                         "MARCELLUS":["MARCELLUS"],
                         "OPHELIA": ["OPHELIA"],
                         "BERNARDO":["BERNARDO"],
                         "FRANCISCO":["FRANCISCO"],
                         "FIRST_CLOWN":["FIRST_CLOWN"],
                         "SECOND_CLOWN":["SECOND_CLOWN"],
                         "CLOWNS":["FIRST_CLOWN","SECOND_CLOWN"],
                         #"MOURNERS":[],
                         "CAPTAIN":["CAPTAIN"],
                         "POLONIUS":["POLONIUS"],
                         "LAERTES":["LAERTES"],
                         "VOLTIMAND":["VOLTIMAND"],
                         "CORNELIUS":["CORNELIUS"],
                         #"LORDS":[], # don't need?
                         #"ATTENDANTS":[], # don't need?
                         "REYNALDO":["REYNALDO"],
                         "ROSENCRANTZ":["ROSENCRANTZ"],
                         "GUILDENSTERN":["GUILDENSTERN"],
                         "PLAYERS":["FIRST_PLAYER","PLAYER_QUEEN","PLAYER_KING"],
                         "PROLOGUE":["PROLOGUE"],
                         "LUCIANUS":["LUCIANUS"],
                         #"ATTENDED":[], # don't need?
                         "FORTINBRAS":["FORTINBRAS"],
                         #"SOLDIERS":[], # don't need?
                         #"OTHERS":[],
                         "GENTLEMAN":["GENTLEMAN"],
                         "DANES":["DANES"],
                         "SERVANT":["SERVANT"],
                         "SAILORS":["SAILOR"],
                         "MESSENGER":["MESSENGER"],
                         "PRIESTS":["PRIEST"],
                         #"TRAINS":[],
                         "OSRIC":["OSRIC"],
                         "LORD":["LORD"],
                         "AMBASSADORS":["FIRST_AMBASSADOR"]
                         }
      # List of all current characters in scene
      self.current_characters = start_characters
   
   #Get current filter takes a chunk.
   # -chunk: Is the data structure described in the comments for __init__
   # -word_index: Is the current word index.
   # -pos_word_key: Is either "pos" or "word" depending on whether we want the filter
   #  for part of speech or word markov.
   # Returns: word and pos a filter list as described in comments for generateNext() in 
   #   markov.py.
   @staticmethod
   def getCurrEmoFilter(chunk, word_index, pos_word_key):
      #select either pos or word.
      if pos_word_key == "pos":
         emotion_ramp = chunk["POS_emotion_ramp"]
      else:
         emotion_ramp = chunk["word_emotion_ramp"]
      #initialize the current emotion levels to null.
      current_fear = -1
      current_anger = -1
      current_joy = -1
      current_sadness = -1
      
      filters = []
      
      # Set the current emotion level for each emotion to the emotion level for 
      # with the larges word_number not exceeding word_index.
      for i in range(len(emotion_ramp)):
         if emotion_ramp[i]["emotion"]=="fear":
            for j in range(len(emotion_ramp[i]["ramp_list"])):
               if emotion_ramp[i]["ramp_list"][j]["word_number"]>word_index:
                  break
               current_fear = emotion_ramp[i]["ramp_list"][j]['emotion_level']
         elif emotion_ramp[i]["emotion"]=="anger":
            for j in range(len(emotion_ramp[i]["ramp_list"])):
               if emotion_ramp[i]["ramp_list"][j]["word_number"]>word_index:
                  break
               current_anger = emotion_ramp[i]["ramp_list"][j]['emotion_level']
         elif emotion_ramp[i]["emotion"]=="joy":
            for j in range(len(emotion_ramp[i]["ramp_list"])):
               if emotion_ramp[i]["ramp_list"][j]["word_number"]>word_index:
                  break
               current_joy = emotion_ramp[i]["ramp_list"][j]['emotion_level']
         elif emotion_ramp[i]["emotion"]=="sadness":
            for j in range(len(emotion_ramp[i]["ramp_list"])):
               if emotion_ramp[i]["ramp_list"][j]["word_number"]>word_index:
                  break
               current_sadness = emotion_ramp[i]["ramp_list"][j]['emotion_level']
        
         #append the filter dictionaries.
         if current_anger != -1:
            filters.append({"index" : 5, "filter" : current_anger, "type" : "threshold"})
         if current_fear != -1:
            filters.append({"index" : 6, "filter" : current_fear, "type" : "threshold"})   
         if current_joy != -1:
            filters.append({"index" : 7, "filter" : current_joy, "type" : "threshold"})
         if current_sadness != -1:
            filters.append({"index" : 8, "filter" : current_sadness, "type" : "threshold"})
      return filters
   
   @staticmethod
   def getCurrOrder(chunk, word_index, pos_word_key):
      current_order = -1
      if pos_word_key == "pos":
         order_ramp = chunk["POS_order_ramp"]
      else:
         order_ramp = chunk["word_order_ramp"]
      for i in range(len(order_ramp)):
         if order_ramp[i]["word_number"] > word_index+1:
            break
         current_order = order_ramp[i]["order"]
      return current_order
   
   # Function to keep track of speaker metadata
   def change_speaker(self,new_speaker,current_chunk):
      if current_chunk['semantic_logic'] and new_speaker not in self.current_characters and new_speaker != "ALL":
         self.add_entrance_exit(new_speaker, "entrance")
         self.current_characters.append(new_speaker)
      if new_speaker == self.current_speaker:
         self.current_speaker_count += 1
      else:
         self.current_speaker = new_speaker
         self.current_speaker_count = 1
         self.current_speaker_line_count = 0
         
   # Function to add an entrance to the output
   # entrance_exit indicates whether this is
   #  an entrance or an exit
   def add_entrance_exit(self,new_speaker,entrance_exit="entrance"):
      insert_entrance = [None]*13
      insert_entrance[-2] = " ( "
      insert_entrance[-1] = " ( "
      self.output.append(insert_entrance)
      insert_entrance = [None]*13
      if entrance_exit == "entrance":
         insert_entrance[-1] = "entrance"
      else:
         insert_entrance[-1] = "exit"
      self.output.append(insert_entrance)
      insert_entrance = [None]*13
      if entrance_exit == "entrance":
         insert_entrance[-1] = "Enter"
      else:
         insert_entrance[-1] = "Exit"
      self.output.append(insert_entrance)
      insert_entrance = [None]*13
      insert_entrance[-1] = new_speaker
      self.output.append(insert_entrance)
      insert_entrance = [None]*13
      insert_entrance[-1] = " . "
      insert_entrance[-2] = " . "
      self.output.append(insert_entrance)
      insert_entrance = [None]*13
      insert_entrance[-2] = " ) "
      insert_entrance[-1] = " ) "
      self.output.append(insert_entrance)
      insert_entrance = [None]*13
      insert_entrance[-2] = "NEWLINE"
      insert_entrance[-1] = "NEWLINE"
      self.output.append(insert_entrance)
      #if entrance_exit == "entrance":
      #   print "ADDING", new_speaker
      #else:
      #   print "REMOVING", new_speaker
   
   # This is a helper method that takes care of polishing text before
   # adding it to the generated text. Mostly, it keeps track of
   # parentheses for stage directions formatting
   def update(self, next_word, current_chunk):
      # We always want the type of stage direction at the beginning
      # of each stage direction
      # grab_stagedir will be set if the last word was an open
      # paren and we need to grab the stagedir from the next word
      if self.grab_stagedir and next_word[-1] != ")": 
         # Reset self.line_length because we're in a stagedir
         # and don't care about line length
         self.line_length = 0
         self.current_line_prose = 0
         insert_stagedir = [None]*13
         insert_stagedir[-1] = next_word[-2]
         self.output.append(insert_stagedir)
         self.last_stagedir_label = next_word[-2]
         # No longer need to grab stage direction to insert
         self.grab_stagedir = False
      # Check to see if we're entering a stage direction
      if next_word[-1]=="(":
         # Reset self.line_length because we're in a stagedir
         # and don't care about line length
         self.line_length = 0
         self.current_line_prose = 0
         if not self.in_paren:
            insert_newline = [None]*13
            insert_newline[-2] = "NEWLINE"
            insert_newline[-1] = "NEWLINE"
            self.output.append(insert_newline)
            self.output.append(next_word)
            # We're now entering a stage direction, so we're in parens
            # and need to grab the type of stage direction with the next
            # word
            self.in_paren = True
            self.grab_stagedir = True
      # Check to see if we're at the end of a stage direction
      elif next_word[-1]==")":
         # Reset self.line_length because we're in a stagedir
         # and don't care about line length
         self.line_length = 0
         self.current_line_prose = 0
         # Check to see if we're already in a stage direction
         if self.in_paren:
            # If we are, then we just want to end it
            # TODO: do we need a NEWLINE after the stagedir?
            self.output.append(next_word)
            insert_newline = [None]*13
            insert_newline[-2] = "NEWLINE"
            insert_newline[-1] = "NEWLINE"
            self.output.append(insert_newline)
            self.in_paren = False
            # If we're leaving an exit, make sure that we have a character speaking
            # this is to ensure that we don't have the speaker exit without
            # reentering
            if self.last_stagedir_label and self.last_stagedir_label in ['exit'] and self.current_speaker:
               insert_newline = [None]*13
               insert_newline[-2] = "NEWLINE"
               insert_newline[-1] = "NEWLINE"
               self.output.append(insert_newline)
               insert_speaker = [None]*13
               insert_speaker[-2] = "SPEAKER"
               insert_speaker[-1] = self.current_speaker
               # If we have a forced character, change this speaker
               # to that one
               if self.forced_character:
                  insert_speaker[-1] = self.forced_character
               self.change_speaker(insert_speaker[-1], current_chunk)
               self.output.append(insert_speaker)
               insert_newline = [None]*13
               insert_newline[-2] = "NEWLINE"
               insert_newline[-1] = "NEWLINE"
               self.output.append(insert_newline)
               # starting new line, reset line length
               self.line_length = 0
               self.current_line_prose = 0
               # we now have a first character
               self.first_character = True
      # Check to see if we've got a speaker now and 
      # we're in a stage direction
      elif next_word[-2] == "SPEAKER" and self.in_paren:
         # Reset self.line_length because we're in a stagedir
         # and don't care about line length
         self.line_length = 0
         self.current_line_prose = 0
         # If we are, then we want to end the stage direction, 
         # then put a NEWLINE and the speaker
         insert_paren = [None]*13
         insert_paren[-2] = " ) "
         insert_paren[-1] = " ) "
         self.output.append(insert_paren)
         insert_newline = [None]*13
         insert_newline[-2] = "NEWLINE"
         insert_newline[-1] = "NEWLINE"
         self.output.append(insert_newline)
         # If we have a forced character, change this speaker
         # to that one
         if self.forced_character:
            next_word[-1] = self.forced_character
         self.change_speaker(next_word[-1], current_chunk)
         self.output.append(next_word)
         # Set in_paren because we're out of the parentheses now
         self.in_paren = False
         #set the has first character to true.
         self.first_character = True
      # Check to see if we're in a stagedir and getting a newline
      elif self.in_paren and next_word[-1] == "NEWLINE":
         # If we are, then we don't want to put the newline in
         # Don't do anything
         # Reset self.line_length because we're in a stagedir
         # and don't care about line length
         self.line_length = 0
         self.current_line_prose = 0
         return None
      elif next_word[-2] == "SPEAKER":
         # Make sure that we have a NEWLINE before and after every speaker
         insert_newline = [None]*13
         insert_newline[-2] = "NEWLINE"
         insert_newline[-1] = "NEWLINE"
         self.output.append(insert_newline)
         # If we have a forced character, change this speaker
         # to that one
         if self.forced_character:
            next_word[-1] = self.forced_character
         self.change_speaker(next_word[-1], current_chunk)
         self.output.append(next_word)
         self.output.append(insert_newline)
         self.line_length = 0
         self.current_line_prose = 0
         self.first_character = True
      else:
         # Check to see if we're getting text but don't yet
         # have a speaker.
         if not self.first_character and next_word[4] != "Stage":
            # We need to put in a speaker
            insert_newline = [None]*13
            insert_newline[-2] = "NEWLINE"
            insert_newline[-1] = "NEWLINE"
            self.output.append(insert_newline)
            insert_speaker = [None]*13
            insert_speaker[-2] = "SPEAKER"
            insert_speaker[-1] = next_word[4].upper()
            # If we have a forced character, change this speaker
            # to that one
            if self.forced_character:
               insert_speaker[-1] = self.forced_character
            self.change_speaker(insert_speaker[-1], current_chunk)
            self.output.append(insert_speaker)
            insert_newline = [None]*13
            insert_newline[-2] = "NEWLINE"
            insert_newline[-1] = "NEWLINE"
            self.output.append(insert_newline)
            # starting new line, reset line length
            self.line_length = 0
            self.current_line_prose = 0
            # we now have a first character
            self.first_character = True
         # If there's a current speaker who's not currently in the scene, make sure
         # to put a speaker in so they get added to the scene
         if 'semantic_logic' in current_chunk and current_chunk['semantic_logic'] and self.current_speaker and self.current_speaker not in self.current_characters and not self.in_paren and next_word[4] != "Stage" and self.current_speaker != "ALL":
            insert_newline = [None]*13
            insert_newline[-2] = "NEWLINE"
            insert_newline[-1] = "NEWLINE"
            self.output.append(insert_newline)
            insert_speaker = [None]*13
            insert_speaker[-2] = "SPEAKER"
            insert_speaker[-1] = self.current_speaker
            # If we have a forced character, change this speaker
            # to that one
            if self.forced_character:
               insert_speaker[-1] = self.forced_character
            self.change_speaker(insert_speaker[-1], current_chunk)
            self.output.append(insert_speaker)
            insert_newline = [None]*13
            insert_newline[-2] = "NEWLINE"
            insert_newline[-1] = "NEWLINE"
            self.output.append(insert_newline)
            # starting new line, reset line length
            self.line_length = 0
            self.current_line_prose = 0
            # we now have a first character
            self.first_character = True
         # Otherwise, we just have a normal word and we want to add it
         self.output.append(next_word)
         # Semantic logic: keep track of characters
         if 'semantic_logic' in current_chunk and current_chunk['semantic_logic']:
            if self.in_paren and self.last_stagedir_label and self.last_stagedir_label in ['entrance','place']:
               # Keep track of who's entering
               who = next_word[-1].strip().upper()
               who = re.sub("_AND_"," ",who)
               # If we have multiple characters, split them up
               who = who.split(" ")
               for w in who:
                  if w in self.characters:
                     for c in self.characters[w]:
                        if c in self.current_characters and self.last_stagedir_label == "entrance":
                           # character is already present. We don't want to let them enter again
                           # Let's go back and make them exit first
                           # We check if it's an entrance because we don't want to make them exit
                           # if they're just mentioned in the place
                           #print c, "ALREADY PRESENT, CAN'T ENTER"
                           # Pop things off the output until we get to the beginning of this entrance
                           # and insert an exit
                           stack = []
                           stack.append(self.output.pop())
                           while not re.match("^\s*\(\s*$",stack[-1][-1]):
                              stack.append(self.output.pop())
                           # Now we can add our exit
                           self.add_entrance_exit(c, "exit")
                           # Put back the stuff we popped off
                           stack.reverse()
                           self.output += stack
                        elif c not in self.current_characters:
                           self.current_characters.append(c)
               #print "ENTRANCE", self.current_characters
            if self.in_paren and self.last_stagedir_label and self.last_stagedir_label in ['exit']:
               # Keep track of who's exiting
               who = next_word[-1].strip().upper()
               who = re.sub("_AND_"," ",who)
               # If we have multiple characters, split them up
               who = who.split(" ")
               for w in who:
                  if w in self.characters:
                     for who_character in self.characters[w]:
                        if who_character in self.current_characters:
                           #print "REMOVING", who_character
                           self.current_characters.remove(who_character)
                        else:
                           #print "CHARACTER",who_character,"NOT PRESENT, CAN'T EXIT"
                           # Let's force this character to enter so that they can exit
                           # Pop things off the output until we get to the beginning of this entrance
                           # and insert an exit
                           stack = []
                           stack.append(self.output.pop())
                           while not re.match("^\s*\(\s*$",stack[-1][-1]):
                              stack.append(self.output.pop())
                           # Now we can add our entrance
                           self.add_entrance_exit(who_character, "entrance")
                           # Put back the stuff we popped off
                           stack.reverse()
                           self.output += stack
                  if w == "EXEUNT":
                     # Get rid of all characters
                     self.current_characters = []
                  #if w == "EXIT" and self.current_speaker and self.current_speaker in self.current_characters:
                  #   self.current_characters.remove(self.current_speaker)
                     # Get rid of the last speaking character
               #print "EXIT", self.current_characters
         if current_chunk['one_word_line'] and next_word[-1] != "NEWLINE":
            insert_newline = [None]*13
            insert_newline[-2] = "NEWLINE"
            insert_newline[-1] = "NEWLINE"
            self.output.append(insert_newline)
            # adding a newline, so reset line length
            self.line_length = 0
            self.current_line_prose = 0
         if next_word[-1] == "NEWLINE":
            # adding a newline, so reset line length
            self.line_length = 0
            self.current_line_prose = 0
            self.current_speaker_line_count += 1
         self.line_length += 1
         if next_word[-3] == "ab":
            self.current_line_prose += 1
         # Check to see if our line is too long
         # We have two sets of criteria, depending on whether this is prose
         # or poetry. We consider a line to prose if it contains at least 
         # 10% words from prose lines and otherwise we consider it poetry.
         # For prose, we want to break on the first punctuation that we see.
         # For poetry, we want to give the line a chance to end itself.
         # For the dumb show, special case: break on any punctuation except commas
         #  whenever. Break on commas after 9 words.
         if self.line_length > 0 and \
            ((next_word[-2] == "dumb" and (re.match(".*[.?!:;]\s*$",next_word[-1]) or self.line_length > 9 and re.match(".*[,]\s*$",next_word[-1]))) or \
            (current_chunk["chunk_type"] != "mirror" and self.current_line_prose/(self.line_length+0.0)>=0.1 and ((self.line_length > 4 and re.match(".*[,]\s*$",next_word[-1])) or (re.match(".*[.?!:;]\s*$",next_word[-1])))) or \
            ((self.line_length > 17 or (self.line_length > 13 and re.match(".*[,]\s*$",next_word[-1])) or (self.line_length > 10 and re.match(".*[.?!:;]\s*$", next_word[-1]))))):

            if self.in_paren:
               insert_paren = [None]*13
               insert_paren[-2] = " ) "
               insert_paren[-1] = " ) "
               self.output.append(insert_paren)
            insert_newline = [None]*13
            insert_newline[-2] = "NEWLINE"
            insert_newline[-1] = "NEWLINE"
            self.output.append(insert_newline)
            if self.in_paren:
               insert_paren = [None]*13
               insert_paren[-2] = " ("
               insert_paren[-1] = " ("
               self.output.append(insert_paren)
               # Insert the last stagedir label here
               insert_label = [None]*13
               insert_label[-1] = self.last_stagedir_label
               self.output.append(insert_label)
            self.line_length = 0
            self.current_line_prose = 0
            self.current_speaker_line_count += 1
         #if self.line_length > 20 and re.match(".*[,:;]\s*$",next_word[-1]) and not self.in_paren:
         #   # it is, let's put a NEWLINE in and reset the counter
         #   insert_newline = [None]*12
         #   insert_newline[-2] = "NEWLINE"
         #   insert_newline[-1] = "NEWLINE"
         #   self.output.append(insert_newline)
         #   self.line_length = 0
         ## Check to see if we're at the end of a sentence
         #elif self.line_length > 15 and re.match(".*[.?!]\s*$", next_word[-1]) and not self.in_paren:
         #   # We are. Make sure that we never have more than a single sentence on a line (as long
         #   # as we're not in a stage direction)
         #   insert_newline = [None]*12
         #   insert_newline[-2] = "NEWLINE"
         #   insert_newline[-1] = "NEWLINE"
         #   self.output.append(insert_newline)

   # This method uses the markov chains and chunk config list to generate the actual text of the scene
   # It then polishes the scene and returns the text
   def generate(self):
   #PseudoCode:
   #for each chunk in the scene
   #  initialize pos and word markovs
   #  find the pos and word order max
   #  initilialize pos and word order
   #  initilialize pos and word filters
   #  for scene_length
   #     compute the filters for the pos markov
   #     generate the next part of speech
   #     compute the filters for the word markov
   #     pass the part of speech to the word and generate
   #      the next word.
      # Make sure to reset output
      self.output = []
      chunkcount = 0
      for chunk in self.chunks:
         # Reset in_paren and grab_stagedir because we're starting a new chunk
         self.in_paren = False
         self.grab_stagedir = False
         self.forced_character = chunk["forced_character"]
         self.current_speaker = None
         self.current_speaker_count = 0
         # Set chunk title stuff
         chunk_title = [None]*13
         chunkcount = chunkcount + 1
         chunkname = chunk["chunk_name"]
         if not self.output:
            if chunkname:
               chunk_title[-1] = "================ CHUNK "+str(chunkcount)+" "+chunkname+" ================ NEWLINE "
               self.output.append(chunk_title)
            else:
               chunk_title[-1] = "================ CHUNK "+str(chunkcount)+" ================ NEWLINE "
               self.output.append(chunk_title)
         else:
            if chunkname:
               chunk_title[-1] = " NEWLINE ================ CHUNK "+str(chunkcount)+" "+chunkname+" ================ NEWLINE "
               self.output.append(chunk_title)
            else:
               chunk_title[-1] = " NEWLINE ================ CHUNK "+str(chunkcount)+" ================ NEWLINE "
               self.output.append(chunk_title)
   
         #initialize pos and word markovs
         max_pos_order = max([a["order"] for a in chunk["POS_order_ramp"]])
         pos_markov = Markov(chunk["POS_training_text"], max_pos_order, 11, chunk["reset"])
         pos_markov.initialize()
         
         max_word_order = max([a["order"] for a in chunk["word_order_ramp"]])
         word_markov = Markov(chunk["word_training_text"], max_word_order, 12, chunk["reset"])
         word_markov.initialize()
         
         #initialize the current order to the first order.
         current_pos_order = chunk["POS_order_ramp"][0]["order"]
         current_word_order = chunk["word_order_ramp"][0]["order"]
         
         #initialize the word and pos filters.
         current_pos_filter = Generator.getCurrEmoFilter(chunk, 1, "pos")
         current_word_filter = Generator.getCurrEmoFilter(chunk, 1, "word")
         i = 0
         # TODO put paren stuff in this check, a la chatter line 1106
         # This while loop will loop through the trial length
         # but, it will keep going until it finds punctuation if 
         # the chunk is marked to finish_sentence
         while i < chunk["trial_length"] or ("finish_sentence" in chunk and chunk["finish_sentence"]):
            # finish sentence?
            if  i >= chunk["trial_length"] and chunk["finish_sentence"] and self.output and (re.match(".*[.?!)]\s*$", self.output[-1][-1]) or (re.match(".*[.?!)]\s*$", self.output[-2][-1]) and self.output[-1][-1] == "NEWLINE")):
               break
            # Don't go too far trying to find punctuation
            if i - chunk["trial_length"] > 150: break
            current_pos_order = Generator.getCurrOrder(chunk, i, "pos")
            current_pos_filters = Generator.getCurrEmoFilter(chunk, i, "pos")
            current_pos = pos_markov.generateNext(current_pos_order, current_pos_filters)
            #print "current pos", current_pos
            current_word_order = Generator.getCurrOrder(chunk, i, "word")
            current_word_filters = Generator.getCurrEmoFilter(chunk, i, "word")
            # Add in the POS filter if we got a POS
            if (current_pos != None):
               current_word_filters.append({"index": 11, "filter": str(current_pos[11]), "type": "text_match"})
            word_exclusions = None
            if 'semantic_logic' in chunk and chunk['semantic_logic']:
               if self.current_speaker and not self.in_paren:
                  # Don't let anyone say their own name
                  word_exclusions = [{"index":12,"exclude":self.current_speaker.title()}]
                  # Don't let Hamlet say My lord, my honoured lord, or "I, of ladies" or "O gentle son"
                  if self.current_speaker == "HAMLET" and (self.output[-1][-1].lower() == "my" or \
                     (self.output[-2][-1].lower() == "my" and self.output[-1][-1].lower() == "honoured")):
                     word_exclusions.append({"index":12,"exclude":"lord"})
                  if self.current_speaker == "HAMLET" and self.output[-3][-1] == "I" and self.output[-2][-1].lower() == "," and self.output[-1][-1].lower() == "of":
                     word_exclusions.append({"index":12,"exclude":"ladies"})
                  if self.current_speaker == "HAMLET" and self.output[-2][-1] == "O" and self.output[-1][-1].lower() == "gentle":
                     word_exclusions.append({"index":12,"exclude":"son"})
                  # Don't let Laertes say "My brother"
                  if self.current_speaker == "LAERTES" and self.output[-1][-1].lower() == "my":
                     word_exclusions.append({"index":12,"exclude":"brother"})
                  # Don't let anyone except for Hamlet say "my uncle"
                  if self.current_speaker != "HAMLET" and self.output[-1][-1].lower() == "my":
                     word_exclusions.append({"index":12,"exclude":"uncle"})
                  # Don't let the ghost say uncle
                  if self.current_speaker == "GHOST":
                     word_exclusions.append({"index":12,"exclude":"uncle"})
                  # Don't let Gertrude say "my mother"
                  if self.current_speaker == "GERTRUDE" and self.output[-1][-1].lower() == "my":
                     word_exclusions.append({"index":12,"exclude":"mother"})
                  # Don't let the same character be chosen too many times in a row
                  if self.current_speaker_count and self.current_speaker_count >= 2:
                     word_exclusions.append({"index":12,"exclude":self.current_speaker})
                  # Don't let minor characters have too many lines in a row
                  if self.current_speaker_line_count > 4 and self.current_speaker not in self.major_characters:
                     current_word_filters.append({"index":11,"filter":"SPEAKER","type":"text_match"})
            current_word = word_markov.generateNext(current_word_order, current_word_filters,word_exclusions)
            # We never want the actor to refer to him/herself
            while chunk['chunk_type'] == "mirror" and current_word[-1] == "Hamlet":
               current_word = word_markov.generateNext(current_word_order, current_word_filters)
            #print "current word", current_word, current_word_filters
            if current_word:
               self.update(current_word, chunk)
            i += 1
         # Make sure that we've ended all stage directions
         if self.in_paren:
            insert_paren = [None]*13
            insert_paren[-2] = " ) "
            insert_paren[-1] = " ) "
            self.output.append(insert_paren)
               
      string_version = " ".join([o[-1] for o in self.output])
      # Formatting stuff left over from Mark
      string_version = re.sub(" NEWLINE \)"," )",string_version)
      string_version = re.sub("(oh oh )+"," oh oh ",string_version)
      string_version = re.sub("(ho ho )+"," ho ho ",string_version)
      string_version = re.sub("(nonny nonny )+"," nonny nonny ",string_version)
      string_version = re.sub("(a-down a-down )+"," nonny nonny ",string_version)
      string_version = re.sub("(\(\s*\))","",string_version)
      string_version = re.sub("( NEWLINE)+"," NEWLINE",string_version)
      # Get rid of quotation marks
      string_version = re.sub("\"\s*","",string_version)
      # Get rid of spaces before punctuation
      string_version = re.sub("\s*([,.?!:;)])","\\1",string_version)
      # Break into separate lines and return
      return string_version.split("NEWLINE")
