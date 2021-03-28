
import re
import typing
from pathlib import Path
from typing import List
from warnings import warn

from fluss.codecs import codec_from_filename, codec_from_name
from fluss.config import global_config
from fluss.meta import Cuesheet, DiscMeta, TrackMeta
from networkx import DiGraph
from PySide6.QtCore import (QAbstractListModel, QAbstractTableModel, QMimeData,
                            QModelIndex, Qt)
from PySide6.QtGui import QBrush, QColor, QDropEvent, QResizeEvent
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QHeaderView,
                               QLabel, QLineEdit, QListView, QListWidget,
                               QWidget, QTableView, QProxyStyle, QStyleOption)

from .edit_convert_tracks_ui import Ui_ConvertTracksTargetDialog
from .edit_copy_target_ui import Ui_CopyTargetDialog
from .edit_transcode_target_ui import Ui_TranscodeTargetDialog
from .edit_transcode_text_target_ui import Ui_TranscodeTextTargetDialog
from .targets import (ConvertTracksTarget, CopyTarget, OrganizeTarget,
                      TranscodePictureTarget, TranscodeTextTarget,
                      TranscodeTrackTarget)

USED_COLOR = QBrush(QColor(200, 255, 200, 255))
PRED_COLOR = QBrush(QColor(255, 200, 200, 255))
SUCC_COLOR = QBrush(QColor(200, 200, 255, 255))

def _get_icon():
    from PySide6.QtCore import QSize
    from PySide6.QtGui import QIcon

    # TODO: find a way to move this to designer file
    icon = QIcon()
    icon.addFile(":/icons/main_32", QSize(32, 32))
    icon.addFile(":/icons/main_16", QSize(16, 16))
    return icon

class DirectoryEdit(QLineEdit):
    def __init__(self, parent) -> None:
        super().__init__(parent=parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, e: QDropEvent):
        data = e.mimeData()
        if data.hasUrls() and len(data.urls()) == 1:
            url = data.urls()[0]
            if url.isLocalFile() and Path(url.toLocalFile()).is_dir():
                e.accept()
            else:
                e.ignore()
        else:
            e.ignore()

    def dropEvent(self, e):
        self.setText(e.mimeData().urls()[0].toLocalFile())

class TargetListModel(QAbstractListModel):
    _targets: typing.List[OrganizeTarget]
    _network: DiGraph

    def __init__(self, parent, network, states, targets=None) -> None:
        super().__init__(parent=parent)
        self._targets = targets or []
        self._network = network
        self._states = states

    def __len__(self):
        return len(self._targets)

    def __getitem__(self, index):
        return self._targets[index]

    def __delitem__(self, index):
        if isinstance(index, int):
            self.removeRow(index, QModelIndex())
        elif isinstance(index, list):
            for row in sorted(index, reverse=True):
                self.removeRow(row, QModelIndex())
        else:
            raise ValueError("Only support deleting one element")

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._targets)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        target = self._targets[index.row()]
        if role == Qt.DisplayRole:
            prefix = '*' if target.temporary else ''
            if isinstance(target, CopyTarget):
                return prefix + target.output_name + " (copy)"
            elif isinstance(target, (TranscodeTextTarget, TranscodePictureTarget)):
                return prefix + target.output_name + " (recode)"
            elif isinstance(target, ConvertTracksTarget):
                return prefix + target.output_name + " (convert)"
            elif isinstance(target, OrganizeTarget):
                return "(dummy)"
        elif role == Qt.BackgroundRole:
            if self._states.hovered is not None:
                if target in self._network.successors(self._states.hovered):
                    return SUCC_COLOR
                elif target in self._network.predecessors(self._states.hovered):
                    return PRED_COLOR
                elif len(list(self._network.successors(target))):
                    return USED_COLOR
                else:
                    return QBrush()

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        return super().flags(index) | Qt.ItemIsDropEnabled

    def mimeTypes(self) -> typing.List:
        return super().mimeTypes()

    def dropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex) -> bool:
        if data.hasFormat(self.mimeTypes()[0]): # qlist item mime
            return super().dropMimeData(data, action, row, column, parent)
        else:
            return False

    def insertRows(self, row: int, count: int, parent: QModelIndex) -> bool:
        super().beginInsertRows(parent, row, row + count)
        self._targets[row:row] = [OrganizeTarget(None) for _ in range(count)]
        super().endInsertRows()
        return True

    def appendTarget(self, target: OrganizeTarget) -> None:
        super().beginInsertRows(QModelIndex(), len(self._targets), len(self._targets)+1)
        self._targets.append(target)
        self._network.add_node(target)
        for tin in target._input:
            self._network.add_edge(tin, target)
        super().endInsertRows()

    def extendTargets(self, targets: List[OrganizeTarget]) -> None:
        super().beginInsertRows(QModelIndex(), len(self._targets), len(self._targets) + len(targets))
        self._targets.extend(targets)
        self._network.add_nodes_from(targets)
        for target in targets:
            for tin in target._input:
                self._network.add_edge(tin, target)
        super().endInsertRows()

    def removeRows(self, row: int, count: int, parent: QModelIndex) -> bool:
        super().beginRemoveRows(parent, row, row + count)
        self._network.remove_nodes_from(self._targets[row:row+count])
        self._targets[row:row + count] = []
        # TODO: also prompt and remove successor targets
        super().endRemoveRows()
        return True

    def removeRow(self, row: int, parent: QModelIndex) -> bool:
        super().beginRemoveRows(parent, row, row + 1)
        self._network.remove_node(self._targets[row])
        del self._targets[row]
        super().endRemoveRows()
        return True

    def setData(self, index: QModelIndex, value: typing.Any, role: int) -> bool:
        if role == Qt.DisplayRole:
            if type(self._targets[index.row()]) == OrganizeTarget:
                target = CopyTarget(value)
                self._targets[index.row()] = target
                self._network.add_edge(value, target)
                return True
            else:
                warn("Should not drop on item!") # TODO: display warning on GUI
                return False
        else:
            return False

class KeywordPanel(QWidget):
    _labels: List[QLabel]

    def __init__(self, parent) -> None:
        super().__init__(parent=parent)

        self._keywords = []
        self._labels = []
        # TODO: reuse QLabel widgets
        # TODO: add scroll bar

    def extendKeywords(self, keywords: List[str]):
        for kw in keywords:
            self._keywords.append(kw)

            label = QLabel(kw, self)
            label.setAutoFillBackground(True)
            label.setFrameShape(QFrame.Panel)
            label.setFrameShadow(QFrame.Raised)
            def click(_label):
                return lambda event: QApplication.clipboard().setText(_label.text())
            label.mousePressEvent = click(label)

            label.show()
            self._labels.append(label)
        self.resizeEvent(None)

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.renderLabels()
        return super().resizeEvent(event)

    def renderLabels(self) -> None:
        colPadding = rowPadding = 2
        leftMargin = rightMargin = 5
        x = leftMargin
        y = rowPadding
        for label in self._labels:
            if x + label.width() + rightMargin > self.width():
                x = leftMargin
                y += label.height() + rowPadding
            label.move(x, y)
            x += label.width() + colPadding

        if len(self._labels) > 0:
            self.setMinimumHeight(self._labels[0].height() + rowPadding * 2)

    def clear(self):
        for label in self._labels:
            label.hide()
        self._labels.clear()
        self._keywords.clear()
        self.setMinimumHeight(0)

class TableRowMarkerStyle(QProxyStyle):
    # https://stackoverflow.com/a/61504603/5960776
    def drawPrimitive(self, element, option, painter, widget=None):
        if element == self.PE_IndicatorItemViewItemDrop and not option.rect.isNull():
            option_new = QStyleOption(option)
            option_new.rect.setLeft(0)
            if widget:
                option_new.rect.setRight(widget.width())
            option = option_new
        super().drawPrimitive(element, option, painter, widget)

class TrackTableModel(QAbstractTableModel):

    # column names
    SOURCE = 'S'
    TITLE = 'T'
    ARTISTS = 'A'
    DURATION = 'D'
    PREGAP = 'P'

    def __init__(self, meta: DiscMeta, split_input: bool, track_length: list = None, track_source: list = None):
        '''
        split_track: Split audio files or single audio file with cuesheet
        '''
        super().__init__()
        self._meta = meta
        self._split_input = split_input
        if self._split_input:
            self._columns = [self.SOURCE, self.TITLE, self.ARTISTS, self.DURATION]
            self._columns_editable = {self.TITLE, self.ARTISTS}
        else:
            self._columns = [self.TITLE, self.ARTISTS, self.DURATION, self.PREGAP]
            self._columns_editable = {self.TITLE, self.ARTISTS, self.DURATION, self.PREGAP}

        self._track_length = track_length
        self._track_source = track_source

    def data(self, index: QModelIndex, role: int):
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if index.row() == 0:
                # placeholder for editing all fields
                if role == Qt.DisplayRole:
                    return "<Edit all>" if self._columns[index.column()] in self._columns_editable else "<Immutable>"
                else:
                    return ""
            else:
                track = self._meta.tracks[index.row()-1]
                if self._columns[index.column()] == self.TITLE:
                    return track.title
                elif self._columns[index.column()] == self.ARTISTS:
                    return track.full_artist
                else:
                    return "N/A"

    def rowCount(self, index: QModelIndex):
        return len(self._meta.tracks)+1

    def columnCount(self, index: QModelIndex):
        return len(self._columns)

    def supportedDropActions(self):
        return Qt.MoveAction

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flag = super().flags(index)
        flag_drop = Qt.ItemIsDropEnabled if self._split_input else 0
        if index.isValid():
            if self._columns[index.column()] in self._columns_editable:
                flag = flag | Qt.ItemIsEditable
            if index.row() > 0:
                flag = flag | Qt.ItemIsDragEnabled | flag_drop
        else:
            flag = flag | Qt.ItemIsDropEnabled | flag_drop
        return flag

    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        if role == Qt.DisplayRole:
            if orientation == Qt.Orientation.Vertical:
                return "*" if section == 0 else str(section)
            elif orientation == Qt.Orientation.Horizontal:
                if self._columns[section] == self.TITLE:
                    return "Title"
                elif self._columns[section] == self.ARTISTS:
                    return "Artists"
                elif self._columns[section] == self.DURATION:
                    return "Duration"
                elif self._columns[section] == self.PREGAP:
                    return "Pregap"
                elif self._columns[section] == self.SOURCE:
                    return "Source"

    def setData(self, index: QModelIndex, value: str, role: int):
        def update_field(i, col, value):
            if self._columns[col] == self.TITLE:
                self._meta.tracks[i].title = value
            elif self._columns[col] == self.ARTISTS:
                self._meta.tracks[i].artists = re.split(r',\s|;\s', value)
            elif self._columns[col] == self.PREGAP:
                pass

        if role == Qt.EditRole:
            if index.row() == 0: # edit all roles
                for i in range(len(self._meta.tracks)):
                    update_field(i, index.column(), value)
            else:
                update_field(index.row()-1, index.column(), value)
            return True

        return False

    def relocateRows(self, srcRows: List[int], targetRow: int):
        # TODO: reorder tracks
        pass

    def patch(self, tableview: QTableView):
        def patchedDropEvent(event: QDropEvent):
            if event.source() is not tableview or event.dropAction() != Qt.MoveAction:
                return QTableView.dropEvent(tableview, event)

            selection = tableview.selectedIndexes()
            from_index = list({i.row() for i in selection})
            to_index = tableview.indexAt(event.pos()).row()
            tableview.model().relocateRows(from_index, to_index)
            event.accept()
            return QTableView.dropEvent(tableview, event)

        tableview.dropEvent = patchedDropEvent
        tableview.setStyle(TableRowMarkerStyle())

def editCopyTarget(self: CopyTarget, input_root: Path = None, output_root: Path = None):
    dialog = QDialog()
    dialog.setWindowIcon(_get_icon())
    layout = Ui_CopyTargetDialog()
    layout.setupUi(dialog)
    layout.retranslateUi(dialog)
    layout.txt_outname.setText(self._outname)
    if dialog.exec_():
        self._outname = layout.txt_outname.text()

def editConvertTracksTarget(self: ConvertTracksTarget, input_root: Path = None, output_root: Path = None):
    dialog = QDialog()
    dialog.setWindowIcon(_get_icon())
    layout = Ui_ConvertTracksTargetDialog()
    layout.setupUi(dialog)
    layout.retranslateUi(dialog)

    # set UI structure
    layout.tbtn_parse_tag.setVisible(len(self._tracks) > 1)
    layout.panel_parsing.setVisible(False)
    layout.tbtn_parse_tag.clicked.connect(lambda: layout.panel_parsing.setVisible(not layout.panel_parsing.isVisible()))
    layout.check_split_tracks.setChecked(self._split_tracks)

    # fill available codecs
    layout.txt_outname.setPlaceholderText(self._default_output_name())
    codecs_names = [f".{codec_from_name[v.type].suffix} ({c})" for c, v in global_config.audio_codecs.items()]
    layout.cbox_suffix.addItems(codecs_names)
    current_codec_type = global_config.audio_codecs[self._codec].type
    layout.cbox_suffix.setCurrentText(f".{codec_from_name[current_codec_type].suffix} ({self._codec})")

    # extract disc meta if first time
    if self._meta is None:
        self._meta = DiscMeta()
        if self._cue:
            if isinstance(self._cue, str):
                cs = Cuesheet.from_file(input_root / self._cue)
            else: # isinstance(self._cue, OrganizeTarget):
                assert isinstance(self._cue, (CopyTarget, TranscodeTextTarget))
                cs = Cuesheet.parse(self._cue.apply_stream(input_root).getvalue().decode('utf-8-sig'))
            self._meta.update(DiscMeta.from_cuesheet(self._cue))

        cue_from_file = False
        for i, track in enumerate(self._tracks):
            # Extract cuesheet
            if isinstance(track, str):
                cls_codec = codec_from_filename(input_root / track)
                file_tags = cls_codec.mutagen(input_root / track)
            else: # isinstance(self._cue, (CopyTarget, TranscodeTrackTarget)):
                assert isinstance(track._input, str), "Cannot parse cuesheet from complex target"
                cls_codec = codec_from_filename(input_root / track._input)
                file_tags = cls_codec.mutagen(input_root / track)

            # Extract cuesheet
            cs = Cuesheet.from_mutagen(file_tags)
            if cs:
                if cue_from_file:
                    raise ValueError("Multiple built-in cuesheet found!")
                self._meta.update(DiskMeta(from_cuesheet(cs)))
                cue_from_file = True

            # Extract other files
            new_meta = DiscMeta.from_mutagen(file_tags)
            self._meta.update(new_meta)
            if not new_meta.tracks or all(t is None for t in new_meta.tracks):
                # assume track number by input order
                self._meta._reserve_tracks(i)
                self._meta.update_track(i, TrackMeta.from_mutagen(file_tags))

    # fill table content
    layout.txt_album_artists.setText("; ".join(self._meta.artists))
    layout.txt_album_title.setText(self._meta.title)

    split_input = not (self._meta.cuesheet and len(self._tracks) == 1)
    meta_copy = DiscMeta()
    meta_copy.update(self._meta)
    table_model = TrackTableModel(meta_copy, split_input)
    table_model.patch(layout.table_tracks)
    layout.table_tracks.setModel(table_model)

    if dialog.exec_():
        self._meta = meta_copy

def editTranscodeTextTarget(self: TranscodeTextTarget, input_root: Path = None, output_root=None):
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

def editTranscodePictureTarget(self: TranscodePictureTarget, input_root: Path = None, output_root: Path = None):
    dialog = QDialog()
    dialog.setWindowIcon(_get_icon())
    layout = Ui_TranscodeTargetDialog()
    layout.setupUi(dialog)
    layout.retranslateUi(dialog)
    layout.txt_outname.setText(self._outstem)

    codecs_names = [f".{v.type} ({c})" for c, v in global_config.image_codecs.items()]
    layout.cbox_suffix.addItems(codecs_names)
    layout.cbox_suffix.setCurrentText(f".{global_config.image_codecs[self._codec].type }({self._codec})")
    if dialog.exec_():
        suffix, codec = parse(".{} ({})", layout.cbox_suffix.currentText())
        self._outstem = layout.txt_outname.text()
        if self._outstem.endswith(suffix):
            self._outstem = self._outstem[:-len(suffix)-1]
        self._codec = codec

def editTarget(target: OrganizeTarget, input_root: Path = None, output_root: Path = None):
    if isinstance(target, ConvertTracksTarget):
        editConvertTracksTarget(target, input_root, output_root)
    elif isinstance(target, CopyTarget):
        editCopyTarget(target, input_root, output_root)
    elif isinstance(target, TranscodePictureTarget):
        editTranscodePictureTarget(target, input_root, output_root)
    elif isinstance(target, TranscodeTextTarget):
        editTranscodeTextTarget(target, input_root, output_root)
    else:
        raise ValueError("Invalid target type for editing!")
