import numpy as np
import pandas as pd
import mygrad as mg
import warnings
import librosa
import pickle
import microphone
from scipy import stats

with open("data/genre_model","rb") as f:
    model_parameters = pickle.load(f)
data = np.load("data/genre_model_aux")
mean = data["mean"]
std = data["std"]
data = np.load("data/songs.npz")
mapping = data["mapping"]

from mynn.activations.relu import relu
class NN:
    def __init__(self, model_parameters):
        self.w1,self.b1,self.w2,self.b2,self.w3,self.b3 = model_parameters
    def __call__(self, X):
        X = relu(mg.matmul(X, self.w1, True) + self.b1)
        X = relu(mg.matmul(X, self.w2, True) + self.b2)
        X = mg.matmul(X, self.w3, True) + self.b3
        return mg.nnet.activations.softmax(X, constant=True)

model = NN(model_parameters)

def columns():
    feature_sizes = dict(chroma_stft=12, chroma_cqt=12, chroma_cens=12,
                         tonnetz=6, mfcc=20, rmse=1, zcr=1,
                         spectral_centroid=1, spectral_bandwidth=1,
                         spectral_contrast=7, spectral_rolloff=1)
    moments = ('mean', 'std', 'skew', 'kurtosis', 'median', 'min', 'max')

    columns = []
    for name, size in feature_sizes.items():
        for moment in moments:
            it = ((name, moment, '{:02d}'.format(i+1)) for i in range(size))
            columns.extend(it)

    names = ('feature', 'statistics', 'number')
    columns = pd.MultiIndex.from_tuples(columns, names=names)

    # More efficient to slice if indexes are sorted.
    return columns.sort_values()


def compute_features(x, sr):

    features = pd.Series(index=columns(), dtype=np.float32, name="features")
    warnings.filterwarnings('ignore', module='librosa')
    def feature_stats(name, values):
        features[name, 'mean'] = np.mean(values, axis=1)
        features[name, 'std'] = np.std(values, axis=1)
        features[name, 'skew'] = stats.skew(values, axis=1)
        features[name, 'kurtosis'] = stats.kurtosis(values, axis=1)
        features[name, 'median'] = np.median(values, axis=1)
        features[name, 'min'] = np.min(values, axis=1)
        features[name, 'max'] = np.max(values, axis=1)

    try:
        f = librosa.feature.zero_crossing_rate(x, frame_length=2048, hop_length=512)
        feature_stats('zcr', f)
        cqt = np.abs(librosa.cqt(x, sr=sr, hop_length=512, bins_per_octave=12,
                                 n_bins=7*12, tuning=None))
        assert cqt.shape[0] == 7 * 12
        assert np.ceil(len(x)/512) <= cqt.shape[1] <= np.ceil(len(x)/512)+1
        
        f = librosa.feature.chroma_cqt(C=cqt, n_chroma=12, n_octaves=7)
        feature_stats('chroma_cqt', f)
        f = librosa.feature.chroma_cens(C=cqt, n_chroma=12, n_octaves=7)
        feature_stats('chroma_cens', f)
        f = librosa.feature.tonnetz(chroma=f)
        feature_stats('tonnetz', f)

        del cqt
        stft = np.abs(librosa.stft(x, n_fft=2048, hop_length=512))
        assert stft.shape[0] == 1 + 2048 // 2
        assert np.ceil(len(x)/512) <= stft.shape[1] <= np.ceil(len(x)/512)+1
        del x
        f = librosa.feature.chroma_stft(S=stft**2, n_chroma=12)
        feature_stats('chroma_stft', f)

        f = librosa.feature.rmse(S=stft)
        feature_stats('rmse', f)

        f = librosa.feature.spectral_centroid(S=stft)
        feature_stats('spectral_centroid', f)
        f = librosa.feature.spectral_bandwidth(S=stft)
        feature_stats('spectral_bandwidth', f)
        f = librosa.feature.spectral_contrast(S=stft, n_bands=6)
        feature_stats('spectral_contrast', f)
        f = librosa.feature.spectral_rolloff(S=stft)
        feature_stats('spectral_rolloff', f)
        mel = librosa.feature.melspectrogram(sr=sr, S=stft**2)
        del stft
        f = librosa.feature.mfcc(S=librosa.power_to_db(mel), n_mfcc=20)
        feature_stats('mfcc', f)

    except FileNotFoundError as e:
        print('{}: {}'.format(tid, repr(e)))

    return features

# BY FILEPATH

from pathlib import Path
BASE = Path("/Volumes/GoogleDrive/My Drive/GitHub/BWSI_2018/week1_capstone/tests/MP3s")
audio_data, sr = librosa.load(BASE / Path("Popper Requiem for three cellos and piano.mp3"), sr=None, mono=True)  # kaiser_fast

# BY MICROPHONE
def input_mic(t=5):
    frames,sr = microphone.record_audio(t)
    audio_data_m = np.hstack([np.frombuffer(i, np.int16) for i in frames])
    audio_data_m = audio_data_m.astype("float")
    audio_data_m /= (2**16)
    return audio_data_m

def get_label(audio,sr=44100):
    features = compute_features(audio,sr)
    inp = np.array(features,dtype="float64").reshape(1,len(features))
    inp = (inp-mean)/std
    output = model(inp)
    label = mapping[np.argsort(output.data)[:,::-1][0][0]]
    return label

from pathlib import Path
def to_path_if_not_already(path):
    if isinstance(path, Path):
        return path
    else:
        return Path(path)

def input_mp3(file_path):
    """ Loads an mp3 file in the given path

        Parameters
        ----------
        file_path: path of the file in the form of a string or pathlib.path

        Returns
        -------
        Audio: the audio of the file as a np.array
    """
    
    file_path = to_path_if_not_already(file_path)
    audio, _ = librosa.load(file_path, 44100, mono=True)

    # saving the digitizes audio data as a numpy array from scale -2**15 to 2**15
    return audio