<h1 align="center">Pypm</h1>
<p align="center">
Process-informed detection of patterns in time series data.
</p>

## Overview

<!-- start overview -->

Pypm supports the analysis of time series data to identify patterns that
reflect the execution of a known process.  Pypm uses a **process model**
to identify patterns, where the execution of a process is decomposed
into a sequence of related activities.  A process model describes the
activities used in the process, dependencies between activities that
constrain their execution, resources needed to execute each activity
and information about the activities that are observable.

Pypm implements *process matching* algorithms that infer a schedule
of the activities in a process model to maximize the alignement of the
process with observational data.  Pypm uses numerical optimization to
search for a maximal match score.  When data is labeled and associated
with the resources in the process model, then integer programming
methods are used to find an optimal match.  For unlabeled data, tabu
search methods are used to predict data labels, which can then be used
by integer programming methods.

Pypm solvers address a variety of complicating concerns, including
variable-duration process activities, gaps in activity execution,
preferences for compact matches, and tailored methods that depend on
data characteristics.

<!-- end overview -->

## Installation For Development

* git clone git@github.com:sandialabs/pypm.git
* cd pypm
* pip install -e .

## Testing

* cd pypm
* pytest
* pytest --cov=pypm --cov-report term-missing

## Acknowledgements

The initial release of pypm was developed by Dylan Anderson, William Hart and Vitus Leung.
