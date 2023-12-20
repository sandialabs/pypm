Process Models
==============

Process Description
-------------------

Pypm considers process models that describe the execution of *activities*
that represent the steps in a process.  Activities define the basic
unit of work in a process, and they have following features:

* **name** - An activity has a unique name
* **resources** - The execution of an activity may require one-or-more resources.  The resources used by an activity can generate observations.
* **dependencies** - The execution of an activity may require the completion of one-or-more activities in the process, including the delay after the activity is executed.
* **duration** - An activity has a minimum and maximum duration, which is an integer value defined in hours or timesteps.
* **delay** - An activity may have a delay after execution before dependent activities can be executed.

The delay following an activity is used to model processes where resources
are used during execution followed by a quiescent time period where no
resources are required.  For example, a painting activity would involve
a delay that models the time required for paint to dry.

Finally, note that pypm requires the activities in a process model to form
an acyclic graph. Cycles and repeated execution execution of activities
is disallowed.

YAML Process Specification
--------------------------

The following example illustrates the YAML data format that is used to
specify a process.  The top-level dictionary includes **resources** and
**activities** to define the resources and activities in the process.
Resources are defined in a dictionary with empty values.  Activities are
defined in an unordered list.  Each activity is defined with a dictionary
where the name, duration, delay, resources and dependencies are specified.

.. literalinclude:: ../pypm/tests/t1/process.yaml

This example illustrates the specification of a process where duration
values are in hours.  Alternatively, a process can be specified using
timesteps.  The **delay_after_hours**, **max_hours** and **min_hours**
keys are respectively replaced with **delay_after_timesteps**,
**max_timesteps** and **min_timesteps**.  Additionally, the top-level
dictionary must include the key **hours_per_timestep** to translate
timesteps into real time.

