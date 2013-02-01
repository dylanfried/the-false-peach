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
      
   # This method generates the single next element in the markov chain.
   # -order: The order of the markov chain for this generation
   # -emotion: A dictionary of the target emotional levels. ex:
   #   {"anger" : 3.0, "fear" : 2.0, "joy": None, "sadness": None, "freq": 1.0}
   # -secondary_key: This key contains the part of speech as a string.
   def generateNext(order, emotion, secondary_key):
