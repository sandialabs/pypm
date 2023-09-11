Matching Constraints
====================

Pypm predicts the best alignment of a process with multi-dimensional data.
However, in practice there is often additional information that we would
like to integrate to inform or constraint this analysis.  For example,
we might know that:

* A specific activity was executed in the time window for our observations, or
* A specific activity was executed after a specified date, or
* A specific activity was started at a specified date.

This type of information can either constrain the search performed by
pypm, or constrain the solutions to include required scheduling values
(e.g. activity start times).  Clearly, this information is directly
relevant when analyzing labeled data.  But this information can also be
integrated into our analysis of unlabeled data.  The mappings generated
by tabu search are evaluated through a labeled process matching analysis,
which can again integrate this type of information.

Thus, the pypm API includes a variety of methods that tailor the
analysis to exploit application-specific information.  Although these
functions are documented in the API Reference, we summarize them here
for convenience.  Suppose that the **api** object is created using
the **PYPM.supervised_mip()** or **PYPM.tabu_labeling()** functions.
Then the following methods can be executed:

* **api.include(activity)** - Include the specified activity in the schedule.

* **api.include_all()** - Include all activities in the schedule.

* **api.set_earliest_start_date(activity, date)** - Set the earliest start date for the specified activity.

* **api.set_earliest_start_dates(date)** - Set the earliest start date for all activities.

* **api.set_latest_start_date(activity, date)** - Set the latest start date for the specified activity.

* **api.set_latest_start_dates(date)** - Set the latest start date for all activities.

* **api.fix_start_date(activity, date)** - Fix the start date for the specified activity.

* **api.relax(activity)** - Relax (unfix) the schedule of the specified activity.

* **api.relax_all()** - Relax (unfix) the schedule of all activities.

* **api.relax_start_date(activity)** - Relax (unfix) the start date of the specified activity.

* **api.relax_start_dates()** - Relax (unfix) the start dates of all activities.

* **api.set_activity_duration(activity, minval, maxval)** - Set the minimum and maximum duration of the specified activity.

These methods can be called in any order before performing optimization,
but the order of execution is meaningful.  In particular, relaxing
the constraints will eliminate information about prior constraints.
The **remove_constraints()** method can be used to remove *all*
constraints in the API.
