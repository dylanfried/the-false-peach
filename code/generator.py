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
   #   "forced_character": "HAMLET"/None}
   def __init__(self, chunks):
      self.chunks = chunks
      # Variable to keep track of whether we're inside parentheses in text
      # generation
      self.in_paren = False
      # We always want the type of stage direction at the beginning
      # of each stage direction
      # grab_stagedir will be set if the last word was an open
      # paren and we need to grab the stagedir from the next word
      self.grab_stagedir = False
      # Variable to keep track of words as we generate them
      self.output = []
      # Variable to keep track of whether we have a first character for 
      # dialogue in a given chunk
      self.first_character = False
      # Variable to keep track of how many words in a row we have
      # without a NEWLINE. This is used as we generate text to make
      # sure that no line gets too long.
      self.line_length = 0
      # Variable to keep track of whether the current chunk has a forced character
      self.forced_character = None
   
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
   
   # This is a helper method that takes care of polishing text before
   # adding it to the generated text. Mostly, it keeps track of
   # parentheses for stage directions formatting
   def update(self, next_word):
      # We always want the type of stage direction at the beginning
      # of each stage direction
      # grab_stagedir will be set if the last word was an open
      # paren and we need to grab the stagedir from the next word
      if self.grab_stagedir and next_word[-1] != ")": 
         # Reset self.line_length because we're in a stagedir
         # and don't care about line length
         self.line_length = 0
         insert_stagedir = [None]*13
         insert_stagedir[-1] = next_word[-2]
         self.output.append(insert_stagedir)
         # No longer need to grab stage direction to insert
         self.grab_stagedir = False
      # Check to see if we're entering a stage direction
      if next_word[-1]=="(":
         # Reset self.line_length because we're in a stagedir
         # and don't care about line length
         self.line_length = 0
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
         # Check to see if we're already in a stage direction
         if self.in_paren:
            # If we are, then we just want to end it
            # TODO: do we need a NEWLINE after the stagedir?
            self.output.append(next_word)
            self.in_paren = False
      # Check to see if we've got a speaker now and 
      # we're in a stage direction
      elif next_word[-2] == "SPEAKER" and self.in_paren:
         # Reset self.line_length because we're in a stagedir
         # and don't care about line length
         self.line_length = 0
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
         self.output.append(next_word)
         self.output.append(insert_newline)
         self.line_length = 0
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
            self.output.append(insert_speaker)
            insert_newline = [None]*13
            insert_newline[-2] = "NEWLINE"
            insert_newline[-1] = "NEWLINE"
            self.output.append(insert_newline)
            # starting new line, reset line length
            self.line_length = 0
            # we now have a first character
            self.first_character = True
         # Otherwise, we just have a normal word and we want to add it
         self.output.append(next_word)
         if next_word[-1] == "NEWLINE":
            # adding a newline, so reset line length
            self.line_length = 0
         self.line_length += 1
         # Check to see if our line is too long
         if (self.line_length > 17 or (self.line_length > 13 and re.match(".*[,]\s*$",next_word[-1])) or (self.line_length > 10 and re.match(".*[.?!:;]\s*$", next_word[-1]))):
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
               self.grab_stagedir = True
            self.line_length = 0
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
            current_word = word_markov.generateNext(current_word_order, current_word_filters)
            #print "current word", current_word, current_word_filters
            if current_word:
               self.update(current_word)
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
      string_version = re.sub("( NEWLINE)+"," NEWLINE",string_version)
      # Get rid of quotation marks
      string_version = re.sub("\"\s*","",string_version)
      # Get rid of spaces before punctuation
      string_version = re.sub("\s*([,.?!:;)])","\\1",string_version)
      # Break into separate lines and return
      return string_version.split("NEWLINE")
