import asyncio
import logging
import os
import re
import sys
from collections import defaultdict
from itertools import islice
from os.path import commonprefix
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from addict import Dict as edict
from dateutil.parser import parse as date_parse
from fluss.config import global_config
from fluss.meta import AlbumMeta, FolderMeta
from networkx import DiGraph, topological_sort
from PySide6.QtCore import QModelIndex, QPoint, Qt, QUrl
from PySide6.QtGui import QAction, QBrush, QDesktopServices, QKeyEvent
from PySide6.QtWidgets import (QApplication, QFileDialog, QListView,
                               QListWidgetItem, QMainWindow, QMenu,
                               QMessageBox)
from qasync import QEventLoop, asyncSlot

from . import main_rc
from .main_ui import Ui_MainWindow
from .targets import MergeTracksTarget, OrganizeTarget, target_types
from .widgets import (PRED_COLOR, USED_COLOR, TargetListModel, _get_icon,
                      editTarget)

_logger = logging.getLogger("fluss.organizer")

# TODO: add help (as below)
# - you can drag file from input to output by pressing alt

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, initial_dir: str = None):
        super().__init__()

        self._input_folder = None
        self._network = DiGraph() # explicit targets dependencies
        self._shared_states = edict(hovered=None)
        self._enable_cross_selection = False
        self._meta = None
        self._placeholders = defaultdict(edict) # save placeholder text for folder-specific fields
        self._last_tab_index = None
        self._executing = False
        self._task = None
        self._status_owner = None

        self.setupUi(self)
        self.retranslateUi(self)
        self.setupSignals()

        # load resources
        self.setWindowIcon(_get_icon())
        for format in global_config.organizer.output_format:
            self.cbox_output_type.addItem(format)
        self.cbox_output_type.setCurrentIndex(0)

        if initial_dir:
            self.txt_input_path.setText(initial_dir)
        if global_config.organizer.default_output_dir:
            self.txt_output_path.setText(global_config.organizer.default_output_dir)

    def setupSignals(self):
        self.btn_input_browse.clicked.connect(self.browseInput)
        self.btn_output_browse.clicked.connect(self.browseOutput)
        self.btn_close.clicked.connect(self.safeClose)
        self.btn_add_folder.clicked.connect(lambda: self.addOutputFolder(self.txt_folder_name.currentText()))
        self.btn_del_folder.clicked.connect(self.removeOutputFolder)
        self.btn_reset.clicked.connect(lambda: self.txt_input_path.clear() or self.reset())
        self.btn_apply.clicked.connect(self.applyRequested)
        self.btn_apply.enterEvent = self.applyButtonEnter
        self.btn_apply.leaveEvent = self.applyButtonLeave
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

    def applyButtonEnter(self, event):
        if self._status_owner is None:
            self._status_owner = self.btn_apply
            if self.formattedOutputName:
                outpath = Path(self.txt_output_path.text(), self.formattedOutputName)
                self.statusbar.showMessage("Start conversion to " + str(outpath))

    def applyButtonLeave(self, event):
        if self._status_owner == self.btn_apply:
            self.statusbar.clearMessage()
            self._status_owner = None

    @property
    def formattedOutputName(self) -> str:
        self.flushFolderMeta()

        if self.cbox_output_type.currentIndex() < 0:
            return ""

        if not self._meta:
            return ""

        datestr = self.txt_date.text() or self.txt_date.placeholderText()
        if datestr:
            date = date_parse(datestr)
            yymmdd = date.strftime("%y%m%d")
        else:
            yymmdd = ""
        partnumbers = [f.partnumber for f in self._meta.folders.values() if f.partnumber]

        name_args = dict(
            title=self.txt_title.text() or self.txt_title.placeholderText(),
            artist=self.txt_artists.text() or self.txt_artists.placeholderText(),
            yymmdd=yymmdd,
            partnumber=self.combinePartnumber(partnumbers) if partnumbers else "",
            event=self.txt_event.text(),
            collaboration="", # TODO: add collaboration option?
        )
        fmt: str = global_config.organizer.output_format[self.cbox_output_type.currentText()]
        name = fmt.format(**name_args)

        # simplify and escape
        name = name.replace("()", "").replace("[]", "")
        while "[(" in name:
            name = name.replace("[(", "(", 1).replace(")]", ")", 1)
        name = name.replace(":", "：").replace("/", "／") # escape characters
        return name.strip().rstrip('.')  # directory with trailing dot is not supported by windows

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
        self._last_tab_index = index

        # update fields
        current_meta = self._meta.folders[self.tab_folders.tabText(index)]
        self.txt_catalog.setText(current_meta.catalog)
        self.txt_partnumber.setText(current_meta.partnumber)
        self.txt_edition.setText(current_meta.edition)
        self.txt_tool.setText(current_meta.tool)
        self.txt_source.setText(current_meta.source)
        self.txt_ripper.setText(current_meta.ripper)
        self.txt_comment.setPlainText(current_meta.comment)

        # update placeholder text
        self.txt_partnumber.setPlaceholderText(self._placeholders[self.currentOutputFolder].partnumber or "")
        self.txt_tool.setPlaceholderText(self._placeholders[self.currentOutputFolder].tool or "")

    def flushFolderMeta(self, index: int = None):
        if index is None:
            index = self.tab_folders.currentIndex()

        if self._meta:
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
        self._placeholders.pop(self.currentOutputFolder)
        self._meta.folders.pop(self.currentOutputFolder)
        self.tab_folders.removeTab(self.tab_folders.currentIndex())
        self.updateFolderNames()

    def updateFolderNames(self):
        # update valid folder names
        valid_folders = ['CD', 'BK', 'DVD', 'DL', 'OL', 'MISC', 'PHOTO', 'LRC']
        for i in range(self.tab_folders.count()):
            valid_folders.remove(self.tab_folders.tabText(i))
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
    def currentOutputFolder(self) -> str:
        return self.tab_folders.tabText(self.tab_folders.currentIndex())

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
        if self.txt_input_path and Path(self.txt_input_path.text()).exists():
            dlg.setDirectory(self.txt_input_path.text())

        if dlg.exec_():
            self.txt_input_path.setText(dlg.selectedFiles()[0])

    def browseOutput(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.Directory)
        if self.txt_output_path and Path(self.txt_output_path.text()).exists():
            dlg.setDirectory(self.txt_output_path.text())

        if dlg.exec_():
            self.txt_output_path.setText(dlg.selectedFiles()[0])

    def safeClose(self):
        check_folder = False
        for i in range(self.tab_folders.count()):
            if len(self.tab_folders.widget(i).model()) > 0:
                check_folder = True
                break

        if not (check_folder or self._executing):
            self.close()
            return

        msgbox = QMessageBox(self)
        msgbox.setWindowTitle("Close")
        msgbox.setIcon(QMessageBox.Warning)
        if self._executing:
            msgbox.setText("There are pending jobs. Do you really want to close?")
        else:
            msgbox.setText("Do you really want to close?")
        msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgbox.setDefaultButton(QMessageBox.No)

        if msgbox.exec_() == QMessageBox.Yes:
            if self._task is not None:
                self._task.cancel()
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

    def combinePartnumber(self, partnumbers: List[str]):
        assert len(partnumbers) > 0
        if len(partnumbers) == 1:
            return partnumbers[0]

        try:
            prefix = commonprefix(partnumbers)
            remain = [pn[len(prefix):] for pn in partnumbers]
            remain_num = [int(i) for i in remain]
            rmin, rmax = min(remain_num), max(remain_num)
            if rmax - rmin + 1 == len(remain):
                rlen = len(remain[0])
                return prefix + str(rmin).zfill(rlen) + '~' + str(rmax).zfill(rlen)
            else:
                return prefix + '&'.join(remain)
        except ValueError: # non trivial part numbers
            return ','.join(partnumbers)

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
                            self._placeholders[self.currentOutputList].tool = comment
                        else:
                            self.txt_comment.setPlaceholderText(comment)
                    if target._meta.cuesheet.rems.get('DATE', ''):
                        self.txt_date.setPlaceholderText(target._meta.cuesheet.rems['DATE'])
                if target._meta.partnumber:
                    partnumbers.append(target._meta.partnumber)

        # combine part numbers
        if len(partnumbers) > 1:
            pnstr = self.combinePartnumber(partnumbers)
            if ',' not in pnstr:
                self.txt_partnumber.setPlaceholderText(pnstr)
                self._placeholders[self.currentOutputFolder].partnumber = pnstr
        elif len(partnumbers) == 1:
            self.txt_partnumber.setPlaceholderText(partnumbers[0])
            self._placeholders[self.currentOutputFolder].partnumber = partnumbers[0]

    @asyncSlot()
    async def editCurrentTarget(self):
        await editTarget(
            self.currentOutputList[self.currentOutputListView.currentIndex().row()],
            input_root=self._input_folder,
            output_root=Path(self.txt_output_path.text(), self.currentOutputFolder)
        )
        self.fillMetaFromFolder()

    def outputContextMenu(self, listview: QListView, pos: QPoint):
        current_model = listview.model()
        menu = QMenu()
        edit_action = QAction("Edit clicked" if len(listview.selectedIndexes()) > 1 else "Edit", menu)
        edit_action.triggered.connect(self.editCurrentTarget)
        menu.addAction(edit_action)

        delete_action = QAction("Remove", menu)
        delete_action.triggered.connect(lambda: current_model.__delitem__(
            [i.row() for i in listview.selectedIndexes()]
        ))
        menu.addAction(delete_action)

        selected_istemp = current_model[listview.currentIndex().row()].temporary
        mark_temp_action = QAction("Mark temp", menu)
        mark_temp_action.setCheckable(True)
        mark_temp_action.setChecked(selected_istemp)
        mark_temp_action.triggered.connect(lambda: [current_model[i.row()].switch_temporary(not selected_istemp)
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
        keypattern = re.compile(global_config.organizer.keyword_splitter)
        keywords.update(k.strip() for k in keypattern.split(path.name) if k.strip())
        if len(os.listdir(path)) == 0:
            subf = next(path.iterdir())
            if subf.is_dir():
                keywords.update(k.strip() for k in keypattern.split(subf.name) if k.strip())
        # TODO: extract metadata from input audio files
        self.widget_keywords.extendKeywords(keywords)

        # default output path
        if not global_config.organizer.default_output_dir:
            self.txt_output_path.setText(str(path.parent / "organized"))

    def reset(self):
        '''
        Reset all information except for input/output path and folder list
        '''
        # clear text
        self.list_input_files.clear()
        self.widget_keywords.clear()
        self.tab_folders.clear()

        self.txt_title.setText(None)
        self.txt_artists.setText(None)
        self.txt_publisher.setText(None)
        self.txt_vendor.setText(None)
        self.txt_partnumber.setText(None)
        self.txt_event.setText(None)
        self.txt_date.setText(None)
        self.txt_genre.setText(None)

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

    @asyncSlot()
    async def applyRequested(self):
        # check all targets has been initialized
        for target in self._network.nodes:
            if isinstance(target, OrganizeTarget) and not target.initialized:
                msgbox = QMessageBox(self)
                msgbox.setWindowTitle("Close")
                msgbox.setIcon(QMessageBox.Critical)
                msgbox.setText("There are uninitialized targets!")
                msgbox.exec_()
                return
                
        # flush folder meta
        self.flushFolderMeta()
        for folder, fmeta in self._meta.folders.items():
            fmeta.tool = fmeta.tool or self._placeholders[folder].tool
            fmeta.partnumber = fmeta.partnumber or self._placeholders[folder].partnumber

        # flush 
        self._meta.title = self.txt_title.text() or self.txt_title.placeholderText()
        artist_text = self.txt_artists.text() or self.txt_artists.placeholderText()
        self._meta.artists = re.split(global_config.organizer.artist_splitter, artist_text)
        self._meta.publisher = self.txt_publisher.text() or self.txt_publisher.placeholderText()
        self._meta.vendor = self.txt_vendor.text() or self.txt_vendor.placeholderText()
        self._meta.event = self.txt_event.text() or self.txt_event.placeholderText()
        self._meta.date = self.txt_date.text() or self.txt_date.placeholderText()
        self._meta.genre = self.txt_genre.text() or self.txt_genre.placeholderText()

        self.statusbar.showMessage("Starting execution...")
        self._task = asyncio.ensure_future(self.executeTargets())
        self._status_owner = self._task
        await self._task
        self._task = None

    async def executeTargets(self):
        self._executing = True

        files_to_remove = []
        try:
            # sort targets
            order = topological_sort(self._network)
            order = [t for t in order if isinstance(t, OrganizeTarget)]

            # get output folder
            folder_map = {}
            disc_targets = defaultdict(list)
            for i in range(self.tab_folders.count()):
                folder = self.tab_folders.tabText(i)
                for target in self.tab_folders.widget(i).model():
                    folder_map[target] = folder
                    if isinstance(target, MergeTracksTarget):
                        disc_targets[folder].append(target)

            # add disc numbers
            for folder, targets in disc_targets.items():
                targets.sort(key=lambda t: t._outstem.lower())
                for i, t in enumerate(targets):
                    t._meta.discnumber = i + 1

            # execute targets
            output_path = Path(self.txt_output_path.text(), self.formattedOutputName)
            output_path.mkdir(exist_ok=True, parents=True)
            for i, target in enumerate(order):
                self._status_owner = target
                self.statusbar.showMessage("(%d/%d) Executing: %s" % (i, len(order), str(target)))
                if isinstance(target, str):
                    continue

                output_folder_root = output_path / folder_map[target]
                output_folder_root.mkdir(exist_ok=True)
                if isinstance(target, MergeTracksTarget):
                    await target.apply(self._input_folder, output_folder_root,
                        lambda q: self.statusbar.showMessage("(%d/%d) Executing: %s (%d%%)" % (i, len(order), str(target), int(q*100))))
                else:
                    await target.apply(self._input_folder, output_folder_root)

                if target.temporary:
                    files_to_remove.append(output_folder_root / target.output_name)

            # create meta.yaml
            meta_dict = self._meta.to_dict()
            with Path(output_path, "meta.yaml").open("w", encoding="utf-8-sig") as fout:
                yaml.dump(meta_dict, fout, encoding="utf-8", allow_unicode=True)

            self.statusbar.showMessage("Organizing done successfully!")

        except Exception as e:
            import traceback
            stack = traceback.format_exc()
            _logger.error("Pipeline execution failed. Full stack:\n" + stack)

            msgbox = QMessageBox(self)
            msgbox.setWindowTitle("Execution failed")
            msgbox.setIcon(QMessageBox.Critical)
            msgbox.setText("Reason: " + str(e))
            msgbox.exec_()

            self.statusbar.showMessage("Organizing failed!")

        finally:
            # clean up
            for f in files_to_remove:
                f.unlink()
            self._status_owner = None
            self._executing = False

def register_context_menu(uninstall: bool = False):
    import distutils.sysconfig, winreg
    pre = distutils.sysconfig.get_config_var("prefix")
    bindir = os.path.join(pre, "Scripts", "fluss-organizer.exe")

    REG_PATH = "SOFTWARE\\Classes\\Directory\\shell\\Fluss"
    if uninstall:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REG_PATH + "\\command")
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REG_PATH)
    else:
        rkey = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH)
        winreg.SetValueEx(rkey, "", 0, winreg.REG_EXPAND_SZ, f'Organize with Fluss')
        command_key = winreg.CreateKey(rkey, "command")
        winreg.SetValueEx(command_key, "", 0, winreg.REG_EXPAND_SZ, f'"{bindir}" -d "%V"')
        winreg.CloseKey(rkey)

def entry_with_args(initial_dir: Optional[str] = None,
                    install_context: Optional[bool] = False,
                    uninstall_context: Optional[bool] = False,):
    '''
    :param initial_dir: Initial directory
    :param install_context: Install the organizer in right click context menu (Windows)
    :param uninstall_context: Uninstall the organizer in right click context menu (Windows)
    '''
    if install_context:
        register_context_menu()
    elif uninstall_context:
        register_context_menu(uninstall=True)
    else:
        app = QApplication(sys.argv)
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)

        with loop:
            window = MainWindow(initial_dir)
            window.show()
            loop.run_forever()

def entry():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("--initial-dir", "-d", help="Initial directory")
    parser.add_argument("--install-context", "-i", action="store_true", help="Install the organizer in right click context menu (Windows)")
    parser.add_argument("--uninstall-context", "-u", action="store_true", help="Uninstall the organizer in right click context menu (Windows)")
    args = parser.parse_args()

    entry_with_args(**vars(args))

if __name__ == "__main__":
    exit(entry())
