import argparse

from infiniteremixer.utils.io import load_from_pickle, write_wav
from infiniteremixer.remix.audiochunkmerger import AudioChunkMerger
from infiniteremixer.remix.featureretriever import FeatureRetriever
from infiniteremixer.search.nnsearch import NNSearch
from infiniteremixer.remix.beatselector import BeatSelector
from infiniteremixer.remix.remixer import Remixer
from glob import glob
import os

# change these paths to run the script with your data
MAPPING_PATH = ""
FEATURES_PATH = ""
NEAREST_NEIGHBOUR_PATH = ""
SAMPLE_RATE = 22050
SEGMENTS_DIR = ""


def generate_remix():
    parser = argparse.ArgumentParser()
    parser.add_argument("jump_rate",
                        help="rate at which you'd like to see remix jumps. "
                             "Must be between 0 and 1")
    parser.add_argument("number_of_beats",
                        help="number of beats for generated remix")
    parser.add_argument("save_path",
                        help="path where to save generated remix")
    args = parser.parse_args()

    jump_rate = float(args.jump_rate)
    num_of_beats = int(args.number_of_beats)
    save_path = args.save_path

    remixer, chunk_merger = _create_objects(jump_rate, num_of_beats)
    remix = remixer.generate_remix()
    print(f"Generated remix with {num_of_beats} beats")
    audio_remix = chunk_merger.concatenate(remix.file_paths)
    print(f"Merged beats together")
    write_wav(save_path, audio_remix, SAMPLE_RATE)
    print(f"Saved new remix to {SAMPLE_RATE}")


def _create_objects(jump_rate, number_of_beats):
    # 1) Discover segment files as PATHS (strings)
    beats_file_paths = sorted(
        glob(os.path.join(SEGMENTS_DIR, "*.wav")) +
        glob(os.path.join(SEGMENTS_DIR, "*.aif")) +
        glob(os.path.join(SEGMENTS_DIR, "*.aiff")) +
        glob(os.path.join(SEGMENTS_DIR, "*.flac")) +
        glob(os.path.join(SEGMENTS_DIR, "*.ogg"))
    )
    if beats_file_paths == None:
        raise RuntimeError(f"No segments found in {SEGMENTS_DIR}. Did you run `segment ...`?")

    # 2) Load models/mappings into separate vars (DO NOT overwrite beats_file_paths)
    mapping_pickle = load_from_pickle(MAPPING_PATH)
    features = load_from_pickle(FEATURES_PATH)
    nearest_neighbour_model = load_from_pickle(NEAREST_NEIGHBOUR_PATH)

    # If your mapping pickle is a dict/list, normalize to a list of PATH STRINGS
    def to_path_list(m):
        # Accept list[str]
        if isinstance(m, list) and all(isinstance(x, str) for x in m):
            return m
        # Accept dict with string keys that look like paths
        if isinstance(m, dict):
            keys = [k for k in m.keys() if isinstance(k, str)]
            vals = [v for v in m.values() if isinstance(v, str)]
            return keys if keys else vals
        # Otherwise, leave None to avoid corrupting beat_file_paths
        return None

    mapping_paths = to_path_list(mapping_pickle)

    # 3) Wire everything
    chunk_merger = AudioChunkMerger()

    feature_retriever = FeatureRetriever()
    # If the retriever expects a path list, use mapping_paths when available, else fall back to beats_file_paths
    feature_retriever.mapping = mapping_pickle
    feature_retriever.features = features

    nn_search = NNSearch()
    nn_search.mapping = mapping_pickle
    nn_search.model = nearest_neighbour_model

    beat_selector = BeatSelector(jump_rate)
    beat_selector.nn_search = nn_search
    beat_selector.feature_retriever = feature_retriever
    beat_selector.beat_file_paths = beats_file_paths       # <-- list[str], OK

    remixer = Remixer(number_of_beats)
    remixer.beat_selector = beat_selector

    return remixer, chunk_merger


if __name__ == "__main__":
    generate_remix()