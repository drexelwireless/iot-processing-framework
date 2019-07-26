# array of strings to pass to plt.plot to plot each respective plot: color and dot type
# parallel arrays, these must have the same size
# plot markers: http://matplotlib.org/api/markers_api.html
# plot colors: http://matplotlib.org/api/colors_api.html
CL_plotcolors = ['b', 'r', 'g', 'c', 'm', 'y', 'k', 'b', 'r', 'b', 'c', 'm']
CL_plotdots   = ['o', 's', '^', 'v', '<', '>', '8', 'p', '*', 'h', '+', 'D'] 

class CoordinateList:
	def __init__(self, _epc96, _index):
		self.epc96 = _epc96
		self.coord_index = int(_index)

		self.xvals = []
		self.yvals = []
