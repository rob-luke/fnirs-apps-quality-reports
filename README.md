# fNIRS App: Quality Reports

[![build](https://github.com/rob-luke/fnirs-apps-quality-reports/actions/workflows/ghregistry.yml/badge.svg)](https://github.com/rob-luke/fnirs-apps-quality-reports/actions/workflows/ghregistry.yml)

Portable fNIRS neuroimaging pipelines that work with BIDS datasets. See http://fnirs-apps.org

This app produces a quality report.
Reports are html documents.
See an example report [here](https://rob-luke.github.io/fnirs-apps-quality-reports/report_basic_02.html).


## Usage

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
| participant_label  | optional | []     | Threshold applied in the peak power figures.           |

--

An example of how to use these arguments:
```bash
docker run -v /path/to/data/:/bids_dataset ghcr.io/rob-luke/fnirs-apps-quality-reports/app --sci_threshold=0.5 --pp_threshold=0.6 --participant_label 06
```


Acknowledgements
----------------

This package uses MNE-Python, MNE-BIDS, and MNE-NIRS under the hood. Please cite those package accordingly.

MNE-Python: https://mne.tools/dev/overview/cite.html

MNE-BIDS: https://github.com/mne-tools/mne-bids#citing

MNE-NIRS: https://github.com/mne-tools/mne-nirs#acknowledgements
