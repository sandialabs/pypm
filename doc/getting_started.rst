Getting Started
===============

Installing pypm
---------------

This software can be installed using **pip**:

.. code-block::

    >>> pip install https://github.com/sandialabs/pypm

This installation includes all required dependencies except for
optimization solvers.  Pypm depends on integer programming solvers,
which must be installed separatly.

Installing Integer Programming Solvers
--------------------------------------

The **conda** environment simplifies the installation of several integer
programming solvers:

* **glpk**

    .. code-block::

        >>> conda install glpk

* **cbc**

    .. code-block::

        >>> conda install coin-cbc

* **scip**

    .. code-block::

        >>> conda install scip



