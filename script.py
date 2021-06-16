#!/usr/bin/env python3
import pandas as pd
import numpy as np
import mne
import argparse
from mne_bids import BIDSPath, read_raw_bids
from glob import glob
import os.path as op

__version__ = "v0.0.1"


parser = argparse.ArgumentParser(description='Quality Reports')
parser.add_argument('--bids_dir', default="/bids_dataset", type=str,
                    help='The directory with the input dataset '
                    'formatted according to the BIDS standard.')
parser.add_argument('--threshold', type=float, default=1.0,
                    help='Threshold below which a channel is marked as bad.')
parser.add_argument('--participant_label',
                    help='The label(s) of the participant(s) that should be '
                    'analyzed. The label corresponds to '
                    'sub-<participant_label> from the BIDS spec (so it does '
                    'not include "sub-"). If this parameter is not provided '
                    'all subjects should be analyzed. Multiple participants '
                    'can be specified with a space separated list.',
                    nargs="+")
parser.add_argument('--task_label',
                    help='The label(s) of the tasks(s) that should be '
                    'analyzed. If this parameter is not provided '
                    'all tasks should be analyzed. Multiple tasks '
                    'can be specified with a space separated list.',
                    nargs="+")
parser.add_argument('-v', '--version', action='version',
                    version='BIDS-App Scalp Coupling Index version '
                    f'{__version__}')
args = parser.parse_args()


########################################
# Extract parameters
########################################

if args.threshold == 1.0:
    print("No threshold was set, so the status column will not be modified")

ids = []
# only for a subset of subjects
if args.participant_label:
    ids = args.participant_label
# for all subjects
else:
    subject_dirs = glob(op.join(args.bids_dir, "sub-*"))
    ids = [subject_dir.split("-")[-1] for
           subject_dir in subject_dirs]
    print(f"No participants specified, processing {ids}")


tasks = []
if args.task_label:
    tasks = args.task_label
else:
    all_snirfs = glob("/bids_dataset/**/*_nirs.snirf", recursive=True)
    for a in all_snirfs:
        s = a.split("_task-")[1]
        s = s.split("_nirs.snirf")[0]
        tasks.append(s)
    tasks = np.unique(tasks)
    print(f"No tasks specified, processing {tasks}")


########################################
# Main script
########################################

print(" ")
for id in ids:
    for task in tasks:
        b_path = BIDSPath(subject=id, task=task,
                          root="/bids_dataset",
                          datatype="nirs", suffix="nirs",
                          extension=".snirf")
        try:
            raw = read_raw_bids(b_path, verbose=True)
            raw = mne.preprocessing.nirs.optical_density(raw)
            sci = mne.preprocessing.nirs.scalp_coupling_index(raw)
            fname_chan = b_path.update(suffix='channels',
                                       extension='.tsv').fpath
            chans = pd.read_csv(fname_chan, sep='\t')
            for idx in range(len(raw.ch_names)):
                assert raw.ch_names[idx] == chans["name"][idx]
            chans["SCI"] = sci
            if args.threshold < 1.0:
                chans["status"] = sci > args.threshold
            chans.to_csv(fname_chan, sep='\t', index=False)
        except FileNotFoundError:
            print(f"Unable to process {b_path.fpath}")
        else:
            print(f"Unknown error processing {b_path.fpath}")

