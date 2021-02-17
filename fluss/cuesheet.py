from collections import namedtuple, defaultdict
from addict import Dict as edict

class CuesheetTrack(object):
    title: str = None
    performer: str = None
    index00 = None
    index01 = None
    isrc = None

    def __str__(self):
        return f"{self.title} / {self.performer}"
    def __repr__(self):
        return f"<Track {self.title}>"

class Cuesheet:
    def __init__(self) -> None:
        self._rems = {}
        self._title = None
        self._performer = None
        self._files = defaultdict(list)

    @classmethod
    def parse(cls, content: str) -> 'Cuesheet':
        cue = Cuesheet()
        cur_file = None
        cur_tracks = defaultdict(CuesheetTrack)
        cur_idx = None
        for line in content.splitlines():
            if line[:3] == "REM":
                field, value = line[4:].split(' ', 1)
                cue._rems[field] = value.strip(" ").strip('"')
            elif line[:5] == "TITLE":
                cue._title = line[6:].strip(" ").strip('"')
            elif line[:9] == "PERFORMER":
                cue._performer = line[10:].strip(" ").strip('"')
            elif line[:4] == "FILE":
                if cur_file is not None:
                    for i in range(max(cur_tracks.keys())):
                        cue._files[cur_file].append(cur_tracks[i])
                cur_tracks.clear()
                cur_file = line[5:].strip(" ").strip('"')
            elif line[:4] == "    ":
                if line[4:9] == "TITLE":
                    cur_tracks[cur_idx].title = line[10:].strip(" ").strip('"')
                elif line[4:13] == "PERFORMER":
                    cur_tracks[cur_idx].performer = line[14:].strip(" ").strip('"')
                # TODO: parse ISRC, index 00, index 01
            elif line[:2] == "  ":
                field, index, content = line[2:].split(" ")
                if field != "TRACK":
                    raise ValueError("Failed to parse cuesheet!")
                if content != "AUDIO":
                    continue
                cur_idx = int(index) - 1
                cur_track = CuesheetTrack()

        if cur_file is not None:
            for i in range(max(cur_tracks.keys())):
                cue._files[cur_file].append(cur_tracks[i])

        return cue

    def __repr__(self):
        message = "<Cuesheet "
        if self._title is not None:
            message += 'of "%s" ' % self._title
        message += "with %d tracks>" % sum(len(trlist) for trlist in self._files.values())
        return message

    def __str__(self):
        lines = []
        for field, value in self._rems.items():
            lines.append(f'REM {field} {value}')
        if self._title is not None:
            lines.append(f'TITLE "{self._title}"')
        if self._performer is not None:
            lines.append(f'PERFORMER "{self._performer}"')
        for file, tracks in self._files.items():
            lines.append(f'FILE "{file}"')
            for idx, tr in enumerate(tracks):
                lines.append(f"  TRACK {idx:02} AUDIO")
                if tr.title is not None:
                    lines.append(f'    TITLE "{tr.title}"')
                if tr.performer is not None:
                    lines.append(f'    PERFORMER "{tr.performer}"')
                # TODO: print index 00 and index 01
        return "\n".join(lines)
