from pathlib import Path
from fluss.cuesheet import Cuesheet

def test_parse_cuesheet():
    test_data = Path(__file__).parent / "normal.cue"
    cue = Cuesheet.parse(test_data.read_text())
    assert len(cue) == 2
    print(cue)
