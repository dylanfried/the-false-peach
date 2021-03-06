import re
class Scene:
   def __init__(self, script):
      self.script = script
      self.length = int(re.sub(".*wordcount:(\d+).*","\\1",self.script[0]))
      self.name = self.script[0].split(" ")[2]
      self.strategy = re.sub(".*strategy:([A-Za-z_]+).*","\\1",self.script[0])
      self.feature_vector = {}
      self.feature_vector["length"] = self.length
      self.feature_vector["name"] = self.name
      self.feature_vector["strategy"] = self.strategy
