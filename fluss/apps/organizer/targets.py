from typing import List, Union
from pathlib import PurePath, Path

from fluss.apps.organizer.edit_copy_target_ui import Ui_CopyTargetDialog
from fluss.apps.organizer.edit_transcode_text_target_ui import Ui_TranscodeTextTargetDialog
from PySide6.QtWidgets import QDialog
import chardet

class OrganizeTarget:
    description = "Target"

    def __init__(self, input_files: List[Union[str, "OrganizeTarget"]]):
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
        assert len(input_files) == 1, "CopyTarget only accept one input!"

        if isinstance(input_files[0], str):
            self._outname = PurePath(input_files[0]).name
        elif isinstance(input_files[0], OrganizeTarget):
            self._outname = input_files[0].output_name
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

    def __init__(self, input_files, encoding="utf-8"):
        super().__init__(input_files)
        self._encoding = encoding
        assert len(self._input) == 1, "CopyTarget only accept one input!"

        if isinstance(input_files[0], str):
            self._outname = PurePath(input_files[0]).name
        elif isinstance(input_files[0], OrganizeTarget):
            self._outname = input_files[0].output_name
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
        if suffix not in ['txt', 'log', 'cue']:
            return False
        return True

    @property
    def output_name(self):
        return self._outname

    def edit(self, input_root: Path = None, output_root=None):
        assert isinstance(self._input[0], str), "Only support reading from file by now!"

        dialog = QDialog()
        layout = Ui_TranscodeTextTargetDialog()
        layout.setupUi(dialog)
        layout.retranslateUi(dialog)
        layout.txt_outname.setText(self._outname)
        layout.txt_content.setPlainText((input_root / self._input[0]).read_text(encoding=self._encoding))
        if dialog.exec_():
            self._outname = layout.txt_outname.text()

class TranscodePictureTarget(OrganizeTarget):
    ''' Support transcoding '''
    pass

class CropPictureTarget:
    ''' Support cover cropping '''
    pass

target_types = [
    CopyTarget,
    TranscodeTracksTarget,
    TranscodeTextTarget,
    TranscodePictureTarget
]
