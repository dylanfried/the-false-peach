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

   # Given scene, return a style
   def generate_style(self, scene):
      for include in includes:
         bs_scene = include.find("scene")
         if bs_scene == scene:
            pass
