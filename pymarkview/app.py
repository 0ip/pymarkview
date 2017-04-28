import os.path
import html


from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from pymarkview.ui.browser import Browser
from pymarkview.ui.editor import LineNumberEditor
from pymarkview.markdown.markdown import Markdown
from pymarkview.resources.defaults import welcome_text, stylesheet


class App(QMainWindow):

    def __init__(self, app):
        super().__init__()

        self.app = app
        self.app_title = "PyMarkView"

        self.setWindowTitle(self.app_title)
        self.setWindowIcon(QIcon('pymarkview/resources/icon.ico'))

        self.init_settings()
        self.init_ui()

    def init_settings(self):
        self.use_css = True
        self.debug_mode = False

        self.message = ""
        self.changes_since_save = False

        self.last_used_file = ".last_used"

        self.path = ""

        if os.path.isfile(self.last_used_file):
            print("Found last_used file!")
            with open(self.last_used_file, 'r') as f:
                last_path = f.read().strip()
                print("Most recently used file: " + last_path)
                if last_path:
                    if os.path.isfile(last_path):
                        print("Most recently used file still exists, loading...")
                        self.path = last_path
                    else:
                        print("Most recently used file does not exist anymore.")
        else:
            open(self.last_used_file, 'a').close()

    def update_last_used(self, path):
        if not path:
            path = ""
            self.message = "untitled"
            self.update_app_title()
        else:
            self.message = path
            self.update_app_title()
            self._set_changes_since_save(False)

        self.path = path
        with open(self.last_used_file, 'w') as f:
            print(path, file=f)

    def init_menu(self):
        new_action = QAction("&New File", self)
        new_action.setShortcut("Ctrl+N")
        new_action.setStatusTip('Create a new document')
        new_action.triggered.connect(self.new_file)

        load_action = QAction("&Open File...", self)
        load_action.setShortcut("Ctrl+O")
        load_action.setStatusTip('Load any text file in Markdown format')
        load_action.triggered.connect(self.load_file)

        save_action = QAction("&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.setStatusTip('Save current file')
        save_action.triggered.connect(self.save_file)

        save_as_action = QAction("&Save As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.setStatusTip('Export text file in selected format')
        save_as_action.triggered.connect(self.save_as_file)

        export_action = QAction("Export As...", self)
        export_action.setStatusTip('Export text file in selected format')
        export_action.triggered.connect(self.export_file)

        hide_prev_action = QAction('&Show preview', self, checkable=True, checked=True)
        hide_prev_action.setShortcut("Ctrl+P")
        hide_prev_action.toggled.connect(lambda: self.preview.setVisible(hide_prev_action.isChecked()))

        debug_action = QAction('&Enable debug mode', self,
                               checkable=True, checked=False)
        debug_action.toggled.connect(self.debug_action_toggled)

        use_css_action = QAction('&Use app stylesheet', self, checkable=True, checked=True)
        use_css_action.toggled.connect(self.use_css_action_toggled)

        inst_action = QAction("&Show instructions", self)
        inst_action.triggered.connect(self.load_instructions)

        menu_bar = self.menuBar()
        menu = menu_bar.addMenu('&File')
        menu.addAction(new_action)
        menu.addAction(load_action)
        menu.addAction(save_action)
        menu.addAction(save_as_action)
        menu.addAction(export_action)

        menu = menu_bar.addMenu('&Editor')
        menu.addAction(hide_prev_action)
        menu.addAction(use_css_action)
        menu.addAction(debug_action)

        menu = menu_bar.addMenu('&Help')
        menu.addAction(inst_action)

        self.statusBar()

    def init_ui(self):
        self.md = Markdown()

        self.editor = LineNumberEditor()
        self.editor.editor.textChanged.connect(self.editor_handler)

        self.preview = Browser()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.editor)
        splitter.addWidget(self.preview)
        splitter.setSizes([500, 900-500])

        rt = QHBoxLayout()
        rt.setContentsMargins(0, 0, 0, 0)
        rt.addWidget(splitter)
        window = QWidget()
        window.setLayout(rt)

        self.setCentralWidget(window)

        self.load_welcome()

        self.init_menu()

        self.show()

        fg = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        fg.moveCenter(cp)
        self.move(fg.topLeft())

    def _set_changes_since_save(self, state):
        self.changes_since_save = state
        self.update_app_title()

    def html_markdown(self, include_stylesheet=False):
        out = self.md.parse(self.editor().toPlainText())

        if include_stylesheet:
            return out + stylesheet

        return out

    def editor_handler(self):
        self._set_changes_since_save(True)

        html_md = self.html_markdown(include_stylesheet=self.use_css)

        if not self.debug_mode:
            self.preview.load_html(html_md)
        else:
            self.preview.load_html(html.escape(html_md))

    def new_file(self):
        if self.changes_since_save:
            proceed = QMessageBox.warning(
                self, self.app_title, "Discard changes and open new file?", QMessageBox.Yes, QMessageBox.No)
        else:
            proceed = QMessageBox.Yes

        if proceed == QMessageBox.No:
            return False

        self.editor.editor.setPlainText("")
        self.update_last_used(None)

        return True

    def load_file(self):
        if self.changes_since_save:
            proceed = QMessageBox.warning(
                self, self.app_title, "Discard changes and open new file?", QMessageBox.Yes, QMessageBox.No)
        else:
            proceed = QMessageBox.Yes

        if proceed == QMessageBox.No:
            return False

        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Markdown text file", "", "Text Files (*.txt;*.md);;All Files (*)")
        if filename:
            self._load_file(filename)

    def _load_file(self, filename):
        if filename:
            with open(filename, 'r') as f:
                data = f.read()
                self.editor.editor.setPlainText(data)

            self.update_last_used(filename)

    def save_file(self):
        if self.path:
            with open(self.path, "w") as f:
                print(self.editor.editor.toPlainText(), file=f)

            self.statusBar().showMessage("Saved {filename}".format(filename=self.path), 5000)
            self._set_changes_since_save(False)
        else:
            self.save_as_file()

    def save_as_file(self):
        filename, sel_filter = QFileDialog.getSaveFileName(
            self, "Save as...", "", "Markdown File (*.md);;Text File (*.txt)")
        if filename:
            with open(filename, "w") as f:
                print(self.editor.editor.toPlainText(), file=f)

            self.update_last_used(filename)
            self.statusBar().showMessage("Saved {filename}".format(filename=filename), 5000)

    def export_file(self):
        filename, sel_filter = QFileDialog.getSaveFileName(self, "Export as...", "", "HTML File (*.html)")
        if filename:
            with open(filename, "w") as f:
                print(self.editor.html_markdown(), file=f)

            self.statusBar().showMessage("Exported {filename}".format(filename=filename), 5000)

    def use_css_action_toggled(self, state):
        self.use_css = state
        self.editor_handler()

    def debug_action_toggled(self, state):
        self.debug_mode = state
        self.editor_handler()

    def load_welcome(self):
        if not self.path:
            self.load_instructions()
        else:
            self._load_file(self.path)

        self._set_changes_since_save(False)

    def load_instructions(self):
        yes = self.new_file()
        if yes:
            self.editor.editor.setPlainText(welcome_text)

    def update_app_title(self):
        if self.message:
            self.setWindowTitle("{msg}{changes} | {title}".format(
                msg=self.message,
                title=self.app_title,
                changes=" •" if self.changes_since_save else "")
            )
        else:
            self.setWindowTitle(self.app_title)

    def closeEvent(self, e):
        if not self.changes_since_save:
            e.accept()
            return

        reply = QMessageBox.warning(
            self, self.app_title, "You have unsaved changes, quit anyway?", QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            e.accept()
        else:
            e.ignore()

    @staticmethod
    def convert_md_to_html(inp, out):
        md = Markdown()

        with open(inp, "r") as i:
            with open(out, "w") as o:
                print(md.parse(i.read()), file=o)
