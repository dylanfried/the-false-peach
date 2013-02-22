# Class used to keep track of whether a trigger
# has been activated
class headless_trigger():

   def __init__(self,stage,words,priority,pause,zero_out):

      self.stage = stage
      self.words = words
      self.priority = priority
      self.pause = pause
      self.zero_out = zero_out
      self.skip = []
      self.cnt = 0
      # Vars for remembering whether we need to
      # zero out this trigger
      self.triggered = False
      self.ready_to_zero = False

   def update(self,word):
      if not self.zero_out:
         if self.words[self.cnt].lower()==word: self.cnt += 1
         else: self.cnt = 0
      else:
         if len(self.words) > self.cnt and self.words[self.cnt].lower()==word: self.cnt += 1

   def active(self):
      return self.cnt == len(self.words)

   def reset(self):
      self.cnt = 0
