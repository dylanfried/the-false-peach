# This class will house the inner workings of the Markov chains. 
# It should provide the functionality for both the POS Markov chain 
# and the bucketed word Markov chain.
class Markov:
   # The constructor takes the following params:
   #  - lines: A list of the lines from brute.txt
   #  - order: The max order generated
   #  - primary_key:  This is what the Markov transitions from and to (ie parts of speech or words),
   #    given as the index within the line (10 for part of speech, 11 for word)
   #  - secondary_key: This is the key used for bucketing (ie part of speech within the word Markov)
   #    given as the index within the line (10 for part of speech, 11 for word)
   def __init__(self, lines, order, primary_key, secondary_key):
      self.lines = lines
      self.order = order
      self.primary_key = primary_key
      self.secondary_key = secondary_key
   
   # The initialize method initializes the markov chain
   # This takes care of the meat of the operation
   def initialize():
      
   # This method does the actual generation of text. It takes the following parameters:
   #  - length: the length of the text to generate (in number of words)
   #  - order_ramp: a list of (order, word number) tuples giving the change in order over time
   #  - emotional_ramp: a list of up to five lists, each of which gives the emotional ramp
   #    for a single emption and is a list of 3-tuples of the form: (emotion, emotion level, word number)
   #    giving the change in emotion of the five emotions over time. If any emotion is omitted, we will
   #    not care about the affect level of that emotion. ex:
   #
   #     [{"emotion" : "fear, "ramp_list" : [{"emotion_level": 3.0, "word_number":1},
   #                                         {"emotion_level":2.0,"word_number":10}]},
   #      {"emotion" : "anger, "ramp_list" : [{"emotion_level": 3.0, "word_number":1}
   #                                          {"emotion_level":2.0,"word_number":10}]},
   #      {"emotion" : "joy, "ramp_list" : [{"emotion_level": 3.0, "word_number":1},
   #                                        {"emotion_level":2.0,"word_number":10}]},
   #      {"emotion" : "sadness, "ramp_list" : []},
   #      {"emotion" : "freq, "ramp_list" : [{"emotion_level": 3.0, "word_number":1},
   #                                         {"emotion_level":2.0,"word_number":10}]}]
   
   
   #     [[{"emotion" : "fear", "emotion_level" : 3.0, "word_number": 1},
   #       {"emotion" : "fear", "emotion_level" : 2.0, "word_number": 10}],
   #      [{"emotion" : "anger", "emotion_level": 1.0, "word_number": 1},
   #       {"emotion" : "anger", "emotion_level": 2.0, "word_number": 100}]]
   def generate(order_ramp, emotional_ramp, length):
      
   def generateNext(order, emotion, secondary_key):
