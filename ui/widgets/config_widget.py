from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
import os

class ConfigWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Create a QTextEdit to display the .env file content
        self.text_edit = QTextEdit(self)
        self.load_config()
        layout.addWidget(self.text_edit)

        # Create a save button
        self.save_button = QPushButton("Salvar", self)
        self.save_button.clicked.connect(self.save_config)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def load_config(self):
        try:
            with open('.env', 'r') as file:
                data = file.read()
                self.text_edit.setPlainText(data)
        except FileNotFoundError:
            QMessageBox.warning(self, "Erro", "Arquivo .env não encontrado.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar o arquivo .env: {e}")

    def save_config(self):
        # Ask the user to confirm
        reply = QMessageBox.question(self, "Confirmação", "Você tem certeza que quer salvar essas alterações?\nQualquer informação incorreta pode interromper a autenticação do sistema.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return

        # Save the data to the .env file
        data = self.text_edit.toPlainText()
        try:
            with open('.env', 'w') as file:
                file.write(data)
            QMessageBox.information(self, "Sucesso", "Configurações salvas com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar o arquivo .env: {e}")
