# beatselector.py
import os
from os import PathLike
import random, math
from infiniteremixer.remix.beat import Beat


AUDIO_EXTS = (".wav", ".flac", ".aiff", ".aif", ".ogg")

class BeatSelector:
    def __init__(self, jump_rate, segments_dir=None):
        self.jump_rate = jump_rate
        self.nn_search = None
        self.feature_retriever = None
        self._beat_file_paths = []  # private storage
        if segments_dir:
            self.load_from_dir(segments_dir)

    @property
    def beat_file_paths(self):
        return self._beat_file_paths

    @beat_file_paths.setter
    def beat_file_paths(self, paths):
        # enforce types on ANY direct assignment
        cleaned = []
        bad_types = []
        for p in paths:
            if isinstance(p, (str, bytes, PathLike)):
                cleaned.append(os.fspath(p))
            else:
                bad_types.append(type(p).__name__)
        if bad_types:
            raise TypeError(f"beat_file_paths must be path-like; got {set(bad_types)}")
        if not cleaned:
            raise ValueError("beat_file_paths cannot be empty.")
        self._beat_file_paths = cleaned

    def set_beat_file_paths(self, paths):
        # keep this for callers; it uses the same validation
        self.beat_file_paths = paths

    def load_from_dir(self, segments_dir):
        files = [
            os.path.join(segments_dir, f)
            for f in os.listdir(segments_dir)
            if f.lower().endswith(AUDIO_EXTS)
        ]
        if not files:
            raise RuntimeError(f"No audio segments found in {segments_dir}")
        self.beat_file_paths = files

    def choose_beat(self, remix):
        if len(remix) == 0:
            return self._choose_first_beat()
        if self._is_beat_jump(remix.num_beats_with_last_track):
            return self._choose_beat_with_jump(remix.last_beat)
        return self._get_next_beat_in_track_if_possible_or_random(remix.last_beat)

    def _choose_first_beat(self):
        return self._choose_beat_randomly()

    def _choose_beat_randomly(self):
        if not self._beat_file_paths:
            raise RuntimeError("beat_file_paths is empty; call load_from_dir() or set beat_file_paths.")
        chosen = random.choice(self._beat_file_paths)
        # hard guard here too
        if not isinstance(chosen, (str, bytes, PathLike)):
            raise TypeError(f"Found {type(chosen).__name__} in beat_file_paths; expected path string.")
        return Beat.from_file_path(os.fspath(chosen))  # <-- return Beat, not str

    def _is_beat_jump(self, num_beats_with_last_track):
        threshold = self._calculate_jump_threshold(num_beats_with_last_track)
        return random.random() <= threshold

    def _calculate_jump_threshold(self, num_beats_with_last_track):
        if num_beats_with_last_track > 0:
            return self.jump_rate * math.log(num_beats_with_last_track, 10)
        return 0

    def _choose_beat_with_jump(self, last_beat):
        feature_vector = self.feature_retriever.get_feature_vector(last_beat.file_path)
        next_beat_file_paths, _ = self.nn_search.get_closest(feature_vector, 500)
        # validate external results too
        self.beat_file_paths = next_beat_file_paths
        return self._get_closest_beat_of_different_track(self._beat_file_paths, last_beat)

    def _get_closest_beat_of_different_track(self, beat_file_paths, last_beat):
        # Sanitize: keep only real paths (str/PathLike). Adapt if nn_search returns richer records.
        cleaned = []
        for fp in beat_file_paths:
            # handle common shapes: str/PathLike, tuple/dict wrappers, numpy scalars
            if isinstance(fp, (str, bytes, PathLike)):
                cleaned.append(os.fspath(fp))
            elif isinstance(fp, tuple) and fp:
                # e.g., (path, distance) or (path, feature)
                if isinstance(fp[0], (str, bytes, PathLike)):
                    cleaned.append(os.fspath(fp[0]))
            elif isinstance(fp, dict):
                # e.g., {"path": "...", "dist": ...}
                p = fp.get("path")
                if isinstance(p, (str, bytes, PathLike)):
                    cleaned.append(os.fspath(p))
            # else: skip non-path entries (e.g., numpy arrays)

        if not cleaned:
            raise RuntimeError(
                f"_get_closest_beat_of_different_track received no valid path-like items "
                f"(got {len(beat_file_paths)} candidates; none were paths)."
            )

        for file_path in cleaned:
            beat = Beat.from_file_path(file_path)
            if beat.track != last_beat.track:
                return beat
        print("sample types in beat_file_paths:", {type(x).__name__ for x in self.beat_file_paths[:5]})

        # fallback: first valid path
        return Beat.from_file_path(cleaned[0])


    def _get_next_beat_in_track_if_possible_or_random(self, beat):
        next_number = beat.number + 1
        next_path = Beat.replace_number_in_file_path(beat.file_path, next_number)
        if next_path in self._beat_file_paths:
            return Beat.from_file_path(next_path)
        return self._choose_beat_randomly()
