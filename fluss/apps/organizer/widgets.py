
from PySide6.QtGui import QDropEvent, QStandardItemModel
from PySide6.QtWidgets import QAbstractItemView, QLineEdit, QListWidget
from PySide6.QtCore import Qt, QModelIndex
from pathlib import Path

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

class FolderOutputList(QListWidget):
    # TODO: change from QListWidget to QListView
    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setAcceptDrops(True)        

    def dragEnterEvent(self, e: QDropEvent):
        items = QStandardItemModel()
        if items.canDropMimeData(e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex()):
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        items = QStandardItemModel()
        items.dropMimeData(e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())
        source_files = [items.item(i, 0).text() for i in range(items.rowCount())]
        # TODO: add corresponding items
        print(source_files)
