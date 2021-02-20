from PySide6.QtGui import QAction, QContextMenuEvent, QKeyEvent
from PySide6.QtWidgets import QAbstractItemView, QListWidget, QListWidgetItem, QMainWindow, QApplication, QFileDialog, QMenu
from PySide6.QtCore import Qt
from fluss.apps.organizer.main_ui import Ui_MainWindow
from fluss.apps.organizer.widgets import FolderOutputList
from pathlib import Path
from itertools import islice

# TODO: add help (as below)
# - you can drag file from input to output by pressing alt

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self._input_folder = None

        self.setupUi(self)
        self.retranslateUi(self)
        self.setupSignals()
        self.createOutputFolder("CD")

        self._last_selected_input = None
        self._enable_cross_selection = False

    def setupSignals(self):
        self.btn_input_browse.clicked.connect(self.browseInput)
        self.btn_output_browse.clicked.connect(self.browseOutput)
        self.btn_close.clicked.connect(self.safeClose)
        self.btn_add_folder.clicked.connect(lambda: self.createOutputFolder(self.txt_folder_name.currentText()))
        self.btn_del_folder.clicked.connect(self.removeOutputFolder)
        self.txt_input_path.textChanged.connect(self.inputChanged)
        self.list_input_files.itemDoubleClicked.connect(self.previewInput)
        self.list_input_files.itemPressed.connect(self.updateSelectedInput)
        self.list_input_files.customContextMenuRequested.connect(self.inputContextMenu)

    def createOutputFolder(self, name: str):
        listview = FolderOutputList()
        listview.setObjectName("tab_" + name.lower())
        self.tab_folders.addTab(listview, name.upper())
        self.updateFolderNames()

    def removeOutputFolder(self):
        self.tab_folders.removeTab(self.tab_folders.currentIndex())
        self.updateFolderNames()

    def updateFolderNames(self):
        # update valid folder names
        valid_folders = set(['CD', 'BK', 'DVD', 'DL', 'OL', 'MISC', 'PHOTO'])
        current_folders = set([self.tab_folders.tabText(i) for i in range(self.tab_folders.count())])
        valid_folders = list(valid_folders.difference(current_folders))
        self.txt_folder_name.clear()
        self.txt_folder_name.addItems(valid_folders)

        # update availability of delete button
        self.btn_del_folder.setEnabled(self.tab_folders.count() > 0)

    def updateSelectedInput(self, item: QListWidgetItem):
        self._last_selected_input = item

        if not self._enable_cross_selection:
            for i in range(self.tab_folders.count()):
                self.tab_folders.widget(i).clearSelection()

    def browseInput(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.Directory)
            
        if dlg.exec_():
            self.txt_input_path.setText(dlg.selectedFiles()[0])

    def browseOutput(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.Directory)
            
        if dlg.exec_():
            self.txt_output_path.setText(dlg.selectedFiles()[0])

    def safeClose(self):
        # TODO: prompt confirmation
        self.close()

    def previewInput(self, item: QListWidgetItem):
        # TODO: preview items
        print("Preview", item.text())

    def inputContextMenu(self, pos):
        menu = QMenu()
        preview_action = QAction("Preview", self.list_input_files)
        preview_action.triggered.connect(lambda: self.previewInput(self._last_selected_input))
        menu.addAction(preview_action)
        # TODO: add actions for preview, add output etc.
        action = menu.exec_(self.list_input_files.mapToGlobal(pos))

    def inputChanged(self, content):
        path = Path(content).resolve()
        
        if content and path.exists():
            if self._input_folder != path:
                self._input_folder = path
                self.list_input_files.clear()
                glob = (p for p in path.rglob("*") if p.is_file())
                files = [str(p.relative_to(path)) for p in islice(glob, 50)]
                self.list_input_files.addItems(files)

                remains = True
                try:
                    next(glob)
                except StopIteration:
                    remains = False
                # TODO: Prompt continuing when input directory is too large
                if remains:
                    print("Too many files, skip loading...")
        else:
            self._input_folder = None
            self.list_input_files.clear()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        super().keyPressEvent(event)

        if event.key() == Qt.Key_Alt:
            self.list_input_files.setDragEnabled(True)
        elif event.key() in [Qt.Key_Shift, Qt.Key_Control]:
            self._enable_cross_selection = True

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        super().keyReleaseEvent(event)

        if event.key() == Qt.Key_Alt:
            self.list_input_files.setDragEnabled(False)
        elif event.key() in [Qt.Key_Shift, Qt.Key_Control]:
            self._enable_cross_selection = False

def entry():
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    entry()
