Process Matching with Labeled Data
==================================

Pypm predicts the best alignment of a process with multi-dimensional
data. We say that data is *labeled* when the features in the data directly
correspond to the resources used in the process model.

Labeled Observations
--------------------

For example, consider the following excerpt of CSV data from the file
``data.csv``.  Each row in the file defines the observations
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


Matching Models
---------------

Pypm supports different matching models to allow for flexibility in the process execution that
may need to be considered when optimizing a schedule.  The following table summarizes these matching models:

+----------------------------------------------------------+----------+-----------------+------------+
| Name                                                     | Schedule | Activity Length | Allow Gaps |
+==========================================================+==========+=================+============+
| UnrestrictedMatches_FixedLengthActivities                | Flexible | Fixed           | No         |
+----------------------------------------------------------+----------+-----------------+------------+
| UnrestrictedMatches_VariableLengthActivities             | Flexible | Variable        | No         |
+----------------------------------------------------------+----------+-----------------+------------+
| UnrestrictedMatches_VariableLengthActivities_GapsAllowed | Flexible | Variable        | Yes        |
+----------------------------------------------------------+----------+-----------------+------------+
| CompactMatches_FixedLengthActivities                     | Compact  | Fixed           | No         |
+----------------------------------------------------------+----------+-----------------+------------+
| CompactMatches_VariableLengthActivities                  | Compact  | Variable        | No         |
+----------------------------------------------------------+----------+-----------------+------------+

Pypm optimizes schedules in two ways.  Unrestricted matches are completely
flexible;  the starting times of activities can occur at any time,
including before or after the time horizon of the available data.  The
only constraint on unrestricted matches is the precedence relationships
between activities, which are specified by activity dependencies in
the process model.  Compact matches schedule minimize the time between the
start of an activity and the end of all dependencies for that activity.
Thus, the schedule of compact matches is largely determined by the
starting times of the earliest scheduled activity with no dependencies.

Pypm supports two models for activity execution:  with fixed-length
activities and with variable-length activities.  When matching with
fixed-length activities, the ``min_hours`` or ``min_timesteps`` value is
used to specify the duration of each activity.  When matching with
variable-length activities, the duration used in a schedule may vary
between  ``min_hours`` and ``max_hours`` (or respectively ``min_timesteps``
and ``max_timesteps``).

Finally, some pypm models support gaps in the execution of activities.
These models are useful in applications where data includes natural
breaks (e.g. weekends or evenings), or where disruptions are expecting
in activity execution.

These different matching models have important implications for the
time required to generate a schedule that best aligns with the data.
The table above is roughly ordered by the time required to compute an
optimal match, from fastest to slowest.  However, it is important to
note that this ordering will depend on the optimization solver used to
optimize the schedule (see below).

The default model used in pypm is ``UnrestrictedMatches_VariableLengthActivities``. The configuration
file can specify the matching model used with the ``model`` key:

.. literalinclude:: ../pypm/tests/t13/config.yaml


