from typing import Generator, Collection
from pathlib import Path

def recursive_file_matcher(input_path: Path, matching_names: Collection) -> Generator:
    """Matches all imaging files from input path for which
    the name is specified within the set of matching names

    Args:
        input_path (Path): _description_
        matching_names (set): _description_

    Yields:
        Generator: _description_
    """
    for child in input_path.iterdir():
        if child.is_dir():
            yield from recursive_file_matcher(child, matching_names)
        if child.name in matching_names:
            yield child
