# pypm.util.load

from .process_model import ProcessModel
import yaml
import os.path


def load_process(filename=None, dirname=None, data={}):
    """
    Load the process from a YAML file.

    This function loads data either from a file or a data dictionary.

    Args
    ----
    filename : string, Default: None
        The filename of the YAML file that describes the process.
    dirname : string, Default: None
        The directory where the file *filename* is found.
    data : dict, Default: {}
        The dictionary that describes the process.

    Returns
    -------
    ProcessModel
        An object that has been initialized with the process description.
    """
    if filename is not None:
        if not dirname is None:
            filename = os.path.join(dirname, filename)
        print("Opening file:", filename)
        with open(filename, 'r') as INPUT:
            data=next(yaml.safe_load_all(INPUT))
    elif type(data) is str:
        data=next(yaml.safe_load_all(data))
    return ProcessModel(data=data)

