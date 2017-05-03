import sys
import io

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from pymarkview.settings import Settings
from pymarkview.ui.browser import Browser
from pymarkview.ui.editor import LineNumberEditor
from pymarkview.markdown.markdown import Markdown
from pymarkview.resources.defaults import welcome_text, stylesheet

from pathlib import Path
from html import escape


class App(QMainWindow):

    def __init__(self, app):
        super().__init__()

        self.app = app
        self.app_title = "PyMarkView"
        self.app_icon = QIcon(self.resource_path("pymarkview/resources/icon.ico"))

        self.setWindowTitle(self.app_title)
        self.setWindowIcon(self.app_icon)

        # Init settings
        self.settings = Settings()

        # Init state
        self.use_css = True
        self.debug_mode = False

        self.message = ""
        self.changes_since_save = False

        self.last_used_file = ".last_used"
        self.path = ""

        if Path(self.last_used_file).exists():
            print("Found last_used file!")
            with io.open(self.last_used_file, "r", encoding="utf-8") as f:
                last_path = f.read().strip()
                print("Most recently used file: " + last_path)
                if last_path:
                    if Path(last_path).exists():
                        print("Most recently used file still exists, loading...")
                        self.path = last_path
                    else:
                        print("Most recently used file does not exist anymore.")
        else:
            print("Welcome to {title}!".format(title=self.app_title))
            io.open(self.last_used_file, "a", encoding="utf-8").close()

        self.md = Markdown()

        # Init UI
        self.init_ui()

    def add_action(self, text, tip=None, shortcut=None, checkable=False, checked=False, function=None):
        action = QAction(
            text,
            self,
            shortcut=shortcut,
            statusTip=tip,
            checkable=checkable,
            checked=checked
        )

        if function:
            if checkable:
                action.toggled.connect(function)
                function(checked)
            else:
                action.triggered.connect(function)

        if shortcut:
            self.addAction(action)

        return action

    def init_menu(self):

        new_action = self.add_action(
            text="&New File", tip="Create a new document",
            shortcut=QKeySequence.New, function=self.new_file
        )

        load_action = self.add_action(
            text="&Open File", tip="Load any text file in Markdown format",
            shortcut=QKeySequence.Open, function=self.open_file
        )

        save_action = self.add_action(
            text="&Save File", tip="Save current file",
            shortcut=QKeySequence.Save, function=self.save_file
        )

        save_as_action = self.add_action(
            text="&Save As...", tip="Export text file in selected format",
            shortcut=QKeySequence.SaveAs, function=self.save_as_file
        )

        export_action = self.add_action(
            text="&Export As...", tip="Export text file in selected format",
            shortcut=QKeySequence.SaveAs, function=self.export_file
        )

        quit_action = self.add_action(
            text="&Exit",
            shortcut=QKeySequence.Quit, function=self.close
        )

        self.line_wrapping_action = self.add_action(
            "&Word Wrap",
            checkable=True, checked=self.settings.word_wrap,
            shortcut="Ctrl+W",
            function=lambda state: self.editor().setLineWrapMode(state)
        )

        self.show_menu_action = self.add_action(
            "&Show Menu", tip="Can be opened temporarily with Alt key",
            checkable=True, checked=self.settings.show_menu,
            shortcut="Ctrl+M",
            function=lambda state: self.menuBar().setVisible(state)
        )

        show_prev_action = self.add_action(
            "&Show Preview",
            checkable=True, checked=True,
            shortcut="Ctrl+P",
            function=lambda state: self.preview.setVisible(state)
        )

        debug_action = self.add_action(
            "&Enable Debug Mode",
            checkable=True, checked=False,
            function=self.debug_action_toggled
        )

        settings_action = self.add_action(
            "&Open Settings",
            function=self.load_settings
        )

        use_css_action = self.add_action(
            "&Use App Stylesheet",
            checkable=True, checked=True,
            function=self.use_css_action_toggled
        )

        inst_action = self.add_action(
            "&Show instructions",
            function=self.load_instructions
        )

        menu_bar = self.menuBar()
        menu = menu_bar.addMenu("&File")
        menu.addAction(new_action)
        menu.addAction(load_action)
        menu.addAction(save_action)
        menu.addAction(save_as_action)
        menu.addAction(export_action)
        menu.addAction(quit_action)

        menu = menu_bar.addMenu("&Editor")
        menu.addAction(self.line_wrapping_action)
        menu.addAction(self.show_menu_action)

        menu = menu_bar.addMenu("&Preview")
        menu.addAction(show_prev_action)
        menu.addAction(use_css_action)
        menu.addAction(debug_action)

        menu = menu_bar.addMenu("&Settings")
        menu.addAction(settings_action)

        menu = menu_bar.addMenu("&Help")
        menu.addAction(inst_action)

        self.statusBar()

    def init_ui(self):
        self.editor = LineNumberEditor(settings=self.settings)
        self.editor().textChanged.connect(self.editor_handler)
        self.editor().document_dropped.connect(self.open_file)

        self.preview = Browser()
        self.preview.pmv_link_clicked.connect(lambda file: self.open_file(file, True))

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.editor)
        splitter.addWidget(self.preview)
        splitter.setSizes([500, 900-500])

        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(splitter)

        window = QWidget()
        window.setLayout(hbox)
        self.setCentralWidget(window)

        self.load_welcome()
        self.init_menu()

        self.app.installEventFilter(self)

        self.show()
        self.center_screen()

    def center_screen(self):
        fg = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        fg.moveCenter(cp)
        self.move(fg.topLeft())

    def update_app_title(self):
        if self.message:
            self.setWindowTitle("{msg}{changes} | {title}".format(
                msg=self.message,
                title=self.app_title,
                changes=" •" if self.changes_since_save else "")
            )
        else:
            self.setWindowTitle(self.app_title)

    def update_last_used(self, path):
        if not path:
            path = ""
            self.message = "untitled"
            self.update_app_title()
        else:
            self.message = path
            self.update_app_title()
            self.set_changes_since_save(False)

        self.path = path
        with io.open(self.last_used_file, "w", encoding="utf-8") as f:
            f.write(path)

    def set_changes_since_save(self, state):
        self.changes_since_save = state
        self.update_app_title()

    def html_markdown(self, include_stylesheet=False):
        out = self.md.parse(self.editor().toPlainText())

        if include_stylesheet:
            return out + stylesheet

        return out

    def editor_handler(self, refresh=False):
        if not refresh:
            self.set_changes_since_save(True)

        html_md = self.html_markdown(include_stylesheet=self.use_css)

        if not self.debug_mode:
            self.preview.load_html(html_md)
        else:
            self.preview.load_html(escape(html_md))

    def show_save_dialog(self):
        msg = QMessageBox()
        msg.setWindowIcon(self.app_icon)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Save Changes?")
        msg.setText("{file} has been modified. Save changes?".format(file=self.message))
        msg.addButton(QMessageBox.Yes)
        msg.addButton(QMessageBox.No)
        msg.addButton(QMessageBox.Cancel)

        return msg.exec()

    def new_file(self):
        if  self.changes_since_save:
            res = self.show_save_dialog()
            if res == QMessageBox.Yes:
                if not self.save_file():
                    return False
            elif res == QMessageBox.Cancel:
                return False

        self.editor.editor.setPlainText("")
        self.update_last_used(None)
        return True

    @pyqtSlot(str)
    @pyqtSlot(bool)
    def open_file(self, filename=None, pmv_file=False):
        if  self.changes_since_save:
            res = self.show_save_dialog()
            if res == QMessageBox.Yes:
                if not self.save_file():
                    return False
            elif res == QMessageBox.Cancel:
                return False

        if filename:
            self.open_file_helper(filename, pmv_file)
        else:
            filename, _ = QFileDialog.getOpenFileName(
                self, "Open Markdown text file", "", "Text Files (*.txt;*.md);;All Files (*)")
            if filename:
                return self.open_file_helper(filename)

            return False

    def open_file_helper(self, filename, pmv_file=False):
        assert filename, "No file name provided!"

        if pmv_file:
            filename = str(Path(self.path).parent.joinpath(filename))

        if Path(filename).exists():
            with io.open(filename, "r", encoding="utf-8") as f:
                data = f.read()
                self.editor.editor.setPlainText(data)

            self.update_last_used(filename)
            return True
        else:
            return False

    def save_file(self):
        if self.path:
            with io.open(self.path, "w", encoding="utf-8") as f:
                f.write(self.editor().toPlainText())

            self.statusBar().showMessage("Saved {filename}".format(filename=self.path), 5000)
            self.set_changes_since_save(False)

            return True
        else:
            return self.save_as_file()

    def save_as_file(self):
        filename, sel_filter = QFileDialog.getSaveFileName(
            self, "Save as...", "", "Markdown File (*.md);;Text File (*.txt)")
        if filename:
            with io.open(filename, "w", encoding="utf-8") as f:
                f.write(self.editor().toPlainText())

            self.update_last_used(filename)
            self.statusBar().showMessage("Saved {filename}".format(filename=filename), 5000)

            return True

        return False

    def export_file(self):
        filename, sel_filter = QFileDialog.getSaveFileName(self, "Export as...", "", "HTML File (*.html)")
        if filename:
            with io.open(filename, "w", encoding="utf-8") as f:
                f.write(self.editor.html_markdown())

            self.statusBar().showMessage("Exported {filename}".format(filename=filename), 5000)

    def load_welcome(self):
        if not self.path:
            self.load_instructions()
        else:
            self.open_file_helper(self.path)

        self.set_changes_since_save(False)

    def load_instructions(self):
        yes = self.new_file()
        if yes:
            self.editor.editor.setPlainText(welcome_text)

    def load_settings(self):
        self.open_file(self.settings.FILE)

    def use_css_action_toggled(self, state):
        self.use_css = state
        self.editor_handler(refresh=True)

    def debug_action_toggled(self, state):
        self.debug_mode = state
        self.editor_handler(refresh=True)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Alt:
            self.menuBar().setVisible(True)

        super().keyPressEvent(e)

    def eventFilter(self, source, event):
        if self.app.activePopupWidget() is None and not self.show_menu_action.isChecked():
            if event.type() == QEvent.MouseButtonPress:
                if not self.menuBar().isHidden():
                    rect = QRect(self.menuBar().mapToGlobal(QPoint(0, 0)), self.menuBar().size())
                    if not rect.contains(event.globalPos()):
                        self.menuBar().hide()
        return QMainWindow.eventFilter(self, source, event)

    def closeEvent(self, e):
        if not self.changes_since_save:
            e.accept()
            return

        result = self.show_save_dialog()
        if result == QMessageBox.Yes:
            if self.save_file():
                e.accept()
            else:
                e.ignore()
        elif result == QMessageBox.No:
            e.accept()
        elif QMessageBox.Cancel:
            e.ignore()

    @staticmethod
    def convert_md_to_html(inp, out):
        md = Markdown()

        with io.open(inp, "r", encoding="utf-8") as i:
            with io.open(out, "w", encoding="utf-8") as o:
                data = i.read()
                parsed = md.parse(data)
                o.write(parsed)

    @staticmethod
    def resource_path(relative_path):
        """ Get absolute path to PyInstaller resource """
        try:
            return str(Path(sys._MEIPASS).joinpath(Path(relative_path).name))
        except Exception:
            return relative_path