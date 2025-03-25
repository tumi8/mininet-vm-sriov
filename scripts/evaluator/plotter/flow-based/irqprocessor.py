#!/usr/bin/python3
# Author: Sebastian Gallenmüller

import argparse
import csv
from pathlib import Path
import shutil
import os

parser = argparse.ArgumentParser()
parser.add_argument("readfolder", help='input folder')
parser.add_argument("writefolder", help='output folder')
args = parser.parse_args()

def read_and_output_csv(readcsv, writecsv):
    with open(readcsv, newline='') as csvfile:
        irqreader = csv.DictReader(csvfile, delimiter=';', quotechar='"')
        dic = dict()
        for row in irqreader:
            for k, v in row.items():
                key = k.replace(',', '')
                if key in dic:
                    dic[key].append(v)
                else:
                    dic[key] = [v]
        initial = dict()
        for k, v in dic.items():
            try:
                initial[k] = float(v[0])
            except ValueError:
                initial[k] = 0.0
        maximum = dict()
        for k, v in dic.items():
            # convert to floats
            liste = []
            for vvv in v:
                try:
                    liste.append(float(vvv))
                except ValueError:
                    pass
            maximum[k] = float(max(liste))
        #print(maximum)
        rel = dict()
        num_entries = 0
        for k, v in dic.items():
            if k == 'timestamp_us':
                rel[k] = v
                num_entries = len(v)
                continue
            lst = []
            for vv in v:
                try:
                    val = (float(vv) - initial[k]) / (maximum[k] - initial[k])
                except ValueError:
                    val = 0.0
                except TypeError:
                    val = 0.0
                except ZeroDivisionError:
                    val = 1.0
                lst.append(val)
            if lst[0] != lst[-1]:
                rel[k] = lst

        with open(writecsv, 'w+', newline='') as outfile:
            writer = csv.DictWriter(outfile, delimiter=',', quotechar='"', fieldnames=rel.keys())
            writer.writeheader()
            for i in range(0, num_entries):
                rowdict = dict()
                for k, v in rel.items():
                    rowdict[k] = v[i]
                writer.writerow(rowdict)

if not os.path.exists(args.writefolder):
    os.mkdir(args.writefolder)

irqfiles = Path(args.readfolder).glob('irq*run*.csv')
for fi in irqfiles:
    read_and_output_csv(str(fi), args.writefolder + '/' +  str(fi.stem) + '.irq.csv')
