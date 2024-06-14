import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QMessageBox
from ui.main_window import MainWindow
from logic.database import DatabaseInitializer
from utils.update_checker import update_application, CURRENT_VERSION

def initialize_database():
    conn = sqlite3.connect('pedidos.db')
    DatabaseInitializer(conn)
    conn.close()

def notify_update_available():
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle("Atualização Disponível")
    msg.setText("Uma nova versão foi baixada e está sendo instalada. O aplicativo será reiniciado.")
    msg.exec_()

if __name__ == "__main__":
    if update_application(CURRENT_VERSION):
        notify_update_available()
        sys.exit(0)

    initialize_database()
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
