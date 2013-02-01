# This class will take care of generating a scene. Essentially, 
# given a list where each element in the list is a set of parameters, 
# this class will take care of instantiating the Markov objects and 
# generating the scene (where the scene is the text generated from each 
# of the elements of the parameter list).
class Generator:
   # The constructor takes a list where each element represents a trial and each trial takes
   # the following form:
   #  {"POS_training_text": [lines],
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
   def __init__(self, trials):
      self.trials = trials
      
   # This method uses the markov chains and trial config list to generate the actual text of the scene
   # It then polishes the scene and returns the text
   def generate():
