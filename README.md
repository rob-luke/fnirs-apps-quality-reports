# fNIRS App: Quality Reports


Portable fNIRS neuroimaging pipelines that work with BIDS datasets. See http://fnirs-apps.org

This app produces a quality report for the data and saves it in `derivatives/fnirs-apps-quality-reports`.
Reports are html documents.

## Usage

```bash
docker run -v /path/to/data/:/bids_dataset ghcr.io/rob-luke/fnirs-apps-quality-reports/app
```


## Arguments

|            | Required | Default | Note                                                   |
|------------|----------|---------|--------------------------------------------------------|
| threshold  | optional | NA      | If not present then the status column is not modified. |



Acknowledgements
----------------

This package uses MNE-Python, MNE-BIDS, and MNE-NIRS under the hood. Please cite those package accordingly.

MNE-Python: https://mne.tools/dev/overview/cite.html

MNE-BIDS: https://github.com/mne-tools/mne-bids#citing

MNE-NIRS: https://github.com/mne-tools/mne-nirs#acknowledgements
