from collections import Counter
from enum import Enum, unique
from os import PathLike
from typing import Union, List

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn

from app.features import N_MELS

MODEL_PATH = 'models/emotions.pt'


@unique
class Emotion(Enum):
    COMFORTABLE = 'comfortable'
    HAPPY = 'happy'
    INSPIRATIONAL = 'inspirational'
    JOY = 'joy'
    LONELY = 'lonely'
    FUNNY = 'funny'
    NOSTALGIC = 'nostalgic'
    PASSIONATE = 'passionate'
    QUIET = 'quiet'
    RELAXED = 'relaxed'
    ROMANTIC = 'romantic'
    SADNESS = 'sadness'
    SOULFUL = 'soulful'
    SWEET = 'sweet'
    SERIOUS = 'serious'
    ANGER = 'anger'
    WARY = 'wary'
    SURPRISE = 'surprise'
    FEAR = 'fear'


EMOTIONS = [e.value for e in Emotion]


class EmotionClassifier(nn.Module):
    """
    LSTM Emotion Classifier
    """

    def __init__(
            self,
            input_dim: int,
            hidden_dim: int,
            batch_size: int = 9,
            output_dim: int = len(Emotion),
            n_layers: int = 2
    ):
        """
        :param input_dim: The number of expected features in the input `x`
        :param hidden_dim: The number of features in the hidden state `h`
        :param batch_size:
        :param output_dim:
        :param n_layers:
        """
        super(EmotionClassifier, self).__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.batch_size = batch_size
        self.n_layers = n_layers

        self.lstm = nn.LSTM(self.input_dim, self.hidden_dim, self.n_layers, batch_first=True)
        self.output = nn.Linear(self.hidden_dim, output_dim)

    def forward(self, x):
        lstm_out, hidden = self.lstm(x)
        logits = self.output(lstm_out[:, -1])
        return F.softmax(logits, dim=1)


def load_model(model_path: Union[str, bytes, PathLike]) -> nn.Module:
    """
    Loads model from state dict
    :param model_path:
    :return:
    """
    input_dim = N_MELS
    hidden_dim = 32
    n_classes = len(Emotion)

    model = EmotionClassifier(
        input_dim=input_dim,
        hidden_dim=hidden_dim,
        output_dim=n_classes
    )
    model.load_state_dict(torch.load(model_path))
    model.eval()
    return model


def predict_topk_emotions(features: np.ndarray, k=3) -> List[str]:
    model = load_model(MODEL_PATH)
    output = model(torch.tensor(features))
    indices = torch.flatten(torch.topk(output, k, dim=1)[1])
    indices = list(map(lambda x: x[0], Counter(indices).most_common(k)))
    return [EMOTIONS[i] for i in indices]
