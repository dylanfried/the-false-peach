from transition_logic import TransitionLogic
import random
class RandomTransition(TransitionLogic):
   def __init__(self):
      TransitionLogic.__init__(self)
   def next_scene(self,feature_vectors,scene_choices):
      no_repeat = []
      for s in scene_choices:
         if s not in [f["name"] for f in feature_vectors]:
            no_repeat.append(s)
      if no_repeat:
         return random.sample(no_repeat,1)[0]
      else:
         return random.sample(scene_choices,1)[0]
