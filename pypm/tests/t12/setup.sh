#!/bin/sh

step="10h_workday(7-17)"

_main() {
    echo ""
    echo "*** Chunking data ***"
    echo ""
    pypm chunk -c ../t1/data.csv -s $step -o data.csv -i DateTime
    echo ""
    echo "*** Chunking process ***"
    echo ""
    pypm chunk -p ../t1/process.yaml -s $step -o process.yaml
}

_main | tee setup.out

