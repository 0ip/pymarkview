import webbrowser

from PyQt5.QtCore import *
from PyQt5.QtWebKit import *
from PyQt5.QtWebKitWidgets import *


class Browser(QWebView):

    def __init__(self):
        self.view = QWebView.__init__(self)
        self.linkClicked.connect(self.handle_link_click)
        self.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.settings().setAttribute(QWebSettings.JavascriptEnabled, False)

    def load_html(self, html):
        self.setHtml(html)

    def load_url(self, url):
        self.setUrl(QUrl(url))

    def handle_link_click(self, url):
        webbrowser.open(url.toString())
        print(url.toString())

    def disable_javascript(self):
        settings = QWebSettings.globalSettings()
        settings.setAttribute(QWebSettings.JavascriptEnabled, False)
