   if trial.name == "sm_filter":

      trialname = trial.find("name")
      if trialname: 
         trialname = trialname.string.encode('utf-8','ignore')
      else: trialname = ""
   
      if not out:
         if trialname:
            out =  "================ FILTER "+str(cnt+1)+" "+trialname+" ================ NEWLINE "
         else:
            out =  "================ FILTER "+str(cnt+1)+" ================ NEWLINE "
      else:
         if trialname:
            out = out + " NEWLINE ================ FILTER "+str(cnt+1)+" "+trialname+" ================ NEWLINE "
         else:
            out = out + " NEWLINE ================ FILTER "+str(cnt+1)+" ================ NEWLINE "
   
      datafile = trial.find("file")
      if datafile: 
         datafile = datafile.string
      else: continue
   
      data = open(datafile).readlines()
      data = [d.strip() for d in data]
      data = [d.split(" ") for d in data]
      data = [d[:5]+[float(dd) for dd in d[5:10]]+d[10:] for d in data]
   
      nmax = len(data[0])
   
      generate = trial.find("generate")
      if not generate: continue
   
      pattern = []
      for p in trial.findAll("pattern"): pattern.append([p["type"],p.string])

      ctype = trial.find("generate").find("type")
      if ctype: ctype = ctype.string
      else: ctype = "line"
   
      reset = True

      finishsent = trial.find("generate").find("finish_sent")
      if finishsent: finishsent = finishsent.string == "True"
      else: finishsent = False

      length = trial.find("generate").find("length")
      if length: length = int(length.string)
      else: length = 0
   
      trial_data = []
      trial_lines = {}

      constraints = []
   
   # 1 1 2 6 Francisco vvb answer
   # 1 1 2 7 Francisco pno11 me
 
      train = trial.find("train") 
      selections = train.find("selections")

      if selections:


         for selection in selections.findAll("selection"):

            acts = selection.find("acts")
            if acts: 
               acts = acts.string
               acts = expand(acts.split(","))
            else: acts=[]
   
            scenes = selection.find("scenes")
            if scenes: 
               scenes = scenes.string
               scenes = expand(scenes.split(","))
            else: scenes=[]
   
            lines = selection.find("lines")
            if lines: 
               lines = lines.string
               lines = expand(lines.split(","))
            else: lines=[]
         
            characters = selection.find("characters")
            if characters: 
               characters = characters.string
               characters = characters.split(",")
               characters = [c.strip() for c in characters]
               characters = [re.sub(" ","_",c.upper()) for c in characters]
            else: characters=[]

            pos = selection.find("pos")
            if pos:
               pos = pos.string
               pos = pos.split(",")
               pos = [c.strip() for c in pos]
               pos = [c.upper() for c in pos]
            else: pos=[]

            constraints.append({"acts":acts,"scenes":scenes,"lines":lines,"characters":characters,"pos":pos})

      else:

         acts = train.find("acts")
         if acts:
            acts = acts.string
            acts = expand(acts.split(","))
         else: acts=[]
 
         scenes = train.find("scenes")
         if scenes:
            scenes = scenes.string
            scenes = expand(scenes.split(","))
         else: scenes=[]
 
         lines = train.find("lines")
         if lines:
            lines = lines.string
            lines = expand(lines.split(","))
         else: lines=[]
 
         characters = train.find("characters")
         if characters:
            characters = characters.string
            characters = characters.split(",")
            characters = [c.strip() for c in characters]
            characters = [re.sub(" ","_",c.upper()) for c in characters]
         else: characters=[]

         constraints.append({"acts":acts,"scenes":scenes,"lines":lines,"characters":characters})

      for m in range(len(data)):
 
         keep = []

         for c in constraints:
 
            if c["acts"] and (not data[m][0] in c["acts"]): 
               keep.append(0)
               continue
        
            if c["scenes"] and (not data[m][1] in c["scenes"]): 
               keep.append(0)
               continue

            if c["lines"] and (not data[m][2] in c["lines"]): 
               keep.append(0)
               continue

            if c["characters"] and (not data[m][4].upper() in c["characters"]): 
               keep.append(0)
               continue

            if 'pos' in c and c['pos']:
               if data[m][nmax-2]=="SPEAKER" or data[m][nmax-2].upper() in c['pos'] or data[m][nmax-1]=="NEWLINE" and not data[m][nmax-1] in [")","("]: keep.append(1)
               else: keep.append(0)
            else: keep.append(1)

         if keep and max(keep)==0: continue
   
         trial_data.append(data[m])

      history = [None]*len(pattern)

      for u in trial_data:
   
         if all(history):
   
            def find_what(w,t):
   
               if t=="pos": return w[nmax-1]
               elif t=="word": return w[nmax]
   
            def match_what(p,w):
   
               if p[0]=="pos": return re.match(p[1],w[nmax-1])
               elif p[0]=="word": return re.match(p[1],w[nmax])
               else: return False 
   
            match = [match_what(pattern[i],history[i]) for i in range(len(pattern))]
   
            if all(match):
  
               tout = " ".join([h[nmax].decode("utf-8") for h in history])
               if not out: out = tout
               else: out += tout + " NEWLINE "

#               tot = sum([len(hyphenate_word(h[1].encode("utf-8"))) for h in history])
   
         for i in range(len(history)-1): history[i]=history[i+1]
         history[-1] = u
