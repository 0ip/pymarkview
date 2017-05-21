import webbrowser

from PyQt5.QtCore import *
from PyQt5.QtWebKit import *
from PyQt5.QtWebKitWidgets import *


class Browser(QWebView):

    PMV_LINK_PREFIX = "pmv://"

    pmv_link_clicked = pyqtSignal(str)

    def __init__(self):
        self.view = QWebView.__init__(self)
        self.linkClicked.connect(self.handle_link_click)
        self.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.settings().setAttribute(QWebSettings.JavascriptEnabled, False)
        self.loadStarted.connect(self.handle_load_started)
        self.loadFinished.connect(self.handle_load_finished)

    def load_html(self, html):
        self.setHtml(html)

    def load_url(self, url):
        self.setUrl(QUrl(url))

    def enable_javascript(self, state):
        self.settings().setAttribute(QWebSettings.JavascriptEnabled, state)

    def handle_load_started(self):
        self.scroll_position = self.page().mainFrame().scrollPosition()

    def handle_load_finished(self):
        self.page().mainFrame().setScrollPosition(self.scroll_position)

    def handle_link_click(self, url):
        url = url.toString()
        if not url.startswith(self.PMV_LINK_PREFIX):
            webbrowser.open(url)
        else:
            self.pmv_link_clicked.emit(url[len(self.PMV_LINK_PREFIX):])
