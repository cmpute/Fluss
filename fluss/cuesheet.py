from collections import namedtuple, defaultdict
from addict import Dict as edict
from typing import Dict
from datetime import time

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
    title: str = None
    performer: str = None
    index00: int = None
    index01: int = None
    isrc: str = None
    pregap: int = None
    postgap: int = None

    def __str__(self):
        return f"{self.title} / {self.performer}"
    def __repr__(self):
        return f"<Track {self.title}>"

class Cuesheet:
    rems: Dict[str, str] = {}
    title: str = None
    performer: str = None
    catalog: str = None
    files: Dict[str, Dict[int, CuesheetTrack]] = defaultdict(dict)

    @classmethod
    def parse(cls, content: str) -> 'Cuesheet':
        cue = Cuesheet()
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
                cur_idx = int(index) - 1
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
        return "\n".join(lines)
