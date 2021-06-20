#!/usr/bin/env python3
import pandas as pd
import numpy as np
import mne
import argparse
from mne_bids import BIDSPath, read_raw_bids
from glob import glob
import os.path as op
from pathlib import Path
from mne.preprocessing.nirs import optical_density
from mne_nirs.preprocessing import peak_power, scalp_coupling_index_windowed
from mne_nirs.visualisation import plot_timechannel_quality_metric
import matplotlib.pyplot as plt
from itertools import compress
import os
import subprocess

__version__ = "v0.1.0"


def fnirsapp_qr(command, env={}):
    merged_env = os.environ
    merged_env.update(env)
    process = subprocess.Popen(command, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, shell=True,
                               env=merged_env)
    while True:
        line = process.stdout.readline()
        line = str(line, 'utf-8')[:-1]
        print(line)
        if line == '' and process.poll() != None:
            break
    if process.returncode != 0:
        raise Exception("Non zero return code: %d" % process.returncode)


parser = argparse.ArgumentParser(description='Quality Reports')
parser.add_argument('--input-datasets', default="/bids_dataset", type=str,
                    help='The directory with the input dataset '
                    'formatted according to the BIDS standard.')
parser.add_argument('--output-location', default="/bids_dataset/derivatives/fnirs-apps-quality-reports",
                    type=str, help='The directory where the output files should be stored.')
parser.add_argument('--subject-label',
                    help='The label(s) of the participant(s) that should be '
                    'analyzed. The label corresponds to '
                    'sub-<subject-label> from the BIDS spec (so it does '
                    'not include "sub-"). If this parameter is not provided '
                    'all subjects should be analyzed. Multiple participants '
                    'can be specified with a space separated list.',
                    nargs="+")
parser.add_argument('--task-label',
                    help='The label(s) of the tasks(s) that should be '
                    'analyzed. If this parameter is not provided '
                    'all tasks should be analyzed. Multiple tasks '
                    'can be specified with a space separated list.',
                    nargs="+")
parser.add_argument('--sci-threshold', type=float, default=0.0,
                    help='Threshold below which a channel is marked as bad.')
parser.add_argument('--pp-threshold', type=float, default=0.0,
                    help='Threshold below which a channel is marked as bad.')
parser.add_argument('-v', '--version', action='version',
                    version='BIDS-App Scalp Coupling Index version '
                    f'{__version__}')
args = parser.parse_args()


########################################
# Extract parameters
########################################


ids = []
# only for a subset of subjects
if args.subject_label:
    ids = args.subject_label
# for all subjects
else:
    subject_dirs = glob(op.join(args.input_datasets, "sub-*"))
    ids = [subject_dir.split("-")[-1] for
           subject_dir in subject_dirs]
    print(f"No participants specified, processing {ids}")


tasks = []
if args.task_label:
    tasks = args.task_label
else:
    all_snirfs = glob(f"{args.input_datasets}/**/*_nirs.snirf", recursive=True)
    for a in all_snirfs:
        s = a.split("_task-")[1]
        s = s.split("_nirs.snirf")[0]
        tasks.append(s)
    tasks = np.unique(tasks)
    print(f"No tasks specified, processing {tasks}")


########################################
# Report Sections
########################################

def plot_raw(raw, report):
    fig1 = raw.plot(n_channels=len(raw.ch_names),
                    duration=raw.times[-1],
                    show_scrollbars=False, clipping=None)

    msg = "Plot of the raw signal"
    report.add_figs_to_section(fig1, comments=msg,
                               captions=op.basename(fname) + "_raw",
                               section="Raw Waveform")

    return raw, report


def summarise_triggers(raw, report):

    events, event_dict = mne.events_from_annotations(raw, verbose=False)
    fig2 = mne.viz.plot_events(events, event_id=event_dict,
                               sfreq=raw.info['sfreq'])
    report.add_figs_to_section(fig2, section="Triggers",
                               captions=op.basename(fname) + "_triggers")

    return raw, report


def summarise_montage(raw, report):
    fig3 = raw.plot_sensors()
    msg = f"Montage of sensors." \
          f"Bad channels are marked in red: {raw.info['bads']}"
    report.add_figs_to_section(fig3, section="Montage", comments=msg,
                               captions=op.basename(fname) + "_montage")

    return raw, report


def summarise_sci(raw, report, threshold=0.8):
    sci = mne.preprocessing.nirs.scalp_coupling_index(raw,
                                                      h_trans_bandwidth=0.1)
    raw.info['bads'] = list(compress(raw.ch_names, sci < threshold))

    fig, ax = plt.subplots()
    ax.hist(sci)
    ax.set(xlabel='Scalp Coupling Index', ylabel='Count', xlim=[0, 1])
    ax.axvline(linewidth=4, color='r', x=threshold)

    msg = f"Scalp coupling index with threshold at {threshold}." \
          f"Results in bad channels {raw.info['bads']}"
    report.add_figs_to_section(fig,
                               comments=msg,
                               captions=op.basename(fname) + "_SCI",
                               section="Scalp Coupling Index")

    return raw, report


def summarise_sci_window(raw, report, threshold=0.8):

    _, scores, times = scalp_coupling_index_windowed(raw, time_window=60)
    fig = plot_timechannel_quality_metric(raw, scores, times,
                                          threshold=threshold,
                                          title="Scalp Coupling Index "
                                          "Quality Evaluation")
    msg = "Windowed SCI."
    report.add_figs_to_section(fig, section="SCI Windowed", comments=msg,
                               captions=op.basename(fname) + "_sciwin")

    return raw, report


def summarise_pp(raw, report, threshold=0.8):

    _, scores, times = peak_power(raw, time_window=10)
    fig = plot_timechannel_quality_metric(raw, scores, times,
                                          threshold=threshold,
                                          title="Peak Power "
                                          "Quality Evaluation")
    msg = "Windowed Peak Power."
    report.add_figs_to_section(fig, section="Peak Power", comments=msg,
                               captions=op.basename(fname) + "_pp")

    return raw, report


def summarise_odpsd(raw, report):

    fig, ax = plt.subplots(ncols=2, figsize=(15, 8))

    raw.plot_psd(ax=ax[0])
    raw.plot_psd(ax=ax[1], average=True)
    ax[1].set_title("Average +- std")

    msg = "PSD of the optical density signal."
    report.add_figs_to_section(fig, section="OD PSD", comments=msg,
                               captions=op.basename(fname) + "_psd")

    return raw, report


########################################
# Main script
########################################

print(" ")
Path(f"{args.output_location}/").\
    mkdir(parents=True, exist_ok=True)
for id in ids:
    report = mne.Report(verbose=True, raw_psd=True)
    report.parse_folder(f"{args.input_datasets}/sub-{id}", render_bem=False)
    for idx, fname in enumerate(report.fnames):
        if mne.report._endswith(fname, 'nirs'):
            raw = mne.io.read_raw_snirf(fname)
            raw, report = plot_raw(raw, report)
            raw, report = summarise_triggers(raw, report)
            raw = optical_density(raw)
            raw, report = summarise_odpsd(raw, report)
            raw, report = summarise_sci_window(raw, report, threshold=args.sci_threshold)
            raw, report = summarise_pp(raw, report, threshold=args.pp_threshold)
            raw, report = summarise_sci(raw, report, threshold=args.sci_threshold)
            raw, report = summarise_montage(raw, report)

            report.save(f"{args.output_location}/"
                        f"report_basic_{id}.html",
                        overwrite=True, open_browser=False)

