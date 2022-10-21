#!/usr/bin/env python3
import pandas as pd
import matplotlib
import mne
import argparse
from mne_bids import BIDSPath, read_raw_bids, get_entity_vals
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
from mne.utils import logger
from pathlib import Path
from datetime import datetime
import json
import hashlib
from pprint import pprint

matplotlib.use('agg')

__version__ = "v0.3.8"


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
parser.add_argument('--session-label',
                    help='The label(s) of the session(s) that should be '
                    'analyzed. The label corresponds to '
                    'ses-<session-label> from the BIDS spec (so it does '
                    'not include "ses-"). If this parameter is not provided '
                    'all sessions should be analyzed. Multiple sessions '
                    'can be specified with a space separated list.',
                    nargs="+")
parser.add_argument('--run-label',
                    help='The label(s) of the run(s) that should be '
                    'analyzed. The label corresponds to '
                    'run-<run-label> from the BIDS spec (so it does '
                    'not include "run-"). If this parameter is not provided '
                    'all runs should be analyzed. Multiple runs '
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

def create_report(app_name=None, pargs=None):

    exec_rep = dict()
    exec_rep["ExecutionStart"] = datetime.now().isoformat()
    exec_rep["ApplicationName"] = app_name
    exec_rep["ApplicationVersion"] = __version__
    exec_rep["Arguments"] = vars(pargs)

    return exec_rep

exec_files = dict()
exec_rep =create_report(app_name="fNIRS-Apps: Quality Reports", pargs=args)

mne.set_log_level("INFO")
logger.info("\n")


########################################
# Extract parameters
########################################


logger.info("Extracting subject metadata.")
subs = []
if args.subject_label:
    logger.info("    Subject data provided as input argument.")
    subs = args.subject_label
else:
    logger.info("    Subject data will be extracted from data.")
    subs = get_entity_vals(args.input_datasets, 'subject')
logger.info(f"        Subjects: {subs}")


logger.info("Extracting session metadata.")
sess = []
if args.session_label:
    logger.info("    Session data provided as input argument.")
    sess = args.session_label
else:
    logger.info("    Session data will be extracted from data.")
    sess = get_entity_vals(args.input_datasets, 'session')
if len(sess) == 0:
    sess = [None]
logger.info(f"        Sessions: {sess}")


logger.info("Extracting run metadata.")
sess = []
if args.session_label:
    logger.info("    Run data provided as input argument.")
    runs = args.session_label
else:
    logger.info("    Run data will be extracted from data.")
    runs = get_entity_vals(args.input_datasets, 'run')
if len(runs) == 0:
    runs = [None]
logger.info(f"        Runs: {runs}")


logger.info("Extracting tasks metadata.")
tasks = []
if args.task_label:
    logger.info("    Task data provided as input argument.")
    tasks = args.task_label
else:
    logger.info("    Session data will be extracted from data.")
    tasks = get_entity_vals(args.input_datasets, 'task')
logger.info(f"        Tasks: {tasks}")


########################################
# Report Sections
########################################

def plot_raw(raw, report):
    logger.debug("    Creating raw plot")
    fig1 = raw.plot(n_channels=len(raw.ch_names),
                    duration=raw.times[-1],
                    show_scrollbars=False, clipping=None)

    msg = "Plot of the raw signal"
    report.add_figure(fig=fig1, caption=msg, title="Raw Waveform")

    return raw, report


def summarise_triggers(raw, report):
    logger.debug("    Creating trigger summary")

    events, event_dict = mne.events_from_annotations(raw, verbose=False)
    fig2 = mne.viz.plot_events(events, event_id=event_dict,
                               sfreq=raw.info['sfreq'])
    report.add_figure(fig=fig2, title="Triggers")

    return raw, report


def summarise_montage(raw, report):
    logger.debug("    Creating montage summary")
    fig3 = raw.plot_sensors()
    msg = f"Montage of sensors." \
          f"Bad channels are marked in red: {raw.info['bads']}"
    report.add_figure(fig=fig3, title="Montage", caption=msg)

    return raw, report


def summarise_sci(raw, report, threshold=0.8):
    logger.debug("    Creating SCI summary")

    if raw.info['lowpass'] < 1.5:
        print("SCI calculation being run over limited frequency range, check if valid.")
        h_trans_bandwidth = 0.2
        h_freq = 1.5 - raw.info['lowpass'] - 0.05
    else:
        h_freq = 1.5
        h_trans_bandwidth = 0.3

    sci = mne.preprocessing.nirs.scalp_coupling_index(raw, h_freq=h_freq, h_trans_bandwidth=h_trans_bandwidth)
    raw.info['bads'] = list(compress(raw.ch_names, sci < threshold))

    fig, ax = plt.subplots()
    ax.hist(sci)
    ax.set(xlabel='Scalp Coupling Index', ylabel='Count', xlim=[0, 1])
    ax.axvline(linewidth=4, color='r', x=threshold)

    msg = f"Scalp coupling index with threshold at {threshold}." \
          f"Results in bad channels {raw.info['bads']}"
    report.add_figure(fig=fig, caption=msg, title="Scalp Coupling Index")

    return raw, report


def summarise_sci_window(raw, report, threshold=0.8):
    logger.debug("    Creating windowed SCI summary")

    if raw.info['lowpass'] < 1.5:
        print("SCI calculation being run over limited frequency range, check if valid.")
        h_trans_bandwidth = 0.2
        h_freq = 1.5 - raw.info['lowpass'] - 0.05
    else:
        h_freq = 1.5
        h_trans_bandwidth = 0.3


    _, scores, times = scalp_coupling_index_windowed(raw, time_window=60, h_freq=h_freq, h_trans_bandwidth=h_trans_bandwidth)
    fig = plot_timechannel_quality_metric(raw, scores, times,
                                          threshold=threshold,
                                          title="Scalp Coupling Index "
                                          "Quality Evaluation")
    msg = "Windowed SCI."
    report.add_figure(fig=fig, title="SCI Windowed", caption=msg)

    return raw, report


def summarise_pp(raw, report, threshold=0.8):
    logger.debug("    Creating peak power summary")

    if raw.info['lowpass'] < 1.5:
        print("PP calculation being run over limited frequency range, check if valid.")
        h_trans_bandwidth = 0.2
        h_freq = 1.5 - raw.info['lowpass'] - 0.05
    else:
        h_freq = 1.5
        h_trans_bandwidth = 0.3

    _, scores, times = peak_power(raw, time_window=10, h_freq=h_freq, h_trans_bandwidth=h_trans_bandwidth)
    fig = plot_timechannel_quality_metric(raw, scores, times,
                                          threshold=threshold,
                                          title="Peak Power "
                                          "Quality Evaluation")
    msg = "Windowed Peak Power."
    report.add_figure(fig=fig, title="Peak Power", caption=msg)

    return raw, report


def summarise_odpsd(raw, report):
    logger.debug("    Creating PSD plot")

    fig, ax = plt.subplots(ncols=2, figsize=(15, 8))

    raw.plot_psd(ax=ax[0])
    raw.plot_psd(ax=ax[1], average=True)
    ax[1].set_title("Average +- std")

    msg = "PSD of the optical density signal."
    report.add_figure(fig=fig, title="OD PSD", caption=msg)

    return raw, report


########################################
# Report script
########################################


def run_report(path, path_out):

    report = mne.Report(verbose=True, raw_psd=True)
    report.parse_folder(f"{path.directory}", render_bem=False, raw_butterfly=False)

    raw = read_raw_bids(path)
    raw, report = plot_raw(raw, report)
    raw, report = summarise_triggers(raw, report)
    raw = optical_density(raw)
    raw, report = summarise_odpsd(raw, report)
    raw, report = summarise_sci_window(raw, report, threshold=args.sci_threshold)
    raw, report = summarise_pp(raw, report, threshold=args.pp_threshold)
    raw, report = summarise_sci(raw, report, threshold=args.sci_threshold)
    raw, report = summarise_montage(raw, report)

    report.save(path_out, overwrite=True, open_browser=False)

    return 1

########################################
# Main script
########################################

logger.info(" ")
Path(f"{args.output_location}").mkdir(parents=True, exist_ok=True)


for sub in subs:
    for task in tasks:
        for ses in sess:
            for run in runs:
                if len(runs) > 1 : 
                    logger.info(f"Processing: sub-{sub}/ses-{ses}/run-{run}/task-{task}")
                    exec_files[f"sub-{sub}_ses-{ses}_task-{task}_run-{run}"] = dict()

                    in_path = BIDSPath(subject=sub, task=task, session=ses, run = rub,
                                       root=f"{args.input_datasets}",
                                       datatype="nirs", suffix="nirs",
                                       extension=".snirf")
                    exec_files[f"sub-{sub}_ses-{ses}_task-{task}_run-{run}"]["FileName"] = str(in_path.fpath)
                    exec_files[f"sub-{sub}_ses-{ses}_task-{task}_run-{run}"]["FileHash"] = hashlib.md5(open(in_path.fpath, 'rb').read()).hexdigest()
                    out_path = BIDSPath(subject=sub, task=task, session=ses,run=run,
                                        root=f"{args.output_location}",
                                        datatype="nirs", suffix="qualityReport",
                                        extension=".html", check=False)
                else
                    logger.info(f"Processing: sub-{sub}/ses-{ses}/task-{task}")
                    exec_files[f"sub-{sub}_ses-{ses}_task-{task}"] = dict()

                    in_path = BIDSPath(subject=sub, task=task, session=ses,
                                       root=f"{args.input_datasets}",
                                       datatype="nirs", suffix="nirs",
                                       extension=".snirf")            

                    exec_files[f"sub-{sub}_ses-{ses}_task-{task}"]["FileName"] = str(in_path.fpath)
                    exec_files[f"sub-{sub}_ses-{ses}_task-{task}"]["FileHash"] = hashlib.md5(open(in_path.fpath, 'rb').read()).hexdigest()

                    out_path = BIDSPath(subject=sub, task=task, session=ses,
                                        root=f"{args.output_location}",
                                        datatype="nirs", suffix="qualityReport",
                                        extension=".html", check=False)

                if op.exists(in_path):
                    logger.info(f"    Found file: {in_path}")
                    out_path.fpath.parent.mkdir(exist_ok=True, parents=True)
                    run_report(in_path, out_path)
                else:
                    logger.info(f"    No file exists: {in_path}")
                    

exec_rep["Files"] = exec_files
exec_path = f"{args.input_datasets}/execution"
exec_rep["ExecutionEnd"] = datetime.now().isoformat()

Path(exec_path).mkdir(parents=True, exist_ok=True)
with open(f"{exec_path}/{exec_rep['ExecutionStart'].replace(':', '-')}-quality_reports.json", "w") as fp:
    json.dump(exec_rep, fp)

pprint(exec_rep)
