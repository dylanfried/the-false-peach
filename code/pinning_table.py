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
   
   
   # Overview of the data structure and initialization algorithm:
   # There are three types of rules for pinnings:
   #  1. Exclusions: These exclude the possibility of whatever is specified in the
   #     scene, video, lights, and sound tags from co-occuring. The values of these
   #     tags should be single styles.
   #  2. Pinnings with scenes: When the specified scene is chosen, these types of pinnings
   #     force the styles to be one of the styles specified in the comma separated list 
   #     within a video, lights, or sound tag. If one of the types (ie video or lights)
   #     is not specified, then it is assumed that any of that types styles can be chosen
   #     from.
   #  3. Pinnings without scenes: These pinnings are a bit more restrictive. In this case,
   #     the pinning forces the styles specified to co-occur. What this means is that if
   #     any of the styles specified are chosen, the other styles are forced to be one of
   #     the other specified styles in the pinning. As above, if a type of style is not
   #     specified, then it is assumed that any style of that type is acceptable.
   #
   # Internal representation:
   # Four dimensional dictionary object where the first dimension keys are the scene names,
   # the second dimension keys are the video style names, the third dimension keys are sound
   # style names, and the fourth dimension keys are lights styles names. Using this system,
   # a style combination would be a set of four keys, one for each of scene name and the three
   # types of styles. If a style combination is valid, then that combination of keys will all
   # exist in the table and will point to True.
   #   {"MadOph": 
   #     {"2": 
   #         {"TTS.aloud":
   #             {"play": True},
   #              {"emotions": True}
   #            }
   #      },
   #    "HamOph": 
   #      {"8": 
   #         {"TTS.mute.MUSIC.emotion":
   #             {"ghost": True},
   #              {"monemo": True}
   #          }
   #       }
   #   }
   #
   # Initialization Algorithm:
   # 1. Initialize the four dimensional table with all possible combinations of 
   #    styles and scenes
   # 2. Grab the pinnings and exclusions from the pinnings table specified
   # 3. Based on the pinnings and exclusions, go through the table and set the
   #    leaf nodes to False if the combination of keys (representing styles) is
   #    invalid.
   # 4. Loop through the table structure and delete any branches with only False
   #    leaf nodes. By only having True leaf nodes in the table, we greatly simplify
   #    the style generation process (we can randomly sample over the keyspace at each
   #    level of the table)
   def __init__(self, pinning_file):
      # Remember the last style that we returned
      self.last_style = {}
      self.table = {}
      # Grab scene files from directory
      scenes = os.listdir("config/SHOW/")
      scenes = [re.sub("^(.*)\.xml$","\\1",s) for s in scenes if re.match("^.*\.xml$",s)]
      # Keep list of possible styles
      video_styles = ["1","2","3","4","6","8","9","10","11","12","13","14","15","16","17"]
      sound_styles = ["zero","TTS.mix","TTS.mute","TTS.aloud","TTS.aloud.SPACE.word","TTS.aloud.SPACE.character","TTS.aloud.ROGUI","TTS.mute.MUSIC.emotion","TTS.aloud.MUSIC.iana","TTS.aloud.MUSIC.emotion","TTS.mute.MUSIC.iana","TTS.inear.VOICE.aloud","TTS.inear.VOICE.space","TTS.inear.VOICE.aloud.MUSIC.iana","TTS.inear.VOICE.aloud.MUSIC.emotion","TTS.mute.VOICE.rogui"]
      lights_styles = ["actor2","theatre","emotions","play","word","ghost","monemo","lightout","lightshow","closet","lighton","actor1","actor3","open"]
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
         break_out = False
         styles = constraint.findAll(["scene","sound","video","lights"])
         # Construct/populate a dictionary to represent the 
         # constraint that we're on
         # Initialize this dictionary to include all of the possible styles
         to_delete = {"scene":scenes[:],"sound":sound_styles[:],"video":video_styles[:],"lights":lights_styles[:]}
         for s in styles:
            if s.name in to_delete:
               # Make sure that this is an acceptable scene
               if s.name == "scene" and s.string not in to_delete[s.name]:
                  break_out = True
                  break
               to_delete[s.name] = [s.string]
            else:
               print "Unacceptable type:", s.name
         if break_out:
            continue
         # Now loop through the deletion keys and get rid of that part of the table
         if constraint.name == "excluded":
            # For exclusions, we want to invalidate any combination of the four dimensions
            # in our to_delete dictionary. For any type that was not specified in the exclusion
            # to_delete will have the list of all possibilities for that style/scene. For any
            # type that was specified, it will have only the one that was specified in the list
            # in to_delete. Thus, by looping through every combination in to_delete, we get 
            # all possible combinations of the specified styles and invalidate them.
            for scene in to_delete["scene"]:
               for video_style in to_delete["video"]:
                  for sound_style in to_delete["sound"]:
                     for lights_style in to_delete["lights"]:
                        self.table[scene][video_style][sound_style][lights_style] = False
         else:
            # For pinnings, things are a bit more complicated. We loop through all of the keys
            # for each dimension in the table and keep a count of how many levels of the table
            # match a style constraint in the constraint. 
            #  - If a combination of keys does not match
            #    any of the constraints (ie it is a combination of styles where none of the styles
            #    were specified in the constraint), then we leave it alone.
            #  - If a combination of keys matches all of the constraints (in which case the count
            #    would be equal to the number of types in the constraint), then we leave it alone
            #    because it satisfies the pinning
            #  - If a combination of keys matches at least one of the constraints but not all of them,
            #    then we want to remove it from the table because it is an invalid combination
            #
            # Notes:
            #  - We keep four counters (matched, video_matched, sound_matched, and lights_matched) rather
            #    than a single counter because we are looping at each level and need to be able to reset
            #    the count to its previous value when we move up a level.
            for scene in self.table.keys():
               if len(to_delete["scene"]) == 1 and to_delete["scene"][0] == scene:
                  matched = 1
               else:
                  matched = 0
               for video_style in self.table[scene].keys():
                  if len(to_delete["video"]) == 1 and video_style in to_delete["video"][0].split(","):
                     video_matched = matched + 1
                  else:
                     video_matched = matched
                  for sound_style in self.table[scene][video_style].keys():
                     if len(to_delete["sound"]) == 1 and sound_style in to_delete["sound"][0].split(","):
                        sound_matched = video_matched + 1
                     else:
                        sound_matched = video_matched
                     for lights_style in self.table[scene][video_style][sound_style].keys():
                        if len(to_delete["lights"]) == 1 and lights_style in to_delete["lights"][0].split(","):
                           lights_matched = sound_matched + 1
                        else:
                           lights_matched = sound_matched
                        #print scene, video_style, sound_style, lights_style, lights_matched
                        if lights_matched > 0 and lights_matched != len(styles):
                           # This is an extra check type 2 pinnings (pinnings with a scene specified) that makes
                           # sure that if we have a scene specified, then we are only invalidating a combination
                           # if it includes the specified scene.
                           # This caveat is necessary because otherwise, for instance we could get 2 out of 3 
                           # matching constraints, where video and lights match, but the scene doesn't. Because
                           # of the semantics of the two different types of pinnings, this would lead to undesirable
                           # behavior in that that combo would be invalidated. What we want, and what this check ensures,
                           # is that if a scene is specified, we only care about invalidations within that scene's branch.
                           if len(to_delete["scene"]) > 1 or (len(to_delete["scene"]) == 1 and scene == to_delete["scene"][0]):
                              self.table[scene][video_style][sound_style][lights_style] = False
                        
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
   # We want to do our best to follow these rules when it isn't scott speaking:
   #  - No two same light styles in a row
   #  - No two music styles in a row
   #  - No two same video styles in a row
   def generate_style(self, scene):
      if scene not in self.table:
         print "NO STYLES FOR SCENE",scene
         return ""
      attempts = 0
      while 1:
         video = random.sample(self.table[scene].keys(), 1)[0]
         sound = random.sample(self.table[scene][video].keys(), 1)[0]
         lights = random.sample(self.table[scene][video][sound].keys(), 1)[0]
         # If we haven't had any styles yet or they were inear, don't worry about the rules
         if not self.last_style or re.match(".*TTS\.inear.*",self.last_style['sound']): break
         # Try to follow the rules:
         if video != self.last_style['video'] and lights != self.last_style['lights'] and (not re.match(".*MUSIC.*",self.last_style['sound']) or not re.match(".*MUSIC.*",sound)): break
         # Don't try too many times to follow the rules
         if attempts > 100:
            print "COULDN'T FOLLOW STYLE RULES"
            print "scene:",scene
            print "table:",self.table[scene]
            print "last style",self.last_style
            break
         attempts += 1
      
      self.last_style['video'] = video
      self.last_style['sound'] = sound
      self.last_style['lights'] = lights
      
      return video + "_" + sound + "_0_" + lights
      
def main(argv):
   # Grab the pinning files
   p = PinningTable("config/pinning_table.xml")
   #print p.table["claudius"]["3"]
   #print p.table["claudius"]["2"]
   
if __name__ == "__main__":
   main(sys.argv)
