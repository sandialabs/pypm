# pypm

Python software package for Process Matching.

## Installation

* git clone git@cee-gitlab.sandia.gov:adapd/pypm.git
* cd pypm
* python setup.py develop

## Example

* cd examples/linear1
* pypm sim sim.yaml linear1.yaml
* pypm mip linear1\_sim.yaml 0

## Testing

* pytest
* pytest --cov=pypm --cov-report term-missing
