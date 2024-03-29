from copy import deepcopy
from io import BytesIO
from typing import Dict, List, Set, Tuple

import mutagen
from mutagen import mp4
from mutagen.apev2 import BINARY, TEXT, APEv2File, APEValue
from mutagen.flac import CueSheetTrack, FLAC, Picture
from mutagen.id3 import ID3, ID3FileType, PictureType
from mutagen.mp4 import MP4, MP4Cover
from PIL import Image

from fluss import cuesheet
from fluss.cuesheet import Cuesheet, CuesheetTrack, _default_cuesheet_file
from fluss.codecs import APETagFiles, ID3TagFiles

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

    def __str__(self) -> str:
        return f'''Track Metadata
\ttitle: {self.title}
\tartists: {self.full_artist}'''

    @property
    def full_artist(self) -> str:
        return ', '.join(self.artists) if self.artists else None

    def update(self, meta: "TrackMeta", overwrite: bool = True):
        if meta is None:
            return

        for key in ['title', 'artists']:
            new_value = getattr(meta, key, None)
            old_value = getattr(self, key, None)
            if (overwrite and new_value) or (not overwrite and not old_value):
                setattr(self, key, new_value)

    @classmethod
    def from_flac(cls, flac_meta: FLAC) -> "TrackMeta":
        if not flac_meta.tags:
            return cls()

        cur_track = TrackMeta()
        cur_updated = False
        if 'TITLE' in flac_meta.tags:
            cur_track.title = flac_meta.tags['TITLE'][0]
            cur_updated = True
        if 'ARTIST' in flac_meta.tags:
            cur_track.artists.update(a for a in flac_meta.tags.get('ARTIST') if a)
            cur_updated = True

        return cur_track if cur_updated else None
        
    @classmethod
    def from_ape(cls, ape_meta: APEv2File) -> "TrackMeta":
        '''
        Create metadata from media with APEv2 tags
        '''
        if not ape_meta.tags:
            return cls()

        raise NotImplementedError()

    @classmethod
    def from_id3(cls, id3_meta: ID3) -> "TrackMeta":
        '''
        Create metadata from media with ID3v2 tags
        '''
        if not id3_meta.tags:
            return cls()

        cur_track = TrackMeta()
        cur_updated = False
        if 'TIT2' in id3_meta.tags:
            cur_track.title = id3_meta.tags['TIT2'].text[0]
            cur_updated = True
        if 'TPE1' in id3_meta:
            cur_track.artists.update(a for a in id3_meta.tags['TPE1'].text if a)
            cur_updated = True

        return cur_track if cur_updated else None

    @classmethod
    def from_mp4(cls, mp4_meta: MP4) -> "TrackMeta":
        if not mp4_meta.tags:
            return cls()

        cur_track = TrackMeta()
        cur_updated = False
        if '\xa9nam' in mp4_meta.tags:
            cur_track.title = mp4_meta.tags['\xa9nam'][0]
            cur_updated = True
        if '\xa9ART' in mp4_meta.tags:
            cur_track.artists.update(a for a in mp4_meta.tags['\xa9ART'] if a)
            cur_updated = True

        return cur_track if cur_updated else None

    @classmethod
    def from_mutagen(cls, mutagen_file: mutagen.FileType) -> "TrackMeta":
        '''
        Create metadata from mutagen file
        track_mode: regard the file as single track
        '''
        if isinstance(mutagen_file, FLAC):
            return cls.from_flac(mutagen_file)
        elif isinstance(mutagen_file, APETagFiles):
            return cls.from_ape(mutagen_file)
        elif isinstance(mutagen_file, ID3TagFiles):
            return cls.from_id3(mutagen_file)
        elif isinstance(mutagen_file, MP4):
            return cls.from_mp4(mutagen_file)
        else:
            raise ValueError("Unsupported mutagen format!")

class DiscMeta:
    '''
    Metadata that corresponds to APEv2 or ID3v2 tags of a disc
    '''
    title: str
    artists: Set[str]
    genre: str
    date: str
    tracks: List[TrackMeta]
    cover: bytes
    discnumber: int
    partnumber: str

    _cuesheet: Cuesheet

    def __init__(self) -> None:
        self._cuesheet = None

        self.title = None
        self.artists = set()
        self.genre = None
        self.date = None
        self.tracks = list()
        self.cover = None
        self.partnumber = None
        self.discnumber = None

    def __str__(self) -> str:
        str_tracks = [f"\n\t{i+1:02} " + str(t).replace("\n", "\n\t") for i, t in enumerate(self.tracks)] # indent
        return f'''Disc Metadata
\ttitle: {self.title}
\tartists: {self.full_artist}
\tgenre: {self.genre}
\tdate: {self.date}
\ttracks: {''.join(str_tracks)}
\tcover: {not (self.cover is None)}'''

    def _reserve_tracks(self, track_idx):
        '''
        track_idx: starts from 0
        '''
        if track_idx >= len(self.tracks):
            for _ in range(len(self.tracks), track_idx + 1):
                self.tracks.append(None)

    def copy(self):
        return deepcopy(self)

    def update(self, meta: "DiscMeta", overwrite: bool = True) -> None:
        '''
        Update information from :attr:`meta` input. This function acts like :func:`dict.update()`

        :overwrite: When values exist in both object, data from :attr:`meta` is chosen if True,
            otherwise keep not modified
        '''
        # update simple fields
        for key in ['title', 'genre', 'date', 'cover', 'artists']:
            new_value = getattr(meta, key, None)
            old_value = getattr(self, key, None)
            if (overwrite and new_value) or (not overwrite and not old_value):
                setattr(self, key, new_value)
        if self._cuesheet is None:
            self._cuesheet = meta._cuesheet.copy() if meta._cuesheet else None
        elif meta._cuesheet is not None:
            self._cuesheet.update(meta._cuesheet, overwrite=overwrite)

        # update tracks
        self._reserve_tracks(len(meta.tracks) - 1)
        for i, new_track in zip(range(len(self.tracks)), meta.tracks):
            self.update_track(i, new_track, overwrite=overwrite)

    def update_track(self, index: int, meta: TrackMeta, overwrite: bool = True):
        if self.tracks[index]:
            self.tracks[index].update(meta, overwrite=overwrite)
        else:
            self.tracks[index] = meta

    @classmethod
    def from_flac(cls, flac_meta: FLAC) -> "DiscMeta":
        '''
        Create metadata from FLAC file
        '''
        meta = cls()
        flac_tags = {k.upper(): v for k, v in flac_meta.tags.items()}

        def get_first(name):
            if name not in flac_tags:
                return None
            value = flac_tags[name][0]
            return value or None

        # parse common fields
        meta.title = get_first('ALBUM')
        if 'ALBUMARTIST' in flac_tags:
            meta.artists.update((a for a in flac_tags.get('ALBUMARTIST') if a))
        if 'ALBUM ARTIST' in flac_tags:
            meta.artists.update((a for a in flac_tags.get('ALBUM ARTIST') if a))
        meta.date = get_first('DATE')

        # parse disc numbers
        disc_str = get_first('DISC')
        if disc_str:
            if '/' in disc_str:
                discnumber, _ = disc_str.rsplit('/')
                meta.discnumber = int(discnumber)
            else:
                meta.discnumber = int(disc_str)
        discnum_str = get_first('DISCNUMBER')
        if discnum_str:
            meta.discnumber = int(discnum_str)

        # prase track numbers
        track_idx_str = get_first('TRACKNUMBER')
        if track_idx_str: # This is an flac for single track
            if '/' in track_idx_str:
                idx_str, total_str = track_idx_str.rsplit('/')
                track_idx = int(idx_str) - 1
                reserved_idx = int(total_str) - 1
            else:
                track_idx = int(track_idx_str) - 1
                reserved_idx = track_idx
            meta._reserve_tracks(reserved_idx)
            meta.tracks[track_idx] = TrackMeta.from_flac(flac_meta)

        # get cuesheet
        if flac_meta.cuesheet:
            meta._cuesheet = Cuesheet.from_flac(flac_meta.cuesheet, flac_meta.info.sample_rate)
        if 'CUESHEET' in flac_tags:
            cs = Cuesheet.parse(get_first('CUESHEET'))
            if meta._cuesheet:
                meta._cuesheet.update(cs)
            else:
                meta._cuesheet = cs

        # get cover
        if flac_meta.pictures:
            for pic in flac_meta.pictures:
                if pic.type == PictureType.COVER_FRONT:
                    meta.cover = pic.data
                    break
            else:
                meta.cover = flac_meta.pictures[0].data

        return meta

    @classmethod
    def from_ape(cls, ape_meta: APEv2File) -> "DiscMeta":
        '''
        Create metadata from media with APEv2 tags
        '''
        if not ape_meta.tags:
            return cls()

        raise NotImplementedError("Parsing metadata from APE tags is not implemented!")

        meta = cls()
        ape_tags = {k.upper(): v for k, v in ape_meta.tags.items()}

        if 'CUESHEET' in ape_tags:
            meta._cuesheet = Cuesheet.parse(ape_tags['CUESHEET'].value)

        return meta

    @classmethod
    def from_mp4(cls, mp4_meta: MP4) -> "DiscMeta":
        '''
        Create metadata from media with APEv2 tags
        '''
        if not mp4_meta.tags:
            return cls()

        meta = cls()

        # parse common fields
        if mp4_meta.tags.get("\xa9alb", None):
            meta.title = mp4_meta.tags["\xa9alb"][0]
        if mp4_meta.tags.get("aART", None):
            meta.artists.update(a for a in mp4_meta.tags["aART"] if a)
        if mp4_meta.tags.get("\xa9day", None):
            meta.date = mp4_meta.tags["\xa9day"][0]

        # parse disc numbers
        if "disk" in mp4_meta.tags:
            discnum_tuple: Tuple[int, int] = mp4_meta.tags["disk"][0]
            meta.discnumber = discnum_tuple[0]

        # parse track numbers
        if "trkn" in mp4_meta.tags: # This is an mp4 file for single track
            track_idx_tuple: Tuple[int, int] = mp4_meta.tags["trkn"][0]
            track_idx = track_idx_tuple[0] - 1
            reserved_idx = track_idx
            meta._reserve_tracks(reserved_idx)
            meta.tracks[track_idx] = TrackMeta.from_mp4(mp4_meta)

        # TODO: it seems that mp4 doesn't support embedded cuesheet

        # get cover
        if mp4_meta.tags.get("covr", None):
            meta.cover = mp4_meta["covr"]

        return meta

    @classmethod
    def from_id3(cls, id3_meta: ID3FileType) -> "DiscMeta":
        '''
        Create metadata from media with ID3v2 tags

        Mutagen reference: https://github.com/quodlibet/mutagen/blob/master/mutagen/easyid3.py#L470
        '''
        if not id3_meta.tags:
            return cls()

        def get_first(name):
            if name not in id3_meta.tags:
                return None
            value = id3_meta.tags[name].text
            if value:
                return value[0]
            return None

        meta = cls()

        # parse common fields
        if "TALB" in id3_meta.tags:
            meta.title = get_first("TALB")
        if 'TPE2' in id3_meta.tags:
            meta.artists.update(a for a in id3_meta.tags.get("TPE2").text if a)
        if 'TDRC' in id3_meta.tags:
            meta.date = get_first("TDRC").text

        # parse disc numbers
        discnum_str = get_first('TPOS')
        if discnum_str:
            if '/' in discnum_str:
                idx_str, total_str = discnum_str.rsplit('/')
                meta.discnumber = int(idx_str)
            else:
                meta.discnumber = int(discnum_str)

        # parse track numbers
        track_idx_str = get_first('TRCK')
        if track_idx_str: # This is an id3 file for single track
            if '/' in track_idx_str:
                idx_str, total_str = track_idx_str.rsplit('/')
                track_idx = int(idx_str) - 1
                reserved_idx = int(total_str) - 1
            else:
                track_idx = int(track_idx_str) - 1
                reserved_idx = track_idx
            meta._reserve_tracks(reserved_idx)
            meta.tracks[track_idx] = TrackMeta.from_flac(id3_meta)

        # TODO: get cuesheet

        # get cover
        if "APIC:" in id3_meta.tags:
            meta.cover = id3_meta["APIC:"].data

        return meta

    @classmethod
    def from_mutagen(cls, mutagen_file: mutagen.FileType) -> "DiscMeta":
        '''
        Create metadata from mutagen file. Note that cuesheet will not fill the main fields in this method.
        track_mode: regard the file as single track
        '''
        if isinstance(mutagen_file, FLAC):
            return cls.from_flac(mutagen_file)
        elif isinstance(mutagen_file, APETagFiles):
            return cls.from_ape(mutagen_file)
        elif isinstance(mutagen_file, ID3TagFiles):
            return cls.from_id3(mutagen_file)
        elif isinstance(mutagen_file, MP4):
            return cls.from_mp4(mutagen_file)
        else:
            raise ValueError("Unsupported mutagen format: " + str(type(mutagen_file)))

    @classmethod
    def from_cuesheet(cls, cuesheet: Cuesheet) -> "DiscMeta":
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
                meta._reserve_tracks(track_idx - 1)

                track_meta = TrackMeta()
                track_updated = False
                if track.title:
                    track_meta.title = track.title
                    track_updated = True
                if track.performer:
                    track_meta.artists.add(track.performer)
                    track_updated = True

                if track_updated:
                    meta.tracks[track_idx-1] = track_meta
        return meta

    @property
    def cuesheet(self) -> Cuesheet:
        return self._cuesheet

    @cuesheet.setter
    def cuesheet(self, value: Cuesheet) -> None:
        # check consistency between metadata and cuesheet
        assert_field(value.title, self.title, "album title")
        assert_field(value.performer, self.full_artist, "album artist")
        assert_field(value.rems.get('GENRE', None), self.genre, "genre")
        assert_field(value.rems.get('DATE', None), self.date, "date")

        for file_tracks in value.files.values():
            for track_idx, track in file_tracks.items():
                if track_idx <= len(self.tracks):
                    cur_track = self.tracks[track_idx-1]
                    if cur_track:
                        assert_field(track.title, cur_track.title, "track %d title" % track_idx)
                        assert_field(track.performer, cur_track.full_artist, "track %d artist" % track_idx)

        self._cuesheet = value

    @property
    def full_artist(self) -> str:
        return ', '.join(self.artists) if self.artists else None

    def to_flac(self, flac_meta: FLAC, builtin_cuesheet=False) -> None:
        '''
        :param builtin_cuesheet: Whether to use the cuesheet field builtin FLAC specs
        '''
        def add_if_exist(obj, tag_key):
            if obj:
                flac_meta.tags[tag_key] = obj

        add_if_exist(self.title, 'ALBUM')
        add_if_exist(self.genre, 'GENRE')
        add_if_exist(self.date, 'DATE')
        if self.artists:
            flac_meta.tags['ALBUM ARTIST'] = list(self.artists)
        if self.discnumber is not None:
            flac_meta.tags['DISCNUMBER'] = str(self.discnumber)

        if self.cover:
            image = Image.open(BytesIO(self.cover))
            pic = Picture()
            pic.type = PictureType.COVER_FRONT
            pic.data = self.cover
            pic.mime = Image.MIME[image.format]
            pic.width = image.width
            pic.height = image.height
            flac_meta.add_picture(pic)

        if self.cuesheet:
            if builtin_cuesheet:
                flac_meta.cuesheet = self.cuesheet.to_flac(flac_meta.info.sample_rate)
                flac_meta.cuesheet.tracks.append(CueSheetTrack(170, flac_meta.info.total_samples)) # lead-out

                # save track-wise tags in foobar2000 style
                tracks = next(iter(self.cuesheet.files.values()))
                for i, track in tracks.items():
                    add_if_exist(track.title, f'CUE_TRACK{i:02}_TITLE')
                    add_if_exist(track.performer, f'CUE_TRACK{i:02}_PERFORMER')
            else:
                flac_meta.tags['CUESHEET'] = str(self.cuesheet)
            add_if_exist(self.cuesheet.catalog, 'Catalog')
            add_if_exist(self.cuesheet.rems.get('COMMENT', None), 'Comment')

        flac_meta.save()

    def to_id3(self, id3_meta: ID3) -> None:
        raise NotImplementedError("Convert metadata to FLAC is not implemented!")

    def to_mp4(self, mp4_meta: MP4) -> None:
        raise NotImplementedError("Convert metadata to MP4(M4A) is not implemented!")

    def to_ape(self, ape_meta: APEv2File) -> None:
        def add_if_exist(obj, tag_key):
            if obj is None:
                return
            if isinstance(obj, str):
                ape_meta.tags[tag_key] = APEValue(obj, TEXT)
            elif isinstance(obj, bytes):
                ape_meta.tags[tag_key] = APEValue(obj, BINARY)
            else:
                raise ValueError("Unknown tag value type")

        if ape_meta.tags is None:
            ape_meta.add_tags()

        add_if_exist(self.title, 'ALBUM')
        add_if_exist(self.full_artist, 'ALBUM ARTIST')
        if self.cover:
            add_if_exist(b'fluss.jpg\x00' + self.cover, 'Cover Art (Front)')
        add_if_exist(self.genre, 'GENRE')
        add_if_exist(self.date, 'YEAR')
        if self.discnumber is not None:
            add_if_exist(str(self.discnumber), 'DISCNUMBER')
        if self.cuesheet:
            ape_meta.tags['CUESHEET'] = str(self.cuesheet)
            add_if_exist(self.cuesheet.catalog, 'CATALOG')
            add_if_exist(self.cuesheet.rems.get('UPC', None), 'UPC')
            add_if_exist(self.cuesheet.rems.get('COMMENT', None), 'COMMENT')

        ape_meta.save()

    def to_mutagen(self, mutagen_file: mutagen.FileType) -> None:
        if isinstance(mutagen_file, FLAC):
            self.to_flac(mutagen_file)
        elif isinstance(mutagen_file, APETagFiles):
            self.to_ape(mutagen_file)
        elif isinstance(mutagen_file, ID3TagFiles):
            self.to_id3(mutagen_file)
        else:
            raise ValueError("Unsupported mutagen format!")

    def to_cuesheet(self):
        '''
        Generate a cuesheet according to this metadata
        '''
        gen = Cuesheet()
        gen.title = self.title
        gen.performer = self.full_artist
        if self.genre:
            gen.rems['GENRE'] = self.genre
        if self.date:
            gen.rems['DATE'] = self.date
        for track_idx, track in enumerate(self.tracks):
            if track is None:
                continue

            cuetrack = CuesheetTrack()
            cuetrack.title = track.title
            cuetrack.performer = track.full_artist
            if _default_cuesheet_file not in gen.files:
                gen.files[_default_cuesheet_file] = {}
            gen.files[_default_cuesheet_file][track_idx + 1] = cuetrack

        if self._cuesheet is not None:
            gen.update(self._cuesheet, overwrite=False)

        return gen

class FolderMeta:
    catalog: str
    partnumber: str
    edition: str
    tool: str
    source: str
    ripper: str
    comment: str
    database: Dict[str, str]

    def __init__(self):
        self.catalog = None
        self.partnumber = None
        self.edition = None
        self.tool = None
        self.source = None
        self.ripper = None
        self.comment = None
        self.database = dict()

    def to_dict(self) -> dict:
        obj = dict()
        for key in ['catalog', 'partnumber', 'edition', 'tool', 'source', 'ripper', 'comment']:
            if getattr(self, key):
                obj[key] = getattr(self, key)
        if self.database:
            obj['database'] = dict(self.database)
        return obj

class AlbumMeta: # corresponds to meta.yaml
    folders: Dict[str, FolderMeta]
    title: str
    artists: Set[str]
    publisher: str
    vendor: str
    event: str
    date: str
    genre: str
    associations: Dict[str, str]

    def __init__(self):
        self.folders = dict()
        self.title = None
        self.artists = None
        self.publisher = None
        self.vendor = None
        self.event = None
        self.date = None
        self.genre = None
        self.associations = dict()

    @property
    def full_artist(self) -> str:
        return ', '.join(self.artists) if self.artists else None

    def to_dict(self) -> dict:
        meta_dict = dict()
        for key in ["title", "event", "date", "genre"]:
            if getattr(self, key):
                meta_dict[key] = getattr(self, key)
        if self.artists:
            meta_dict['artists'] = list(self.artists)
        if self.associations:
            meta_dict['associations'] = dict(self.associations)

        obj = dict(meta=meta_dict)
        for folder, fmeta in self.folders.items():
            obj[folder] = fmeta.to_dict()
        return obj

    def update(self, kv: dict, overwrite=True):
        for key, val in kv.items():
            old_value = getattr(self, key, None)
            if (overwrite and val) or (not overwrite and not old_value):
                setattr(self, key, val)
