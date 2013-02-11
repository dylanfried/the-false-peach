class Scene:
   def __init__(self, script):
      self.script = script
      self.length = re.sub(".*wordcount:(\d+).*","\\1",self.script[0])
      self.feature_vector = {}
      self.feature_vector["length"] = self.length
