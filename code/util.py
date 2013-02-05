# This file houses useful functions that may be used in many
# places

# Function for making a smooth curve
# For instance, this is used to make a smooth
# line for thresholding emotional values
# Params:
#  - x: x points
#  - y: corresponding y points
#  - m: maximum x-value to go out to
# Returns: An array of length m with, where the index is
#          the x value and the value is the y value
def interpolate(x,y,m):
   what = range(m)
   val = []
   for i in what:
      right = min([j for j in range(len(x)) if i < x[j]])
      left = max([j for j in range(len(x)) if i >= x[j]])
      xleft = x[left]+0.0
      xright = x[right]+0.0
      yleft = y[left]+0.0
      yright = y[right]+0.0
      val.append( yright*(xleft-i)/(xleft-xright)+yleft*(i-xright)/(xleft-xright) )
   return val
