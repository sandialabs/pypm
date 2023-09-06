Process Matching with Labeled Data
==================================

Pypm predicts the best alignment of a process with multi-dimensional
data. We say that data is *labeled* when the features in the data directly
correspond to the resources used in the process model.

Labeled Observations
--------------------

For example, consider the following excerpt of CSV data from the file
``observations.csv``.  Each row in the file defines the observations
associated with the features ``A`` through ``E`` at a specific date-time.
The values of each observations are assumed to lie in the interval
[0,1]. Zero indicates no observation of a resource, one indicates an
observation of a resource, and values in-between reflect a weighted
observation.

.. literalinclude:: ../pypm/tests/t1/data.csv
    :lines: 1-30

A Simple Example
----------------

The following script illustrates a simple use of the pypm API:

.. code-block::

    # Create the pypm solver for supervised process matching
    >>> pm = PYPM.supervised_mip()

    # Load options from a YAML configuration file, including
    # the specification of the observations
    >>> pm.load_config("config.yaml")

    # Generate a schedule for the process that aligns with the data
    >>> results = pm.generate_schedule()

    # Write out the results to a YAML file
    >>> results.write("results.yaml")

The configuration file supports a variety of customizations for process
matching, which enables the use of relatively simple scripts for pypm.
For example, the following configuration file specifies the process
model and observations:

.. literalinclude:: ../pypm/tests/t1/config.yaml

The YAML results file includes a detailed description of the predicted
schedule.  For example:

.. literalinclude:: ../pypm/tests/t1/baseline.yaml

.. note::

    What does it mean if Gamma is omitted?  I think we want Gamma=0 to be the default.

