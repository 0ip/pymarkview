.PHONY: package-win

package-win:
	pyinstaller main.pyw --onefile --noconsole --icon="pymarkview/resources/icon.ico"