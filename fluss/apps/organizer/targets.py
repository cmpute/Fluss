import asyncio
from pathlib import Path, PurePath
from typing import Callable, List, Union
from io import BytesIO
from shutil import copy2 as copy
from PIL import Image
import traceback

from PySide6.QtWidgets import QMessageBox
from fluss import codecs

from fluss.config import global_config
from fluss.codecs import codec_from_filename, codec_from_name
from fluss.meta import DiscMeta
from fluss.utils import merge_tracks, convert_track
from fluss.accurip import verify_accurip, parse_accurip

# readable suffixes supported by pillow
PILLOW_SUFFIXES = ['png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tif']
_image_suffix_from_format = {
    "jpeg": "jpg",
    "png": "png",
    "bmp": "bmp",
    "tiff": "tiff"
}
AUDIO_SUFFIXES = set(c.suffix for c in codec_from_name.values())

class OrganizeTarget:
    description = "Target"

    def __init__(self, input_files: List[Union[str, "OrganizeTarget"]]) -> None:
        if not isinstance(input_files, list):
            self._input = [input_files]
        else:
            self._input = input_files
        self.temporary = False

    def switch_temporary(self, value: bool = None) -> None:
        if value is None:
            self.temporary = not self.temporary
        else:
            self.temporary = value

    @classmethod
    def validate(self, input_files: List[Union[str, "OrganizeTarget"]]) -> bool:
        return False

    @property
    def initialized(self):
        return True

    @property
    def output_name(self) -> str:
        ''' output file name'''
        raise NotImplementedError("Abstract property!")

    async def apply_stream(self, input_root: Path = None, output_root: Path = None) -> BytesIO:
        ''' execute target to BytesIO
        Should return the generated binary data
        '''
        raise NotImplementedError("Abstract property!")

    async def apply(self, input_root: Path, output_root: Path) -> None:
        ''' execute target
        input_root is used when input is str
        output_root is used when this target is not marked as temporary
        Should return the path to result file
        '''
        data = await self.apply_stream(input_root, output_root)
        Path(output_root, self.output_name).write_bytes(data.getvalue())


def _split_name(target: Union[str, OrganizeTarget]):
    if isinstance(target, str):
        name = PurePath(target).name
    elif isinstance(target, OrganizeTarget):
        name = target.output_name
    else:
        raise ValueError("Incorrect target type!")

    split = name.rsplit(".", 1)
    if len(split) == 1:
        return split[0], ""
    else:
        return split[0], split[1].lower()  # return lower case suffix by default

class CopyTarget(OrganizeTarget):    
    description = "Copy"

    def __init__(self, input_files):
        super().__init__(input_files)
        assert len(self._input) == 1, "CopyTarget only accept one input!"

        stem, suffix = _split_name(self._input[0])
        self._outname = stem + '.' + suffix if suffix else stem

    @classmethod
    def validate(self, input_files):
        return len(input_files) == 1 # only support one files

    @property
    def output_name(self):
        return self._outname

    def __str__(self):
        return "Copying %s" % self.output_name

    def __repr__(self):
        return "<CopyTarget output=%s>" % self.output_name

    async def apply(self, input_root, output_root):
        def task(): # prevent copying large file from blocking main thread
            copy(Path(input_root, self._input[0]), Path(output_root, self._outname))
        await asyncio.get_running_loop().run_in_executor(None, task)

    async def apply_stream(self, input_root, output_root):
        return BytesIO(Path(input_root, self._input[0]).read_bytes())

class TranscodeTrackTarget(OrganizeTarget):
    ''' Support recoding single audio files '''
    description = "Transcode Tracks"

    def __init__(self, input_files, codec=global_config.organizer.output_codec.audio):
        super().__init__(input_files)

        if codec in global_config.audio_codecs:
            self._codec = codec
        else:
            self._codec = global_config.organizer.output_codec.audio

        if isinstance(self._input[0], str):
            self._outstem = PurePath(self._input[0]).stem
        elif isinstance(self._input[0], OrganizeTarget):
            self._outstem = self._input[0].output_name.rsplit('.', 1)[0]
        else:
            raise ValueError("Incorrect input type!")

    @classmethod
    def validate(cls, input_files):
        if len(input_files) != 1:
            return False
        suffix = _split_name(input_files[0])[1].lower()
        if suffix not in AUDIO_SUFFIXES:
            return False
        return True

    @property
    def output_name(self):
        fname = self._outstem
        codec_cls = codec_from_name[global_config.audio_codecs[self._codec].type.lower()]
        return fname + "." + codec_cls.suffix

    def __str__(self):
        return "Converting track into %s" % self.output_name

    def __repr__(self):
        return "<TranscodeTrackTarget output=%s>" % self.output_name

    async def apply(self, input_root, output_root, progress_callback: Callable[[float], None] = None):
        await convert_track(
            Path(input_root, self._input[0]),
            Path(output_root, self.output_name),
            codec_out=self._codec,
            progress_callback=progress_callback
        )


class MergeTracksTarget(OrganizeTarget):
    ''' Support recoding, merging, embedding cue and embedding cover
    only allow 1 cover, 1 cue, n audio files
    '''
    description = "Merge Tracks"
    _meta: DiscMeta

    def __init__(self, input_files, codec=global_config.organizer.output_codec.audio):
        super().__init__(input_files)

        self._outstem = "" # empty means using default name
        if codec in global_config.audio_codecs:
            self._codec = codec
        else:
            self._codec = global_config.organizer.output_codec.audio

        self._tracks, self._cue, self._cover, unknown_files = MergeTracksTarget._sort_files(input_files)
        if len(unknown_files) > 0:
            raise ValueError("Not all input files are accepted.")

        # sort tracks lexically
        self._tracks.sort(key=MergeTracksTarget._track_key)

        self._meta = None

    @staticmethod
    def _track_key(track):
        name = track if isinstance(track, str) else track.output_name
        nums = []
        for i, c in enumerate(name):
            if c.isspace():
                continue
            if c.isdigit():
                nums.append(c)
            else:
                break

        # cover prefix number (up to 256) to character for sorting
        lexical_name = chr(int(''.join(nums)) % 0xff) + name[i:] if nums else name
        return lexical_name

    @staticmethod
    def _sort_files(input_files):
        cue_file = None
        cover_file = None
        audio_files = []
        unknown_files = []

        for fin in input_files:
            suffix = _split_name(fin)[1].lower()
            if not suffix:
                unknown_files.append(fin)
            elif suffix in AUDIO_SUFFIXES:
                audio_files.append(fin)
            elif suffix == 'cue':
                if cue_file is None:
                    cue_file = fin
                else:
                    unknown_files.append(fin)
            elif suffix in PILLOW_SUFFIXES:
                if cover_file is None:
                    cover_file = fin
                else:
                    unknown_files.append(fin)
            else:
                unknown_files.append(fin)

        return audio_files, cue_file, cover_file, unknown_files

    @property
    def initialized(self):
        return self._meta is not None

    @classmethod
    def validate(cls, input_files):
        track_files, _, _, unknown_files = MergeTracksTarget._sort_files(input_files)
        return len(unknown_files) == 0 and len(track_files) > 0

    def _default_output_name(self):
        if self._meta and self._meta.partnumber:
            return self._meta.partnumber
        if len(self._tracks) == 1:
            return "CDImage"
        else:
            return "Merged"

    @property
    def output_name(self):
        fname = self._outstem or self._default_output_name()
        codec_cls = codec_from_name[global_config.audio_codecs[self._codec].type.lower()]
        return fname + "." + codec_cls.suffix

    def __str__(self):
        if len(self._tracks) == 1:
            return "Converting CD image into %s" % self.output_name
        else:
            return "Merging tracks into %s" % self.output_name

    def __repr__(self):
        return "<MergeTracksTarget output=%s>" % self.output_name

    async def apply(self, input_root, output_root, progress_callback: Callable[[float], None] = None):
        if self._cover:
            if isinstance(self._cover, str):
                cover_path = Path(input_root, self._cover)
            elif isinstance(self._cover, OrganizeTarget):
                cover_path = Path(output_root, self._cover.output_name)
            else:
                raise ValueError("Unrecognized cover input!")
            self._meta.cover = cover_path.read_bytes()

        if len(self._tracks) == 1:
            await convert_track(
                Path(input_root, self._tracks[0]),
                Path(output_root, self.output_name),
                meta=self._meta,
                codec_out=self._codec,
                progress_callback=progress_callback
            )
        else:
            await merge_tracks(
                [Path(input_root, f) for f in self._tracks],
                Path(output_root, self.output_name),
                meta=self._meta,
                codec_out=self._codec,
                progress_callback=progress_callback
            )

    async def apply_stream(self, input_root, output_root):
        # could apply and then read
        raise NotImplementedError()

class TranscodeTextTarget(OrganizeTarget):
    ''' Support text encoding fixing '''
    description = "Transcode Text"
    valid_encodings = ['utf-8-sig', 'gbk', 'big5', 'shift_jis', 'utf-16-le', 'utf-16-be', 'big5hkscs', 'euc_jp']
    valid_file_types = ['txt', 'log', 'cue']

    def __init__(self, input_files, encoding="utf-8-sig"):
        super().__init__(input_files)
        if encoding in self.valid_encodings:
            self._encoding = encoding
        else:
            self._encoding = "utf-8-sig"
        assert len(self._input) == 1, "CopyTarget only accept one input!"

        stem, suffix = _split_name(self._input[0])
        self._outname = stem + '.' + suffix if suffix else stem

    @classmethod
    def validate(cls, input_files):
        if len(input_files) != 1:
            return False
        suffix = _split_name(input_files[0])[1].lower()
        if suffix not in cls.valid_file_types:
            return False
        return True

    @property
    def output_name(self):
        return self._outname

    async def apply_stream(self, input_root, output_root):
        content = Path(input_root, self._input[0]).read_text(encoding=self._encoding, errors="replace")
        return BytesIO(content.encode('utf-8-sig'))

    def __str__(self):
        return "Transcoding text to %s" % self.output_name

    def __repr__(self):
        return "<TranscodeTextTarget output=%s>" % self.output_name

class TranscodePictureTarget(OrganizeTarget):
    ''' Support transcoding '''
    description = "Transcode Image"

    def __init__(self, input_files, codec=global_config.organizer.output_codec.image):
        super().__init__(input_files)
        if codec in global_config.image_codecs:
            self._codec = codec
        else:
            self._codec = global_config.organizer.output_codec.image
        assert len(self._input) == 1, "CopyTarget only accept one input!"

        if isinstance(self._input[0], str):
            self._outstem = PurePath(self._input[0]).stem
        elif isinstance(self._input[0], OrganizeTarget):
            self._outstem = self._input[0].output_name.rsplit('.', 1)[0]
        else:
            raise ValueError("Incorrect input type!")

    @property
    def output_name(self):
        suffix = _image_suffix_from_format[global_config.image_codecs[self._codec].type]
        return self._outstem + "." + suffix

    @classmethod
    def validate(cls, input_files):
        if len(input_files) != 1:
            return False
        suffix = _split_name(input_files[0])[1].lower()
        if suffix not in PILLOW_SUFFIXES:
            return False
        return True

    def convert_if_necessary(self, im, target_fmt):
        # remove transparency if necessary
        assert target_fmt
        if im.mode in {"RGBA", "P"} and target_fmt == "jpeg":
            return im.convert("RGB")
        else:
            return im

    def __str__(self):
        return "Transcoding picture to %s" % self.output_name

    def __repr__(self):
        return "<TranscodePictureTarget output=%s>" % self.output_name

    async def apply_stream(self, input_root, output_root):
        im = Image.open(Path(input_root, self._input[0]))

        buf = BytesIO()
        codec = dict(global_config.image_codecs[self._codec])
        format = codec.pop('type')

        im = self.convert_if_necessary(im, format)
        im.save(buf, format=format, **codec)
        buf.seek(0)
        return buf

class CropPictureTarget(TranscodePictureTarget):
    ''' Support cover cropping '''
    description = "Crop Image"

    def __init__(self, input_files, codec="jpg"):
        super().__init__(input_files, codec)
        self._outstem = "cover" # default name is cover
        self._centerx = None
        self._centery = None
        self._scale = None
        self._rotation = None # degrees, clockwise
        self._output_size = 800 # in pixel

    @property
    def initialized(self):
        return self._scale is not None


    async def apply_stream(self, input_root, output_root):
        buf = BytesIO()
        def task():
            im = Image.open(Path(input_root, self._input[0]))
            im = im.rotate(-self._rotation, center=(self._centerx, self._centery), fillcolor=(255,255,255), resample=Image.BICUBIC)
            scaled_size = self._output_size / self._scale
            im = im.transform((int(scaled_size), int(scaled_size)), Image.EXTENT, [
                self._centerx - scaled_size/2, self._centery - scaled_size/2,
                self._centerx + scaled_size/2, self._centery + scaled_size/2], fillcolor=(255,255,255), resample=Image.BICUBIC)
            im = im.resize((self._output_size, self._output_size), resample=Image.BICUBIC)

            codec = dict(global_config.image_codecs[self._codec])
            format = codec.pop('type')

            im = self.convert_if_necessary(im, format)
            im.save(buf, format=format, **codec)
            buf.seek(0)

        await asyncio.get_running_loop().run_in_executor(None, task)
        return buf

    def __str__(self):
        return "Croping picture to %s" % self.output_name

    def __repr__(self):
        return "<CropPictureTarget output=%s>" % self.output_name

class VerifyAccurateRipTarget(OrganizeTarget):
    ''' Support cover cropping '''
    description = "Verify with AccurateRip"

    def __init__(self, input_files: List[Union[str, OrganizeTarget]]) -> None:
        super().__init__(input_files)
        assert len(self._input) == 1, "CopyTarget only accept one input!"

        if isinstance(self._input[0], str):
            self._outstem = PurePath(self._input[0]).stem
        elif isinstance(self._input[0], OrganizeTarget):
            self._outstem = self._input[0].output_name.rsplit('.', 1)[0]
        else:
            raise ValueError("Incorrect input type!")

    @classmethod
    def validate(cls, input_files):
        if len(input_files) != 1:
            return False
        suffix = _split_name(input_files[0])[1].lower()
        if suffix not in AUDIO_SUFFIXES:
            return False
        return True

    @property
    def output_name(self):
        return self._outstem + ".accurip"

    def __str__(self):
        return "Verity with AccurateRip, log to %s" % self.output_name

    def __repr__(self):
        return "<VerifyAccurateRipTarget output=%s>" % self.output_name

    async def apply_stream(self, input_root, output_root):
        if isinstance(self._input[0], OrganizeTarget):
            cdfile = Path(output_root, self._input[0].output_name)
        else:
            cdfile = Path(input_root, self._input[0])
        results = await verify_accurip(cdfile)

        parsed = parse_accurip(results)
        if parsed.fail:
            msgbox = QMessageBox()
            msgbox.setWindowTitle("Verify failed")
            msgbox.setIcon(QMessageBox.Critical)
            msgbox.setText("AccurateRip verification failed! Please check the output file " + str(Path(output_root, self.output_name)))
            msgbox.exec_()

        return BytesIO(results)

target_types = [
    CopyTarget,
    CropPictureTarget,
    MergeTracksTarget,
    TranscodeTrackTarget,
    TranscodeTextTarget,
    TranscodePictureTarget,
    VerifyAccurateRipTarget
]
