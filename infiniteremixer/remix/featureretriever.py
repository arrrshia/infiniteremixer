# infiniteremixer/remix/featureretriever.py
import os

class FeatureRetriever:
    def __init__(self):
        self.mapping = None      # list[str] of paths saved with the model
        self.features = None     # np.ndarray aligned with mapping's order
        self._basename_to_index = None
        self._stem_to_index = None

    def _build_indexes_if_needed(self):
        if self.mapping is None:
            raise RuntimeError("FeatureRetriever.mapping is not set")
        if self._basename_to_index is not None:
            return
        # Build lookup tables
        self._basename_to_index = {}
        self._stem_to_index = {}
        for i, p in enumerate(self.mapping):
            base = os.path.basename(p)
            self._basename_to_index.setdefault(base, i)
            stem = os.path.splitext(base)[0]
            self._stem_to_index.setdefault(stem, i)

    def _from_path_to_index(self, file_path: str) -> int:
        # 1) exact match if possible
        try:
            return self.mapping.index(file_path)
        except ValueError:
            pass

        # 2) fallback to basename/stem matching
        self._build_indexes_if_needed()
        base = os.path.basename(file_path)
        if base in self._basename_to_index:
            return self._basename_to_index[base]

        stem = os.path.splitext(base)[0]
        if stem in self._stem_to_index:
            return self._stem_to_index[stem]

        # 3) nothing matched: raise with context
        raise ValueError(
            f"{file_path!r} not found in mapping; "
            f"tried exact, basename, and stem matching "
            f"(mapping size={len(self.mapping)})"
        )

    def get_feature_vector(self, file_path: str):
        idx = self._from_path_to_index(file_path)
        return self.features[idx]
