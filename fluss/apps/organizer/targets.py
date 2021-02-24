from pathlib import Path, PurePath
from typing import List, Union

from PySide6.QtWidgets import QDialog

from .edit_copy_target_ui import Ui_CopyTargetDialog
from .edit_transcode_text_target_ui import Ui_TranscodeTextTargetDialog
from .edit_transcode_picture_target_ui import Ui_TranscodePictureTargetDialog


def _get_icon():
    from PySide6.QtCore import QSize
    from PySide6.QtGui import QIcon

    # TODO: find a way to move this to designer file
    icon = QIcon()
    icon.addFile(":/icons/main_32", QSize(32, 32))
    icon.addFile(":/icons/main_16", QSize(16, 16))
    return icon

class OrganizeTarget:
    description = "Target"

    def __init__(self, input_files: List[Union[str, "OrganizeTarget"]]):
        if not isinstance(input_files, list):
            self._input = [input_files]
        else:
            self._input = input_files

    @classmethod
    def validate(self, input_files: List[Union[str, "OrganizeTarget"]]):
        return False

    @property
    def output_name(self):
        raise NotImplementedError("Abstract property!")

    def edit(self, input_root: Path = None, output_root: Path = None):
        # open edit dialog
        raise NotImplementedError("Abstract property!")

class CopyTarget(OrganizeTarget):    
    description = "Copy"

    def __init__(self, input_files):
        super().__init__(input_files)
        assert len(self._input) == 1, "CopyTarget only accept one input!"

        if isinstance(self._input[0], str):
            self._outname = PurePath(self._input[0]).name
        elif isinstance(self._input[0], OrganizeTarget):
            self._outname = self._input[0].output_name
        else:
            raise ValueError("Incorrect input type!")

    @classmethod
    def validate(self, input_files):
        return len(input_files) == 1 # only support one files

    @property
    def output_name(self):
        return self._outname

    def edit(self, input_root=None, output_root=None):
        dialog = QDialog()
        dialog.setWindowIcon(_get_icon())
        layout = Ui_CopyTargetDialog()
        layout.setupUi(dialog)
        layout.retranslateUi(dialog)
        layout.txt_outname.setText(self._outname)
        if dialog.exec_():
            self._outname = layout.txt_outname.text()

class TranscodeTracksTarget(OrganizeTarget):
    ''' Support recoding, merging, embedding cue and embedding cover '''
    description = "Transcode Tracks"

class TranscodeTextTarget(OrganizeTarget):
    ''' Support text encoding fixing '''
    description = "Transcode Text"
    valid_encodings = ['utf-8', 'utf-8-sig', 'gb2312', 'big5', 'gbk', 'shift_jis']
    valid_file_types = ['txt', 'log', 'cue']

    def __init__(self, input_files, encoding="utf-8"):
        super().__init__(input_files)
        if encoding in self.valid_encodings:
            self._encoding = encoding
        else:
            self._encoding = "utf-8"
        assert len(self._input) == 1, "CopyTarget only accept one input!"

        if isinstance(self._input[0], str):
            self._outname = PurePath(self._input[0]).name
        elif isinstance(self._input[0], OrganizeTarget):
            self._outname = self._input[0].output_name
        else:
            raise ValueError("Incorrect input type!")

    @classmethod
    def validate(cls, input_files):
        if len(input_files) != 1:
            return False
        if isinstance(input_files[0], str):
            suffix = input_files[0].rsplit(".", 1)[1]
        else: # OrganizeTarget
            suffix = input_files[0].output_name.rsplit(".", 1)[1]
        if suffix not in cls.valid_file_types:
            return False
        return True

    @property
    def output_name(self):
        return self._outname

    def edit(self, input_root: Path = None, output_root=None):
        assert isinstance(self._input[0], str), "Only support reading from file by now!"

        dialog = QDialog()
        dialog.setWindowIcon(_get_icon())
        layout = Ui_TranscodeTextTargetDialog()
        layout.setupUi(dialog)
        layout.retranslateUi(dialog)
        layout.txt_outname.setText(self._outname)
        content = Path(input_root, self._input[0]).read_bytes()
        layout.txt_content.setPlainText(content.decode(encoding=self._encoding, errors="replace"))

        layout.cbox_encoding.addItems(self.valid_encodings)
        layout.cbox_encoding.setCurrentText(self._encoding)
        layout.cbox_encoding.currentTextChanged.connect(lambda text: layout.txt_content.setPlainText(content.decode(encoding=text, errors="replace")))
        if dialog.exec_():
            self._outname = layout.txt_outname.text()
            self._encoding = layout.cbox_encoding.currentText()

class TranscodePictureTarget(OrganizeTarget):
    ''' Support transcoding '''
    description = "Transcode Image"
    valid_input_codecs = ['jpg', 'png', 'tif', 'bmp']
    valid_output_codecs = ['jpg', 'png']

    def __init__(self, input_files, codec=".png"):
        super().__init__(input_files)
        if codec in self.valid_output_codecs:
            self._codec = codec
        else:
            self._codec = "png"
        assert len(self._input) == 1, "CopyTarget only accept one input!"

        if isinstance(self._input[0], str):
            self._outstem = PurePath(self._input[0]).stem
        elif isinstance(self._input[0], OrganizeTarget):
            self._outstem = self._input[0].output_name.rsplit('.', 1)[0]
        else:
            raise ValueError("Incorrect input type!")
        self._quality = .8 # compression rate

    @property
    def output_name(self):
        return self._outstem + "." + self._codec

    @classmethod
    def validate(cls, input_files):
        if len(input_files) != 1:
            return False
        if isinstance(input_files[0], str):
            suffix = input_files[0].rsplit(".", 1)[1]
        else: # OrganizeTarget
            suffix = input_files[0].output_name.rsplit(".", 1)[1]
        if suffix not in cls.valid_input_codecs:
            return False
        return True

    def edit(self, input_root: Path = None, output_root=None):
        dialog = QDialog()
        dialog.setWindowIcon(_get_icon())
        layout = Ui_TranscodePictureTargetDialog()
        layout.setupUi(dialog)
        layout.retranslateUi(dialog)
        layout.txt_outname.setText(self._outstem)
        layout.cbox_suffix.addItems(['.' + ext for ext in self.valid_output_codecs])
        layout.cbox_suffix.setCurrentText('.' + self._codec)
        layout.slider_quality.setValue(int(self._quality * 100))
        if dialog.exec_():
            suffix = layout.cbox_suffix.currentText()
            self._outstem = layout.txt_outname.text()
            if self._outstem.endswith(suffix):
                self._outstem = self._outstem[:-len(suffix)]
            self._codec = suffix[1:]
            self._quality = layout.slider_quality.value() / 100

class CropPictureTarget:
    ''' Support cover cropping '''
    description = "Crop Image"
    pass

target_types = [
    CopyTarget,
    TranscodeTracksTarget,
    TranscodeTextTarget,
    TranscodePictureTarget
]
