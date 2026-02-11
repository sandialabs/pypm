import os
import yaml
import pytest
from pypm.util.process_model import potentially_simultaneous_activities
from pypm.util.load import load_process
from pypm.util.fileutils import this_file_dir

currdir = this_file_dir()


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
    assert potentially_simultaneous_activities(pm) == [(), ("a1",), ("a2",)]


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
    assert potentially_simultaneous_activities(pm) == [
        (),
        ("a1",),
        ("a2",),
        ("a2", "a3"),
        ("a3",),
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
    assert potentially_simultaneous_activities(pm) == [
        (),
        ("a1",),
        ("a1", "a3"),
        ("a2",),
        ("a3",),
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
    assert potentially_simultaneous_activities(pm) == [
        (),
        ("a1",),
        ("a2",),
        ("a2", "a4"),
        ("a3",),
        ("a4",),
    ]


def test_ex5():
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
    assert potentially_simultaneous_activities(pm) == [
        (),
        ("a1",),
        ("a2",),
        ("a2", "a4"),
        ("a3",),
        ("a4",),
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
    assert potentially_simultaneous_activities(pm) == [
        (),
        ("a1",),
        ("a2",),
        ("a2", "a4"),
        ("a3",),
        ("a4",),
    ]


def test_example1():
    pm = load_process(filename=os.path.join(currdir, "example1.yaml"))

    assert len(pm) == 2
    assert potentially_simultaneous_activities(pm) == [(), ("a1",), ("a2",)]


def test_example2():
    pm = load_process(filename=os.path.join(currdir, "example2.yaml"))

    assert len(pm) == 2
    assert potentially_simultaneous_activities(pm) == [(), ("a1",), ("a2",)]


def test_example3():
    pm = load_process(filename=os.path.join(currdir, "example3.yaml"))

    assert len(pm) == 4
    assert potentially_simultaneous_activities(pm) == [
        (),
        ("a1",),
        ("a2",),
        ("a2", "a3"),
        ("a3",),
        ("a4",),
    ]


def test_example4():
    pm = load_process(filename=os.path.join(currdir, "example4.yaml"))

    assert len(pm) == 4
    assert potentially_simultaneous_activities(pm) == [
        (),
        ("a1",),
        ("a2",),
        ("a2", "a3"),
        ("a3",),
        ("a4",),
    ]
