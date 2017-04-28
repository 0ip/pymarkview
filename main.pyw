if __name__ == '__main__':
    import sys
    import argparse
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
    from pymarkview.app import App

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="input file")
    parser.add_argument("-o", "--output", help="output file")
    args = parser.parse_args()

    if len([x for x in (args.input, args.output) if x is not None]) == 1:
        parser.error('-i or --input and -o or --output must be given together.')

    if args.input and args.output:
        # Console handling
        App.convert_md_to_html(args.input, args.output)
    else:
        # GUI handling
        # Fix for HiDPI displays
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        app = QApplication(sys.argv)
        App(app)
        sys.exit(app.exec_())
