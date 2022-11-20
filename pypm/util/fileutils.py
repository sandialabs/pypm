# Adapted from Pyutilib2 and Pyomo

import inspect
import os


def this_file(stack_offset=1):
    """
    Returns the file name for the module that calls this function.

    This function is more reliable than __file__ on platforms like
    Windows and in situations where the program has called
    ``os.chdir()``.

    Args
    ----
    stack_offset : int, Default: 1
        Specify the offset from the current stack, to identify the caller frame
        that was executed from a file import

    Returns
    -------
    The filename of the file that Python imported.
    """
    # __file__ fails if script is called in different ways on Windows
    # __file__ fails if someone does os.chdir() before
    # sys.argv[0] also fails because it does not always contains the path
    callerFrame = inspect.currentframe()
    while stack_offset:
        callerFrame = callerFrame.f_back
        stack_offset -= 1
    frameName = callerFrame.f_code.co_filename
    if frameName and frameName[0] == "<" and frameName[-1] == ">":
        return frameName
    return os.path.abspath(inspect.getfile(callerFrame))


def this_file_dir():
    """
    Returns the directory containing the module that calls this function.
    """
    return os.path.dirname(this_file(stack_offset=2))
