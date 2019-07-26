"""
Matplotlib Animation Example

author: Jake Vanderplas
email: vanderplas@astro.washington.edu
website: http://jakevdp.github.com
license: BSD
Please feel free to use and modify this, but keep the above information. Thanks!
"""

# Adapted by Bill Mongan 11/28/2013

# requires matplotlib, numpy, pylab and scipy
# requires ffmpeg (apt-get install ffmpeg) to be installed
import matplotlib.pyplot as plt
from matplotlib import animation
import numpy as np
from scipy import interpolate
from pylab import *
from coordinate_list import *
import time

class GraphAnimator:
     tag_report_array = None
     GA_fig = None
     GA_ax = None
     GA_line = None
     GA_lines = []
     interval = 1000
     x = []
     y = []
     xfield = ''
     yfield = ''
     unitx = ''
     unity = ''
     anim = None
     fps = 30
     time = 600000
     nframes = fps * time / 1000000
     dynamic_y_axis = True
     sigfield = ''
     coord_index = 0
     plots = dict()
     xtime = 0
     title = ""
     invert_y = False

     # initialization function: plot the background of each frame
     def init(self):
         self.GA_line.set_data([], [])
         return self.GA_line,

     # can be optionally called by animate_step to compute the x axis scale based on a time window given, i.e., the last N seconds
     def recalculate_x_axis(self):
          if len(self.tag_report_array) > 0:
               max_relative_timestamp = self.tag_report_array[-1]['relative_timestamp']
               
               xmin, xmax = self.GA_ax.set_xlim()
               if max_relative_timestamp >= (xmax-self.xtime):
                   newxmax = xmax + self.xtime
                   newxmin = xmin + self.xtime
                   #print 'Resetting x axis to', newxmin, newxmax
                   self.GA_ax.set_xlim([newxmin, newxmax])


     def getelementfield(self, e, field):
          if not '|' in field:    
               return e[field]
          else: # if the field is split with a | pipe character, make a field that contains those values concatenated also with a |
               val = ''
               fields = field.split('|')
               for f in fields:
                    val = val + str(e[f]) + '|'
               return val[:-1]
        
     # can be optionally called by animate_step to compute the y axis scale based on the min and max y values seen
     def recalculate_y_axis(self):
               if len(self.y) > 0:
                    newmin = float(min(self.y))
                    newmax = float(max(self.y))

                    if newmin > newmax:
                         temp = newmin
                         newmin = newmax
                         newmax = temp
                    
                    newmin = newmin - 5
                    newmax = newmax + 5

                    self.GA_ax.set_ylim([newmin, newmax])
                    #print 'Resetting y axis to', newmin, newmax, 'based on min and max of', float(min(self.y)), float(max(self.y))

                    # invert the y axis if specified
                    if self.invert_y == True:
                         plt.gca().invert_yaxis()

     # animation function.  This is called sequentially
     def animate_step(self, i):
          old_title = self.title # only update the title if it changes to save time

          # Search the tag_report_array for new tag entries, add them to the x and y animation plot, and graph
          # Assumes these are sorted by timestamp, but they can be sorted by tag_data if they are not
          # Assumes the tag_report_array is updated by an external thread
          for t in self.tag_report_array:
               # if the x/y plots for this signature don't exist yet, create it before appending
               if not self.getelementfield(t, self.sigfield) in self.plots:
                    self.plots[self.getelementfield(t, self.sigfield)] = CoordinateList(self.getelementfield(t, self.sigfield), self.coord_index)

                    # add a plot to the graph to go with this new data tag, should have an index of coord_index
                    new_GA_line, = self.GA_ax.plot([], [], CL_plotcolors[self.coord_index % len(CL_plotcolors)] + '-', lw=2)
                    self.GA_lines.append(new_GA_line)

                    # add the newly found RFID chip to the title with its legend identifier
                    self.title = self.title + str(self.coord_index) + ': ' + self.getelementfield(t, self.sigfield) + ' ' + CL_plotcolors[self.coord_index % len(CL_plotcolors)] + '-\n'

                    self.coord_index = self.coord_index + 1

               if not (self.getelementfield(t, self.xfield) in self.x):
                    self.x.append(self.getelementfield(t, self.xfield)) # still maintain global x/y list so that we can adjust the x/y axis using all plotted data (would need to scale)
                    self.y.append(self.getelementfield(t, self.yfield))

                    self.plots[self.getelementfield(t, self.sigfield)].xvals.append(self.getelementfield(t, self.xfield)) # but also add it to the particular GA_line plot list
                    self.plots[self.getelementfield(t, self.sigfield)].yvals.append(self.getelementfield(t, self.yfield))

          for p in self.plots:
               gal = self.GA_lines[self.plots[p].coord_index]
               gal.set_data(self.plots[p].xvals, self.plots[p].yvals) # set the GA lines being plotted

          # recalculate the y axis ranges dynamically with a little buffer room
          if self.dynamic_y_axis == True:
               self.recalculate_y_axis()

          # set the x axis ranges if specified
          if self.xtime > 0:
               self.recalculate_x_axis()

          # set title
          if not self.title in old_title:
               plt.suptitle(self.title)
            
          #plt.pause(0.1) # allow thread to re-draw
          time.sleep(0.025)

          return self.GA_line, # is GA_line necessary anymore now that we have GA_lines?

     def animate(self, moviefilename = None):
          # if saving a movie file, take more frames because 30 fps is too few to capture the entire movie; there is also a lag at the beginning which likely causes these wasted frames
          if moviefilename != None:
               self.nframes = self.nframes * 2

          self.nframes = int(self.nframes)
               
          # call the animator.  blit=True means only re-draw the parts that have changed.
          self.anim = animation.FuncAnimation(self.GA_fig, self.animate_step, init_func=self.init, frames=self.nframes, interval=self.interval, blit=False)

          # clear, label and draw/update
          plt.ylabel(self.yfield + ' (' + self.unity + ')')
          plt.xlabel(self.xfield + ' (' + self.unitx + ')')

          if moviefilename != None:
               # save the animation as an mp4.  This requires ffmpeg or mencoder to be
               # installed.  The extra_args ensure that the x264 codec is used, so that
               # the video can be embedded in html5.  You may need to adjust this for
               # your system: for more information, see
               # http://matplotlib.sourceforge.net/api/animation_api.html
               # note that some arch's don't recognize extra_args
               self.anim.save(moviefilename, fps=self.fps) #, extra_args=['-vcodec', 'libx264'])

          plt.ion()
          plt.show() # blocking call until closed but background thread will run
          while 1:
               plt.pause(0.1) # allow thread to re-draw
        
          return


     # tag_report_array is an array of TagReport objects from tag_data
     # ymin and ymax are initial graph axis scale values that may change dynamically over time as it animates (these can be recalculated) - this is optionally done via a call to calculate_y_axis in animate_step (since this is where the new data is read which would cause the axis scale to change); use dynamic_y_axis parameter to cause this behavior
     # xmin and xmax are computed based on the length of the simulation, known a priori
        # xtime is whether to adjust the x axis dynamically and by how much upon reaching the right margin
        # invert_y is True if the y axis should be inverted
     def __init__(self, _tag_report_array, xfield, yfield, unitx, unity, ymin=-256, ymax=256, interval=50, time=60 * 1000000, dynamic_y_axis=True, keyfield='epc96', xtime=0, invert_y=False):
          self.tag_report_array = _tag_report_array

          self.xfield = xfield
          self.yfield = yfield
          self.unitx = unitx
          self.unity = unity

          self.fps = 30
          self.time = time
          self.nframes = self.fps * (time / 1000000)
          self.interval = interval

          self.dynamic_y_axis = dynamic_y_axis

          self.sigfield = keyfield

          self.xtime = xtime

          self.title = ""

          self.invert_y = invert_y

          xmin = 0
          xmax = time

          # First set up the figure, the axis, and the plot element we want to animate
          self.GA_fig = plt.figure()
          self.GA_ax = plt.axes(xlim=(xmin, xmax), ylim=(ymin, ymax)) #plt.axes(xlim=(0, 2), ylim=(-2, 2))
          self.GA_line, = self.GA_ax.plot([], [], lw=2)

# References:
#     http://jakevdp.github.io/blog/2012/08/18/matplotlib-animation-tutorial/
