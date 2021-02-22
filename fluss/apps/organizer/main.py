from PySide6.QtGui import QAction, QContextMenuEvent, QKeyEvent
from PySide6.QtWidgets import QAbstractItemView, QListView, QListWidget, QListWidgetItem, QMainWindow, QApplication, QFileDialog, QMenu, QMessageBox
from PySide6.QtCore import QModelIndex, Qt
from fluss.apps.organizer.main_ui import Ui_MainWindow
from fluss.apps.organizer.widgets import TargetListModel
from pathlib import Path
from itertools import islice
from networkx import DiGraph

# TODO: add help (as below)
# - you can drag file from input to output by pressing alt

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()

        self._input_folder = None
        self._network = DiGraph() # explicit targets dependencies
        self._hovered_target = None
        self._enable_cross_selection = False

        self.setupUi(self)
        self.retranslateUi(self)
        self.setupSignals()
        self.addOutputFolder("CD")

        # TODO: For debug
        self.txt_input_path.setText(r"D:\Github\fluss\codecs")

    def setupSignals(self):
        self.btn_input_browse.clicked.connect(self.browseInput)
        self.btn_output_browse.clicked.connect(self.browseOutput)
        self.btn_close.clicked.connect(self.safeClose)
        self.btn_add_folder.clicked.connect(lambda: self.addOutputFolder(self.txt_folder_name.currentText()))
        self.btn_del_folder.clicked.connect(self.removeOutputFolder)
        self.btn_reset.clicked.connect(self.reset)
        self.txt_input_path.textChanged.connect(self.inputChanged)
        self.list_input_files.itemDoubleClicked.connect(self.previewInput)
        self.list_input_files.itemPressed.connect(self.updateSelectedInput)
        self.list_input_files.itemEntered.connect(self.updateHighlightInput)
        self.list_input_files.customContextMenuRequested.connect(self.inputContextMenu)

    def addOutputFolder(self, name: str):
        listview = QListView(self)
        listview.setObjectName("tab_" + name.lower())

        listview.setSelectionMode(QListView.ExtendedSelection)
        listview.setAcceptDrops(True)
        listview.setModel(TargetListModel(parent=listview, network=self._network))
        listview.pressed.connect(self.updateSelectedOutput)

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
        if not self._enable_cross_selection:
            for i in range(self.tab_folders.count()):
                self.tab_folders.widget(i).clearSelection()

    def updateHighlightInput(self, item: QListWidgetItem):
        print("Hover", item.text())

    def getOutputListView(self, index: int) -> QListView:
        return self.tab_folders.widget(index)

    def getOutputList(self, index: int) -> TargetListModel:
        return self.getOutputListView(index).model()

    def getCurrentOutputListView(self) -> QListView:
        return self.getOutputListView(self.tab_folders.currentIndex())

    def getCurrentOutputList(self) -> TargetListModel:
        return self.getCurrentOutputListView().model()

    def updateSelectedOutput(self, index: QModelIndex):
        if not self._enable_cross_selection:
            self.list_input_files.clearSelection()
            for i in range(self.tab_folders.count()):
                if i != self.tab_folders.currentIndex():
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
        preview_action.triggered.connect(lambda: self.previewInput(self.list_input_files.currentItem()))
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
                    remains = next(glob)
                except StopIteration:
                    remains = False

                if remains:
                    msgbox = QMessageBox(self)
                    msgbox.setIcon(QMessageBox.Warning)
                    msgbox.setText("There are too many files in the directory.")
                    msgbox.setInformativeText("Do you still want to list them?")
                    msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                    msgbox.setDefaultButton(QMessageBox.No)

                    if msgbox.exec_() == QMessageBox.Yes:
                        self.list_input_files.addItem(str(remains.relative_to(path)))
                        files = [str(p.relative_to(path)) for p in glob]
                        self.list_input_files.addItems(files)

    def reset(self):
        self._input_folder = None
        self._hovered_target = None
        self._network.clear()
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
