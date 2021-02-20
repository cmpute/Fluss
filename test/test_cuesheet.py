from pathlib import Path
from fluss.cuesheet import Cuesheet
import pytest

def test_parse_cuesheet():
    test_data = Path(__file__).parent / "normal.cue"
    cue = Cuesheet.from_file(test_data)
    assert len(cue) == 2

    test_data = Path(__file__).parent / "multi-files-explicit-gap.cue"
    cue = Cuesheet.from_file(test_data)
    assert len(cue) == 2

    test_data = Path(__file__).parent / "multi-files-prepend-gap.cue"
    cue = Cuesheet.from_file(test_data)
    assert len(cue) == 2

    test_data = Path(__file__).parent / "multi-files-append-gap.cue"
    cue = Cuesheet.from_file(test_data)
    assert len(cue) == 3
