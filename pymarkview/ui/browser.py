import webbrowser

from PyQt5.QtCore import *
from PyQt5.QtWebEngineWidgets import *

class WebEnginePage(QWebEnginePage):
    def acceptNavigationRequest(self, url, navtype, mainframe):
        return False

class Browser(QWebEngineView):
    PMV_LINK_PREFIX = "pmv://"

    pmv_link_clicked = pyqtSignal(str)

    def __init__(self):
        self.view = QWebEngineView.__init__(self)
        self.setPage(WebEnginePage(self))
        self.page().acceptNavigationRequest = self.handle_link_click
        self.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        self.settings().setAttribute(QWebEngineSettings.FocusOnNavigationEnabled, False)
        self.loadStarted.connect(self.handle_load_started)
        self.loadFinished.connect(self.handle_load_finished)

    def load_html(self, html):
        self.setHtml(html)

    def load_url(self, url):
        self.setUrl(QUrl(url))

    def enable_javascript(self, state):
        self.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, state)

    def handle_load_started(self):
        self.scroll_position = self.page().scrollPosition()

    def handle_load_finished(self):
        self.page().runJavaScript(
            f"window.scrollTo({self.scroll_position.x()}, {self.scroll_position.y()});"
        )

    def handle_link_click(self, url, navtype, mainframe):
        url = url.toString()

        if not url.startswith(self.PMV_LINK_PREFIX):
            webbrowser.open(url)
        else:
            self.pmv_link_clicked.emit(url[len(self.PMV_LINK_PREFIX):])

        return False
