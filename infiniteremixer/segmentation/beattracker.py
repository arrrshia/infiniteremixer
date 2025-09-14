import librosa
import numpy as np

def estimate_beats(signal, sr):
    # units is keyword-only; ask for sample indices
    _, beats = librosa.beat.beat_track(y=signal, sr=sr, units="samples")
    beats = np.asarray(beats, dtype=np.int64).reshape(-1)
    # keep only valid indices
    beats = beats[(beats >= 0) & (beats <= len(signal))]
    return beats


def estimate_beats_and_tempo(signal, sr):
    """Beat tracker that extracts beat events and global tempo. It uses
    librosa facilities under the hood.

    :param signal: (np.ndarray) Audio time series to analyse
    :param sr: (int) Sample rate

    :return: (float) Estimated global tempo (in beats per minute)
    :return: (np.ndarray) Estimated beat events measured in samples
    """
    tempo, beats = librosa.beat.beat_track(y=signal, sr=sr, units="samples")
    return beats, tempo