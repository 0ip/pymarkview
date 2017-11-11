import io

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from pymarkview.settings import Settings
from pymarkview.ui.browser import Browser
from pymarkview.ui.editor import LineNumberEditor
from pymarkview.ui.tabbed_editor import TabbedEditor

from pymarkview.resources.defaults import stylesheet, mathjax
from pymarkview.util import resource_path

from html import escape


class App(QMainWindow):

    def __init__(self, app, *args):
        super().__init__(*args)

        self.app = app
        self.app_title = "PyMarkView"
        self.app_icon = QIcon(resource_path("pymarkview/resources/icon.ico"))

        self.setWindowTitle(self.app_title)
        self.setWindowIcon(self.app_icon)

        # Init settings
        self.settings = Settings()

        # Init state
        self.state = {
            "use_css": True,
            "use_mathjax": self.settings.mathjax,
            "debug_mode": False
        }

        # Select and inizialize MD parser
        if self.settings.md_parser == "internal":
            from pymarkview.markdown.markdown import Markdown
            md = Markdown()
            self.md = md.parse
        elif self.settings.md_parser == "markdown2":
            from markdown2 import Markdown
            md = Markdown(extras=["fenced-code-blocks", "cuddled-lists", "code-friendly"])
            self.md = md.convert
        else:
            raise Exception("No Markdown parser selected!")

        self.type_delay_tmr = QTimer()
        self.type_delay_tmr.setSingleShot(True)
        self.type_delay_tmr.timeout.connect(self.update_preview)

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
            shortcut=QKeySequence.New, function=self.tabbed_editor.new_tab
        )

        load_action = self.add_action(
            text="&Open File", tip="Load any text file in Markdown format",
            shortcut=QKeySequence.Open, function=self.tabbed_editor.open_file
        )

        save_action = self.add_action(
            text="&Save", tip="Save current file",
            shortcut=QKeySequence.Save, function=self.tabbed_editor.save_file
        )

        save_as_action = self.add_action(
            text="&Save As...", tip="Export text file in selected format",
            shortcut=QKeySequence.SaveAs, function=self.tabbed_editor.save_as_file
        )

        export_action = self.add_action(
            text="&Export As...", tip="Export text file in selected format",
            shortcut=QKeySequence.SaveAs, function=self.export_file
        )

        quit_action = self.add_action(
            text="&Exit",
            shortcut=QKeySequence.Quit, function=self.close
        )

        line_wrapping_action = self.add_action(
            "&Word Wrap",
            checkable=True, checked=self.settings.word_wrap,
            shortcut="Ctrl+W",
            function=lambda state: self.tabbed_editor.current_editor.setLineWrapMode(state)
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
            function=lambda: self.tabbed_editor.open_file(self.settings.FILE)
        )

        use_css_action = self.add_action(
            "&Use App Stylesheet",
            checkable=True, checked=self.state["use_css"],
            function=self.use_css_action_toggled
        )

        use_mathjax_action = self.add_action(
            "&Use MathJax",
            checkable=True, checked=self.state["use_mathjax"],
            function=self.use_mathjax_action_toggled
        )

        inst_action = self.add_action(
            "&Show instructions",
            function=self.tabbed_editor.load_instructions
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
        menu.addAction(line_wrapping_action)
        menu.addAction(self.show_menu_action)

        menu = menu_bar.addMenu("&Preview")
        menu.addAction(show_prev_action)
        menu.addAction(use_css_action)
        menu.addAction(use_mathjax_action)
        menu.addAction(debug_action)

        menu = menu_bar.addMenu("&Settings")
        menu.addAction(settings_action)

        menu = menu_bar.addMenu("&Help")
        menu.addAction(inst_action)

        self.statusBar()

    def init_ui(self):
        self.tabbed_editor = TabbedEditor(self, LineNumberEditor, self.settings)
        self.tabbed_editor.text_changed.connect(self.handle_text_changed)
        self.tabbed_editor.tab_changed.connect(self.handle_tab_changed)
        self.tabbed_editor.tab_title_changed.connect(self.update_app_title)
        self.tabbed_editor.file_saved.connect(self.handle_file_saved)

        self.preview = Browser()
        self.preview.pmv_link_clicked.connect(lambda file: self.tabbed_editor.open_file(file, True))

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.tabbed_editor)
        splitter.addWidget(self.preview)
        splitter.setSizes([500, 900 - 500])

        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(splitter)

        window = QWidget()
        window.setLayout(hbox)
        self.setCentralWidget(window)

        self.init_menu()

        self.app.installEventFilter(self)

        self.show()
        self.center_screen()

    def center_screen(self):
        fg = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        fg.moveCenter(cp)
        self.move(fg.topLeft())

    @pyqtSlot(str)
    def update_app_title(self, message=None):
        if message:
            self.setWindowTitle("{msg} | {title}".format(
                msg=message,
                title=self.app_title,
            )
            )
        else:
            self.setWindowTitle(self.app_title)

    def html_markdown(self, include_stylesheet=False, include_mathjax=False):
        text = self.tabbed_editor.get_text()
        out = self.md(text)

        if include_stylesheet:
            out += stylesheet

        if include_mathjax:
            out += mathjax

        return out

    def update_preview(self):
        html_md = self.html_markdown(include_stylesheet=self.state[
                                     "use_css"], include_mathjax=self.state["use_mathjax"])

        if not self.state["debug_mode"]:
            self.preview.load_html(html_md)
        else:
            self.preview.load_html(escape(html_md))

    def export_file(self):
        filename, sel_filter = QFileDialog.getSaveFileName(
            self, "Export as...", "", "HTML File (*.html)")
        if filename:
            with io.open(filename, "w", encoding="utf-8") as f:
                f.write(self.html_markdown())

            self.statusBar().showMessage("Exported {filename}".format(filename=filename), 5000)

    def use_css_action_toggled(self, state):
        self.state["use_css"] = state
        self.update_preview()

    def use_mathjax_action_toggled(self, state):
        self.preview.enable_javascript(state)
        self.state["use_mathjax"] = state
        self.update_preview()

    def debug_action_toggled(self, state):
        self.state["debug_mode"] = state
        self.update_preview()

    @pyqtSlot(str)
    def handle_file_saved(self, path):
        self.statusBar().showMessage("Saved {filename}".format(filename=path), 5000)

    def handle_text_changed(self):
        self.type_delay_tmr.start(500)

    def handle_tab_changed(self):
        self.update_preview()
        self.update_app_title(self.tabbed_editor.get_filename())

    def closeEvent(self, event):
        self.tabbed_editor.save_state()

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

    @staticmethod
    def convert_md_to_html(inp, out):
        md = Markdown()

        with io.open(inp, "r", encoding="utf-8") as i:
            with io.open(out, "w", encoding="utf-8") as o:
                data = i.read()
                parsed = md.parse(data)
                o.write(parsed)
