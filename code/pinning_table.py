import os
from bs4 import BeautifulSoup
import sys
import re
import random

# Class for defining the Pinning Table that specifies constriants on which
# styles can occur for a scene. Also can pin which styles can occur together.
# Methods:
# - constructor:
# - generated_style: outputs an array of length four of styles given a scene. 
class PinningTable:
   
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
      self.table = {}
      # Grab scene files from directory
      scenes = os.listdir("config/SHOW/")
      scenes = [re.sub("^(.*)\.xml$","\\1",s) for s in scenes if re.match("^.*\.xml$",s)]
      # Keep list of possible styles
      video_styles = ["1","2","3","6","8","9","10","11","12","13","14","15","16","17"]
      sound_styles = ["zero","TTS.mute","TTS.aloud","TTS.aloud.SPACE.word","TTS.aloud.SPACE.character","TTS.aloud.ROGUI","TTS.mute.MUSIC.emotion","TTS.aloud.MUSIC.iana","TTS.aloud.MUSIC.emotion","TTS.mute.MUSIC.iana","TTS.inear.VOICE.aloud","TTS.inear.VOICE.space","TTS.inear.VOICE.aloud.MUSIC.iana","TTS.inear.VOICE.aloud.MUSIC.emotion","TTS.inear.VOICE.mute.MUSIC.emotion"]
      lights_styles = ["skot","theatre","emotions","play","word","ghost","monemo","lightout","lightshow","closet","lighton"]
      # Initialize and populate dictionary
      for scene in scenes:
         self.table[scene] = {}
         for video_style in video_styles:
            self.table[scene][video_style] = {}
            for sound_style in sound_styles:
               self.table[scene][video_style][sound_style] = {}
               for lights_style in lights_styles:
                  self.table[scene][video_style][sound_style][lights_style] = True
      # Go through our pinnings and excludes
      table = BeautifulSoup(open(pinning_file).read()).find("table")
      for constraint in table.findAll(["pinned","excluded"]):
         styles = constraint.findAll(["scene","sound","video","lights"])
         # Construct/populate a dictionary to represent the 
         # constraint that we're on
         to_delete = {"scene":scenes[:],"sound":sound_styles[:],"video":video_styles[:],"lights":lights_styles[:]}
         for s in styles:
            if s.name in to_delete:
               #if constraint.name == "pinned":
               #   to_delete[s.name] = [style for style in to_delete[s.name] if style != s.string]
               #elif constraint.name == "excluded":
               to_delete[s.name] = [s.string]
               #else:
               #   print "Unacceptable type:",constraint.name
            else:
               print "Unacceptable type:", s.name
         # Now loop through the deletion keys and get rid of that part of the table
         if constraint.name == "excluded":
            for scene in to_delete["scene"]:
               for video_style in to_delete["video"]:
                  for sound_style in to_delete["sound"]:
                     for lights_style in to_delete["lights"]:
                        self.table[scene][video_style][sound_style][lights_style] = False
         else:
            for scene in self.table.keys():
               if len(to_delete["scene"]) == 1 and to_delete["scene"][0] == scene:
                  matched = 1
               else:
                  matched = 0
               for video_style in self.table[scene].keys():
                  if len(to_delete["video"]) == 1 and to_delete["video"][0] == video_style:
                     video_matched = matched + 1
                  else:
                     video_matched = matched
                  for sound_style in self.table[scene][video_style].keys():
                     if len(to_delete["sound"]) == 1 and to_delete["sound"][0] == sound_style:
                        sound_matched = video_matched + 1
                     else:
                        sound_matched = video_matched
                     for lights_style in self.table[scene][video_style][sound_style].keys():
                        if len(to_delete["lights"]) == 1 and to_delete["lights"][0] == lights_style:
                           lights_matched = sound_matched + 1
                        else:
                           lights_matched = sound_matched
                        #print scene, video_style, sound_style, lights_style, lights_matched
                        if lights_matched > 0 and lights_matched != len(styles):
                           if len(to_delete["scene"]) > 1 or (len(to_delete["scene"]) == 1 and scene == to_delete["scene"][0]):
                              self.table[scene][video_style][sound_style][lights_style] = False
                        
      #print self.table["2bMirror"]["11"]
      # Now that we've done all of our setting to false, let's delete everything
      # that is False and all empty branches
      for scene in self.table.keys():
         possible_styles = 0
         for video_style in self.table[scene].keys():
            for sound_style in self.table[scene][video_style].keys():
               for lights_style in self.table[scene][video_style][sound_style].keys():
                  if not self.table[scene][video_style][sound_style][lights_style]:
                     del self.table[scene][video_style][sound_style][lights_style]
                  else:
                     possible_styles += 1
               if not self.table[scene][video_style][sound_style]:
                  del self.table[scene][video_style][sound_style]
            if not self.table[scene][video_style]:
               del self.table[scene][video_style]
         print "Scene",scene,"has",str(possible_styles),"potential styles"
         if possible_styles <= 0:
            print "\nNO STYLES FOR SCENE",scene,"\n"
         if not self.table[scene]:
            del self.table[scene]

   # Given scene, return a style
   def generate_style(self, scene):
      if scene not in self.table:
         print "NO STYLES FOR SCENE",scene
         return ""
      video = random.sample(self.table[scene].keys(), 1)[0]
      sound = random.sample(self.table[scene][video].keys(), 1)[0]
      lights = random.sample(self.table[scene][video][sound].keys(), 1)[0]
      
      return video + "_" + sound + "_0_" + lights
      
def main(argv):
   # Grab the pinning files
   p = PinningTable("config/pinning_table.xml")
   #print p.table["2bMirror"]["1"]
   
if __name__ == "__main__":
   main(sys.argv)
