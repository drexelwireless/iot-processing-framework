[![v1.1 Release DOI, 5/13/2020](https://zenodo.org/badge/DOI/10.5281/zenodo.3786930.svg)](https://doi.org/10.5281/zenodo.3786930)

# IoT Sensor Framework Processing and Visualization

This software suite contains scripts to visualize and process signals from the Iot Sensor Framework.

*Note: These instructions assume that the web server, interrogation and
visualizer will be run on the same machine (IP addresses in all shell scripts
have been set to `localhost`).  The host, port, keys, and other parameters can be set when running the scripts in the instructions.  We also assume that the IoT Sensor Framework database is running.

### Requirements
The following software packages need to be installed before running these modules. 
You will have to use the same install method (such as
`pip install` or `easy_install`) listed here. Also, alternatives to using
`sudo` for `pip install` are  `sudo -H pip install <package-name>` or
`pip install --user <package-name>`.

Packages: 
See the Dockerfile in each subdirectory for deployment instructions; these can be executed manually for a local installation, or containerized using Docker.  The deploy.sh script will handle the installation.

On Cygwin, you may need to set `export MPLBACKEND=Qt4Agg` to use with matplotlib.

This package assumes an installation of python3 and pip3.

### System Architecture
#### Visualizer
Each tag and antenna 
are plotted on the same graph and color coded.  The Visualizer is invoked on a running 
server via \texttt{python3 visualizer.py}, with an optional \texttt{-i} parameter to 
specify ``simulated'' mode as described previously.

#### Detector Processing Module
The `Detector` `get\_data()` method
returns a dictionary structure containing the structure as shown
in the Listing below.

The dictionary is populated with arrays of x and y values.  If multiple plots are desired, 
additional x/y arrays can be provided within the `data` subobject.  To group them,
the `X` and `Y` objects are specified as parallel arrays (note that the first
entry in `X` and the first entry in `Y` specify the name of the arrays
in the `data` subobject to be used for the corresponding x and y values.  The 
labels for these plots are given as an identically-structured parallel array and, finally
the title is given.  The `Plotter` will automatically poll this function for 
new data in these arrays, and update the plot just as the `Visualizer` module does.

``
"xlabel": ["Axis Label", ...],
"ylabel": ["Axis Label", ...],
"X": ["x-timestamp", ...],
"Y": ["y-rssi", ...],
"title": "Title of the Plot",
"data": {
    "x-timestamp": [0, 1, 2, ...]
    "y-rssi": [0, 5, 10, ...]
    ...
}
``

The `Processor` implementation object is populated automatically by the 
superclass interface with data as it is polled from the server.  
The `process_loop()` function can access this data through its `self.df` 
Pandas Dataframe, maintained by the superclass `Processor`.  Here, the data can 
be queried, processed, and visualized according to a selected algorithm.  The 
`Processor` is invoked by calling 
`python3 detector.py processor\_test.TestProcessor` 
(again with an optional `-i` parameter 
for "simulated mode").  The `processor_test.TestProcessor` corresponds to the 
name of the file and class to be invoked by the `Detector`: in this example,
is assumed that a class called `TestProcessor`, which extends `Processor` and is 
implemented in a file `processor_test.py`.  For consistency, all such modules
are named according to a common format, such that
`processor_some.py` contains a class called `SomeProcessor` (Note that only the first letter of the class name is capitalized along with the "P" in "Processor").

#### Sensor Fusion Framework
The `Measure` subclass requires implementing only one method: `process().  
This method uses the same `self.df` Pandas DataFrame used by the `Processor`,
and is populated by RESTful calls to the database server made automatically by the 
superclass.  If a `Perturber` subclass is provided, it will be called by the 
`Sensor` to manipulate the data and introduce probabilistic noise artifacts.  
Subclasses of `Perturber` implement a method `perturb(body)` which accepts 
an array of dictionaries containing the data.
Next, a `Fuser` subclass is instantiated if it is provided in the `Sensor` 
class implementation.  It accepts a maxtrix of measurements (one vector of all historical measurements computed by each `Measure` objects during each processing iteration)  
and a sliding window size specifying how many of the most recent measurements to consider,
and applies a fusion strategy 
such as a voting classifier, a Mixture Model, a Kalman Filter, or Maximum Likelihood
Estimation, to compute a fused measurement.  This is passed to a `Ground Truth` 
module, if one is provided; this module contains one method called `truth(time)`, 
which accepts the current time as a parameter, and returns the ground-truth value 
corresponding to that time.  The `Sensor` computes the Root Mean Squared (RMS) error
from this ground truth and the fused estimates.  Like the `Detector`, the 
`Fusion Framework` is invoked as follows:
`python3 simulator.py sensor_fusion.FusionSensor`

### Instructions (Running framework on localhost for testing/development)
Start the following components in the order presented below.

#### Create a processing module
* Create a module sensor_your.py with a class called YourSensor inside.
* This class should extend the Sensor class
* Implement a constructor that invokes the superclass constructor
* Impmenent a `start(self,body)` method that passes the `body` argument to the superclass `start` method.
* The v2 module should also create measure_your.py modules with YourMeasure classes inside (that extend the Measure class).  These should be instantiated in the sensor_your.py module for automated fusion.  Optionally create and add data perturbation modules and ground truth error measurement.

#### Run a processing module
* Change into the `fusionframework_v1` directory (or `fusionframework_v2` or
other processing unit as appropriate)
* Run `./simulate.sh sensor_test.TestSensor` (replace with
`sensor_your.YourSensor` for a YourSensor class written into the sensor_your.py
file)
* The Fusion Framework is conducive for prototyping ML or DSP algorithms against a dataset running on the server.  For real-time deployment, use the Detector module.  Its execution is similar to the Fusion Framework.

#### Visualization
* Change into the Visualizer subdirectory.
* Execute the `./live.sh` (for real-time data collection) or `./simulate.sh` for offline visualization of an existing dataset.
* To quit: in the directory running the visualizer, create a file called 'quit'.

----

## Containerization
*TODO*: This section should be considered WIP. Add updates to this section until
the full software stack is capable or independently running containerized.

### Software Requirements
1. [Docker](https://www.docker.com/products/docker-engine)
2. [Docker Compose](https://docs.docker.com/compose/)

### Using the Containers
#### Container Build & Startup
```
$ docker-compose build
$ docker-compose up
```

#### Container Shutdown
```
$ docker-compose down
```

## Development Guidelines
### Formatting Python
Install the `autopep8` code formatting tool.
```
pip install autopep8
```
Run the following command from within the root directory of the repository.
```
autopep8 --in-place --recursive .
```
In the future we may want to use the `--aggressive` option to make
non-whitespace style changes.

## License
Copyright 2014 William M. Mongan
billmongan@gmail.com
See license for license information
