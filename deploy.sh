#!/bin/bash

if [[ -z `which python3` ]]
then
        alias python3="python"
        alias pip3="pip"
fi

sudo apt-get update

sudo apt-get -y install python3.6
sudo apt-get -y install python-pip
sudo apt-get -y install python3-pip
sudo apt-get -y install python-dev
sudo apt-get -y install python3-dev
sudo pip3 install --upgrade pip

sudo apt-get -y install libcurl4-openssl-dev
sudo apt-get -y install libffi-dev
sudo apt-get -y install libssl-dev
export PYCURL_SSL_LIBRARY=openssl

sudo pip3 install service_identity
sudo apt-get install python3-matplotlib # was python-matplotlib
sudo apt-get install libblas-dev liblapack-dev libatlas-base-dev gfortran

sudo pip3 install flask
sudo pip3 install numpy
sudo pip3 install scipy
sudo pip3 install pycurl --global-option="--with-openssl"
sudo pip3 install pycrypto
sudo pip3 install python-dateutil

# Packages needed by common ML/DSP systems that depend on the IOT Sensor Framework
sudo pip3 install pandas
sudo pip3 install filterpy

#httplib2 default installation is incompatible with Python 3 when using SSL
PKGDIRS=`python -c "import site; p=site.getsitepackages(); print('\n'.join(str(x) for x in p))"`
for P in PKGDIRS
do
        find $P -iname '*httplib2*' -exec sudo mv {} /tmp
done
sudo pip3 install httplib2 # may need to manually remove and then upgrade to fix a bug in httplib2 regarding verifying SSL certificates

sudo pip3 install werkzeug
sudo pip3 install hashlib
sudo pip3 install sklearn
sudo pip3 install pykalman
sudo pip3 install scikit-image
sudo pip3 install peakutils
sudo pip3 install hmmlearn
sudo pip3 install statsmodels 

sudo pip3 install --upgrade pip
sudo pip3 install --upgrade filterpy # this upgrades numpy / scipy stack

sudo apt-get install libgsl0-dev
sudo apt-get install libgsl0ldbl
#sudo pip install git+https://github.com/ajmendez/PyMix.git
git clone https://github.com/ajmendez/PyMix.git
touch PyMix/README.rst
sed 's/from distutils.core import setup, Extension,DistutilsExecError/#from distutils.core import setup, Extension,DistutilsExecError\nfrom distutils.core import setup, Extension' PyMix/setup.py
sed "s/numpypath =  prefix + '\/lib\/python' +pyvs + '\/site-packages\/numpy\/core\/include\/numpy'  # path to arrayobject.h/#numpypath =  prefix + '\/lib\/python' +pyvs + '\/site-packages\/numpy\/core\/include\/numpy'  # path to arrayobject.h\n    try:\n        import numpy\n        numpypath = os.path.join(numpy.get_include(), 'numpy')\n    except ImportError:\n        raise ImportError("Unable to import Numpy, which is required by PyMix")\n/g" PyMix/setup.py
sed -i 's/^as =/dummy =/g' PyMix/AminoAcidPropertyPrior.py
find ./PyMix -iname '*.py' -exec 2to3 -w {} \;
python3 PyMix/setup.py install
