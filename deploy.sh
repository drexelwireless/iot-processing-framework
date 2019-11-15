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
sudo python3 -m pip uninstall pip && sudo apt install -y python3-pip --reinstall
sudo apt-get -y install python-dev
sudo apt-get -y install python3-dev
pip3 --user install --upgrade pip

sudo apt-get -y install libcurl4-openssl-dev
sudo apt-get -y install libffi-dev
sudo apt-get -y install libssl-dev
export PYCURL_SSL_LIBRARY=openssl

pip3 --user install service_identity
sudo apt-get install python3-matplotlib # was python-matplotlib
sudo apt-get install libblas-dev liblapack-dev libatlas-base-dev gfortran

pip3 --user install flask
pip3 --user install numpy
pip3 --user install scipy
pip3 --user install pycurl --global-option="--with-openssl"
pip3 --user install pycrypto
pip3 --user install python-dateutil

# Packages needed by common ML/DSP systems that depend on the IOT Sensor Framework
pip3 --user install pandas
pip3 --user install filterpy

#httplib2 default installation is incompatible with Python 3 when using SSL
PKGDIRS=`python -c "import site; p=site.getsitepackages(); print('\n'.join(str(x) for x in p))"`
for P in PKGDIRS
do
        find $P -iname '*httplib2*' -exec sudo mv {} /tmp
done
pip3 --user install httplib2 # may need to manually remove and then upgrade to fix a bug in httplib2 regarding verifying SSL certificates

pip3 --user install werkzeug
#pip3 --user install hashlib
pip3 --user install sklearn
pip3 --user install pykalman
pip3 --user install scikit-image
pip3 --user install peakutils
pip3 --user install hmmlearn
pip3 --user install statsmodels 

pip3 --user install seaborn

pip3 --user install --upgrade pip
pip3 --user install --upgrade filterpy # this upgrades numpy / scipy stack

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
