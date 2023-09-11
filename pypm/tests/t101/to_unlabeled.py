import itertools
import csv
import sys
import random

random.seed(123456789)


def colname(x):
    for i in range(len(x)):
        for j in range(i + 1, len(x)):
            yield x[i] + x[j]


def meanval(x):
    for i in range(len(x)):
        for j in range(i + 1, len(x)):
            # yield (float(x[i])+float(x[j]))/2
            if random.random() < 0.8:
                yield max(float(x[i]), float(x[j]))
            else:
                yield round(random.random(), 1)


unlabeled = []
with open("data.csv", "r") as INPUT:
    reader = csv.reader(INPUT)
    row = next(reader)
    unlabeled.append([row[0]] + list(colname(row[1:])))
    for row in reader:
        unlabeled.append([row[0]] + list(meanval(row[1:])))

with open("unlabeled.csv", "w") as OUTPUT:
    writer = csv.writer(OUTPUT)
    writer.writerows(unlabeled)
