import os
from typing import Dict, Union, List, Tuple

import librosa as lbr
import numpy as np
import pandas as pd
from pydub import AudioSegment

from app.common.columns import Column, EMOTIONS
from pickle import dump, load
from sklearn.preprocessing import MultiLabelBinarizer, OneHotEncoder

WINDOW_SIZE = 2048
WINDOW_STRIDE = WINDOW_SIZE // 2
N_MELS = 128
MEL_KWARGS = {
    'n_fft': WINDOW_SIZE,
    'hop_length': WINDOW_STRIDE,
    'n_mels': N_MELS
}

SECOND_IN_MILLIES = 1000


def extract_audio_features_v1(filename, enforce_shape=None):
    print(f'Extracting audio features from file {filename}...')
    new_input, sample_rate = lbr.load(filename, mono=True)
    features = lbr.feature.melspectrogram(new_input, **MEL_KWARGS).T

    if enforce_shape is not None:
        if features.shape[0] < enforce_shape[0]:
            delta_shape = (enforce_shape[0] - features.shape[0],
                           enforce_shape[1])
            features = np.append(features, np.zeros(delta_shape), axis=0)
        elif features.shape[0] > enforce_shape[0]:
            features = features[: enforce_shape[0], :]

    features[features == 0] = 1e-6
    return np.log(features)


def prepare_data_v1(
        tracks: pd.DataFrame,
        label_column: Column,
        label_values: List[str],
        enforce_shape=None
) -> Tuple[np.ndarray, np.ndarray]:
    tracks_count = len(tracks)
    if tracks_count == 0:
        return np.zeros(1), np.zeros(1)

    # separate first audio to get features shape
    first_track = tracks.iloc[0]
    first_track_features = extract_audio_features_v1(first_track.audio_path, enforce_shape)
    features_shape = first_track_features.shape

    X = np.zeros((tracks_count,) + features_shape, dtype=np.float32)
    X[0] = first_track_features
    for track_index, track in tracks.iloc[1:].iterrows():
        print(f'Track #{track_index} out of {len(tracks)}')
        X[track_index] = extract_audio_features_v1(track.audio_path, features_shape)

    mlb = MultiLabelBinarizer(classes=label_values)
    mlb.fit([])
    y = mlb.transform(tracks[label_column.value].apply(lambda s: str(s).split('|')).tolist())
    return X, y


def dump_data(x: np.array, y: np.array, output_path: str):
    data = {'x': x, 'y': y}
    with open(output_path, 'wb') as f:
        dump(data, f)
    return data


def load_data(data_path: str) -> Dict[str, np.array]:
    with open(data_path, 'rb') as f:
        return load(f)


def prepare_data_emotions_v1(df: pd.DataFrame, enforce_shape=None) -> Tuple[np.ndarray, np.ndarray]:
    return prepare_data_v1(df, Column.EMOTIONS, EMOTIONS, enforce_shape)


HOP_LENGTH = 512
TIMESERIES_LENGTH = (128)


def extract_audio_features_v2(filename: str):
    print(f'Extracting audio features from file {filename}...')

    y, sr = lbr.load(filename)
    mfcc = lbr.feature.mfcc(
        y=y, sr=sr, hop_length=HOP_LENGTH, n_mfcc=13
    )
    spectral_center = lbr.feature.spectral_centroid(
        y=y, sr=sr, hop_length=HOP_LENGTH
    )
    chroma = lbr.feature.chroma_stft(y=y, sr=sr, hop_length=HOP_LENGTH)
    spectral_contrast = lbr.feature.spectral_contrast(
        y=y, sr=sr, hop_length=HOP_LENGTH
    )

    features = np.zeros(33)
    r1 = mfcc.T[0:TIMESERIES_LENGTH, :]
    r2 = spectral_center.T[0:TIMESERIES_LENGTH, :]
    r3 = chroma.T[0:TIMESERIES_LENGTH, :]
    r4 = spectral_contrast.T[0:TIMESERIES_LENGTH, :]
    print(r1.shape)
    print(r2.shape)
    print(r3.shape)
    print(r4.shape)

    # data[i, :, 0:13] = mfcc.T[0:TIMESERIES_LENGTH, :]
    # data[i, :, 13:14] = spectral_center.T[0:TIMESERIES_LENGTH, :]
    # data[i, :, 14:26] = chroma.T[0:TIMESERIES_LENGTH, :]
    # data[i, :, 26:33] = spectral_contrast.T[0:TIMESERIES_LENGTH, :]
