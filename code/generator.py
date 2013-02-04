from markov import Markov
# This class will take care of generating a scene. Essentially, 
# given a list where each element in the list is a set of parameters, 
# this class will take care of instantiating the Markov objects and 
# generating the scene (where the scene is the text generated from each 
# of the elements of the parameter list).
class Generator:
   # The constructor takes a list where each element represents a chunk and each chunk takes
   # the following form:
   #  {"chunk_length" : 100,
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
   #                                                            {"emotion_level":2.0,"word_number":10}]}]
   def __init__(self, chunks):
      self.chunks = chunks
   
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
            for j in len(emotion_ramp[i]["ramp_list"]):
               if emotion_ramp[i]["ramp_list"][j]["word_number"]>word_index:
                  break
               current_fear = emotion_ramp[i]
         elif emotion_ramp[i]["emotion"]=="anger":
            for j in len(emotion_ramp[i]["ramp_list"]):
               if emotion_ramp[i]["ramp_list"][j]["word_number"]>word_index:
                  break
               current_anger = emotion_ramp[i]
         elif emotion_ramp[i]["emotion"]=="joy":
            for j in len(emotion_ramp[i]["ramp_list"]):
               if emotion_ramp[i]["ramp_list"][j]["word_number"]>word_index:
                  break
               current_joy = emotion_ramp[i]
         elif emotion_ramp[i]["emotion"]=="sadness":
            for j in len(emotion_ramp[i]["ramp_list"]):
               if emotion_ramp[i]["ramp_list"][j]["word_number"]>word_index:
                  break
               current_sadness = emotion_ramp[i]
        
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
      output = []
      chunkcount = 0
      for chunk in self.chunks: 
         chunk_title = [None]*12
         chunkcount = chunkcount + 1
         chunkname = chunk["trialname"]
         if chunkname:
            chunk_title[-1] = "================ CHUNK "+str(chunkcount)+" "+chunkname+" ================ NEWLINE "
            output.append(chunk_title)
         else:
            chunk_title[-1] = "================ CHUNK "+str(chunkcount)+" ================ NEWLINE "
            output.append(chunk_title)
   
         #initialize pos and word markovs
         #print chunk
         max_pos_order = max([a["order"] for a in chunk["POS_order_ramp"]])
         pos_markov = Markov(chunk["POS_training_text"], max_pos_order, 10)
         pos_markov.initialize()
         
         max_word_order = max([a["order"] for a in chunk["word_order_ramp"]])
         word_markov = Markov(chunk["word_training_text"], max_word_order, 11)
         word_markov.initialize()
         
         #initialize the current order to the first order.
         current_pos_order = chunk["POS_order_ramp"][0]["order"]
         current_word_order = chunk["word_order_ramp"][0]["order"]
         
         #initialize the word and pos filters.
         current_pos_filter = Generator.getCurrEmoFilter(chunk, 1, "pos")
         current_word_filter = Generator.getCurrEmoFilter(chunk, 1, "word")
         for i in range(chunk["trial_length"]):
            print "i::::::::", i
            current_pos_order = Generator.getCurrOrder(chunk, i, "pos")
            current_pos_filters = Generator.getCurrEmoFilter(chunk, i, "pos")
            print "generate Next params", current_pos_order,current_pos_filters
            current_pos = pos_markov.generateNext(current_pos_order, current_pos_filters)
            current_word_order = Generator.getCurrOrder(chunk, i, "word")
            current_word_filters = Generator.getCurrEmoFilter(chunk, i, "word")
            
            # Add in the POS filter if we got a POS
            print "current pos before if", current_pos
            if (current_pos != None):
               current_word_filters.append({"index": 10, "filter": str(current_pos[10]), "type": "text_match"})
               print "current POS Generator", str(current_pos[10])
            current_word = word_markov.generateNext(current_word_order, current_word_filters)
            print "current word", current_word
            if current_word:
               output.append(current_word)
               
      return " ".join([o[-1] for o in output])
