from typing import List
from mutagen.flac import FLAC
from mutagen.apev2 import APEv2File
from mutagen.id3 import ID3


class TrackMeta:
    title: str = None
    artist: str = None
    track_idx: int = None
    total_tracks: int = None
    
    def update(meta: "TrackMeta"):
        pass

class AlbumMeta:
    title: str = None
    artist: List[str] = None
    disc_idx: int = 1
    total_discs: int = None
    tracks: List[TrackMeta] = None

    def from_flac(flac_meta: FLAC):
        '''
        Update metadata from FLAC file
        '''
        pass

    def from_ape(ape_meta: APEv2File):
        '''
        Update metadata from media with APEv2 tags
        '''
        pass

    def from_id3(id3_meta: ID3):
        '''
        Update metadata from media with ID3v2 tags
        '''
        pass

    def update(meta: "AlbumMeta"):
        pass

    def to_flac(flac_meta: FLAC):
        raise NotImplementedError("Convert metadata to FLAC is not implemented!")

    def to_id3(id3_meta: ID3):
        raise NotImplementedError("Convert metadata to FLAC is not implemented!")
