# Class used to keep track of whether a trigger
# has been activated
class headless_trigger():

   def __init__(self,stage,words,priority,pause,wait):

      self.stage = stage
      self.words = words
      self.priority = priority
      self.pause = pause
      self.wait = wait
      self.cnt = 0

   def update(self,word):

      if not self.wait:

         if self.words[self.cnt]==word: self.cnt += 1
         else: self.cnt = 0
   
      else:

         if len(self.words) > self.cnt and self.words[self.cnt]==word: self.cnt += 1

   def active(self):
 
      return self.cnt == len(self.words)

   def reset(self):

      self.cnt = 0
