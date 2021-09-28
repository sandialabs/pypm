# pypm
"""
pypm

This package defines methods for analyzing collections of time series
data to identify whether the execution of a known process is reflected
in the data.  This capability provides the ability to both detect and
characterize process execution using indirect measures. We call this
capability *process matching*.

Pypm includes a variety of methods for process matching, including both
dynamic programming and optimization algorithms.  Additionally, pypm
includes different formulations that reflect knowledge and constraints
on the matched solutions.  In particular, pypm includes *supervised
process matching* methods that assumed that the data is well-labeled,
as well as *unsupervised process matching* methods that assume the data
is unlabeled.  Unsupervised methods simultaneously label the data and
align the process with the data.

Version: %s
"""

from pypm._version import __version__
__doc__ = __doc__ % __version__

__all__ = ('__version__')

from . import util
from . import pypm
from . import mip
from . import vis
from . import chunk
