#  Copyright (C) 2021  Igor Garmaev, garmaev@gmx.net
#
#  This program is made available under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#  A copy of the GNU General Public License is available at http://www.gnu.org/licenses/
#
#  This program is made available under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#  A copy of the GNU General Public License is available at http://www.gnu.org/licenses/

from PyQt5.QtCore import pyqtSignal, QModelIndex, QTimer
from PyQt5.QtGui import QClipboard
from PyQt5.QtWidgets import QAction, QMenu, QApplication, QDialog, QMessageBox

from aas_editor.delegates import ColorDelegate
from aas_editor import dialogs
from aas_editor.models import StandardTable
from aas_editor.settings.app_settings import *
from aas_editor.utils.util import getDefaultVal, getReqParams4init, delAASParents
from aas_editor.utils.util_type import checkType, isSimpleIterable, isIterable, getIterItemTypeHint

from aas_editor.utils.util_classes import DictItem, ClassesInfo
from aas_editor.package import Package
from aas_editor.widgets.treeview_basic import BasicTreeView


class TreeView(BasicTreeView):
    openInCurrTabClicked = pyqtSignal(QModelIndex)
    openInNewTabClicked = pyqtSignal(QModelIndex)
    openInBgTabClicked = pyqtSignal(QModelIndex)
    openInNewWindowClicked = pyqtSignal(QModelIndex)

    treeObjClipboard = []

    def __init__(self, parent=None, **kwargs):
        super(TreeView, self).__init__(parent, **kwargs)
        self.initActions()
        self.initMenu()
        self.setUniformRowHeights(True)
        self.buildHandlers()
        self.setItemDelegate(ColorDelegate())  # set ColorDelegate as standard delegate
        # TODO make it possible to turn off sorting
        self.setSortingEnabled(True)
        header = self.header()
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)
        header.setSortIndicator(-1, 0)

    # noinspection PyArgumentList
    def initActions(self):
        self.copyAct = QAction(COPY_ICON, "Copy", self,
                               statusTip="Copy selected item",
                               shortcut=SC_COPY,
                               shortcutContext=Qt.WidgetWithChildrenShortcut,
                               triggered=self.onCopy,
                               enabled=False)
        self.addAction(self.copyAct)

        self.pasteAct = QAction(PASTE_ICON, "Paste", self,
                                statusTip="Paste from clipboard",
                                shortcut=SC_PASTE,
                                shortcutContext=Qt.WidgetWithChildrenShortcut,
                                triggered=self.onPaste,
                                enabled=False)
        self.addAction(self.pasteAct)

        self.cutAct = QAction(CUT_ICON, "Cut", self,
                              statusTip="Cut selected item",
                              shortcut=SC_CUT,
                              shortcutContext=Qt.WidgetWithChildrenShortcut,
                              triggered=self.onCut,
                              enabled=False)
        self.addAction(self.cutAct)

        self.addAct = QAction(ADD_ICON, "&Add", self,
                              statusTip="Add item to selected",
                              shortcut=SC_NEW,
                              shortcutContext=Qt.WidgetWithChildrenShortcut,
                              triggered=self.onAddAct,
                              enabled=False)
        self.addAction(self.addAct)

        self.delClearAct = QAction(DEL_ICON, "Delete/clear", self,
                                   statusTip="Delete/clear selected item",
                                   shortcut=SC_DELETE,
                                   shortcutContext=Qt.WidgetWithChildrenShortcut,
                                   triggered=self.onDelClear,
                                   enabled=False)
        self.addAction(self.delClearAct)

        self.undoAct = QAction(UNDO_ICON, "Undo", self,
                               statusTip="Undo last edit action",
                               shortcut=SC_UNDO,
                               shortcutContext=Qt.WidgetWithChildrenShortcut,
                               triggered=self.onUndo,
                               enabled=False)
        self.addAction(self.undoAct)

        self.redoAct = QAction(REDO_ICON, "Redo", self,
                               statusTip="Redo last edit action",
                               shortcut=SC_REDO,
                               shortcutContext=Qt.WidgetWithChildrenShortcut,
                               triggered=self.onRedo,
                               enabled=False)
        self.addAction(self.redoAct)

        self.collapseAct = QAction("Collapse", self,
                                   statusTip="Collapse selected item",
                                   shortcutContext=Qt.WidgetWithChildrenShortcut,
                                   triggered=lambda: self.collapse(self.currentIndex()))
        self.addAction(self.collapseAct)

        self.collapseRecAct = QAction("Collapse recursively", self,
                                      shortcut=SC_COLLAPSE_RECURS,
                                      shortcutContext=Qt.WidgetWithChildrenShortcut,
                                      statusTip="Collapse recursively selected item",
                                      triggered=lambda: self.collapse(self.currentIndex()))
        self.addAction(self.collapseRecAct)

        self.collapseAllAct = QAction(COLLAPSE_ALL_ICON, "Collapse all", self,
                                      shortcut=SC_COLLAPSE_ALL,
                                      shortcutContext=Qt.WidgetWithChildrenShortcut,
                                      statusTip="Collapse all items",
                                      triggered=self.collapseAll)
        self.addAction(self.collapseAllAct)

        self.expandAct = QAction("Expand", self,
                                 statusTip="Expand selected item",
                                 shortcutContext=Qt.WidgetWithChildrenShortcut,
                                 triggered=lambda: self.expand(self.currentIndex()))
        self.addAction(self.expandAct)

        self.expandRecAct = QAction("Expand recursively", self,
                                    shortcut=SC_EXPAND_RECURS,
                                    shortcutContext=Qt.WidgetWithChildrenShortcut,
                                    statusTip="Expand recursively selected item",
                                    triggered=lambda: self.expandRecursively(self.currentIndex()))
        self.addAction(self.expandRecAct)

        self.expandAllAct = QAction(EXPAND_ALL_ICON, "Expand all", self,
                                    shortcut=SC_EXPAND_ALL,
                                    shortcutContext=Qt.WidgetWithChildrenShortcut,
                                    statusTip="Expand all items",
                                    triggered=self.expandAll)
        self.addAction(self.expandAllAct)

        self.openInCurrTabAct = QAction("Open in current ta&b", self,
                                        statusTip="Open selected item in current tab",
                                        enabled=False)

        self.openInNewTabAct = QAction("Open in new &tab", self,
                                       statusTip="Open selected item in new tab",
                                       enabled=False)

        self.openInBackgroundAct = QAction("Open in &background tab", self,
                                           statusTip="Open selected item in background tab",
                                           enabled=False)

        self.openInNewWindowAct = QAction("Open in new window", self,
                                          statusTip="Open selected item in new window",
                                          enabled=False)

        self.zoomInAct = QAction(ZOOM_IN_ICON, "Zoom in", self,
                                 shortcut=SC_ZOOM_IN,
                                 shortcutContext=Qt.WidgetShortcut,
                                 statusTip="Zoom in",
                                 triggered=self.zoomIn)
        self.addAction(self.zoomInAct)

        self.zoomOutAct = QAction(ZOOM_OUT_ICON, "Zoom out", self,
                                  shortcut=SC_ZOOM_OUT,
                                  shortcutContext=Qt.WidgetShortcut,
                                  statusTip="Zoom out",
                                  triggered=self.zoomOut)
        self.addAction(self.zoomOutAct)

    def initMenu(self) -> None:
        self.attrsMenu = QMenu(self)
        self.attrsMenu.addAction(self.cutAct)
        self.attrsMenu.addAction(self.copyAct)
        self.attrsMenu.addAction(self.pasteAct)
        self.attrsMenu.addSeparator()
        self.attrsMenu.addAction(self.delClearAct)
        self.attrsMenu.addAction(self.addAct)
        self.attrsMenu.addSeparator()
        self.attrsMenu.addAction(self.undoAct)
        self.attrsMenu.addAction(self.redoAct)
        self.attrsMenu.addSeparator()
        self.attrsMenu.addAction(self.zoomInAct)
        self.attrsMenu.addAction(self.zoomOutAct)
        self.attrsMenu.addSeparator()
        foldingMenu = self.attrsMenu.addMenu("Folding")
        foldingMenu.addAction(self.collapseAct)
        foldingMenu.addAction(self.collapseRecAct)
        foldingMenu.addAction(self.collapseAllAct)
        foldingMenu.addAction(self.expandAct)
        foldingMenu.addAction(self.expandRecAct)
        foldingMenu.addAction(self.expandAllAct)
        self.attrsMenu.addSeparator()
        self.attrsMenu.addAction(self.openInCurrTabAct)
        self.attrsMenu.addAction(self.openInNewTabAct)
        self.attrsMenu.addAction(self.openInBackgroundAct)
        self.attrsMenu.addAction(self.openInNewWindowAct)

    def openMenu(self, point):
        self.attrsMenu.exec_(self.viewport().mapToGlobal(point))

    def buildHandlers(self):
        self.customContextMenuRequested.connect(self.openMenu)
        self.modelChanged.connect(self.onModelChanged)
        self.ctrlWheelScrolled.connect(lambda delta: self.zoom(delta=delta))

    def onModelChanged(self, model: StandardTable):
        self.selectionModel().currentChanged.connect(self.onCurrentChanged)
        self.setCurrentIndex(self.rootIndex())
        self.model().dataChanged.connect(self.onDataChanged)
        self.model().rowsInserted.connect(self.onRowsInserted)
        self.model().rowsRemoved.connect(self.onRowsRemoved)

    def onCurrentChanged(self, current: QModelIndex, previous: QModelIndex):
        self.updateActions(current)

    def onDataChanged(self, topLeft: QModelIndex, bottomRight: QModelIndex, roles):
        self.itemDataChangeFailed(topLeft, bottomRight, roles)
        # completion list will be hidden now; we will show it again after a delay
        QTimer.singleShot(100, self.updateUndoRedoActs)
        self.setCurrentIndex(bottomRight)

    def onRowsInserted(self, parent: QModelIndex, first: int, last: int):
        index = parent.child(last, 0)
        self.setCurrentIndex(index)
        QTimer.singleShot(100, self.updateUndoRedoActs)

    def onRowsRemoved(self, parent: QModelIndex, first: int, last: int):
        self.setCurrentIndex(parent)
        QTimer.singleShot(100, self.updateUndoRedoActs)

    def updateActions(self, index: QModelIndex):
        # update paste action
        self.pasteAct.setEnabled(self.isPasteOk(index))

        # update copy/cut/delete actions
        if index.isValid():
            self.copyAct.setEnabled(True)
            self.cutAct.setEnabled(True)
            self.delClearAct.setEnabled(True)
        else:
            self.copyAct.setEnabled(False)
            self.cutAct.setEnabled(False)
            self.delClearAct.setEnabled(False)

        # update add action
        obj = index.data(OBJECT_ROLE)
        objType = type(obj)
        attrName = index.data(NAME_ROLE)

        if ClassesInfo.addActText(objType):
            addActText = ClassesInfo.addActText(objType)
            enabled = True
        elif attrName in Package.addableAttrs():
            addActText = ClassesInfo.addActText(Package, attrName)
            enabled = True
        elif isIterable(obj):
            addActText = f"Add {attrName} element"
            enabled = True
        else:
            addActText = "Add"
            enabled = False
        self.addAct.setEnabled(enabled)
        self.addAct.setText(addActText)

    def updateUndoRedoActs(self):
        # update undo/redo actions
        undoEnabled = bool(self.model().data(QModelIndex(), UNDO_ROLE))
        self.undoAct.setEnabled(undoEnabled)
        redoEnabled = bool(self.model().data(QModelIndex(), REDO_ROLE))
        self.redoAct.setEnabled(redoEnabled)

    def zoomIn(self):
        self.zoom(delta=+2)

    def zoomOut(self):
        self.zoom(delta=-2)

    def zoom(self, pointSize: int = DEFAULT_FONT.pointSize(), delta: int = 0):
        if self.model():
            font = QFont(self.model().data(QModelIndex(), Qt.FontRole))
            if delta > 0:
                fontSize = min(font.pointSize() + 2, MAX_FONT_SIZE)
            elif delta < 0:
                fontSize = max(font.pointSize() - 2, MIN_FONT_SIZE)
            elif MIN_FONT_SIZE < pointSize < MAX_FONT_SIZE:
                fontSize = pointSize
            else:
                return
            font.setPointSize(fontSize)
            self.model().setData(QModelIndex(), font, Qt.FontRole)
            self.setFont(font)
        else:
            print("zoom pressed with no model")

    def onUndo(self):
        self.model().setData(QModelIndex(), NOT_GIVEN, UNDO_ROLE)

    def onRedo(self):
        self.model().setData(QModelIndex(), NOT_GIVEN, REDO_ROLE)

    def onDelClear(self):
        index = self.currentIndex()
        attribute = index.data(NAME_ROLE)
        try:
            parentObjType = type(index.data(PARENT_OBJ_ROLE))
            defaultVal = getDefaultVal(parentObjType, attribute)
            self.model().setData(index, defaultVal, CLEAR_ROW_ROLE)
        except (AttributeError, IndexError):
            self.model().setData(index, NOT_GIVEN, CLEAR_ROW_ROLE)

    def onCopy(self):
        index = self.currentIndex()
        obj2copy = index.data(OBJECT_ROLE)
        delAASParents(obj2copy)  # TODO check if there is a better solution to del aas parents
        self.treeObjClipboard.clear()
        self.treeObjClipboard.append(obj2copy)
        clipboard = QApplication.clipboard()
        clipboard.setText(index.data(Qt.DisplayRole), QClipboard.Clipboard)
        if self.isPasteOk(index):
            self.pasteAct.setEnabled(True)
        else:
            self.pasteAct.setEnabled(False)

    def isPasteOk(self, index: QModelIndex) -> bool:
        if not self.treeObjClipboard or not index.isValid():
            return False

        obj2paste = self.treeObjClipboard[0]
        targetTypeHint = index.data(TYPE_HINT_ROLE)

        try:
            if checkType(obj2paste, targetTypeHint):
                return True
            targetObj = index.data(OBJECT_ROLE)
            if isIterable(targetObj):
                return checkType(obj2paste, getIterItemTypeHint(targetTypeHint))
        except (AttributeError, TypeError) as e:
            print(e)
        return False

    def onPaste(self):
        obj2paste = self.treeObjClipboard[0]
        index = self.currentIndex()
        targetParentObj = index.parent().data(OBJECT_ROLE)
        targetObj = index.data(OBJECT_ROLE)
        targetTypeHint = index.data(TYPE_HINT_ROLE)
        reqAttrsDict = getReqParams4init(type(obj2paste), rmDefParams=True)

        # if no req. attrs, paste data without dialog
        # else paste data with dialog for asking to check req. attrs
        if isIterable(targetObj):
            try:
                iterItemTypehint = getIterItemTypeHint(targetTypeHint)
            except TypeError:
                iterItemTypehint = getIterItemTypeHint(type(targetObj))
            if checkType(obj2paste, iterItemTypehint):
                self._onPasteAdd(index, obj2paste, withDialog=bool(reqAttrsDict))
                return
        if checkType(obj2paste, targetTypeHint):
            if isIterable(targetParentObj):
                self._onPasteAdd(index.parent(), obj2paste, withDialog=bool(reqAttrsDict))
            else:
                self._onPasteReplace(index, obj2paste, withDialog=bool(reqAttrsDict))

    def _onPasteAdd(self, index, obj2paste, withDialog):
        if withDialog:
            self.addItemWithDialog(index, type(obj2paste), objVal=obj2paste,
                                   title=f"Paste element", rmDefParams=True)
        else:
            self.model().setData(index, obj2paste, ADD_ITEM_ROLE)

    def _onPasteReplace(self, index, obj2paste, withDialog):
        if withDialog:
            self.replItemWithDialog(index, type(obj2paste), objVal=obj2paste,
                                    title=f"Paste element", rmDefParams=True)
        else:
            self.model().setData(index, obj2paste, Qt.EditRole)

    def onCut(self):
        self.onCopy()
        self.onDelClear()

    def addItemWithDialog(self, parent: QModelIndex, objType, objVal=None,
                          title="", rmDefParams=False):
        dialog = dialogs.AddObjDialog(objType, self, rmDefParams=rmDefParams,
                                      objVal=objVal, title=title)
        result = False
        while not result and dialog.exec_() == QDialog.Accepted:
            try:
                obj = dialog.getObj2add()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
                continue

            if isinstance(obj, dict):
                for key, value in obj.items():
                    result = self.model().setData(parent, DictItem(key, value), ADD_ITEM_ROLE)
            elif isSimpleIterable(obj):
                for i in obj:
                    result = self.model().setData(parent, i, ADD_ITEM_ROLE)
            else:
                result = self.model().setData(parent, obj, ADD_ITEM_ROLE)
        if dialog.result() == QDialog.Rejected:
            print("Item adding cancelled")
        dialog.deleteLater()
        self.setFocus()

    def replItemWithDialog(self, index, objType, objVal=None, title="", rmDefParams=False):
        title = title if title else f"Edit {index.data(NAME_ROLE)}"
        dialog = dialogs.AddObjDialog(objType, self, rmDefParams=rmDefParams, objVal=objVal, title=title)
        result = False
        while not result and dialog.exec_() == QDialog.Accepted:
            try:
                obj = dialog.getObj2add()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
                continue

            result = self.model().setData(index, obj, Qt.EditRole)
        if dialog.result() == QDialog.Rejected:
            print("Item editing cancelled")
        dialog.deleteLater()
        self.setFocus()
        self.setCurrentIndex(index)

    def itemDataChangeFailed(self, topLeft, bottomRight, roles):
        """Check dataChanged signal if data change failed and show Error dialog if failed"""
        if DATA_CHANGE_FAILED_ROLE in roles:
            QMessageBox.critical(self, "Error", self.model().data(topLeft, DATA_CHANGE_FAILED_ROLE))
