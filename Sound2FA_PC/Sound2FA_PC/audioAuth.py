import librosa
import librosa.display
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from pydub import AudioSegment, silence

fft_length = 512 * 16
window = "hann"

def convert_to_decibel(arr):
    ref = 1
    if arr != 0:
        return 20 * np.log10(abs(arr) / ref)

    else:
        return -60


def moving_average(data, window_size):
    return np.convolve(data, np.ones(window_size) / window_size, mode='valid')


def get_audio_specifications(y, sr, silence_times):
    # Calculate the corresponding start and end samples for each cut
    cut_samples = []
    for start_time, end_time in silence_times:
        start_sample = int(start_time * sr)
        end_sample = int(end_time * sr)
        cut_samples.append((start_sample, end_sample))

    mask = np.ones_like(y)

    for start, end in cut_samples:
        mask[start:end] = 0

    # Apply the mask to the original audio signal
    section = y * mask

    # Get decibel - sample and preprocess it.
    db_sample = pd.Series([convert_to_decibel(i) for i in section])

    # Calculate the average over intervals
    interval_size = 500
    db_sample_shrinked = db_sample.groupby(np.arange(len(db_sample)) // interval_size).mean()

    # Apply moving average to decibel levels
    smoothed_db_sample = pd.Series(moving_average(db_sample_shrinked, window_size=3))
    # Get the spectral centroid and get rid of bad parts
    spectral_centroid = pd.Series(librosa.feature.spectral_centroid(y=section, sr=sr)[0])
    smoothed_spectral_centroid = pd.Series(moving_average(spectral_centroid, window_size=3))

    # Return the extracted specifications
    specifications = {
        'spectral_centroid': smoothed_spectral_centroid,
        'db_sample': smoothed_db_sample
    }

    return specifications


def spectrum_stft(audio, sr, n_fft, window):
    """Method 1: Compute magnitude spectrogram, average over time"""
    S = librosa.stft(audio, n_fft=n_fft, window=window)
    S_db = librosa.amplitude_to_db(np.abs(S * S), ref=0.0, top_db=120)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    spectrum = np.mean(S_db, axis=1)
    return pd.Series(spectrum, index=freqs)


def plot(c1, c2, d1, d2):
    # Plotting Spectral Centroid
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    c1.plot(ax=ax2, label="Recording1")
    c2.plot(ax=ax2, label="Recording2")
    ax2.legend()
    ax2.set_title('Spectral Centroid')
    fig2.savefig("soundSpecs/centroid.png")
    #plt.show()

    fig3, ax3 = plt.subplots(figsize=(10, 6))
    d1.plot(ax=ax3, label="Recording1")
    d2.plot(ax=ax3, label="Recording2")
    ax3.legend()
    ax3.set_title('DB Sample')
    fig3.savefig("soundSpecs/db.png")
    #plt.show()

def calcOffset(section1, sr1, y2, sr2):
    max_db = -1
    max_section = None
    offset = 0
    d1 = pd.Series(librosa.feature.spectral_centroid(y=section1, sr=sr1)[0])

    for i in range(129):
        section2 = y2[int((0.20 + (i * 0.01)) * sr2):int((3.7 + (i * 0.01)) * sr2)]

        d2 = pd.Series(librosa.feature.spectral_centroid(y=section2, sr=sr2)[0])

        db = d1.corr(d2, method='spearman')

        if db > max_db:
            max_db = db
            max_section = section2
            offset = i * 0.01 - 0.90

    return max_section, offset


def removeSilenceTest(path, offset=None, threshold=-65):
    myaudio = AudioSegment.from_wav(path)
    myaudio = myaudio[1100:4600]

    if offset is None:
        silenc = silence.detect_silence(myaudio, min_silence_len=400, silence_thresh=threshold)
    else:
        silenc = silence.detect_silence(myaudio[offset:], min_silence_len=400, silence_thresh=threshold)

    silenc = [((start / 1000), (stop / 1000)) for start, stop in silenc]

    silence_duration = sum(end_time - start_time for start_time, end_time in silenc)
    return silenc, silence_duration


def find_intersection(list1, list2):
    result = []

    for range1 in list1:
        for range2 in list2:
            intersection_start = max(range1[0], range2[0])
            intersection_end = min(range1[1], range2[1])

            if intersection_start <= intersection_end:
                result.append((intersection_start, intersection_end))

    return result


def audioAuth(path1, path2):
    y1, sr1 = librosa.load(path1, sr=None)
    y2, sr2 = librosa.load(path2, sr=None)

    print("Matching the audio..")
    section1 = y1[int(1.1 * sr1):int(4.6 * sr1)]
    section2, offset = calcOffset(section1, sr1, y2, sr2)

    print("Detecting silence..")
    silence_list1 , silence_duration1 = removeSilenceTest(path1)
    silence_list2 , silence_duration2 = removeSilenceTest(path2, offset, -50)
    silence_times = find_intersection(silence_list1, silence_list2)

    print("Calculating specs..")
    spec1 = get_audio_specifications(section1, sr1, silence_times)
    spec2 = get_audio_specifications(section2, sr2, silence_times)

    c1 = spec1['spectral_centroid']
    c2 = spec2['spectral_centroid']

    d1 = spec1['db_sample']
    d2 = spec2['db_sample']

    print("Calculating correlation..")
    cent = c1.corr(c2, method='spearman')
    db = d1.corr(d2, method='spearman')

    print("Plotting visuals..")
    plot(c1, c2, d1, d2)

    print("Centroid-Spectrum Score:", round(cent, 3))
    print("DB-Sample Score:        ", round(db, 3))

    score = cent * 0.40 + db * 0.60
    print("\nWeighted Score:         ", round(score, 3))

    silence_duration = sum(end_time - start_time for start_time, end_time in silence_times)
    if silence_duration > 3.5 * 0.6 or silence_duration1 > 3.5 * 0.75 or silence_duration2 > 3.5 * 0.75:
        print("Too quiet!")
        print("Silence durations: ", silence_duration, silence_duration1, silence_duration2)
        return False, True  # Too quiet
    elif cent > 0.4 and db > 0.5 and score > 0.65:
        print("User has been authenticated!")
        return True, False
    else:
        print("Intruder Alert!")
        return False, False