# fNIRS App: Quality Reports

[![build](https://github.com/rob-luke/fnirs-apps-quality-reports/actions/workflows/ghregistry.yml/badge.svg)](https://github.com/rob-luke/fnirs-apps-quality-reports/actions/workflows/ghregistry.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4999161.svg)](https://doi.org/10.5281/zenodo.4999161)



This [*fNIRS App*](http://fnirs-apps.org) will produce data quality reports for all measurements in your BIDS dataset.
Reports are html documents.
See an example report [here](https://rob-luke.github.io/fnirs-apps-quality-reports/example_report.html).


## Usage

To run the app you must have [docker installed](https://docs.docker.com/get-docker/). See here for details about [installing fNIRS Apps](http://fnirs-apps.org/details/). You do NOT need to have MATLAB or python installed, and you do not need any scripts.

To run the app you must inform it where the `bids_dataset` to be formatted resides.
This is done by passing the app the location of the dataset using the `-v` command.
To run this app use the command:

```bash
docker run -v /path/to/data/:/bids_dataset ghcr.io/rob-luke/fnirs-apps-quality-reports/app
```

By default the app will process all subject and tasks.
You can modify the behaviour of the script using the options below.

## Arguments

|                | Required | Default | Note                                                   |
|----------------|----------|---------|--------------------------------------------------------|
| sci_threshold  | optional | 0.0     | Threshold applied in the scalp coupling index figures. |
| pp_threshold   | optional | 0.0     | Threshold applied in the peak power figures.           |
| participant_label  | optional | []     | Participants to process. Default is to process all. |



An example of how to use these arguments:
```bash
docker run -v /path/to/data/:/bids_dataset ghcr.io/rob-luke/fnirs-apps-quality-reports/app --sci_threshold 0.5 --pp_threshold 0.6 --participant_label 06
```

## Updating

To update to the latest version run.

```bash
docker pull ghcr.io/rob-luke/fnirs-apps-quality-reports/app
```

Or to run a specific version:

```bash
docker run -v /path/:/bids_dataset ghcr.io/rob-luke/fnirs-apps-quality-reports/app:v1.4.2
```


Acknowledgements
----------------

This app is directly based on BIDS Apps and BIDS Execution. Please cite those projects when using this app.

BIDS Apps: https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005209

BIDS Execution: https://github.com/bids-standard/bids-specification/issues/313

This app uses MNE-Python, MNE-BIDS, and MNE-NIRS under the hood. Please cite those package accordingly.

MNE-Python: https://mne.tools/dev/overview/cite.html

MNE-BIDS: https://github.com/mne-tools/mne-bids#citing

MNE-NIRS: https://github.com/mne-tools/mne-nirs#acknowledgements
