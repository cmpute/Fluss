from collections import defaultdict, namedtuple
from pathlib import Path
from typing import Dict, Union
from os import linesep

import chardet
from chardet.enums import LanguageFilter
from mutagen import flac


def _parse_index_point(timestr: str) -> int:
    timestr = timestr.strip()
    mm, ss, ff = int(timestr[:2]), int(timestr[3:5]), int(timestr[6:8])
    return (mm * 60 + ss) * 75 + ff
def _print_index_point(offset: int) -> str:
    c = offset % 75
    offset = offset // 75
    b = offset % 60
    a = offset // 60
    return f"{a:02}:{b:02}:{c:02}"

class CuesheetTrack(object):
    title: str
    performer: str
    index00: int
    index01: int
    isrc: str
    pregap: int
    postgap: int

    def __init__(self):
        self.title = None
        self.performer = None
        self.index00 = None
        self.index01 = None
        self.isrc = None
        self.pregap = None
        self.postgap = None

    def update(self, cuetrack: "CuesheetTrack"):
        # merge simple fields
        for key in ['title', 'performer', 'index00', 'index01', 'isrc', 'pregap', 'postgap']:
            new_value = getattr(cuetrack, key, None)
            if new_value:
                setattr(self, key, new_value)

    def __str__(self):
        return f"{self.title} / {self.performer}"
    def __repr__(self):
        return f"<Cuetrack {self.title}>"

_default_cuesheet_file = "CDImage.wav"

class Cuesheet:
    rems: Dict[str, str]
    title: str
    performer: str
    catalog: str
    files: Dict[str, Dict[int, CuesheetTrack]]
    '''
    A dictionary storing the mapping for file to the tracks in the file. Notice
    that the track index in cuesheet starts from 1.
    '''

    def __init__(self) -> None:
        self.rems = dict()
        self.title = None
        self.performer = None
        self.catalog = None
        self.files = defaultdict(dict)

    def update(self, cuesheet: "Cuesheet", merge_file: bool = None):
        '''
        :param merge_file: Whether merge track list to be under the same file.
            Only take place when both cuesheet has only one file.
            If None, then only file named as CDImage.wav will be merged.
        '''
        # merge simple fields
        for key in ['title', 'performer', 'catalog']:
            new_value = getattr(cuesheet, key, None)
            if new_value:
                setattr(self, key, new_value)
        self.rems.update(cuesheet.rems)

        # merge tracks
        def merge_tracks(file_cur, file_merge):
            for track_idx, track in cuesheet.files[file_merge].items():
                if track_idx not in self.files[file_cur]:
                    self.files[file_cur][track_idx] = track
                else:
                    self.files[file_cur][track_idx].update(track)

        if len(self.files) == 1 and len(cuesheet.files) == 1:
            file_cur = next(iter(self.files.keys()))
            file_merge = next(iter(cuesheet.files.keys()))
            if merge_file == True:
                merge_tracks(file_cur, file_merge)
            elif merge_file is None and file_merge == _default_cuesheet_file:
                merge_tracks(file_cur, file_merge)
            elif merge_file is None and file_cur == _default_cuesheet_file:
                if file_cur != file_merge: # change file name
                    self.files[file_merge] = self.files[file_cur]
                    del self.files[file_cur]
                merge_tracks(file_merge, file_merge)
            else:
                merge_tracks(file_merge, file_merge)
        else:
            for file, file_tracks in cuesheet.files.items():
                if file in self.files:
                    merge_tracks(file, file)
                else:
                    self.files[file] = file_tracks

    @classmethod
    def from_flac(cls, flac_cuesheet: flac.CueSheet) -> "Cuesheet":
        '''
        Update cuesheet structure from FLAC embedded cuesheet
        '''
        cue = cls()
        cue.catalog = flac_cuesheet.media_catalog_num

        file = _default_cuesheet_file
        for track in flac_cuesheet.tracks:
            cue.files[file][track.track_number] = CuesheetTrack()
            cue.files[file][track.track_number].isrc = track.isrc
            for index in track.indexes:
                if index.index_number == 0:
                    cue.files[file][track.track_number].index00 += track.start_offset + index.index_offset
                elif index.index_number == 1:
                    cue.files[file][track.track_number].index01 += track.start_offset + index.index_offset
        return cue

    @classmethod
    def from_file(cls, path: Union[str, Path], encoding=None) -> "Cuesheet":
        content = Path(path).read_bytes()
        if encoding is None:
            detector = chardet.UniversalDetector(lang_filter=LanguageFilter.CHINESE | LanguageFilter.JAPANESE)
            detector.feed(content)
            encoding = detector.close()['encoding']
        return cls.parse(content.decode(encoding))

    @classmethod
    def parse(cls, content: str) -> 'Cuesheet':
        cue = cls()
        cur_file = None
        cur_tracks = defaultdict(CuesheetTrack)
        cur_idx = None
        for line in content.splitlines():
            if line[:3] == "   ": # 3-4 spaces prefix
                field, value = line.strip().split(' ', 1)
                field = field.upper()
                if field == "TITLE":
                    cur_tracks[cur_idx].title = value.strip().strip('"')
                elif field == "PERFORMER":
                    cur_tracks[cur_idx].performer = value.strip().strip('"')
                elif field == "INDEX":
                    idx, offset = value.split(" ", 1)
                    idx, offset = int(idx), _parse_index_point(offset)
                    if int(idx) == 0:
                        cur_tracks[cur_idx].index00 = offset
                    elif int(idx) == 1:
                        cur_tracks[cur_idx].index01 = offset
                    else:
                        raise ValueError("Track index %02d is not supported!" % idx)
                elif field == "PREGAP":
                    cur_tracks[cur_idx].pregap = _parse_index_point(value)
                elif field == "POSTGAP":
                    cur_tracks[cur_idx].postgap = _parse_index_point(value)
                elif field == "ISRC":
                    cur_tracks[cur_idx].isrc = value
            elif line[:2] == "  ": # 1-2 spaces prefix
                field, index, content = line[2:].split(" ")
                if field.upper() != "TRACK":
                    raise ValueError("Unrecognized line: " + line)
                if content != "AUDIO":
                    continue
                cur_idx = int(index)
            else:
                field, value = line.strip().split(' ', 1)
                field = field.upper()
                if field == "REM":
                    rem, rem_value = value.split(' ', 1)
                    cue.rems[rem] = rem_value.strip().strip('"')
                elif field == "TITLE":
                    cue.title = value.strip().strip('"')
                elif field == "PERFORMER":
                    cue.performer = value.strip().strip('"')
                elif field == "CATALOG":
                    cue.catalog = value.strip()
                elif field == "FILE":
                    # dump current file tracks
                    if cur_file is not None:
                        cue.files[cur_file] = dict(cur_tracks)

                    # start parsing new file
                    cur_tracks.clear()
                    _, cur_file, file_type = value.split('"')
                    if file_type.strip() != "WAVE":
                        raise ValueError("Unsupported media type: %s!" % file_type)
                else:
                    raise ValueError("Unrecognized line: " + line)

        if cur_file is not None:
            cue.files[cur_file] = dict(cur_tracks)

        return cue

    def __len__(self):
        return sum(len(trlist) for trlist in self.files.values())

    def __repr__(self):
        message = "<Cuesheet "
        if self.title is not None:
            message += 'of "%s" ' % self.title
        message += "with %d tracks>" % len(self)
        return message

    def __str__(self):
        lines = []
        for field, value in self.rems.items():
            lines.append(f'REM {field} {value}')
        if self.title is not None:
            lines.append(f'TITLE "{self.title}"')
        if self.performer is not None:
            lines.append(f'PERFORMER "{self.performer}"')
        for file, tracks in self.files.items():
            lines.append(f'FILE "{file}" WAVE')
            for idx, tr in tracks.items():
                lines.append(f"  TRACK {idx:02} AUDIO")
                if tr.title is not None:
                    lines.append(f'    TITLE "{tr.title}"')
                if tr.performer is not None:
                    lines.append(f'    PERFORMER "{tr.performer}"')
                if tr.pregap is not None:
                    lines.append(f'    PREGAP ' + _print_index_point(tr.pregap))
                if tr.postgap is not None:
                    lines.append(f'    POSTGAP ' + _print_index_point(tr.postgap))
                if tr.index00 is not None:
                    lines.append(f'    INDEX 00 ' + _print_index_point(tr.index00))
                if tr.index01 is not None:
                    lines.append(f'    INDEX 01 ' + _print_index_point(tr.index01))
                if tr.isrc is not None:
                    lines.append(f'    ISRC ' + _print_index_point(tr.isrc))
        return linesep.join(lines)

    def to_file(self, path: Union[str, Path]) -> None:
        Path(path).write_text(str(self), encoding="utf-8-sig")
