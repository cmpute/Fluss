import re, os
from os.path import commonprefix
from itertools import islice
from pathlib import Path
from typing import List

from addict import Dict as edict
from fluss.config import global_config
from fluss.meta import AlbumMeta, FolderMeta
from networkx import DiGraph, topological_sort
from PySide6.QtCore import QModelIndex, QPoint, QSize, Qt, QUrl, Signal
from PySide6.QtGui import (QAction, QBrush, QColor, QContextMenuEvent,
                           QDesktopServices, QIcon, QKeyEvent)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFileDialog,
                               QFrame, QLabel, QListView, QListWidget,
                               QListWidgetItem, QMainWindow, QMenu,
                               QMessageBox)

from . import main_rc
from .main_ui import Ui_MainWindow
from .targets import target_types, MergeTracksTarget, OrganizeTarget
from .widgets import _get_icon, TargetListModel, PRED_COLOR, USED_COLOR, editTarget

# TODO: add help (as below)
# - you can drag file from input to output by pressing alt

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()

        self._input_folder = None
        self._network = DiGraph() # explicit targets dependencies
        self._shared_states = edict(hovered=None)
        self._enable_cross_selection = False
        self._meta = None
        self._last_tab_index = None

        self.setupUi(self)
        self.retranslateUi(self)
        self.setupSignals()

        # load resources
        self.setWindowIcon(_get_icon())
        for format in global_config.output_format:
            self.cbox_output_type.addItem(format)

        # TODO: For debug
        self.txt_input_path.setText(r"C:\Users\cmput\Music\Sennzai - Tødestrieb")

    def setupSignals(self):
        self.btn_input_browse.clicked.connect(self.browseInput)
        self.btn_output_browse.clicked.connect(self.browseOutput)
        self.btn_close.clicked.connect(self.safeClose)
        self.btn_add_folder.clicked.connect(lambda: self.addOutputFolder(self.txt_folder_name.currentText()))
        self.btn_del_folder.clicked.connect(self.removeOutputFolder)
        self.btn_reset.clicked.connect(lambda: self.txt_input_path.clear() or self.reset())
        self.btn_apply.clicked.connect(self.executeTargets)
        self.txt_input_path.textChanged.connect(self.inputChanged)
        self.list_input_files.itemDoubleClicked.connect(self.previewInput)
        self.list_input_files.itemPressed.connect(self.updateSelectedInput)
        self.list_input_files.itemEntered.connect(self.updateHighlightInput)
        self.list_input_files.leaveEvent = self.listInputViewLeave
        self.list_input_files.customContextMenuRequested.connect(self.inputContextMenu)
        self.panel_folder_meta.setVisible(False)
        self.btn_expand_meta.clicked.connect(lambda: (
            self.panel_folder_meta.setVisible(not self.panel_folder_meta.isVisible()),
            self.btn_expand_meta.setText("Fold Meta" if self.panel_folder_meta.isVisible() else "Expand Meta")
        ))
        self.tab_folders.currentChanged.connect(self.updateSelectedFolder)

    def listInputViewLeave(self, event):
        self._shared_states.hovered = None

    def refreshOutputBgcolor(self):
        start = self.currentOutputList.createIndex(0,0)
        end = self.currentOutputList.createIndex(-1,0)
        self.currentOutputListView.dataChanged(start, end, [Qt.BackgroundRole])

    def refreshInputBgcolor(self):
        for i in range(self.list_input_files.count()):
            item = self.list_input_files.item(i)
            if self._shared_states.hovered is not None and \
               item.text() in self._network.predecessors(self._shared_states.hovered):
                item.setBackground(PRED_COLOR)
            elif len(list(self._network.successors(item.text()))):
                item.setBackground(USED_COLOR)
            else:
                item.setBackground(QBrush())

    def updateHighlightOutput(self, index: QModelIndex):
        self._shared_states.hovered = self.currentOutputList[index.row()]
        self.refreshInputBgcolor()
        self.refreshOutputBgcolor()

    def updateSelectedFolder(self, index: int):
        if self.tab_folders.count() == 0: # happens when reset
            return

        if self._last_tab_index is not None:
            self.flushFolderMeta(self._last_tab_index)
            # TODO: save and load placeholder text for partnumber
        self._last_tab_index = index

        current_meta = self._meta.folders[self.tab_folders.tabText(index)]
        self.txt_catalog.setText(current_meta.catalog)
        self.txt_partnumber.setText(current_meta.partnumber)
        self.txt_edition.setText(current_meta.edition)
        self.txt_tool.setText(current_meta.tool)
        self.txt_source.setText(current_meta.source)
        self.txt_ripper.setText(current_meta.ripper)
        self.txt_comment.setPlainText(current_meta.comment)

    def flushFolderMeta(self, index: int):
        target_meta = self._meta.folders[self.tab_folders.tabText(index)]
        target_meta.catalog = self.txt_catalog.text()
        target_meta.partnumber = self.txt_partnumber.text()
        target_meta.edition = self.txt_edition.text()
        target_meta.tool = self.txt_tool.text()
        target_meta.source = self.txt_source.text()
        target_meta.ripper = self.txt_ripper.text()
        target_meta.comment = self.txt_comment.toPlainText()

    def listOutputViewLeave(self, event):
        self._shared_states.hovered = None
        self.refreshInputBgcolor()

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
        listview.setContextMenuPolicy(Qt.CustomContextMenu)
        listview.customContextMenuRequested.connect(lambda pos: self.outputContextMenu(listview, pos))

        self._meta.folders[name] = FolderMeta()
        self.tab_folders.addTab(listview, name.upper())

        self.updateFolderNames()

    def removeOutputFolder(self):
        self._meta.folders.pop(self.tab_folders.tabText(self.tab_folders.currentIndex()))
        self.tab_folders.removeTab(self.tab_folders.currentIndex())
        self.updateFolderNames()

    def updateFolderNames(self):
        # update valid folder names
        valid_folders = set(['CD', 'BK', 'DVD', 'DL', 'OL', 'MISC', 'PHOTO', 'LRC'])
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
        self.refreshOutputBgcolor()

    @property
    def currentOutputListView(self) -> QListView:
        return self.tab_folders.currentWidget()

    @property
    def currentOutputList(self) -> TargetListModel:
        return self.currentOutputListView.model()

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
        check = False
        for i in range(self.tab_folders.count()):
            if len(self.tab_folders.widget(i).model()) > 0:
                check = True
                break

        if not check:
            self.close()
            return

        msgbox = QMessageBox(self)
        msgbox.setWindowTitle("Close")
        msgbox.setIcon(QMessageBox.Warning)
        msgbox.setText("Do you really want to close?")
        msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgbox.setDefaultButton(QMessageBox.No)

        if msgbox.exec_() == QMessageBox.Yes:
            self.close()

    def previewInput(self, item: QListWidgetItem):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._input_folder / item.text())))

    def addTargetActions(self, menu: QMenu):
        selected_items = [i.text() for i in self.list_input_files.selectedItems()]
        selected_items += [self.currentOutputList[i.row()] for i in self.currentOutputListView.selectedIndexes()]

        menu.addSeparator()
        # cannot use default arg to force coping the type here, since the signal also provides other inputs
        func_create = lambda _t, items: lambda: self.currentOutputList.appendTarget(_t(items))
        for t in target_types:
            if t.validate(selected_items):
                create_action = QAction(t.description, menu)
                create_action.triggered.connect(func_create(t, selected_items))
                menu.addAction(create_action)

        menu.addSeparator()
        func_create_batch = lambda _t, items: lambda: self.currentOutputList.extendTargets([_t(i) for i in items])
        for t in target_types:
            if all(t.validate([item]) for item in selected_items):
                create_action = QAction("Batch " + t.description, menu)
                create_action.triggered.connect(func_create_batch(t, selected_items))
                menu.addAction(create_action)

    def inputContextMenu(self, pos: QPoint):
        menu = QMenu()
        preview_action = QAction("Preview", menu)
        preview_action.triggered.connect(lambda: self.previewInput(self.list_input_files.currentItem()))
        menu.addAction(preview_action)

        self.addTargetActions(menu)
        action = menu.exec_(self.list_input_files.mapToGlobal(pos))

    def fillMetaFromFolder(self):
        partnumbers = []
        for target in self.currentOutputList._targets:
            if isinstance(target, MergeTracksTarget):
                if target._meta.title:
                    self.txt_title.setPlaceholderText(target._meta.title)
                if target._meta.full_artist:
                    self.txt_artists.setPlaceholderText(target._meta.full_artist)
                if target._meta.cuesheet:
                    if target._meta.cuesheet.rems.get('COMMENT', ''):
                        comment = target._meta.cuesheet.rems['COMMENT']
                        if 'Exact Audio Copy' in comment:
                            self.txt_tool.setPlaceholderText(comment)
                        else:
                            self.txt_comment.setPlaceholderText(comment)
                    if target._meta.cuesheet.rems.get('DATE', ''):
                        self.txt_date.setText(target._meta.cuesheet.rems['DATE'])
                if target._meta.partnumber:
                    partnumbers.append(target._meta.partnumber)

        # combine part numbers
        if len(partnumbers) > 1:
            try:
                prefix = commonprefix(partnumbers)
                remain = [pn[len(prefix):] for pn in partnumbers]
                remain_num = [int(i) for i in remain]
                rmin, rmax = min(remain_num), max(remain_num)
                if rmax - rmin + 1 == len(remain):
                    rlen = len(remain[0])
                    self.txt_partnumber.setPlaceholderText(prefix + str(rmin).zfill(rlen) + '~' + str(rmax).zfill(rlen))
            except ValueError: # non trivial part numbers
                pass
        elif len(partnumbers) == 1:
            self.txt_partnumber.setPlaceholderText(partnumbers[0])

    def outputContextMenu(self, listview: QListView, pos: QPoint):
        current_model = listview.model()
        menu = QMenu()
        edit_action = QAction("Edit clicked" if len(listview.selectedIndexes()) > 1 else "Edit", menu)
        edit_action.triggered.connect(lambda: editTarget(
            current_model[listview.currentIndex().row()],
            input_root=self._input_folder,
            output_root=Path(self.txt_output_path.text(), self.tab_folders.tabText(self.tab_folders.currentIndex()))
        ) or self.fillMetaFromFolder())
        menu.addAction(edit_action)
        delete_action = QAction("Remove", menu)
        delete_action.triggered.connect(lambda: current_model.__delitem__(
            [i.row() for i in listview.selectedIndexes()]
        ))
        menu.addAction(delete_action)
        mark_temp_action = QAction("Mark temp", menu)
        mark_temp_action.setCheckable(True)
        mark_temp_action.setChecked(current_model[listview.currentIndex().row()].temporary)
        mark_temp_action.triggered.connect(lambda: [current_model[i.row()].switch_temporary()
            for i in listview.selectedIndexes()])
        menu.addAction(mark_temp_action)

        self.addTargetActions(menu)
        menu.exec_(listview.mapToGlobal(pos))

    def inputChanged(self, content):
        path = Path(content)

        if not (content and path.exists()):
            return
        if self._input_folder == path:
            return

        self.reset()

        # read file list
        self._input_folder = path
        glob = (p for p in path.rglob("*") if p.is_file())
        files = [str(p.relative_to(path)) for p in islice(glob, 50)]
        self.list_input_files.addItems(files)
        self._network.add_nodes_from(files)

        # read more files
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

            if msgbox.exec_() != QMessageBox.Yes:
                self.reset()
                return

            self.list_input_files.addItem(str(remains.relative_to(path)))
            self._network.add_node(str(remains.relative_to(path)))

            files = [str(p.relative_to(path)) for p in glob]
            self.list_input_files.addItems(files)
            self._network.add_nodes_from(files)

        # generate keywords
        keywords = set()
        keypattern = re.compile(r';| - |\[|\]|\(|\)')
        keywords.update(keypattern.split(path.name))
        if len(os.listdir(path)) == 0:
            subf = next(path.iterdir())
            if subf.is_dir():
                keywords.update(keypattern.split(subf.name))
        # TODO: extract metadata from input audio files
        self.widget_keywords.extendKeywords(keywords)

        # default output path
        self.txt_output_path.setText(str(path.parent / "organized" / path.name))

    def reset(self):
        '''
        Reset all information except for input/output path and folder list
        '''
        # clear text
        self.list_input_files.clear()
        self.widget_keywords.clear()
        self.tab_folders.clear()

        # clear placeholder text
        self.txt_title.setPlaceholderText(None)
        self.txt_artists.setPlaceholderText(None)
        self.txt_partnumber.setPlaceholderText(None)
        self.txt_date.setPlaceholderText(None)
        self.txt_comment.setPlaceholderText(None)

        self._input_folder = None
        self._shared_states.hovered = None
        self._network.clear()
        self._meta = AlbumMeta()
        self._last_tab_index = None

        self.addOutputFolder("CD")

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

    def executeTargets(self):
        order: List[OrganizeTarget]
        order = topological_sort(self._network)

        # get output folder
        folder_map = {}
        for i in range(self.tab_folders.count()):
            folder = self.tab_folders.tabText(i)
            for target in self.tab_folders.widget(i).model():
                folder_map[target] = folder

        output_root=Path(self.txt_output_path.text())
        output_root.mkdir(exist_ok=True, parents=True)
        files_to_remove = []
        for target in order:
            if isinstance(target, str):
                continue

            output_folder_root = output_root / folder_map[target]
            output_folder_root.mkdir(exist_ok=True)
            self.statusbar.showMessage("Executing " + str(target))
            target.apply(self._input_folder, output_folder_root)

            if target.temporary:
                files_to_remove.append(output_folder_root / target.output_name)

        for f in files_to_remove:
            f.unlink()
        self.statusbar.showMessage("Organizing done successfully!")

def entry():
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec_()

if __name__ == "__main__":
    exit(entry())
