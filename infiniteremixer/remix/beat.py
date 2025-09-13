# infiniteremixer/remix/beat.py
import os
from dataclasses import dataclass
from os import PathLike

@dataclass
class Beat:
    """Represents one beat segment on disk."""
    file_path: str
    track: str
    number: int

    @classmethod
    def from_file_path(cls, file_path):
        if not isinstance(file_path, (str, bytes, PathLike)):
            raise TypeError(
                f"Beat.from_file_path expects a path-like (str/PathLike), got {type(file_path).__name__}"
            )
        file_path = os.fspath(file_path)
        track = cls._get_track_from_file_path(file_path)
        number = cls._get_beat_number_from_file_path(file_path)
        return cls(file_path, track, number)

    @staticmethod
    def _basename_no_ext(file_path: str) -> str:
        base = os.path.basename(file_path)
        name, _ext = os.path.splitext(base)
        return name

    @staticmethod
    def _get_beat_number_from_file_path(file_path: str) -> int:
        name = Beat._basename_no_ext(file_path)
        if "_" not in name:
            raise ValueError(f"Expected '<track>_<index>.ext' but got '{name}'")
        number_str = name.rsplit("_", 1)[1]
        return int(number_str)

    @staticmethod
    def _get_track_from_file_path(file_path: str) -> str:
        name = Beat._basename_no_ext(file_path)
        if "_" not in name:
            raise ValueError(f"Expected '<track>_<index>.ext' but got '{name}'")
        return name.rsplit("_", 1)[0]

    @staticmethod
    def replace_number_in_file_path(file_path: str, number: int) -> str:
        dir_ = os.path.dirname(file_path)
        base = os.path.basename(file_path)
        name, ext = os.path.splitext(base)
        if "_" not in name:
            raise ValueError(f"Expected '<track>_<index>.ext' but got '{name}'")
        track_part = name.rsplit("_", 1)[0]
        new_name = f"{track_part}_{number}{ext}"
        return os.path.join(dir_, new_name)
