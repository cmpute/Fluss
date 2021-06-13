
import math
import re
import typing
from pathlib import Path
from typing import List, Union

from addict import Dict as edict
from fluss.codecs import codec_from_filename, codec_from_name
from fluss.config import global_config
from fluss.meta import Cuesheet, DiscMeta, TrackMeta
from networkx import DiGraph
from networkx.algorithms.distance_measures import center
from parse import parse
from PySide6.QtCore import (QAbstractListModel, QAbstractTableModel,
                            QItemSelection, QItemSelectionModel, QMimeData,
                            QModelIndex, QRect, Qt, Signal)
from PySide6.QtGui import (QBrush, QColor, QDropEvent, QImage, QKeyEvent,
                           QMouseEvent, QPen, QPixmap, QResizeEvent,
                           QWheelEvent)
from PySide6.QtWidgets import (QApplication, QDialog, QFrame,
                               QGraphicsLineItem, QGraphicsPixmapItem,
                               QGraphicsRectItem, QGraphicsScene,
                               QGraphicsView, QLabel, QLineEdit, QProxyStyle,
                               QStyleOption, QTableView, QWidget)

from .targets import (CopyTarget, CropPictureTarget, MergeTracksTarget,
                      OrganizeTarget, TranscodePictureTarget,
                      TranscodeTextTarget, TranscodeTrackTarget)

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
            elif isinstance(target, CropPictureTarget):
                return prefix + target.output_name + " (crop)"
            elif isinstance(target, (TranscodeTextTarget, TranscodePictureTarget, TranscodeTrackTarget)):
                return prefix + target.output_name + " (recode)"
            elif isinstance(target, MergeTracksTarget):
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
                print("WARNING: Should not drop target on list item!") # TODO: display warning on GUI
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
            if not kw.strip(): # skip empty string
                continue
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
        nrows = 1
        for label in self._labels:
            if x + label.width() + rightMargin > self.width():
                x = leftMargin
                y += label.height() + rowPadding
                nrows += 1
            label.move(x, y)
            x += label.width() + colPadding

        if len(self._labels) > 0:
            self.setMinimumHeight(self._labels[0].height() * nrows + rowPadding * 2)

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

    def __init__(self, parent: QTableView, meta: DiscMeta, track_source: List[Union[str, OrganizeTarget]], track_length: List[float] = None):
        '''
        '''
        super().__init__(parent)
        self._view = parent
        self._meta = meta
        self._columns = [self.TITLE, self.ARTISTS, self.DURATION]
        self._columns_editable = {self.TITLE, self.ARTISTS}
        if len(track_source) > 1:
            self._columns = [self.SOURCE] + self._columns
        if meta.cuesheet:
            self._columns.append([self.PREGAP])
            self._columns_editable.add(self.DURATION)
            self._columns_editable.add(self.PREGAP)

        # logging order change
        self._track_order = list(range(len(track_length) if track_length else len(self._meta.tracks)))
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
                i = index.row()-1
                if self._columns[index.column()] == self.TITLE:
                    return self._meta.tracks[i].title
                elif self._columns[index.column()] == self.ARTISTS:
                    return self._meta.tracks[i].full_artist
                elif self._columns[index.column()] == self.SOURCE:
                    actual_idx = self._track_order[i]
                    if isinstance(self._track_source[actual_idx], str):
                        return self._track_source[actual_idx]
                    else:
                        return self._track_source[actual_idx].output_name
                elif self._columns[index.column()] == self.DURATION:
                    actual_idx = self._track_order[i]
                    if self._meta.cuesheet:
                        # TODO: implement, need to align cuesheet file name with input name
                        return "N/A"
                    else:
                        l = self._track_length[actual_idx]
                    s, ss = int(l), l-int(l)
                    fss = ("%.3f" % ss)[1:]
                    return f"{s//60}:{s%60:02}{fss} ({round(ss*75):02})"
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
        flag_drop = Qt.ItemIsDropEnabled if not self._meta.cuesheet else 0
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
                self._meta.tracks[i].artists = set(re.split(r',\s|;\s', value))
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
        print(srcRows, targetRow)
        srcRows = [i-1 for i in srcRows]

        src_indices = []
        src_tracks = []
        for i in srcRows:
            src_indices.append(self._track_order[i])
            src_tracks.append(self._meta.tracks[i])
            self._track_order[i] = None
            self._meta.tracks[i] = None
        if targetRow == -2:
            new_indices = self._track_order + src_indices
            new_tracks  = self._meta.tracks + src_tracks
        elif targetRow < 1:
            new_indices = src_indices + self._track_order
            new_tracks  = src_tracks + self._meta.tracks
        else:
            new_indices = self._track_order[:targetRow] + src_indices + self._track_order[targetRow:]
            new_tracks  = self._meta.tracks[:targetRow] + src_tracks  + self._meta.tracks[targetRow:]
        self._track_order = [v for v in new_indices if v is not None]
        self._meta.tracks = [v for v in new_tracks if v is not None]

        # self._view.setCurrentIndex()
        topleft = self.index(self._track_order.index(src_indices[0])+1, 0)
        bottomright = self.index(self._track_order.index(src_indices[-1])+1, len(self._columns)-1)
        selection = QItemSelection(topleft, bottomright)
        self._view.selectionModel().select(selection, QItemSelectionModel.ClearAndSelect)

    def dropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex) -> bool:
        if data.hasFormat(self.mimeTypes()[0]): # qlist item mime
            selection = self._view.selectedIndexes()
            from_index = list({i.row() for i in selection})
            if parent.isValid():
                to_index = parent.row()
            else:
                to_index = row - 1
            self.relocateRows(from_index, to_index)
            return True
        else:
            return False
        return super().dropMimeData(data, action, row, column, parent)

class CropImageView(QGraphicsView):
    xOffsetChanged = Signal(float)
    yOffsetChanged = Signal(float)
    scaleChanged = Signal(float)
    rotationChanged = Signal(float)
    speedChanged = Signal(int)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(scene=QGraphicsScene(), parent=parent)
        self._box_pad_scale = 0.95 # ratio of margin between displayed crop box and widget frame
        self._box_actual_dim = 800 # px, actual output size of cropped image
        self._click_type = None
        self._click_origin = None
        self._offset_origin = None
        self._speed_origin = None
        self._line_len = 20 # length of crop box center cross
        self._modifier_state = None

    def setup(self, image: Path, **initial_config: dict) -> None:
        self._image = QImage(str(image))
        self.resetConfig()
        if initial_config:
            for k, v in initial_config.items():
                if v is not None:
                    self._config[k] = v

        self._image_item = QGraphicsPixmapItem(QPixmap.fromImage(self._image))
        pen = QPen(QColor(200, 100, 0, 128))
        pen.setWidth(0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self._crop_box_item = QGraphicsRectItem(
            -self._box_actual_dim / 2, -self._box_actual_dim / 2,
            self._box_actual_dim, self._box_actual_dim
        )
        self._crop_box_item.setPen(pen)
        self._crop_box_hline = QGraphicsLineItem(-self._line_len / 2-1, 0, self._line_len / 2, 0)
        self._crop_box_hline.setPen(pen)
        self._crop_box_vline = QGraphicsLineItem(0, -self._line_len / 2-1, 0, self._line_len / 2)
        self._crop_box_vline.setPen(pen)

        self.scene().addItem(self._image_item)
        self.scene().addItem(self._crop_box_item)
        self.scene().addItem(self._crop_box_hline)
        self.scene().addItem(self._crop_box_vline)

    def resetConfig(self) -> None:
        key_dim = min(self._image.width(), self._image.height())
        default_s = self._box_actual_dim / key_dim
        self._config = edict(
            xoffset = -key_dim / 2,
            yoffset = -key_dim / 2,
            scale = default_s,
            rotation = 0,
            speed = 0 # power index
        )
        self.xOffsetChanged.emit(self._config.xoffset)
        self.yOffsetChanged.emit(self._config.yoffset)
        self.scaleChanged.emit(self._config.scale)
        self.rotationChanged.emit(self._config.rotation)
        self.speedChanged.emit(self._config.speed)

    def updateConfig(self, **configs) -> None:
        # this function won't trigger signals, for internal use
        for k, v in configs.items():
            if v is not None:
                self._config[k] = v
        self.refreshSceneLayout()

    def refreshSceneLayout(self) -> None:
        r = self.size().width() / self.size().height()
        box_actual_dim = self._box_actual_dim / self._box_pad_scale

        if r > 1:
            viewport = QRect(
                -r * box_actual_dim / 2,
                -box_actual_dim / 2,
                r * box_actual_dim, box_actual_dim
            )
        else:
            viewport = QRect(
                -box_actual_dim / 2,
                -box_actual_dim / r / 2,
                box_actual_dim, box_actual_dim / r
            )
        self.setSceneRect(viewport)
        self.fitInView(viewport)

        self._image_item.setPos(self._config.xoffset, self._config.yoffset)
        self._image_item.setTransformOriginPoint(-self._config.xoffset, -self._config.yoffset)
        self._image_item.setScale(self._config.scale)
        self._image_item.setRotation(self._config.rotation)

    def speedRatio(self):
        return 1.2 ** self._config.speed

    def applyOffset(self, xpixels, ypixels, origin=None):
        scale = min(self.width(), self.height()) / (self._box_actual_dim / self._box_pad_scale) * self._config.scale
        dx = xpixels / scale * self.speedRatio()
        dy = ypixels / scale * self.speedRatio()
        r = math.radians(self._config.rotation)
        if origin is None:
            self._config.xoffset +=  dx*math.cos(r) + dy*math.sin(r)
            self._config.yoffset += -dx*math.sin(r) + dy*math.cos(r)
        else:
            self._config.xoffset = origin[0] + dx*math.cos(r) + dy*math.sin(r)
            self._config.yoffset = origin[1] - dx*math.sin(r) + dy*math.cos(r)

        self.xOffsetChanged.emit(self._config.xoffset)
        self.yOffsetChanged.emit(self._config.yoffset)
        self.refreshSceneLayout()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        super().keyPressEvent(event)

        if event.key() == Qt.Key_Alt:
            self._modifier_state = "alt"
        elif event.key() == Qt.Key_Shift:
            self._modifier_state = "shift"
        elif event.key() == Qt.Key_Control:
            self._modifier_state = "ctrl"
        elif event.key() == Qt.Key_R:
            self.resetConfig()
        elif event.key() == Qt.Key_Q:
            self._speed_origin = self._config.speed
            self._config.speed = max(self._config.speed - 2, -10)
            self.speedChanged.emit(self._config.speed)
        elif event.key() == Qt.Key_E:
            self._speed_origin = self._config.speed
            self._config.speed = min(self._config.speed + 2, 10)
            self.speedChanged.emit(self._config.speed)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        super().keyReleaseEvent(event)

        if event.key() == Qt.Key_Alt and self._modifier_state == "alt":
            self._modifier_state = None
        elif event.key() == Qt.Key_Shift and self._modifier_state == "shift":
            self._modifier_state = None
        elif event.key() == Qt.Key_Control and self._modifier_state == "ctrl":
            self._modifier_state = None
        elif event.key() in [Qt.Key_Q, Qt.Key_E]:
            self._config.speed = self._speed_origin
            self.speedChanged.emit(self._config.speed)

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.refreshSceneLayout()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._click_type is None:
            self._click_origin = (event.x(), event.y())
            self._offset_origin = (self._config.xoffset, self._config.yoffset)
            self._angle_start = self._config.rotation
        self._click_type = event.button()
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._click_type == Qt.LeftButton:
            self.applyOffset(event.x() - self._click_origin[0], event.y() - self._click_origin[1], self._offset_origin)
        elif self._click_type == Qt.RightButton:
            astart = math.atan2(self._click_origin[1] - self.height() / 2, self._click_origin[0] - self.width() / 2)
            aend = math.atan2(event.y() - self.height() / 2, event.x() - self.width() / 2)
            self._config.rotation = (self._angle_start + math.degrees(aend - astart)  * self.speedRatio()) % 360
            self.rotationChanged.emit(self._config.rotation)
            self.refreshSceneLayout()
        
        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._click_type = None

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self._modifier_state is None:
            delta = event.angleDelta().y()
            delta = delta if delta < 100 else 10 # larger or smaller than 100 is usually mouse scroll
            delta = delta if delta > -100 else -10
            delta *= self.speedRatio()
            self._config.scale *= 1.01 ** delta
            self.scaleChanged.emit(self._config.scale)
        elif self._modifier_state == "alt": # TODO: implement 2D translate support from touch pad events
            # by default delta value is at y direction. when pressing alt it will be x direction.
            self.applyOffset(event.angleDelta().x(), 0)
        elif self._modifier_state == "shift":
            self.applyOffset(0, event.angleDelta().y())
        elif self._modifier_state == "ctrl":
            self._config.rotation += event.angleDelta().y() * self.speedRatio()
            self.rotationChanged.emit(self._config.rotation)
        self.refreshSceneLayout()

from .edit_copy_target_ui import Ui_CopyTargetDialog
from .edit_crop_picture_ui import Ui_CropPictureDialog
# delay import to prevent cyclic reference
from .edit_merge_tracks_ui import Ui_MergeTracksTargetDialog
from .edit_transcode_target_ui import Ui_TranscodeTargetDialog
from .edit_transcode_text_target_ui import Ui_TranscodeTextTargetDialog


def editCopyTarget(self: CopyTarget, input_root: Path = None, output_root: Path = None):
    dialog = QDialog()
    dialog.setWindowIcon(_get_icon())
    layout = Ui_CopyTargetDialog()
    layout.setupUi(dialog)
    layout.retranslateUi(dialog)
    layout.txt_outname.setText(self._outname)
    if dialog.exec_():
        self._outname = layout.txt_outname.text()

def editMergeTracksTarget(self: MergeTracksTarget, input_root: Path = None, output_root: Path = None):
    dialog = QDialog()
    dialog.setWindowIcon(_get_icon())
    layout = Ui_MergeTracksTargetDialog()
    layout.setupUi(dialog)
    layout.retranslateUi(dialog)

    # set UI structure, TODO: implement extracting tag from file name
    layout.panel_parsing.setVisible(False)
    layout.tbtn_parse_tag.clicked.connect(lambda: layout.panel_parsing.setVisible(not layout.panel_parsing.isVisible()))

    # fill available codecs
    layout.txt_outname.setPlaceholderText(self._default_output_name())
    layout.txt_outname.setText(self._outstem)
    codecs_names = [f".{codec_from_name[v.type].suffix} ({c})" for c, v in global_config.audio_codecs.items()]
    layout.cbox_suffix.addItems(codecs_names)
    current_codec_type = global_config.audio_codecs[self._codec].type
    layout.cbox_suffix.setCurrentText(f".{codec_from_name[current_codec_type].suffix} ({self._codec})")

    # util for extract tag
    def tag_from_source(source):
        if isinstance(source, str):
            cls_codec = codec_from_filename(input_root / source)
            return cls_codec.mutagen(input_root / source)
        else: # isinstance(self._cue, (CopyTarget, TranscodeTrackTarget)):
            assert isinstance(source._input, str), "Cannot parse tags from complex target"
            cls_codec = codec_from_filename(input_root / source._input)
            return cls_codec.mutagen(input_root / source)

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
            file_tags = tag_from_source(track)
            cs = Cuesheet.from_mutagen(file_tags)
            if cs:
                if cue_from_file:
                    raise ValueError("Multiple built-in cuesheet found!")
                self._meta.update(DiscMeta.from_cuesheet(cs))
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
    layout.txt_partnumber.setText(self._meta.partnumber)
    layout.tbtn_parse_tag.setVisible(self._meta.cuesheet is None)

    # set up model
    meta_copy = DiscMeta()
    meta_copy.update(self._meta)
    track_lengths = [tag_from_source(track).info.length for track in self._tracks]
    table_model = TrackTableModel(layout.table_tracks, meta_copy, self._tracks, track_lengths)
    layout.table_tracks.setModel(table_model)
    layout.table_tracks.setStyle(TableRowMarkerStyle())
    layout.table_tracks.resizeColumnsToContents()

    if dialog.exec_():
        self._meta = meta_copy
        self._meta.title = layout.txt_album_title.text()
        self._meta.artists = set(re.split(r",\s+|;\s+", layout.txt_album_artists.text()))
        self._meta.partnumber = layout.txt_partnumber.text()
        self._outstem = layout.txt_outname.text()

        # update codec selection
        suffix, codec = parse(".{} ({})", layout.cbox_suffix.currentText())
        self._outstem = layout.txt_outname.text()
        if self._outstem.endswith(suffix):
            self._outstem = self._outstem[:-len(suffix)-1]
        self._codec = codec

        # update track order
        tracks_new = [self._tracks[i] for i in table_model._track_order]
        self._tracks = tracks_new

def editTranscodeTextTarget(self: TranscodeTextTarget, input_root: Path = None, output_root: Path = None):
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

def editTranscodeTrackTarget(self: TranscodeTrackTarget, input_root: Path = None, output_root: Path = None):
    dialog = QDialog()
    dialog.setWindowIcon(_get_icon())
    layout = Ui_TranscodeTargetDialog()
    layout.setupUi(dialog)
    layout.retranslateUi(dialog)
    layout.txt_outname.setText(self._outstem)

    codecs_names = [f".{v.type} ({c})" for c, v in global_config.audio_codecs.items()]
    layout.cbox_suffix.addItems(codecs_names)
    layout.cbox_suffix.setCurrentText(f".{global_config.audio_codecs[self._codec].type }({self._codec})")
    if dialog.exec_():
        suffix, codec = parse(".{} ({})", layout.cbox_suffix.currentText())
        self._outstem = layout.txt_outname.text()
        if self._outstem.endswith(suffix):
            self._outstem = self._outstem[:-len(suffix)-1]
        self._codec = codec

def editCropPictureTarget(self: CropPictureTarget, input_root: Path = None, output_root: Path = None):
    dialog = QDialog()
    dialog.setWindowIcon(_get_icon())
    layout = Ui_CropPictureDialog()
    layout.setupUi(dialog)
    layout.retranslateUi(dialog)
    layout.txt_outname.setText(self._outstem)

    # set up image widget
    layout.image_box.setFocus()
    layout.image_box.xOffsetChanged.connect(lambda xoffset: layout.sbox_centerx.setValue(xoffset))
    layout.image_box.yOffsetChanged.connect(lambda yoffset: layout.sbox_centery.setValue(yoffset))
    layout.image_box.scaleChanged.connect(lambda scale: layout.sbox_scale.setValue(scale))
    layout.image_box.rotationChanged.connect(lambda rotation: layout.sbox_rotation.setValue(rotation))
    layout.image_box.speedChanged.connect(lambda speed: layout.dial_speed.setValue(speed))
    layout.image_box.setup(input_root / self._input[0],
        xoffset = self._centerx, yoffset = self._centery,
        rotation = self._rotation, scale = self._scale)

    if self._centerx is not None: layout.sbox_centerx.setValue(self._centerx)
    if self._centery is not None: layout.sbox_centery.setValue(self._centery)
    if self._scale is not None: layout.sbox_scale.setValue(self._scale)
    if self._rotation is not None: layout.sbox_rotation.setValue(self._rotation)
    layout.sbox_centerx.valueChanged.connect(lambda value: layout.image_box.updateConfig(xoffset=value))
    layout.sbox_centery.valueChanged.connect(lambda value: layout.image_box.updateConfig(yoffset=value))
    layout.sbox_scale.valueChanged.connect(lambda value: layout.image_box.updateConfig(scale=value))
    layout.sbox_rotation.valueChanged.connect(lambda value: layout.image_box.updateConfig(rotation=value))
    layout.dial_speed.valueChanged.connect(lambda value: layout.image_box.updateConfig(speed=value))

    codecs_names = [f".{v.type} ({c})" for c, v in global_config.image_codecs.items()]
    layout.cbox_suffix.addItems(codecs_names)
    layout.cbox_suffix.setCurrentText(f".{global_config.image_codecs[self._codec].type }({self._codec})")
    if dialog.exec_():
        suffix, codec = parse(".{} ({})", layout.cbox_suffix.currentText())
        self._outstem = layout.txt_outname.text()
        if self._outstem.endswith(suffix):
            self._outstem = self._outstem[:-len(suffix)-1]
        self._codec = codec
        self._centerx = layout.image_box._config.xoffset
        self._centery = layout.image_box._config.yoffset
        self._scale = layout.image_box._config.scale
        self._rotation = layout.image_box._config.rotation

def editTarget(target: OrganizeTarget, input_root: Path = None, output_root: Path = None):
    if isinstance(target, MergeTracksTarget):
        editMergeTracksTarget(target, input_root, output_root)
    elif isinstance(target, CropPictureTarget):
        editCropPictureTarget(target, input_root, output_root)
    elif isinstance(target, CopyTarget):
        editCopyTarget(target, input_root, output_root)
    elif isinstance(target, TranscodePictureTarget):
        editTranscodePictureTarget(target, input_root, output_root)
    elif isinstance(target, TranscodeTextTarget):
        editTranscodeTextTarget(target, input_root, output_root)
    elif isinstance(target, TranscodeTrackTarget):
        editTranscodeTrackTarget(target, input_root, output_root)
    else:
        raise ValueError("Invalid target type for editing!")
