import os
if os.path.exists(os.path.join(\
    os.path.dirname(os.path.dirname(__file__)), 'py2app_setup.py')):
    raise ImportError('PyMca cannot be imported from source directory')

# mandatory modules for compatibility
from .PyMcaCore import Plugin1DBase, StackPluginBase, PyMcaDirs, DataObject

#convenience modules that could be directly imported
# using from PyMca5.PyMca import 
try:
    from .PyMcaIO import specfilewrapper, EdfFile, specfile, ConfigDict
except:
    print("WARNING importing IO directly")
    from PyMcaIO import specfilewrapper, EdfFile, specfile, ConfigDict

from .PyMcaMath.fitting import SpecfitFuns, Gefit, Specfit
from .PyMcaMath.fitting import SpecfitFunctions

# this one is slow and responsible of the lost of time
from .PyMcaPhysics import Elements

#all the rest can be imported using from PyMca5.PyMca import ...
from . import PyMca
