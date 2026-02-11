import os
import yaml
import pytest
from pypm.util.load import load_process
from pypm.util.run_simian import run_simian
from pypm.util.fileutils import this_file_dir

currdir = this_file_dir()
quiet = True


def test_ex1():
    """
    a1 -> a2
    """
    data = """
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
    pm = load_process(data=data)

    assert len(pm) == 2

    data = run_simian(pm=pm, num_time_steps=10, seed=123456789, quiet=quiet)
    assert data[0] == [
        (0, ("a1",)),
        (1, ("a1",)),
        (2, ("a1",)),
        (3, ("a1",)),
        (4, ("a2",)),
        (5, ("a2",)),
        (6, ("a2",)),
        (7, ("a2",)),
        (8, ("a2",)),
        (9, ()),
    ]

    data = run_simian(
        pm=pm, num_time_steps=20, max_delay_before=5, seed=123456789, quiet=quiet
    )
    assert data[0] == [
        (0, ()),
        (1, ()),
        (2, ()),
        (3, ()),
        (4, ("a1",)),
        (5, ("a1",)),
        (6, ("a1",)),
        (7, ("a1",)),
        (8, ()),
        (9, ()),
        (10, ("a2",)),
        (11, ("a2",)),
        (12, ("a2",)),
        (13, ("a2",)),
        (14, ("a2",)),
        (15, ()),
        (16, ()),
        (17, ()),
        (18, ()),
        (19, ()),
    ]


def test_ex2():
    """
    a1 -> a2
    a1 -> a3
    """
    data = """
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
    pm = load_process(data=data)

    assert len(pm) == 3

    data = run_simian(pm=pm, num_time_steps=10, seed=123456789, quiet=quiet)
    assert data[0] == [
        (0, ("a1",)),
        (1, ("a1",)),
        (2, ("a1",)),
        (3, ("a1",)),
        (4, ("a2", "a3")),
        (5, ("a2", "a3")),
        (6, ("a2", "a3")),
        (7, ("a2",)),
        (8, ("a2",)),
        (9, ()),
    ]

    data = run_simian(
        pm=pm, num_time_steps=20, max_delay_before=5, seed=123456789, quiet=quiet
    )
    assert data[0] == [
        (0, ()),
        (1, ()),
        (2, ()),
        (3, ()),
        (4, ("a1",)),
        (5, ("a1",)),
        (6, ("a1",)),
        (7, ("a1",)),
        (8, ()),
        (9, ()),
        (10, ()),
        (11, ("a3",)),
        (12, ("a3",)),
        (13, ("a2", "a3")),
        (14, ("a2",)),
        (15, ("a2",)),
        (16, ("a2",)),
        (17, ("a2",)),
        (18, ()),
        (19, ()),
    ]


def test_ex3():
    """
    a1 -> a2
    a3 -> a2
    """
    data = """
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
    pm = load_process(data=data)

    assert len(pm) == 3

    data = run_simian(pm=pm, num_time_steps=10, seed=123456789, quiet=quiet)
    assert data[0] == [
        (0, ("a1", "a3")),
        (1, ("a1", "a3")),
        (2, ("a1", "a3")),
        (3, ("a1",)),
        (4, ("a2",)),
        (5, ("a2",)),
        (6, ("a2",)),
        (7, ("a2",)),
        (8, ("a2",)),
        (9, ()),
    ]

    data = run_simian(
        pm=pm, num_time_steps=20, max_delay_before=5, seed=123456789, quiet=quiet
    )
    assert data[0] == [
        (0, ()),
        (1, ()),
        (2, ("a1",)),
        (3, ("a1", "a3")),
        (4, ("a1", "a3")),
        (5, ("a1", "a3")),
        (6, ()),
        (7, ()),
        (8, ()),
        (9, ("a2",)),
        (10, ("a2",)),
        (11, ("a2",)),
        (12, ("a2",)),
        (13, ("a2",)),
        (14, ()),
        (15, ()),
        (16, ()),
        (17, ()),
        (18, ()),
        (19, ()),
    ]


def test_ex4():
    """
    a1 -> a2 -> a3
    a1 -> a4 -> a3
    """
    data = """
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
    pm = load_process(data=data)

    assert len(pm) == 4

    data = run_simian(pm=pm, num_time_steps=15, seed=123456789, quiet=quiet)
    assert data[0] == [
        (0, ("a1",)),
        (1, ("a1",)),
        (2, ("a1",)),
        (3, ("a1",)),
        (4, ("a2", "a4")),
        (5, ("a2", "a4")),
        (6, ("a2", "a4")),
        (7, ("a2",)),
        (8, ("a2",)),
        (9, ("a3",)),
        (10, ("a3",)),
        (11, ("a3",)),
        (12, ()),
        (13, ()),
        (14, ()),
    ]

    data = run_simian(
        pm=pm, num_time_steps=20, max_delay_before=5, seed=123456789, quiet=quiet
    )
    assert data[0] == [
        (0, ()),
        (1, ()),
        (2, ()),
        (3, ()),
        (4, ("a1",)),
        (5, ("a1",)),
        (6, ("a1",)),
        (7, ("a1",)),
        (8, ()),
        (9, ()),
        (10, ()),
        (11, ("a4",)),
        (12, ("a4",)),
        (13, ("a2", "a4")),
        (14, ("a2",)),
        (15, ("a2",)),
        (16, ("a2",)),
        (17, ("a2",)),
        (18, ()),
        (19, ()),
    ]


def test_ex5():
    """
        a1 -> a2 -> a3
        a1 -> a4 -> a3

    Activity a4 has a delay after completing
    """
    data = """
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
    pm = load_process(data=data)

    assert len(pm) == 4

    data = run_simian(pm=pm, num_time_steps=16, seed=123456789, quiet=quiet)
    assert data[0] == [
        (0, ("a1",)),
        (1, ("a1",)),
        (2, ("a1",)),
        (3, ("a1",)),
        (4, ("a2", "a4")),
        (5, ("a2", "a4")),
        (6, ("a2", "a4")),
        (7, ("a2",)),
        (8, ("a2",)),
        (9, ()),
        (10, ()),
        (11, ()),
        (12, ("a3",)),
        (13, ("a3",)),
        (14, ("a3",)),
        (15, ()),
    ]

    data = run_simian(
        pm=pm, num_time_steps=30, max_delay_before=5, seed=123456789, quiet=quiet
    )
    assert data[0] == [
        (0, ()),
        (1, ()),
        (2, ()),
        (3, ()),
        (4, ("a1",)),
        (5, ("a1",)),
        (6, ("a1",)),
        (7, ("a1",)),
        (8, ()),
        (9, ()),
        (10, ()),
        (11, ("a4",)),
        (12, ("a4",)),
        (13, ("a2", "a4")),
        (14, ("a2",)),
        (15, ("a2",)),
        (16, ("a2",)),
        (17, ("a2",)),
        (18, ()),
        (19, ()),
        (20, ()),
        (21, ()),
        (22, ("a3",)),
        (23, ("a3",)),
        (24, ("a3",)),
        (25, ()),
        (26, ()),
        (27, ()),
        (28, ()),
        (29, ()),
    ]


def test_ex6():
    """
        a1 -> a2 -> a3
        a1 -> a4 -> a3

    Activity a4 has a delay starting
    """
    data = """
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
    pm = load_process(data=data)

    assert len(pm) == 4

    data = run_simian(pm=pm, num_time_steps=20, seed=123456789, quiet=quiet)
    assert data[0] == [
        (0, ("a1",)),
        (1, ("a1",)),
        (2, ("a1",)),
        (3, ("a1",)),
        (4, ()),
        (5, ()),
        (6, ()),
        (7, ()),
        (8, ("a2", "a4")),
        (9, ("a2", "a4")),
        (10, ("a2", "a4")),
        (11, ("a2",)),
        (12, ("a2",)),
        (13, ()),
        (14, ()),
        (15, ()),
        (16, ("a3",)),
        (17, ("a3",)),
        (18, ("a3",)),
        (19, ()),
    ]

    data = run_simian(
        pm=pm, num_time_steps=30, max_delay_before=5, seed=123456789, quiet=quiet
    )
    assert data[0] == [
        (0, ()),
        (1, ()),
        (2, ()),
        (3, ()),
        (4, ("a1",)),
        (5, ("a1",)),
        (6, ("a1",)),
        (7, ("a1",)),
        (8, ()),
        (9, ()),
        (10, ()),
        (11, ()),
        (12, ()),
        (13, ()),
        (14, ()),
        (15, ("a4",)),
        (16, ("a4",)),
        (17, ("a2", "a4")),
        (18, ("a2",)),
        (19, ("a2",)),
        (20, ("a2",)),
        (21, ("a2",)),
        (22, ()),
        (23, ()),
        (24, ()),
        (25, ()),
        (26, ("a3",)),
        (27, ("a3",)),
        (28, ("a3",)),
        (29, ()),
    ]


def test_ex7():
    """
    Example3 has parallel activities that are run simultaneously.
    """
    pm = load_process(filename=os.path.join(currdir, "example3.yaml"))

    assert len(pm) == 4

    data = run_simian(pm=pm, num_time_steps=25, seed=1234567, quiet=quiet)
    assert data[0] == [
        (0, ("a1",)),
        (1, ("a1",)),
        (2, ("a1",)),
        (3, ("a1",)),
        (4, ("a1",)),
        (5, ("a1",)),
        (6, ("a1",)),
        (7, ("a1",)),
        (8, ("a2", "a3")),
        (9, ("a2", "a3")),
        (10, ("a2", "a3")),
        (11, ("a2",)),
        (12, ("a2",)),
        (13, ("a4",)),
        (14, ("a4",)),
        (15, ("a4",)),
        (16, ("a4",)),
        (17, ()),
        (18, ()),
        (19, ()),
        (20, ()),
        (21, ()),
        (22, ()),
        (23, ()),
        (24, ()),
    ]

    data = run_simian(
        pm=pm, num_time_steps=35, max_delay_before=5, seed=123456789, quiet=quiet
    )
    assert data[0] == [
        (0, ()),
        (1, ()),
        (2, ()),
        (3, ("a1",)),
        (4, ("a1",)),
        (5, ("a1",)),
        (6, ("a1",)),
        (7, ("a1",)),
        (8, ("a1",)),
        (9, ("a1",)),
        (10, ("a1",)),
        (11, ("a1",)),
        (12, ("a1",)),
        (13, ()),
        (14, ()),
        (15, ()),
        (16, ("a3",)),
        (17, ("a3",)),
        (18, ("a2", "a3")),
        (19, ("a2", "a3")),
        (20, ("a2", "a3")),
        (21, ("a2", "a3")),
        (22, ()),
        (23, ()),
        (24, ("a4",)),
        (25, ("a4",)),
        (26, ("a4",)),
        (27, ("a4",)),
        (28, ("a4",)),
        (29, ()),
        (30, ()),
        (31, ()),
        (32, ()),
        (33, ()),
        (34, ()),
    ]
