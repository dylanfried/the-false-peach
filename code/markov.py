# This class will house the inner workings of the Markov chains. 
# It should provide the functionality for both the POS Markov chain 
# and the bucketed word Markov chain.
class Markov:
   # The constructor takes the following params:
   #  - lines: A list of the lines from brute.txt
   #  - max_order: The max order generated
   #  - primary_key:  This is what the Markov transitions from and to (ie parts of speech or words),
   #    given as the index within the line (10 for part of speech, 11 for word)
   def __init__(self, lines, max_order, primary_key):
      self.lines = lines
      self.max_order = max_order
      self.primary_key = primary_key
      self.lines_so_far = []
      
      # contexts holds the markov chain
      # It is a list where each element is a markov
      # context for a given order (where the 0th element is for
      # an order 0 Markov, etc)
      # The inner contexts are dictionaries with the keys being
      # strings representing the histories and the values being
      # arrays of lines
      self.contexts = []
      for order in range(self.max_order):
         self.contexts.append({})
   
   # The initialize method initializes the markov chain
   def initialize():
      # Go through each of the lines in the input
      # data
      current_lines = []
      for line in self.lines:
         #collate all of the lines up to this line
         current_lines.append(line)
         
         # We're generating a Markov chain
         # for each order up to the max_order
         for order in range(max_order):
            # Make sure that we've got enough
            # data for this order
            if len(current_lines) > order:
               # Get the history as a string of the last "order" words
               history = " ".join([history_line[self.primary_key] for history_line in current_lines[(-1-order-1):-1]])
               
               # If the history isn't already in the context, add it
               if not history in self.contexts[order]: self.contexts[order][history] = []
               # Add the most recent line to the context keyed on the preceding history
               self.contexts[i][history].append(current_lines[-1])
      
      
   # This method generates the single next element in the markov chain. This element is added to the lines_so_far and
   # returned as well. This method will also incorporate the backoff logic.
   # -order: The order of the markov chain for this generation
   # -filters: This is a list of filters for the transition (ie affect level or part of speech). It is given
   #  as a list of dictionaries with the index into the line (following the brute.txt format) for what we're 
   #  filtering on and the filter itself (ie what we're matching). ex:
   #   [{"index": 10, "filter": "noun", "type": "text_match"},
   #    {"index": 8, "filter": 3.0, "type": "threshold"}]
   def generateNext(order, filters):
