from PyQt5.QtWidgets import QMainWindow, QTabWidget, QApplication
from ui.widgets.cotar_widget import CotarWidget
from ui.widgets.result_widget import ResultWidget
from ui.widgets.pedidos_widget import PedidosWidget
from ui.widgets.produtos_widget import ProdutosWidget
from ui.widgets.transportadoras_widget import TransportadorasWidget
from ui.widgets.config_widget import ConfigWidget
import sqlite3
import os
import requests
from dotenv import load_dotenv

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interface de Gerenciamento")
        self.setGeometry(100, 100, 800, 600)
        
        self.quotes = []
        self.current_quote = -1
        
        self.setup_ui()

    def setup_ui(self):
        self.center_window()

        # Create a Tab Widget
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # Initialize the environment
        load_dotenv()
        self.session = requests.Session()

        # Initialize database connection
        self.conn = sqlite3.connect('pedidos.db')
        self.cursor = self.conn.cursor()

        # Fetch all transportadoras from the database
        self.cursor.execute("SELECT nome FROM transportadora")
        self.transportadoras = [row[0] for row in self.cursor.fetchall()]

        # Initialize state dictionaries
        self.modalidades = ['Rodoviário', 'Rodoexpresso', 'Aéreo', 'Aéreo Coleta']
        self.state_abbreviations = {
            'Acre': 'AC', 'Alagoas': 'AL', 'Amapá': 'AP', 'Amazonas': 'AM', 'Bahia': 'BA', 
            'Ceará': 'CE', 'Distrito Federal': 'DF', 'Espírito Santo': 'ES', 'Goiás': 'GO', 
            'Maranhão': 'MA', 'Mato Grosso': 'MT', 'Mato Grosso do Sul': 'MS', 'Minas Gerais': 'MG',
            'Pará': 'PA', 'Paraíba': 'PB', 'Paraná': 'PR', 'Pernambuco': 'PE', 'Piauí': 'PI', 
            'Rio de Janeiro': 'RJ', 'Rio Grande do Norte': 'RN', 'Rio Grande do Sul': 'RS', 
            'Rondônia': 'RO', 'Roraima': 'RR', 'Santa Catarina': 'SC', 'São Paulo': 'SP', 
            'Sergipe': 'SE', 'Tocantins': 'TO'
        }
        self.state_names = {v: k for k, v in self.state_abbreviations.items()}

        # Add tabs
        self.add_tabs()

    def center_window(self):
        # Get screen width and height
        screen_width = self.screen().size().width()
        screen_height = self.screen().size().height()

        # Calculate position
        position_top = int(screen_height / 2 - 720 / 2)
        position_right = int(screen_width / 2 - 450 / 2)

        # Set position and size
        self.setGeometry(position_right, position_top, 460, 638)

        # Prevent window from being resized
        self.setFixedSize(460, 638)

    def add_tabs(self):
        # Create tabs and add them to the QTabWidget
        self.cotar_widget = CotarWidget(self)
        self.result_widget = ResultWidget(self)
        self.pedidos_widget = PedidosWidget(self)
        self.produtos_widget = ProdutosWidget(self)
        self.transportadoras_widget = TransportadorasWidget(self)
        self.config_widget = ConfigWidget(self)

        self.tab_widget.addTab(self.cotar_widget, "Cotar")
        self.tab_widget.addTab(self.result_widget, "Resultados")
        self.tab_widget.addTab(self.pedidos_widget, "Pedidos")
        self.tab_widget.addTab(self.produtos_widget, "Produtos")
        self.tab_widget.addTab(self.transportadoras_widget, "Transportadoras")
        self.tab_widget.addTab(self.config_widget, "Opções")

    def get_database_connection(self):
        return self.conn, self.cursor

    def get_transportadoras(self):
        return self.transportadoras

    def get_modalidades(self):
        return self.modalidades

    def get_state_abbreviations(self):
        return self.state_abbreviations

    def get_state_names(self):
        return self.state_names

    def get_session(self):
        return self.session

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
