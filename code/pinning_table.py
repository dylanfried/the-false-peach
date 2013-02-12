import os
from bs4 import BeautifulSoup

# Class for defining the Pinning Table that specifies constriants on which
# styles can occur for a scene. Also can pin which styles can occur together.
# Methods:
# - constructor:
# - generated_style: outputs an array of length four of styles given a scene. 
class pinningTable:
   
   # Constructor has attributes.
   # - table: Four dimensional dictionary object. 
   #   {"scene_name": 
   #     {"video_name": 
   #         {"sound_name":
   #             {"lights_name1": 1},
   #              {"lights_name2": 1}
   #            }
   #      },
   #    "scene_name": 
   #      {"video_name": 
   #         {"sound_name":
   #             {"lights_name1": 1},
   #              {"lights_name2": 1}
   #          }
   #       }
   #   }
   def __init__(self, pinning_file):
      self.table = BeautifulSoup(open(pinning_file).read()).find("table")
      # Grab scene files from directory
      # Keep list of possible styles
      # Initialize and populate dictionary

   # Given scene, return a style
   def generate_style(self, scene):
      video = random.sample(self.table[scene].keys(), 1)[0]
      sound = random.sample(self.table[scene][video].keys(), 1)[0]
      lights = random.sample(self.table[scene][video][sound].keys(), 1)[0]
      
      return video + "_" + sound + "_0_" + lights
