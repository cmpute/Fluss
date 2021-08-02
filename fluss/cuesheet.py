from ast import parse
from collections import OrderedDict, defaultdict
from copy import deepcopy
from os import linesep
from pathlib import Path
from typing import Dict, Optional, Union

import chardet
from chardet.enums import LanguageFilter
from mutagen import FileType, Tags, flac
from mutagen.apev2 import APETextValue, APEv2File
from mutagen.id3 import ID3FileType
from mutagen.mp4 import MP4

from fluss.codecs import APETagFiles, ID3TagFiles

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

    def update(self, cuetrack: "CuesheetTrack", overwrite: bool = True):
        # merge simple fields
        for key in ['title', 'performer', 'index00', 'index01', 'isrc', 'pregap', 'postgap']:
            new_value = getattr(cuetrack, key, None)
            old_value = getattr(self, key, None)
            if key in ['index00', 'index01']:
                new_exist = new_value is not None
                old_exist = old_value is not None
            else:
                new_exist = bool(new_value)
                old_exist = bool(old_value)
            if (overwrite and new_exist) or (not overwrite and not old_exist):
                setattr(self, key, new_value)

    def __str__(self):
        return f"{self.title} / {self.performer}"
    def __repr__(self):
        return f"<Cuetrack {self.title}>"

    @staticmethod
    def duration(track: "CuesheetTrack", next_track: "CuesheetTrack") -> int:
        if next_track.index00:
            return next_track.index00 - track.index01
        return next_track.index01 - track.index01

    @staticmethod
    def gap(track: "CuesheetTrack", prev_track: Optional["CuesheetTrack"] = None) -> int:
        if track.pregap:
            return track.pregap
        if track.index00:
            return track.index01 - track.index00
        if prev_track and prev_track.postgap:
            return prev_track.postgap
        return 0

_default_cuesheet_file = "CDImage.wav"

class Cuesheet:
    rems: Dict[str, str]
    title: str
    songwriter: str
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
        self.songwriter = None
        self.catalog = None
        self.files = OrderedDict()

    def copy(self):
        return deepcopy(self)

    def update(self, cuesheet: "Cuesheet", overwrite: bool = True, merge_file: bool = None):
        '''
        :param merge_file: Whether merge track list to be under the same file.
            Only take place when both cuesheet has only one file.
            If None, then only file named as default name (CDImage.wav) will be merged.
        '''
        # merge simple fields
        for key in ['title', 'performer', 'catalog', 'songwriter']:
            new_value = getattr(cuesheet, key, None)
            old_value = getattr(self, key, None)
            if (overwrite and new_value) or (not overwrite and not old_value):
                setattr(self, key, new_value)
        if overwrite:
            self.rems.update(cuesheet.rems)
        else:
            self.rems = dict(cuesheet.rems, **self.rems)

        # merge tracks
        def merge_tracks(file_cur, file_merge):
            for track_idx, track in cuesheet.files[file_merge].items():
                if file_cur not in self.files:
                    self.files[file_cur] = dict()
                if track_idx not in self.files[file_cur]:
                    self.files[file_cur][track_idx] = track
                else:
                    self.files[file_cur][track_idx].update(track, overwrite=overwrite)

        if len(self.files) == 1 and len(cuesheet.files) == 1:
            file_cur = next(iter(self.files.keys()))
            file_merge = next(iter(cuesheet.files.keys()))
            if merge_file == True:
                merge_tracks(file_cur, file_merge)
            elif merge_file is None and file_merge == _default_cuesheet_file:
                merge_tracks(file_cur, file_merge)
            elif merge_file is None and file_cur == _default_cuesheet_file:
                if file_cur != file_merge: # change file name
                    self.files = OrderedDict([(file_merge, v) if k == file_cur else (k, v) for k, v in self.files.items()])
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

    def to_flac(self) -> flac.CueSheet:
        '''
        Dump the cuesheet data to flac format
        '''
        cue = flac.CueSheet(None)

        if len(self.files) > 1:
            raise ValueError("Only cuesheet with single file section is able to be converted to flac cuesheet!")

        for f, tracks in self.files.items():
            for i, track in tracks.items():
                indexes = []
                if track.index00 is not None:
                    start_offset = track.index00
                    indexes.append(flac.CueSheetTrackIndex(0, 0))
                    if track.index01 is not None:
                        indexes.append(flac.CueSheetTrackIndex(1, track.index01 - track.index00))
                elif track.index01 is not None:
                    start_offset = track.index01
                    indexes.append(flac.CueSheetTrackIndex(1, 0))

                flac_track = flac.CueSheetTrack(i, start_offset)
                flac_track.isrc = track.isrc
                flac_track.indexes.extend(indexes)
                cue.tracks.append(flac_track)

        return cue

    @classmethod
    def from_mutagen(cls, tag: Union[flac.FLAC, FileType]) -> "Cuesheet":
        if isinstance(tag, flac.FLAC):
            if tag.cuesheet:
                return cls.from_flac(tag.cuesheet)
            else:
                tags_upper = {k.upper(): v[0] for k, v in tag.tags.items()}
        elif isinstance(tag, APETagFiles):
            if not tag.tags:
                return None
            tags_upper = {k.upper(): v.value for k, v in tag.tags.items() if isinstance(v, APETextValue)}
        elif isinstance(tag, ID3TagFiles):
            return None  # TODO: implement
        elif isinstance(tag, MP4):
            return None  # it seems that MP4 doesn't support embedded cuesheet
        else:
            raise ValueError("Unrecognized mutagen input: " + str(type(tag)))
            
        if 'CUESHEET' in tags_upper:
            return cls.parse(tags_upper['CUESHEET'])
        else:
            return None

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
            if not line.rstrip():
                continue
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
                        print("WARNING: Track index %02d is not supported, will be ignored!" % idx)
                elif field == "PREGAP":
                    cur_tracks[cur_idx].pregap = _parse_index_point(value)
                elif field == "POSTGAP":
                    cur_tracks[cur_idx].postgap = _parse_index_point(value)
                elif field == "ISRC":
                    cur_tracks[cur_idx].isrc = value
            elif line[:2] == "  ": # 1-2 spaces prefix
                field, index, content = line[2:].split(" ")
                if field.upper() != "TRACK":
                    raise SyntaxError("Unrecognized line: " + line)
                if content != "AUDIO":
                    continue
                cur_idx = int(index)
            else:
                field, value = line.strip().split(' ', 1)
                field = field.upper()
                if field == "REM":
                    rem_split = value.split(' ', 1)
                    if len(rem_split) < 2:
                        continue
                    rem, rem_value = value.split(' ', 1)
                    cue.rems[rem] = rem_value.strip().strip('"')
                elif field == "TITLE":
                    cue.title = value.strip().strip('"')
                elif field == "PERFORMER":
                    cue.performer = value.strip().strip('"')
                elif field == "SONGWRITER":
                    cue.songwriter = value.strip().strip('"')
                elif field == "CATALOG":
                    cue.catalog = value.strip()
                elif field == "FILE":
                    # dump current file tracks
                    if cur_file is not None:
                        cue.files[cur_file] = dict(cur_tracks)

                    # start parsing new file
                    cur_tracks.clear()
                    _, cur_file, file_type = value.split('"')
                    if file_type.strip().upper() != "WAVE":
                        raise SyntaxError("Unsupported media type: %s!" % file_type)
                else:
                    raise SyntaxError("Unrecognized line: " + repr(line))

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
        if self.title:
            lines.append(f'TITLE "{self.title}"')
        if self.performer:
            lines.append(f'PERFORMER "{self.performer}"')
        if self.songwriter:
            lines.append(f'SONGWRITER "{self.songwriter}"')
        for file, tracks in self.files.items():
            lines.append(f'FILE "{file}" WAVE')
            sorted_tracks = list(tracks.items())
            sorted_tracks.sort(key=lambda t: t[0])
            for idx, tr in sorted_tracks:
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
                    lines.append(f'    ISRC ' + tr.isrc)
        return linesep.join(lines)

    def to_file(self, path: Union[str, Path]) -> None:
        Path(path).write_text(str(self), encoding="utf-8-sig")
