"""UI-related CLI Commands (web and desktop)"""

import os
import sys

from rich.console import Console

from agentos.core.scheduler import scheduler

console = Console()


def cmd_ui(args):
    """Start the web UI"""
    try:
        console.print(f"[blue]🌐 Starting AgentOS Web UI...[/blue]")
        console.print(f"[green]📍 Access at: http://localhost:{args.port}[/green]")
        console.print(f"[dim]Press Ctrl+C to stop[/dim]")

        if not scheduler.running:
            scheduler.start()

        from agentos.web.web_ui import app
        app.run(host=args.host, port=args.port, debug=False)

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Web UI stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Failed to start web UI: {e}[/red]")
        console.print(f"[dim]Make sure Flask is installed: pip install flask[/dim]")


def cmd_app(args):
    """Start the desktop app using pywebview"""
    devnull_stderr = None
    devnull_stdout = None
    try:
        old_stderr = sys.stderr
        old_stdout = sys.stdout
        devnull_stderr = open(os.devnull, "w")
        devnull_stdout = open(os.devnull, "w")
        sys.stderr = devnull_stderr
        sys.stdout = devnull_stdout

        console.print(f"[blue]🖥️  Starting AgentOS Desktop App...[/blue]")

        os.environ["QT_STYLE_OVERRIDE"] = "Fusion"
        os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.*=false"

        try:
            from PyQt5.QtCore import QCoreApplication, Qt
            from PyQt5.QtGui import QColor, QPalette
            from PyQt5.QtWidgets import QApplication

            QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)

            if not QApplication.instance():
                app_qt = QApplication(sys.argv)
                app_qt.setStyle("Fusion")

                palette = QPalette()
                palette.setColor(QPalette.Window, QColor(53, 53, 53))
                palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
                palette.setColor(QPalette.Base, QColor(25, 25, 25))
                palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
                palette.setColor(QPalette.Button, QColor(53, 53, 53))
                palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
                palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
                palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
                app_qt.setPalette(palette)
        except ImportError:
            pass

        if not scheduler.running:
            scheduler.start()

        import logging
        import socket
        import threading
        import time

        import webview
        from agentos.web.web_ui import app

        logging.getLogger("webview").setLevel(logging.CRITICAL)
        logging.getLogger("PyQt5").setLevel(logging.CRITICAL)

        def find_free_port():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", 0))
                return s.getsockname()[1]

        port = find_free_port()

        def start_flask():
            log = logging.getLogger("werkzeug")
            log.setLevel(logging.ERROR)
            app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)

        flask_thread = threading.Thread(target=start_flask, daemon=True)
        flask_thread.start()
        time.sleep(1.5)

        console.print(f"[green]✨ Launching desktop window...[/green]")

        class Api:
            def __init__(self):
                self.window = None

            def minimize_window(self):
                if self.window:
                    self.window.minimize()

            def toggle_fullscreen(self):
                if self.window:
                    try:
                        from PyQt5.QtWidgets import QApplication
                        for widget in QApplication.instance().topLevelWidgets():
                            if widget.isMaximized():
                                widget.showNormal()
                            else:
                                widget.showMaximized()
                    except:
                        pass

            def close_window(self):
                if self.window:
                    self.window.destroy()

        api = Api()

        window = webview.create_window(
            "AgentOS",
            f"http://127.0.0.1:{port}",
            width=1200,
            height=800,
            min_size=(800, 600),
            resizable=True,
            background_color="#000000",
            text_select=False,
            frameless=False,
            js_api=api,
        )

        api.window = window
        webview.start(debug=False, gui="qt", http_server=True)

    except ImportError as e:
        console.print(f"[red]❌ Missing dependencies: {e}[/red]")
        console.print("[dim]Install with: pip install PyQtWebEngine[/dim]")
        console.print("[dim]Or system: sudo apt install python3-pyqt5.qtwebengine[/dim]")
        console.print("[dim]Falling back to web UI...[/dim]")
        args.port = 5001
        cmd_ui(args)
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Desktop app stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Failed to start desktop app: {e}[/red]")
        console.print("[dim]Falling back to web UI...[/dim]")
        args.port = 5001
        cmd_ui(args)

    finally:
        if "old_stderr" in locals():
            sys.stderr = old_stderr
        if "old_stdout" in locals():
            sys.stdout = old_stdout
        if devnull_stderr:
            devnull_stderr.close()
        if devnull_stdout:
            devnull_stdout.close()
