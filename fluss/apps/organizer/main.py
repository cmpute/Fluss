from PySide6.QtGui import QAction, QBrush, QColor, QContextMenuEvent, QKeyEvent
from PySide6.QtWidgets import QAbstractItemView, QListView, QListWidget, QListWidgetItem, QMainWindow, QApplication, QFileDialog, QMenu, QMessageBox
from PySide6.QtCore import QModelIndex, Qt, Signal
from fluss.apps.organizer.main_ui import Ui_MainWindow
from fluss.apps.organizer.widgets import TargetListModel
from pathlib import Path
from itertools import islice
from networkx import DiGraph
from addict import Dict as edict

# TODO: add help (as below)
# - you can drag file from input to output by pressing alt

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()

        self._input_folder = None
        self._network = DiGraph() # explicit targets dependencies
        self._shared_states = edict(hovered=None)
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
        self.list_input_files.leaveEvent = self.listInputViewLeave
        self.list_input_files.customContextMenuRequested.connect(self.inputContextMenu)

    def listInputViewLeave(self, event):
        self._shared_states.hovered = None

    def updateHighlightOutput(self, index: QModelIndex):
        self._shared_states.hovered = self.getCurrentOutputList()._targets[index.row()]
        for i in range(self.list_input_files.count()):
            if self.list_input_files.item(i).text() in self._network.predecessors(self._shared_states.hovered):
                self.list_input_files.item(i).setBackground(QBrush(QColor(255, 200, 200, 255)))
            else:
                self.list_input_files.item(i).setBackground(QBrush())

    def listOutputViewLeave(self, event):
        self._shared_states.hovered = None
        for i in range(self.list_input_files.count()):
            self.list_input_files.item(i).setBackground(QBrush())

    def addOutputFolder(self, name: str):
        listview = QListView(self)
        listview.setObjectName("tab_" + name.lower())

        listview.setSelectionMode(QListView.ExtendedSelection)
        listview.setAcceptDrops(True)
        listview.setMouseTracking(True)
        listview.setModel(TargetListModel(listview, self._network, self._shared_states))
        listview.pressed.connect(self.updateSelectedOutput)
        listview.entered.connect(self.updateHighlightOutput)
        listview.leaveEvent = self.listOutputViewLeave

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
        self._shared_states.hovered = item.text()
        
        start = QModelIndex()
        start = self.getCurrentOutputList().createIndex(0,0)
        end = self.getCurrentOutputList().createIndex(-1,0)
        self.getCurrentOutputListView().dataChanged(start, end, [Qt.BackgroundRole])
        # print("Successor", self._network.successors(item.text()))
        # for i in range(self.tab_folders.count()):
        #     self.tab_folders.widget(i).
        # print("Hover", item.text())

    def getOutputListView(self, index: int) -> QListView:
        return self.tab_folders.widget(index)

    def getOutputList(self, index: int) -> TargetListModel:
        return self.getOutputListView(index).model()

    def getCurrentOutputListView(self) -> QListView:
        return self.tab_folders.currentWidget()

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
                self._network.add_nodes_from(files)

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
                        self._network.add_node(str(remains.relative_to(path)))

                        files = [str(p.relative_to(path)) for p in glob]
                        self.list_input_files.addItems(files)
                        self._network.add_nodes_from(files)

    def reset(self):
        self._input_folder = None
        self._shared_states = edict(hovered=None)
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
