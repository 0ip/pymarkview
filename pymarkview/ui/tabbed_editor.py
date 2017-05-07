import io
import pickle

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QTabWidget

from pymarkview.resources.defaults import welcome_text
from pymarkview.util import resource_path

from pathlib import Path


class TabbedEditor(QTabWidget):

    text_changed = pyqtSignal()
    tab_changed = pyqtSignal()
    tab_title_changed = pyqtSignal(str)
    file_saved = pyqtSignal(str)

    STATE_FILE = ".saved_state"

    DEFAULT_TAB_NAME = "untitled"

    def __init__(self, parent, editor_widget, settings, *args):
        super().__init__(*args)
        self.__set_style()

        self._parent = parent
        self._editor_widget = editor_widget
        self._settings = settings

        self._editor_state = {}
        self._tab_state = {}
        self._mapping = self.TabIndexMapping()

        self.__load_state()

        self.tabCloseRequested.connect(self.close_tab)
        self.currentChanged.connect(self.__tab_changed)

    @property
    def current_editor(self):
        return self._editor_state.get(self._mapping.get_uid(self.currentIndex()))

    @property
    def current_tab_state(self):
        return self._tab_state.get(self._mapping.get_uid(self.currentIndex()))

    def __get_tab_state(self, tab_index=None):
        if tab_index is not None:
            return self._tab_state.get(self._mapping.get_uid(tab_index))
        else:
            return self._tab_state.get(self._mapping.get_uid(self.currentIndex()))

    def __get_editor_state(self, tab_index):
        if tab_index is not None:
            return self._editor_state.get(self._mapping.get_uid(tab_index))
        else:
            return self._editor_state.get(self._mapping.get_uid(self.currentIndex()))

    def __new_state(self, tab_index, editor_obj):
        uid = self._mapping.add(tab_index)

        self._tab_state.update({uid: {
            "modified": False,
            "path": None,
            "text": ""
        }})

        self._editor_state.update({uid: editor_obj})

    def __update_tab_state(self, attrib_dict, tab_index=None):
        if tab_index is None:
            tab_index = self.currentIndex()

        uid = self._mapping.get_uid(tab_index)

        if self._tab_state.get(uid):
            update_tab_title = False

            for attrib, value in attrib_dict.items():
                self._tab_state.get(uid)[attrib] = value
                if attrib in ("path", "modified"):
                    update_tab_title = True

            if update_tab_title:
                self.__update_tab_title()

    def __get_path(self, tab_index=None):
        state = self.__get_tab_state(tab_index)
        return state["path"]

    def __get_filename(self, tab_index=None):
        path = self.__get_path(tab_index)

        if path:
            return str(Path(path).name)
        else:
            return self.DEFAULT_TAB_NAME

    def get_filename(self):
        return self.tabText(self.currentIndex())

    def new_tab(self, append=False):
        new_ln_editor = self._editor_widget(self._settings)
        if append:
            tab_index = self.addTab(new_ln_editor, self.DEFAULT_TAB_NAME)
        else:
            tab_index = self.insertTab(self.currentIndex() + 1, new_ln_editor, self.DEFAULT_TAB_NAME)

        self.__new_state(tab_index, new_ln_editor.editor)

        if len(self._editor_state) == 1:
            self.__connect_tab_signals(tab_index)
        else:
            self.setCurrentIndex(tab_index)

        return tab_index

    def close_tab(self, tab_index):
        state = self.__get_tab_state(tab_index)
        if state["modified"]:
            res = self.__show_save_dialog()
            if res == QMessageBox.Yes:
                if not self.save_file():
                    return False
            elif res == QMessageBox.Cancel:
                return False

        if len(self._editor_state) == 1:
            self.new_tab()

        self.removeTab(tab_index)

        uid = self._mapping.remove(tab_index)
        self._tab_state.pop(uid)
        self._editor_state.pop(uid)

        self.tab_changed.emit()

    def set_text(self, text, tab_index=None):
        editor = self.__get_editor_state(tab_index)

        if editor:
            editor.setPlainText(text)

    def get_text(self, tab_index=None):
        editor = self.__get_editor_state(tab_index)

        if editor:
            return editor.toPlainText()

    def open_file(self, path, pmv_file=False):
        if path:
            return self.__open_file_helper(path, pmv_file)
        else:
            filename, _ = QFileDialog.getOpenFileName(self._parent,
                "Open Markdown text file", "", "Text Files (*.txt;*.md);;All Files (*)")
            if filename:
                return self.__open_file_helper(filename)
            else:
                return False

    def __open_file_helper(self, path, pmv_file=False):
        assert path, "No file name provided!"

        if pmv_file:
            path = str(Path(self.__get_path()).parent.joinpath(path))

        for uid, attrib_dict in self._tab_state.items():
            if attrib_dict["path"]:
                if Path(attrib_dict["path"]) == Path(path):
                    self.setCurrentIndex(self._mapping.get_index(uid))
                    return False

        if Path(path).exists():
            with io.open(path, "r", encoding="utf-8") as f:
                data = f.read()

            tab_index = self.new_tab(append=True)
            self.set_text(data, tab_index)
            self.__update_tab_state({"path": path, "modified": False})

            return True
        else:
            return False

    def save_file(self):
        state = self.current_tab_state
        path = state["path"]

        if path:
            with io.open(path, "w", encoding="utf-8") as f:
                f.write(self.get_text())

            self.file_saved.emit(path)
            self.__update_tab_state({"modified": False})
            return True
        else:
            return self.save_as_file()

    def save_as_file(self):
        path, sel_filter = QFileDialog.getSaveFileName(self._parent, "Save as...", "", "Markdown File (*.md);;Text File (*.txt)")
        if path:
            with io.open(path, "w", encoding="utf-8") as f:
                f.write(self.get_text())

            self.file_saved.emit(path)
            self.__update_tab_state({"path": path, "modified": False})

            return True

        return False

    def load_instructions(self):
        tab_index = self.new_tab()
        self.set_text(welcome_text, tab_index)
        self.__update_tab_state({"modified": False}, tab_index)

    def __handle_text_change(self):
        self.__update_tab_state({"modified": True})

        self.text_changed.emit()

    def __connect_tab_signals(self, tab_index):
        self.__get_editor_state(tab_index).textChanged.connect(self.__handle_text_change)
        self.__get_editor_state(tab_index).document_dropped.connect(self.open_file)

    def __tab_changed(self, tab_index):
        self.__connect_tab_signals(tab_index)
        self.tab_changed.emit()

    def __load_state(self):
        if Path(self.STATE_FILE).exists():
            with io.open(self.STATE_FILE, "rb") as f:
                state = pickle.load(f)

            self._mapping.import_mapping(state["mapping"])

            for uid in self._mapping.mapping:
                new_ln_editor = self._editor_widget(self._settings)
                tab_index = self.addTab(new_ln_editor, self.DEFAULT_TAB_NAME)

                self._editor_state.update({uid: new_ln_editor.editor})

                self.__connect_tab_signals(tab_index)

            self._tab_state = state["tab_state"]

            for uid, tab_state in self._tab_state.copy().items():
                tab_index = self._mapping.get_index(uid)
                self.setCurrentIndex(tab_index)
                if tab_state["modified"]:
                    self.set_text(tab_state["text"], tab_index)
                    self._tab_state[uid]["modified"] = True
                else:
                    path = tab_state["path"]
                    if path:
                        if Path(path).exists():
                            with io.open(path, "r", encoding="utf-8") as f:
                                data = f.read()
                            self.set_text(data, tab_index)
                            self._tab_state[uid]["modified"] = False
                        else:
                            self.set_text(tab_state["text"], tab_index)
                            self._tab_state[uid]["modified"] = True
                    else:
                        self.set_text(tab_state["text"], tab_index)
                        self._tab_state[uid]["modified"] = False

                self.__update_tab_title(self._mapping.get_index(uid))

            self.setCurrentIndex(state["active_tab"])

            current_editor = self.current_editor
            current_editor.moveCursor(QTextCursor.End)
            cursor = QTextCursor(current_editor.document().findBlockByLineNumber(state["active_line"]))
            current_editor.setTextCursor(cursor)
        else:
            self.load_instructions()

    def save_state(self):
        for tab_index in range(self.count()):
            self.__update_tab_state({"text": self.get_text(tab_index)}, tab_index)

        state = {
            "active_tab": self.currentIndex(),
            "active_line": self.current_editor.textCursor().blockNumber(),
            "mapping": self._mapping.export_mapping(),
            "tab_state": self._tab_state
        }

        with io.open(self.STATE_FILE, "wb") as f:
            pickle.dump(state, f)

    def __update_tab_title(self, tab_index=None):
        if tab_index is None:
            tab_index = self.currentIndex()

        state = self.__get_tab_state(tab_index)

        title = ""
        title += self.__get_filename(tab_index)
        title += " •" if state["modified"] else ""

        self.setTabText(tab_index, title)
        self.tab_title_changed.emit(title)

    def __show_save_dialog(self):
        msg = QMessageBox()
        # msg.setWindowIcon(self.app_icon)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Save Changes?")
        msg.setText("{file} has been modified. Save changes?".format(file=self.__get_filename()))
        msg.addButton(QMessageBox.Yes)
        msg.addButton(QMessageBox.No)
        msg.addButton(QMessageBox.Cancel)

        return msg.exec()

    def __set_style(self):
        self.setTabsClosable(True)

        self.setStyleSheet('''
            QTabBar::close-button {
                image: url(''' + resource_path("pymarkview/resources/close.png") + ''');
            }

            QTabBar::close-button:hover {
                image: url(''' + resource_path("pymarkview/resources/close-hover.png") + ''');
            }
        ''')

    class TabIndexMapping:

        def __init__(self):
            self._mapping = []
            self._mapping_uid = 1000

        def add(self, index=None):
            uid = self._mapping_uid
            if index is not None:
                self._mapping.insert(index, uid)
            else:
                self._mapping.append(uid)

            self._mapping_uid += 1

            return uid

        def remove(self, index):
            return self._mapping.pop(index)

        def get_uid(self, index):
            return self._mapping[index]

        def get_index(self, uid):
            return self._mapping.index(uid)

        @property
        def mapping(self):
            return self._mapping

        def export_mapping(self):
            return {"__mapping": self._mapping, "__mapping_uid": self._mapping_uid}

        def import_mapping(self, mapping_dict):
            self._mapping = mapping_dict["__mapping"]
            self._mapping_uid = mapping_dict["__mapping_uid"]
