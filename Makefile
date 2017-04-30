.PHONY: package-win

package-win:
	pyinstaller main.pyw --onefile --noconsole --icon="pymarkview/resources/icon.ico"
	echo "a.datas += [('icon.ico','pymarkview/resources/icon.ico', 'Data')]" >> main.spec
	pyinstaller main.spec