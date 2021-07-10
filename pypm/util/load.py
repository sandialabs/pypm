# pypm.util.load

from .process_model import ProcessModel
import yaml
import os.path


def load_data(filename=None, dirname=None, data=None):
    if data is None:
        if not dirname is None:
            filename = os.path.join(dirname, filename)
        print("Opening file: ", filename)
        with open(filename, 'r') as INPUT:
            yamldata=yaml.safe_load(INPUT)
    else:
        yamldata=yaml.safe_load(data)
    return ProcessModel(data=yamldata)

