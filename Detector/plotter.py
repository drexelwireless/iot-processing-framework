import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import time

# http://matplotlib.org/examples/animation/simple_anim.html
# https://jakevdp.github.io/blog/2012/08/18/matplotlib-animation-tutorial/
class Plotter:
    def __init__(self, processor_threads, xwin=60, xscale=1e6):
        self.pts = processor_threads
        self.lines = []
        self.xwin = xwin
        self.xscale = xscale
        self.axes = []

    def init(self):
        for j in range(len(self.pts)):
            for i in range(len(self.pts[j].get_data()['X'])):
                self.lines[i].set_data([], [])
        return self.lines,

    def start(self, save=False, runtime=120, fps=30, moviefilename='out.mp4'):
        self.fig = plt.figure()

        subplots = 0

        for j in range(len(self.pts)):
            data = self.pts[j].get_data()

            subplots = subplots + len(data['X'])

        if subplots == 0:
            return

        subplotnum = 1
        
        maxxscale = 1
        
        for j in range(len(self.pts)):
            data = self.pts[j].get_data()

            for i in range(len(data['X'])):
                ax = self.fig.add_subplot(subplots, 1, subplotnum)
                self.axes.append(ax)

                xcol = data['X'][i]
                line, = ax.plot([], [], lw=2)
                ax.set_xlabel(data['xlabel'][i])
                ax.set_ylabel(data['ylabel'][i])
                ax.set_title(data['title'] + ': ' + data['Y'][i] + ' vs ' + xcol)
                self.lines.append(line)
                
                subplotnum = subplotnum + 1
                
            if 'xscale' in data:
                xscale = data['xscale']
            else:
                xscale = self.xscale
                    
            if xscale > maxxscale:
                maxxscale = xscale
                    
            if 'xwin' in data:
                if data['xwin'] > self.xwin and data['xwin'] > 0:
                    self.xwin = data['xwin']
                
        self.xscale = maxxscale

        self.fig.subplots_adjust(hspace=0.5)

        # frames is important if saving to ensure that the right number of frames are captured
        if save:
            nframes=int(runtime)*int(fps)*int(self.xscale)
        else:
            nframes=int(runtime)*int(fps)

        self.anim = animation.FuncAnimation(self.fig, self.animate, init_func=self.init, interval=1, frames=nframes, blit=False)

        # enable draw in the background
        plt.ion()

        if save:
            # http://matplotlib.org/examples/animation/basic_example_writer.html
            FFwriter = animation.FFMpegWriter(fps=fps)
            self.anim.save(moviefilename, writer=FFwriter, fps=fps, extra_args=['-vcodec', 'libx264'])

        # enable background processing while displaying plot
        plt.show()
        while 1:
            plt.pause(0.1)

    def animate(self, step):
        axnum = 0

        for j in range(len(self.pts)):
            data = self.pts[j].get_data()
            for i in range(len(data['X'])):
                xcol = data['X'][i]
                ycol = data['Y'][i]

                X = data['data'][xcol]
                Y = data['data'][ycol]
                self.lines[axnum].set_data(X, Y)

                if len(X) >= 1 or len(Y) >= 1:
                    minx = min(X)
                    miny = min(Y)
                    maxy = max(Y)
                    maxx = max(X)

                    if maxx < (self.xwin-1) * self.xscale:
                        newxmax = self.xscale * (self.xwin - 1)
                        newxmin = minx
                    elif maxx - minx > (self.xwin-1) * self.xscale:
                        newxmax = maxx + self.xscale
                        newxmin = maxx - self.xwin * self.xscale
                    else:
                        newxmax = maxx + self.xscale
                        newxmin = minx

                    if abs(maxy) > 1:
                        yscale = 1
                    else:
                        yscale = maxy * 2

                    newymin = miny - yscale
                    newymax = maxy + yscale

                    self.axes[axnum].set_xlim([newxmin, newxmax])
                    self.axes[axnum].set_ylim([newymin, newymax])

                #print data['title'], max(X)

                axnum = axnum + 1

        plt.draw()
        plt.pause(0.1)
        time.sleep(0.25)

        return self.lines,
