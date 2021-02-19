from collections import defaultdict
from typing import List, Set
import mutagen
from mutagen.flac import FLAC
from mutagen.apev2 import APEv2File
from mutagen.id3 import ID3
from fluss.cuesheet import Cuesheet, CuesheetTrack, _default_cuesheet_file

def assert_field(v1, v2, field_name):
    assert not v1 or not v2 or v1 == v2, f"Inconsistent {field_name} between cuesheet and metadata!"

class TrackMeta:
    '''
    Metadata that corresponds to APEv2 or ID3v2 tags of a track
    '''
    title: str
    artists: Set[str]

    def __init__(self) -> None:
        self.title = None
        self.artists = set()

    @property
    def full_artist(self) -> str:
        return ', '.join(self.artists) if self.artists else None

    def update(self, meta: "TrackMeta"):
        if meta.title:
            self.title = meta.title
        self.artists.update(meta.artists)

class DiscMeta:
    '''
    Metadata that corresponds to APEv2 or ID3v2 tags of a disc
    '''
    title: str
    artists: Set[str]
    genre: str
    date: str
    tracks: List[TrackMeta]
    _cuesheet: Cuesheet
    cover: bytes

    def __init__(self) -> None:
        self.title = None
        self.artists = set()
        self.genre = None
        self.date = None
        self.tracks = list()
        self._cuesheet = None
        self.cover = None

    def _reserve_tracks(self, track_idx):
        if track_idx > len(self.tracks):
            for _ in range(len(self.tracks), track_idx):
                self.tracks.append(TrackMeta())

    def update(self, meta: "DiscMeta"):
        '''
        Update information from meta input. This function acts like :func:`dict.update()`
        '''
        # update simple fields
        for key in ['title', 'genre', 'date', 'cover']:
            new_value = getattr(meta, key, None)
            if new_value:
                setattr(self, key, new_value)
        self.artists.update(meta.artists)
        if self._cuesheet is None:
            self._cuesheet = meta._cuesheet
        else:
            self._cuesheet.update(meta._cuesheet)

        # update tracks
        self._reserve_tracks(len(meta.tracks))
        for track, new_track in zip(self.tracks, meta.tracks):
            track.update(new_track)

    @classmethod
    def from_flac(cls, flac_meta: FLAC):
        '''
        Create metadata from FLAC file
        '''
        meta = cls()
        def get_first(name):
            if name not in flac_meta.tags:
                return None
            value = flac_meta.tags[name][0]
            return value or None
        if get_first('ALBUM'):
            meta.title = get_first('ALBUM')
        if 'ALBUMARTIST' in flac_meta:
            meta.artists.update((a for a in flac_meta.tags.get('ALBUMARTIST') if a))
        if get_first('DATE'):
            meta.date = get_first('DATE')
        track_idx = int(get_first('TRACKNUMBER'))
        if track_idx: # This is an flac for single track
            meta._reserve_tracks(track_idx)
            cur_track = meta.tracks[track_idx-1]
            if get_first('TITLE'):
                cur_track.title = get_first('TITLE')
            if 'ARTIST' in flac_meta:
                cur_track.artists.update((a for a in flac_meta.tags.get('ARTIST') if a))

        if flac_meta.cuesheet:
            meta._cuesheet = Cuesheet.from_flac(flac_meta.cuesheet)
        if flac_meta.pictures:
            meta.cover = flac_meta.pictures # TODO: parse

        return meta

    def from_ape(self, ape_meta: APEv2File):
        '''
        Create metadata from media with APEv2 tags
        '''
        pass

    def from_id3(self, id3_meta: ID3):
        '''
        Create metadata from media with ID3v2 tags
        '''
        raise NotImplementedError("Parse metadata from ID3 tag is not implemented!")

    @classmethod
    def from_mutagen(cls, mutagen_file: mutagen.FileType):
        '''
        Create metadata from mutagen file
        '''
        if isinstance(mutagen_file, FLAC):
            return cls.from_flac(mutagen_file)
        elif isinstance(mutagen_file, APEv2File):
            return cls.from_ape(mutagen_file)
        elif isinstance(mutagen_file, ID3):
            return cls.from_id3(mutagen_file)
        else:
            raise ValueError("Unsupported mutagen format!")

    @classmethod
    def from_cuesheet(cls, cuesheet: Cuesheet):
        '''
        Create metadata from cuesheet
        '''
        meta = cls()
        meta.title = cuesheet.title
        if cuesheet.performer:
            meta.artists.add(cuesheet.performer)
        meta.genre = cuesheet.rems.get('GENRE', None)
        meta.date = cuesheet.rems.get('DATE', None)
        for file_tracks in cuesheet.files.values():
            for track_idx, track in file_tracks.items():
                meta._reserve_tracks(track_idx)
                meta.tracks[track_idx-1].title = track.title
                if track.performer:
                    meta.tracks[track_idx-1].artists.add(track.performer)

    @property
    def cuesheet(self) -> Cuesheet:
        return self._cuesheet

    @cuesheet.setter
    def cuesheet(self, value: Cuesheet):
        # check consistency between metadata and cuesheet
        assert_field(value.title, self.title, "album title")
        assert_field(value.performer, self.full_artist, "album artist")
        assert_field(value.rems.get('GENRE', None), self.genre, "genre")
        assert_field(value.rems.get('DATE', None), self.date, "date")

        for file_tracks in value.files.values():
            for track_idx, track in file_tracks.items():
                if track_idx <= len(self.tracks):
                    cur_track = self.tracks[track_idx-1]
                    assert_field(track.title, cur_track.title, "track %d title" % track_idx)
                    assert_field(track.performer, cur_track.full_artist, "track %d artist" % track_idx)

        self._cuesheet = value

    @property
    def full_artist(self) -> str:
        return ', '.join(self.artists) if self.artists else None

    def to_flac(self, flac_meta: FLAC):
        raise NotImplementedError("Convert metadata to FLAC is not implemented!")

    def to_id3(self, id3_meta: ID3):
        raise NotImplementedError("Convert metadata to FLAC is not implemented!")

    def to_ape(self, ape_meta: APEv2File):
        if ape_meta.tags is None:
            ape_meta.add_tags()
        if self.title:
            ape_meta.tags['Album'] = self.title
        if self.artists:
            ape_meta.tags['Album artist'] = self.full_artist
        if self.cuesheet:
            ape_meta.tags['Cuesheet'] = str(self.cuesheet)
        if self.cover:
            ape_meta.tags['Cover Art (Front)'] = self.cover # TODO: parse
        # TODO: parse other fields

    def to_mutagen(self, mutagen_file: mutagen.FileType):
        if isinstance(mutagen_file, FLAC):
            return self.to_flac(mutagen_file)
        elif isinstance(mutagen_file, APEv2File):
            return self.to_ape(mutagen_file)
        elif isinstance(mutagen_file, ID3):
            return self.to_id3(mutagen_file)
        else:
            raise ValueError("Unsupported mutagen format!")

    def to_cuesheet(self, cuesheet: Cuesheet = None):
        '''
        Generate cuesheet of vverride fields in given cuesheet according to this metadata
        '''
        gen = Cuesheet()
        gen.title = self.title
        gen.performer = self.full_artist
        if self.genre:
            gen.rems['GENRE'] = self.genre
        if self.date:
            gen.rems['DATE'] = self.date
        for track_idx, track in enumerate(self.tracks):
            cuetrack = CuesheetTrack()
            cuetrack.title = track.title
            cuetrack.performer = track.full_artist
            gen.files[_default_cuesheet_file][track_idx + 1] = cuetrack

        if cuesheet is not None:
            cuesheet.update(gen)
            return cuesheet
        else:
            return gen

class AlbumMeta: # corresponds to meta.yaml
    pass
