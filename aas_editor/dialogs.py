#  Copyright (C) 2021  Igor Garmaev, garmaev@gmx.net
#
#  This program is made available under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#  A copy of the GNU General Public License is available at http://www.gnu.org/licenses/

from aas.model.base import *

from enum import Enum, unique
from inspect import isabstract
from typing import Union, List, Dict, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPaintEvent
from PyQt5.QtWidgets import QLabel, QPushButton, QDialog, QDialogButtonBox, \
    QGroupBox, QWidget, QVBoxLayout, QHBoxLayout

from aas_editor.editWidgets import StandardInputWidget, SpecialInputWidget
from aas_editor.settings import DEFAULTS, DEFAULT_COMPLETIONS, ATTRIBUTE_COLUMN, OBJECT_ROLE,\
    DEFAULT_ATTRS_TO_HIDE
from aas_editor.delegates import ColorDelegate
from aas_editor.utils.util import inheritors, getReqParams4init, getParams4init, getDefaultVal, \
    getAttrDoc
from aas_editor.utils.util_type import getTypeName, issubtype, isoftype, isSimpleIterableType, \
    isIterableType, isIterable
from aas_editor.utils.util_classes import DictItem
from aas_editor.widgets import *
from aas_editor import widgets


class AddDialog(QDialog):
    """Base abstract class for custom dialogs for adding data"""

    def __init__(self, parent=None, title=""):
        QDialog.__init__(self, parent)
        self.setWindowTitle(title)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.buttonOk = self.buttonBox.button(QDialogButtonBox.Ok)
        self.buttonOk.setDisabled(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
        self.setMinimumWidth(400)
        self.setMaximumHeight(900)

    def getObj2add(self):
        pass


def checkIfAccepted(func):
    """Decorator for checking if user clicked ok"""

    def wrap(addDialog):
        if addDialog.result() == QDialog.Accepted:
            return func(addDialog)
        else:
            raise ValueError("Adding was cancelled")

    return wrap


def getInputWidget(objType, rmDefParams=True, title="", attrsToHide: dict = None,
                   parent=None, objVal=None, **kwargs) -> QWidget:
    print(objType, objType.__str__, objType.__repr__, objType.__class__)

    if objVal and not isoftype(objVal, objType):
        print("Given object type does not match to real object type:", objType, objVal)
        objVal = None

    attrsToHide = attrsToHide if attrsToHide else DEFAULT_ATTRS_TO_HIDE.copy()
    kwargs = {
        "rmDefParams": rmDefParams,
        "title": title,
        "attrsToHide": attrsToHide,
        "parent": parent,
        "objVal": objVal,
        **kwargs
    }

    if isabstract(objType) and not isIterableType(objType):
        objTypes = inheritors(objType)
        widget = TypeOptionObjGroupBox(objTypes, **kwargs)
    elif isSimpleIterableType(objType):
        widget = IterableGroupBox(objType, **kwargs)
    elif issubtype(objType, Union):
        objTypes = objType.__args__
        widget = TypeOptionObjGroupBox(objTypes, **kwargs)
    elif issubtype(objType, AASReference):
        widget = AASReferenceGroupBox(objType, **kwargs)
    elif issubtype(objType, SpecialInputWidget.types):
        widget = SpecialInputWidget(objType, **kwargs)
    elif issubtype(objType, StandardInputWidget.types):
        widget = StandardInputWidget(objType, **kwargs)
    else:
        widget = ObjGroupBox(objType, **kwargs)
    return widget


class AddObjDialog(AddDialog):
    def __init__(self, objType, parent: 'TreeView', title="", rmDefParams=True, objVal=None):
        title = title if title else f"Add {getTypeName(objType)}"
        AddDialog.__init__(self, parent, title=title)
        self.buttonOk.setEnabled(True)

        kwargs = {
            "rmDefParams": rmDefParams,
            "objVal": objVal,
            "parent": self,
        }

        # if obj is given and rmDefParams = True, save all init params of obj in attrsToHide
        # and show user only required params to set
        if objVal and rmDefParams:
            attrsToHide = {}

            params, defaults = getParams4init(objType)
            for key in params.keys():
                try:
                    attrsToHide[key] = getattr(objVal, key.rstrip("_"))  # TODO fix if aas changes
                except AttributeError:
                    attrsToHide[key] = getattr(objVal, key)

            reqParams = getReqParams4init(objType, rmDefParams=True)
            for key in reqParams.keys():
                try:
                    attrsToHide.pop(key.rstrip("_"))  # TODO fix if aas changes
                except KeyError:
                    attrsToHide.pop(key)

            self.inputWidget = getInputWidget(objType, attrsToHide=attrsToHide, **kwargs)
        else:
            self.inputWidget = getInputWidget(objType, **kwargs)
        self.inputWidget.setObjectName("mainBox")
        self.inputWidget.setStyleSheet("#mainBox{border:0;}") #FIXME
        self.layout().insertWidget(0, self.inputWidget)

    def getInputWidget(self):
        pass

    @checkIfAccepted
    def getObj2add(self):
        return self.inputWidget.getObj2add()


@unique
class GroupBoxType(Enum):
    SIMPLE = 0
    CLOSABLE = 1
    ADDABLE = 2


class GroupBox(QGroupBox):
    """Groupbox which also can be closable groupbox"""
    def __init__(self, objType, parent=None, title="", attrsToHide: dict = None, rmDefParams=True,
                 objVal=None, **kwargs):
        super().__init__(parent)
        if title:
            self.setTitle(title)

        self.objType = objType
        self.attrsToHide = attrsToHide if attrsToHide else DEFAULT_ATTRS_TO_HIDE.copy()
        self.rmDefParams = rmDefParams
        self.objVal = objVal

        self.setAlignment(Qt.AlignLeft)
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        self.type = GroupBoxType.SIMPLE

    def paintEvent(self, a0: QPaintEvent) -> None:
        super(GroupBox, self).paintEvent(a0)
        if self.isCheckable():
            self.setStyleSheet(
                "GroupBox::indicator:checked"
                "{"
                "    border-image: url(aas_editor/icons/close-hover.svg);"
                "}"
                "GroupBox::indicator:checked:hover,"
                "GroupBox::indicator:checked:focus,"
                "GroupBox::indicator:checked:pressed"
                "{"
                "    border-image: url(aas_editor/icons/close-pressed.svg);"
                "}"
            )

    def setClosable(self, b: bool) -> None:
        self.type = GroupBoxType.CLOSABLE if b else GroupBoxType.SIMPLE
        self.setCheckable(b)

    def isClosable(self) -> bool:
        return self.isCheckable() and self.type is GroupBoxType.CLOSABLE

    def setAddable(self, b: bool) -> None:
        self.type = GroupBoxType.ADDABLE if b else GroupBoxType.SIMPLE
        self.setCheckable(b)

    def isAddable(self) -> bool:
        return self.isCheckable() and self.type is GroupBoxType.ADDABLE

    def setVal(self, val):
        pass


class ObjGroupBox(GroupBox):
    def __init__(self, objType, parent=None, attrsToHide: dict = None, objVal=None, **kwargs):
        super().__init__(objType, objVal=objVal, parent=parent, attrsToHide=attrsToHide, **kwargs)

        self.inputWidgets: List[QWidget] = []
        self.attrWidgetDict: Dict[str, QWidget] = {}

        self.reqAttrsDict = getReqParams4init(self.objType, self.rmDefParams, self.attrsToHide)
        self.kwargs = kwargs.copy() if kwargs else {}
        self.kwargs.pop("objVal", None)
        self.initLayout()

    def initLayout(self):
        if self.reqAttrsDict:
            for attr, attrType in self.reqAttrsDict.items():
                # TODO delete when right _ will be deleted in aas models
                val = getattr(self.objVal, attr.rstrip("_"),
                              DEFAULTS.get(self.objType, {}).get(attr, getDefaultVal(self.objType, attr, None)))
                self.kwargs["completions"] = DEFAULT_COMPLETIONS.get(self.objType, {}).get(attr, [])
                inputWidget = self.getInputWidget(attr, attrType, val, **self.kwargs)
                self.inputWidgets.append(inputWidget)
                self.layout().addWidget(inputWidget)
        # else: # TODO check if it works ok
        #     inputWidget = self.getInputWidget(objName, objType, rmDefParams, objVal)
        #     self.layout().addWidget(inputWidget)

    def getInputWidget(self, attr: str, attrType, val, **kwargs) -> QHBoxLayout:
        print(f"Getting widget for attr: {attr} of type: {attrType}")
        widget = getInputWidget(attrType, objVal=val, **kwargs)
        self.attrWidgetDict[attr] = widget

        if isinstance(widget, QGroupBox):
            widget.setTitle(f"{attr}:")
            return widget
        else:
            label = QLabel(f"{attr}:", toolTip=getAttrDoc(attr, self.objType))
            layoutWidget = QWidget()
            layout = QHBoxLayout(layoutWidget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(label)
            layout.addWidget(widget)
            return layoutWidget

    def getObj2add(self):
        """Return resulting obj due to user input data"""
        attrValueDict = {}
        for attr, widget in self.attrWidgetDict.items():
            attrValueDict[attr] = widget.getObj2add()
        for attr, value in self.attrsToHide.items():
            attrValueDict[attr] = value
        try:
            obj = self.objType(**attrValueDict)
        except TypeError:
            for key in DEFAULT_ATTRS_TO_HIDE:
                try:
                    attrValueDict.pop(key)
                except KeyError:
                    continue
            obj = self.objType(**attrValueDict)
        return obj

    def delInputWidget(self, widget: QWidget):
        self.layout().removeWidget(widget)
        widget.close()
        self.inputWidgets.remove(widget)

        self.adjustSize()
        self.window().adjustSize()

    def setVal4attr(self, attr: str, val):
        attrWidget = self.attrWidgetDict[attr]
        attrWidget.setVal(val)

    def setVal(self, val):
        if val and isoftype(val, self.objType):
            self.objVal = val
            for widget in reversed(self.inputWidgets):
                self.delInputWidget(widget)
            self.initLayout()
        else:
            print("Value does not fit to req obj type", type(val), self.objType)


class SingleWidgetGroupBox(GroupBox):
    def __init__(self, widget: Union[StandardInputWidget, SpecialInputWidget], parent=None):
        super(SingleWidgetGroupBox, self).__init__(widget.objType, parent)
        self.inputWidget = widget
        self.layout().addWidget(widget)

    def getObj2add(self):
        """Return resulting obj due to user input data"""
        return self.inputWidget.getObj2add()

    def setVal(self, val):
        self.inputWidget.setVal(val)


class IterableGroupBox(GroupBox):
    def __init__(self, objType, **kwargs):
        super().__init__(objType, **kwargs)
        self.argTypes = list(self.objType.__args__)
        self.kwargs = kwargs.copy() if kwargs else {}
        plusButton = QPushButton(f"+ Element", self,
                                 toolTip="Add element",
                                 clicked=self._addInputWidget)
        self.layout().addWidget(plusButton)
        self.inputWidgets = []
        self.setVal(self.objVal)

    def _addInputWidget(self, objVal=None):
        if ... in self.argTypes:
            self.argTypes.remove(...)

        if not issubtype(self.objType, dict):
            if len(self.argTypes) == 1:
                argType = self.argTypes[0]
            else:
                raise TypeError(f"expected 1 argument, got {len(self.argTypes)}", self.argTypes)
        else: #  if parentType = dict
            if len(self.argTypes) == 2:
                DictItem._field_types["key"] = self.argTypes[0]
                DictItem._field_types["value"] = self.argTypes[1]
                argType = DictItem
            else:
                raise TypeError(f"expected 2 arguments, got {len(self.argTypes)}", self.argTypes)

        self.kwargs.update({
            "objType": argType,
            "title": f"{getTypeName(argType)} {len(self.inputWidgets)}",
            "rmDefParams": self.rmDefParams,
            "objVal": objVal
        })
        widget = getInputWidget(**self.kwargs)
        if not isinstance(widget, GroupBox):
            widget = SingleWidgetGroupBox(widget)
        widget.setClosable(True)
        widget.setFlat(True)
        widget.toggled.connect(lambda: self.delInputWidget(widget))
        self.inputWidgets.append(widget)
        self.layout().insertWidget(self.layout().count()-1, widget)

    def delInputWidget(self, widget: QWidget):
        self.layout().removeWidget(widget)
        widget.close()
        self.inputWidgets.remove(widget)

        self.adjustSize()
        self.window().adjustSize()

    def getObj2add(self):
        """Return resulting obj due to user input data"""
        listObj = []
        for widget in self.inputWidgets:
            listObj.append(widget.getObj2add())
        if issubtype(self.objType, tuple):
            obj = tuple(listObj)
        elif issubtype(self.objType, list):
            obj = list(listObj)
        elif issubtype(self.objType, set):
            obj = set(listObj)
        elif issubtype(self.objType, dict):
            obj = dict(listObj)
        else:
            obj = list(listObj)
        return obj

    def setVal(self, val):
        if isinstance(val, dict):
            val = [DictItem(key, value) for key, value in val.items()]

        if val and isIterable(val):
            for widget in reversed(self.inputWidgets):
                self.delInputWidget(widget)
            self.objVal = val
            for val in self.objVal:
                self._addInputWidget(val)
        else:
            print("Value is not iterable")
            self._addInputWidget()


class TypeOptionObjGroupBox(GroupBox):
    def __init__(self, objTypes, **kwargs):
        super(TypeOptionObjGroupBox, self).__init__(objTypes, **kwargs)

        self.initTypeComboBox()
        currObjType = self.typeComboBox.currentData()

        kwargs["parent"] = self
        kwargs["title"] = ""
        self.widget = QWidget()
        self.replaceGroupBoxWidget(currObjType, **kwargs)
        self.layout().addWidget(self.widget)

        # change input widget for new type if type in combobox changed
        self.typeComboBox.currentIndexChanged.connect(
            lambda i: self.replaceGroupBoxWidget(self.typeComboBox.itemData(i), **kwargs))

    def initTypeComboBox(self):
        """Init func for ComboBox where desired Type of input data will be chosen"""
        self.typeComboBox = CompleterComboBox(self)
        for typ in self.objType:
            self.typeComboBox.addItem(getTypeName(typ), typ)
            self.typeComboBox.model().sort(0, Qt.AscendingOrder)
        if self.objVal:
            self.typeComboBox.setCurrentIndex(self.typeComboBox.findData(type(self.objVal)))
        else:
            self.typeComboBox.setCurrentIndex(0)
        self.layout().insertWidget(0, self.typeComboBox)

    def replaceGroupBoxWidget(self, objType, **kwargs):
        """Changes input GroupBox due to objType structure"""
        kwargs["objVal"] = self.objVal
        newWidget = getInputWidget(objType, **kwargs)
        self.layout().replaceWidget(self.widget, newWidget)
        self.widget.close()
        newWidget.showMinimized()
        self.widget = newWidget
        if isinstance(self.widget, QGroupBox):
            self.widget.setFlat(True)
        if isinstance(self.widget, (ObjGroupBox, IterableGroupBox)) and not self.widget.inputWidgets:
            self.widget.hide()
        self.window().adjustSize()

    def getObj2add(self):
        """Return resulting obj due to user input data"""
        return self.widget.getObj2add()

    def setVal(self, val):
        if val and type(val) in self.objType:
            self.objVal = val
            self.typeComboBox.setCurrentIndex(self.typeComboBox.findData(type(self.objVal)))


class ChooseItemDialog(AddDialog):
    def __init__(self, view: 'TreeView', columnsToShow=[ATTRIBUTE_COLUMN],
                 validator=lambda chosenIndex: chosenIndex.isValid(),
                 parent: Optional[QWidget] = None, title: str = ""):
        super(ChooseItemDialog, self).__init__(parent, title)
        self.setFixedHeight(500)
        self.validator = validator
        self.view = view
        self.view.setParent(self)
        self.view.setItemDelegate(ColorDelegate())
        self.view.setModelWithProxy(self.view.sourceModel())
        self.view.expandAll()
        self.view.setHeaderHidden(True)

        for column in range(self.view.model().columnCount()):
            if column not in columnsToShow:
                self.view.hideColumn(column)

        self.searchBar = SearchBar(self.view, parent=self, filterColumns=columnsToShow)
        self.toolBar = ToolBar(self)
        self.toolBar.addAction(self.view.collapseAllAct)
        self.toolBar.addAction(self.view.expandAllAct)
        self.toolBar.addWidget(self.searchBar)

        self.layout().insertWidget(0, self.toolBar)
        self.layout().insertWidget(1, self.view)
        self.buildHandlers()

    def buildHandlers(self):
        self.view.selectionModel().currentChanged.connect(self.validate)

    def validate(self):
        chosenIndex = self.view.currentIndex()
        if chosenIndex.isValid() and self.validator(chosenIndex):
            self.buttonOk.setEnabled(True)
        else:
            self.buttonOk.setDisabled(True)

    def getObj2add(self):
        return self.view.currentIndex()

    def getChosenItem(self):
        return self.getObj2add()


class AASReferenceGroupBox(ObjGroupBox):
    # use CHOOSE_FRM_VIEW if no chooseFrmView is given
    # can be changed outside of class
    CHOOSE_FRM_VIEW = None

    def __init__(self, objType, chooseFrmView=None, **kwargs):
        super(AASReferenceGroupBox, self).__init__(objType, **kwargs)
        self.chooseFrmView: 'TreeView' = chooseFrmView if chooseFrmView else self.CHOOSE_FRM_VIEW
        if self.chooseFrmView:
            plusButton = QPushButton(f"Choose from local", self,
                                     toolTip="Choose element for reference",
                                     clicked=self.chooseFromLocal)
            self.layout().insertWidget(0, plusButton)

    def chooseFromLocal(self):
        tree = widgets.PackTreeView()
        sourceModel = self.chooseFrmView.sourceModel()
        tree.setModel(sourceModel)

        dialog = ChooseItemDialog(
            view=tree, parent=self, title="Choose item for reference",
            validator=lambda chosenIndex: isinstance(chosenIndex.data(OBJECT_ROLE), Referable))

        if dialog.exec_() == QDialog.Accepted:
            print("Item adding accepted")
            item = dialog.getChosenItem()
            referable = item.data(OBJECT_ROLE)
            reference = AASReference.from_referable(referable)
            self.setVal(reference)
        else:
            print("Item adding cancelled")
        dialog.deleteLater()
