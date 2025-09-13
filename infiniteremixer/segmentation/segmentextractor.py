# infiniteremixer/segmentation/segmentextractor.py
import os
from infiniteremixer.utils.io import load, write_wav
from infiniteremixer.segmentation.beattracker import estimate_beats
from infiniteremixer.segmentation.trackcutter import cut

class SegmentExtractor:
    def __init__(self, sample_rate):
        self.sample_rate = sample_rate
        self._audio_format = "wav"

    def create_and_save_segments(self, dir, save_dir):
        # 1) make sure save_dir exists
        os.makedirs(save_dir, exist_ok=True)

        for root, _, files in os.walk(dir):
            for file in files:
                # 2) pass the actual root from os.walk
                self._create_and_save_segments_for_file(file, root, save_dir)

    def _create_and_save_segments_for_file(self, file, root, save_dir):
        file_path = os.path.join(root, file)
        signal = load(file_path, self.sample_rate)

        beat_events = estimate_beats(signal, self.sample_rate)  # returns 1D int sample indices
        segments = cut(signal, beat_events)

        if not segments:  # 4) optional guard
            print(f"No segments produced for {file_path} — skipping.")
            return

        self._write_segments_to_wav(file, save_dir, segments)
        print(f"Beats saved for {file_path}")

    def _write_segments_to_wav(self, file, save_dir, segments):
        # 1) ensure directory exists (also protects if save_dir is nested)
        os.makedirs(save_dir, exist_ok=True)

        for i, segment in enumerate(segments):
            save_path = self._generate_save_path(file, save_dir, i)
            # write_wav uses soundfile under the hood
            write_wav(save_path, segment, self.sample_rate)

    def _generate_save_path(self, file, save_dir, num_segment):
        # 3) sanitize: strip original extension -> ant "file.mp3_0.wav"
        base, _ = os.path.splitext(file)
        file_name = f"{base}_{num_segment}.{self._audio_format}"
        return os.path.join(save_dir, file_name)
