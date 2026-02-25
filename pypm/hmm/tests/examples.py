def config(**kwds):
    return munch.DefaultMunch(None, **kwds)


# ---------------------------------------------------------------------------
# ex1
# ---------------------------------------------------------------------------

ex1 = """
resources:
  rA:
  rB:
  rC:

activities:

- dependencies:
  duration:
    max_hours: 4
    min_hours: 4
  resources:
    rB:
    rC:
  name: a1

- dependencies:
  - a1
  duration:
    max_hours: 5
    min_hours: 5
  resources:
    rA:
  name: a2
"""


# ---------------------------------------------------------------------------
# ex2
# ---------------------------------------------------------------------------

ex2 = """
resources:
  rA:
  rB:
  rC:

activities:

- dependencies:
  duration:
    max_hours: 4
    min_hours: 4
  resources:
    rB:
    rC:
  name: a1

- dependencies:
  - a1
  duration:
    max_hours: 5
    min_hours: 5
  resources:
    rA:
  name: a2

- dependencies:
  - a1
  duration:
    max_hours: 3
    min_hours: 3
  resources:
    rA:
  name: a3
"""


# ---------------------------------------------------------------------------
# ex3
# ---------------------------------------------------------------------------

ex3 = """
resources:
  rA:
  rB:
  rC:

activities:

- dependencies:
  duration:
    max_hours: 4
    min_hours: 4
  resources:
    rB:
    rC:
  name: a1

- dependencies:
  - a1
  - a3
  duration:
    max_hours: 5
    min_hours: 5
  resources:
    rA:
  name: a2

- dependencies:
  duration:
    max_hours: 3
    min_hours: 3
  resources:
    rA:
  name: a3
"""


# ---------------------------------------------------------------------------
# ex4
# ---------------------------------------------------------------------------

ex4 = """
resources:
  rA:
  rB:
  rC:

activities:

- dependencies:
  duration:
    max_hours: 4
    min_hours: 4
  resources:
    rB:
    rC:
  name: a1

- dependencies:
  - a1
  duration:
    max_hours: 5
    min_hours: 5
  resources:
    rA:
  name: a2

- dependencies:
  - a2
  - a4
  duration:
    max_hours: 3
    min_hours: 3
  resources:
    rA:
  name: a3

- dependencies:
  - a1
  duration:
    max_hours: 3
    min_hours: 3
  resources:
    rA:
  name: a4
"""


# ---------------------------------------------------------------------------
# ex5
# ---------------------------------------------------------------------------

ex5 = """
resources:
  rA:
  rB:
  rC:

activities:

- name: a1
  dependencies:
  duration:
    max_hours: 4
    min_hours: 4
  resources:
    rB:
    rC:

- name: a2
  dependencies:
  - a1
  duration:
    max_hours: 5
    min_hours: 5
  resources:
    rA:

- name: a3
  dependencies:
  - a2
  - a4
  duration:
    max_hours: 3
    min_hours: 3
  resources:
    rA:

- name: a4
  delay_after_hours: 5
  dependencies:
  - a1
  duration:
    max_hours: 3
    min_hours: 3
  resources:
    rA:
"""


# ---------------------------------------------------------------------------
# ex6
# ---------------------------------------------------------------------------

ex6 = """
resources:
  rA:
  rB:
  rC:

activities:

- name: a1
  delay_after_hours: 4
  dependencies:
  duration:
    max_hours: 4
    min_hours: 4
  resources:
    rB:
    rC:

- name: a2
  dependencies:
  - a1
  duration:
    max_hours: 5
    min_hours: 5
  resources:
    rA:

- name: a3
  dependencies:
  - a2
  - a4
  duration:
    max_hours: 3
    min_hours: 3
  resources:
    rA:

- name: a4
  delay_after_hours: 5
  dependencies:
  - a1
  duration:
    max_hours: 3
    min_hours: 3
  resources:
    rA:
"""

