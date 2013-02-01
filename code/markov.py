# This class will house the inner workings of the Markov chains. 
# It should provide the functionality for both the POS Markov chain 
# and the bucketed word Markov chain.
class Markov:
   # The constructor takes the following params:
   #  - lines: A list of the lines from brute.txt
   #  - order: The max order generated
   #  - primary_key:  This is what the Markov transitions from and to (ie parts of speech or words),
   #    given as the index within the line (10 for part of speech, 11 for word)
   def __init__(self, lines, order, primary_key):
      self.lines = lines
      self.order = order
      self.primary_key = primary_key
      self.lines_so_far = []
   
   # The initialize method initializes the markov chain
   def initialize():
      
      
   # This method generates the single next element in the markov chain. This element is added to the lines_so_far and
   # returned as well. This method will also incorporate the backoff logic.
   # -order: The order of the markov chain for this generation
   # -filters: This is a list of filters for the transition (ie affect level or part of speech). It is given
   #  as a list of dictionaries with the index into the line (following the brute.txt format) for what we're 
   #  filtering on and the filter itself (ie what we're matching). ex:
   #   [{"index": 10, "filter": "noun", "type": "text_match"},
   #    {"index": 8, "filter": 3.0, "type": "threshold"}]
   def generateNext(order, filters):
