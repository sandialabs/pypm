import os
import csv
import datetime
import pandas as pd


def csv_k_generator(nrows, k, offset):
    """
    Generator that return a sequence (i, chunk, j):
        i       - Row index
        chunk   - Boolean value indicating if chunk is collected
        j       - Counter used for debugging
    """
    i = 0
    kk = 0
    nk = len(k)
    j = offset
    while i < nrows:
        if j == k[kk]:
            yield i,True,j,kk
            kk = (kk+1) % nk
            j = 0
        else:
            yield i,False,j,kk
        j += 1
        i += 1
        

def chunk_csv_k(df, k, offset=0, hours=[]):
    chunked = []
    if hours:
        chunked.append( "DateTime," + ",".join(df.columns) )
    else:
        chunked.append( ",".join(df.columns) )
    values = []
    dt = str(hours[0])
    for i,chunk,j,kk in csv_k_generator(df.shape[0], k, offset):
        if chunk:
            if hours:
                chunked.append( dt + "," + ",".join(map(str,values)) )
            else:
                chunked.append( ",".join(map(str,values)) )
            dt = str(hours[i])
            values = [df[col][i] for col in df.columns]
        else:
            if len(values) == 0:
                values = [df[col][i] for col in df.columns]
            else:
                values = [max(l1, l2) for l1, l2 in zip(values, [df[col][i] for col in df.columns])]
    return chunked


def chunk_csv(filename, output, index, step):
    assert os.path.exists(filename), "Cannot find CSV file: {}".format(filename)
    df = pd.read_csv(filename)

    date_time_index = False
    if not index is None:
        assert (index in df.columns), "Missing date-time index column: {}".format(index)
        date_time_index = True
        print("Chunking with date-time index: {}".format(index))
    elif 'DateTime' in df.columns:
        print("WARNING: A 'DateTime' data column is specified, but we are not treating this as an index for the data")

    if date_time_index:
        #
        # Collect data and verify that it is in 1-hour increments
        #
        df[index] = pd.to_datetime(df[index])
        df = df.set_index(index)
        df = df.sort_index()
        #print(df.head())
        #print(list(df.index)[0])
        #for i in df.index:
        #    print(i, type(i))
        start = list(df.index)[0]
        stop = list(df.index)[-1]
        hour = datetime.timedelta(hours=1)

        hours = [start]
        curr = start
        while curr < stop:
            curr = curr + hour
            hours.append(curr)

        if len(hours) != len(df.index):
            print("WARNING: Possible missing data. \n\t{} hours from start-to-stop, but only {} time steps in the data".format(len(hours), len(df.index)))
        tmp = set(hours)
        for t in df.index:
            assert (t in tmp), "ERROR: Time step '{}' is not an hourly time step".format(t)
        #
        # Rounding-off the time horion to the beginning and end of the start/end of the horizon
        #
        start_ = datetime.datetime(year=start.year, month=start.month, day=start.day, tzinfo=start.tzinfo)
        while start_ < start:
            start_ = start_ + hour
            hours.append(start_)
        stop_ = datetime.datetime(year=stop.year, month=stop.month, day=stop.day, tzinfo=start.tzinfo) + 24*hour
        while stop < stop_:
            stop = stop + hour
            hours.append(stop)
        if len(hours) != len(df.index):
            print("WARNING: Additional time steps added at the beginning and end of the time horizon.  \n\t{} hours from start-to-stop, but only {} time steps in the data".format(len(hours), len(df.index)))
    else:
        hours = []

    if step == "2h":
        #
        # Assume the rows of the CSV file represent hours.
        # Chunk the CSV into 2-hour blocks
        #
        chunked = chunk_csv_k(df, [2], hours=hours)
        print("Writing file: {}".format(output))
        with open(output, 'w') as OUTPUT:
            OUTPUT.write( "\n".join(chunked) )
    elif step == "4h":
        #
        # Assume the rows of the CSV file represent hours.
        # Chunk the CSV into 4-hour blocks
        #
        chunked = chunk_csv_k(df, [4], hours=hours)
        print("Writing file: {}".format(output))
        with open(output, 'w') as OUTPUT:
            OUTPUT.write( "\n".join(chunked) )
    elif step == "8h":
        #
        # Assume the rows of the CSV file represent hours.
        # Chunk the CSV into 8-hour blocks
        #
        chunked = chunk_csv_k(df, [8], hours=hours)
        print("Writing file: {}".format(output))
        with open(output, 'w') as OUTPUT:
            OUTPUT.write( "\n".join(chunked) )
    elif step == "3:55554h":
        #
        # Assume the rows of the CSV file represent hours.
        # Chunk the CSV into 8-hour blocks
        #
        # The offset of 3 ensures that a 5-hour block starts at 7am.
        #
        chunked = chunk_csv_k(df, [5,5,5,5,4], offset=3, hours=hours)
        print("Writing file: {}".format(output))
        with open(output, 'w') as OUTPUT:
            OUTPUT.write( "\n".join(chunked) )
    else:
        print("Unexpected chunk step: {}".format(step))

