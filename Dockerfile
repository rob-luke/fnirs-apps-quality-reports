FROM ghcr.io/mne-tools/mne-python:main

USER root

RUN pip install https://codeload.github.com/rob-luke/mne-bids/zip/nirs
RUN pip install https://github.com/nilearn/nilearn/archive/main.zip
RUN pip install https://github.com/mne-tools/mne-nirs/archive/main.zip
RUN pip install h5py
RUN pip install seaborn

COPY fnirsapp_qr.py /run.py
RUN chmod +x /run.py

ENTRYPOINT ["/run.py"]