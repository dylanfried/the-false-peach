import copy
import pprint
import random

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
      self.cursor = []
      
      #Have we used the markov process yet or have we just returned
      #from the first "order" lines.
      self.markoved = False
      
      # contexts holds the markov chain
      # It is a list where each element is a markov
      # context for a given order (where the 0th element is for
      # an order 0 Markov, etc)
      # The inner contexts are dictionaries with the keys being
      # strings representing the histories and the values being
      # arrays of lines
      self.contexts = []
      for order in range(self.max_order + 1):
         self.contexts.append({})
   
   # The initialize method initializes the markov chain
   def initialize(self):
      # Go through each of the lines in the input
      # data
      current_lines = []
      for line in self.lines:
         #collate all of the lines up to this line
         current_lines.append(line)
         
         # We're generating a Markov chain
         # for each order up to the max_order
         for order in range(self.max_order + 1):
            # Make sure that we've got enough
            # data for this order
            if len(current_lines) > order:
               # Get the history as a string of the last "order" words
               history = " ".join([history_line[self.primary_key] for history_line in current_lines[(-1-order):-1]])
               # If the history isn't already in the context, add it
               if not history in self.contexts[order]: self.contexts[order][history] = []
               # Add the most recent line to the context keyed on the preceding history
               self.contexts[order][history].append(current_lines[-1])
      
      
   # This method generates the single next element in the markov chain. This element is added to the lines_so_far and
   # returned as well. This method will also incorporate the backoff logic.
   # -order: The order of the markov chain for this generation
   # -filters: This is a list of filters for the transition (ie affect level or part of speech). It is given
   #  as a list of dictionaries with the index into the line (following the brute.txt format) for what we're 
   #  filtering on and the filter itself (ie what we're matching). ex:
   #   [{"index": 10, "filter": "noun", "type": "text_match"},
   #    {"index": 8, "filter": 3.0, "type": "threshold"}]
   def generateNext(self, order, filters):
      # Dynamically populate cursor until it's as big as the max order
      # Start by returning the first order words from the testing text
      if len(self.cursor) < order and not self.markoved:
         self.cursor.append(self.lines[len(self.cursor)])
         print "cursor", self.cursor
         self.lines_so_far.append(self.cursor[-1])
         return self.cursor[-1]
      
      while order > -1:
         # Generate the string key from the cursor
         history = " ".join([history_line[self.primary_key] for history_line in self.cursor[-(order):]])      
         print "history in generateNext",history
         # Check to see if we have this history/stem in our context
         if history in self.contexts[order].keys():
            print "got into the keys check"
            # We do! Now check to see if the filters are met:
            new_context = self.contexts[order][history][:]
            for f in filters:
               if f["type"] == "text_match":
                  new_context = [met_filter for met_filter in new_context if met_filter[f["index"]] == f["filter"]]
               elif f["type"] == "threshold":
                  new_context = [met_filter for met_filter in new_context if met_filter[f["index"]] >= f["filter"]]
               else:
                  print "Bad filter type, skipping"
                  continue
            
            # Is there anything left?
            if len(new_context) > 0:
               # Yep! Randomly sample and return stuff
               # We have the key already, let's grab the next element
               self.lines_so_far.append(random.sample(new_context,1)[0])
               # Update the cursor (pop off the first element and add the new line)
               if len(self.cursor) > 0:
                  self.cursor.append(self.lines_so_far[-1])
                  if len(self.cursor) > self.max_order: self.cursor.pop(0)
               
               # Return the newest line:
               self.markoved = True
               return self.lines_so_far[-1]
            else:
               # Nope, let's back off the order
               order = order-1
         else:
            order = order-1
      
      # Uh-oh, this should never happen
      #print "Oh no, we didn't get anything"
      return None
