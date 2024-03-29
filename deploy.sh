#!/bin/bash

sudo apt-get update

sudo apt-get -y install python3.6
sudo apt-get -y install python-pip
sudo apt-get -y install python3-pip
sudo apt-get -y install python-dev
sudo apt-get -y install python3-dev
pip3 install --user --upgrade pip

sudo apt-get -y install libcurl4-openssl-dev
sudo apt-get -y install libffi-dev
sudo apt-get -y install libssl-dev
export PYCURL_SSL_LIBRARY=openssl

pip3 install --user service_identity
sudo apt-get install python3-matplotlib # was python-matplotlib
sudo apt-get install libblas-dev liblapack-dev libatlas-base-dev gfortran

pip3 install --user flask
pip3 install --user numpy
pip3 install --user scipy
pip3 install --user pycurl --global-option="--with-openssl"
pip3 install --user pycryptodome
pip3 install --user python-dateutil

# Packages needed by common ML/DSP systems that depend on the IOT Sensor Framework
pip3 install --user pandas
pip3 install --user filterpy

pip3 install --user 2to3
sudo apt-get install 2to3

#httplib2 default installation is incompatible with Python 3 when using SSL
PKGDIRS=`python3 -c "import site; p=site.getsitepackages(); print('\n'.join(str(x) for x in p))"`
USERSITE=`python3 -m site --user-site`
for P in "$PKGDIRS"
do
        find $P -iname '*httplib2*' -exec sudo mv '{}' /tmp \;
done
pushd $USERSITE 
find $P -iname '*httplib2*' -exec sudo mv '{}' /tmp \;
popd

pip3 install --user httplib2 # may need to manually remove and then upgrade to fix a bug in httplib2 regarding verifying SSL certificates

pip3 install --user adaptfilt
# upgrade adaptfilt to python3
for P in "$PKGDIRS"
do
        pushd $P/adaptfilt && 2to3 -w *.py && popd
done
pushd $USERSITE/adaptfilt && 2to3 -w *.py && popd

pip3 install --user werkzeug
#pip3 install --user hashlib
# pip3 install --user sklearn
pip3 install --user scikit-learn
pip3 install --user pykalman
pip3 install --user padasip
pip3 install --user scikit-image
pip3 install --user peakutils
pip3 install --user hmmlearn
pip3 install --user statsmodels 
pip3 install --user pyserial

pip3 install --user seaborn

pip3 install --user --upgrade pip
pip3 install --user --upgrade filterpy # this upgrades numpy / scipy stack

sudo apt-get install libgsl0-dev
#sudo apt-get install libgsl0ldbl

sudo apt-get install tcl-dev tk-dev python-tk python3-tk

#sudo pip install git+https://github.com/ajmendez/PyMix.git
pip3 install --user git+https://github.com/BillJr99/PyMix.git
#pushd /tmp
#git clone https://github.com/ajmendez/PyMix.git
#touch PyMix/README.rst
#sed -i 's/from distutils.core import setup, Extension,DistutilsExecError/#from distutils.core import setup, Extension,DistutilsExecError\nfrom distutils.core import setup, Extension/g' PyMix/setup.py
#sed -i 's/numpypath =  prefix + "\/lib\/python" +pyvs + "\/site-packages\/numpy\/core\/include\/numpy"  # path to arrayobject.h/#numpypath =  prefix + "\/lib\/python" +pyvs + "\/site-packages\/numpy\/core\/include\/numpy"  # path to arrayobject.h\n    try:\n        import numpy\n        numpypath = os.path.join(numpy.get_include(), "numpy")\n    except ImportError:\n        raise ImportError("Unable to import Numpy, which is required by PyMix")\n/g' PyMix/setup.py
#sed -i 's/as =  alpha/dummy = alpha/g' PyMix/pymix/AminoAcidPropertyPrior.py
#pushd PyMix
#find . -iname '*.py' -exec 2to3 -w '{}' \;
#python3 setup.py install --user
#popd
#popd
