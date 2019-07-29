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
wmm24@cs.drexel.edu
See license for license information
