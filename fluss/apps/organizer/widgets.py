
import typing
from pathlib import Path
from typing import List

from networkx import DiGraph
from PySide6.QtCore import QAbstractListModel, QMimeData, QModelIndex, Qt
from PySide6.QtGui import QBrush, QColor, QDropEvent, QResizeEvent
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QLineEdit,
                               QListView, QListWidget, QWidget)

from .targets import (CopyTarget, ConvertTracksTarget, OrganizeTarget, TranscodePictureTarget,
                      TranscodeTextTarget, TranscodeTracksTarget)

USED_COLOR = QBrush(QColor(200, 255, 200, 255))
PRED_COLOR = QBrush(QColor(255, 200, 200, 255))
SUCC_COLOR = QBrush(QColor(200, 200, 255, 255))

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
        # TODO: add grey background to files marked as intermediate
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
                raise RuntimeError("Unexpected setData() call")
        else:
            return False

class KeywordPanel(QWidget):
    _labels: List[QLabel]

    def __init__(self, parent) -> None:
        super().__init__(parent=parent)

        self._keywords = []
        self._labels = []
        # TODO: reuse labels
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
