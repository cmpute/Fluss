
from PySide6.QtGui import QDropEvent, QStandardItemModel
from PySide6.QtWidgets import QAbstractItemView, QLineEdit, QListWidget, QListView
from PySide6.QtCore import QAbstractListModel, QDataStream, QIODevice, QMimeData, QStringListModel, Qt, QModelIndex
from pathlib import Path
from fluss.apps.organizer.targets import OrganizeTarget, CopyTarget, TranscodePictureTarget, TranscodeTextTarget, TranscodeTracksTarget
import typing
from networkx import DiGraph

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

    def __init__(self, parent=None, targets=None, network=None) -> None:
        super().__init__(parent=parent)
        self._targets = targets or []
        self._network = network

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._targets)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if role == Qt.DisplayRole:
            target = self._targets[index.row()]
            if isinstance(target, CopyTarget):
                return target.output_name + " (copy)"
            if isinstance(target, (TranscodeTextTarget, TranscodePictureTarget)):
                return target.output_name + " (convert)"
        # elif role == Qt.BackgroundColorRole:
        #     return Qt.darkBlue

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
        self._targets[row:row] = [CopyTarget([""]) for _ in range(count)]
        super().endInsertRows()
        return True

    def setData(self, index: QModelIndex, value: typing.Any, role: int) -> bool:
        target = self._targets[index.row()]
        if target._input[0]:
            self._network.remove_edge(target._input[0], target)
        target._input = [value]
        self._network.add_edge(value, target)
        return True

    def itemData(self, index: QModelIndex) -> typing.Dict:
        print("ITEM_DATA")
        return super().itemData(index)
