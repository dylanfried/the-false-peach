from transition_logic import TransitionLogic
import random
import re
class RandomTransition(TransitionLogic):
   def __init__(self):
      TransitionLogic.__init__(self)
      # Rules for things that cannot follow other things
      self.no_follow = [{"from":['OneOne','ghostscene','FiveTwo','hamoph','dumb','it_is','O','closet','straightdo','thisfilter'], 
                         "to":  ['OneOne','ghostscene','FiveTwo','hamoph','dumb','it_is','O','closet','straightdo','thisfilter']},
                        {"from":['gertrude','deathspeech','MadOph'], 
                         "to":  ['gertrude','deathspeech','MadOph']},
                        {"from":["kingrises","affrighted","thedrink","rot","tocome","sweetprince","mansmemory","is_not",'kingthing','groups'],
                         "to":  ["kingrises","affrighted","thedrink","rot","tocome","sweetprince","mansmemory","is_not",'kingthing','groups']}]
                         
   def next_scene(self,feature_vectors,scene_choices):
      no_repeat = []
      # Loop through the no follow data and compile a list
      # of the scenes that can't follow this one
      no_follow = []
      for no_follow_list in self.no_follow:
         if feature_vectors and feature_vectors[-1]['name'] in no_follow_list['from']:
            no_follow += no_follow_list["to"]
      for s in scene_choices:
         if re.sub("^(.*)\.xml$","\\1",s) not in [f["name"] for f in feature_vectors] and re.sub("^(.*)\.xml$","\\1",s) not in no_follow:
            no_repeat.append(s)
      if not no_repeat:
         print "SCENE CHOICE: eleminated all possibilities", scene_choices
         # we didn't get anything, try relaxing the follow constraints
         for s in scene_choices:
            if re.sub("^(.*)\.xml$","\\1",s) not in [f["name"] for f in feature_vectors]:
               no_repeat.append(s)
      # Now, if we have anything in our no repeat list, use it
      if no_repeat:
         return random.sample(no_repeat,1)[0]
      else:
         # Otherwise, randomly sample over everything
         # DON'T EVER REPEAT SCENES
         print "\n\nNEVER REPEAT A SCENE!!!!!!!!\n\n"
         sys.exit()
         return random.sample(scene_choices,1)[0]
