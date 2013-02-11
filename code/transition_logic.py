class TransitionLogic:
   def __init__(self):
      pass
   # Method to be overwritten by subclasses that
   # figures out the next scene
   def next_scene(feature_vectors, scene_choices):
      return scene_choices[0]
