from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QDialog, QFormLayout, QLineEdit, QMessageBox
from PyQt5.QtCore import Qt

class TransportadorasWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.cursor = self.main_window.cursor
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Create the table to display transportadoras
        self.transportadoras_table = QTableWidget()
        self.transportadoras_table.setColumnCount(4)
        self.transportadoras_table.setHorizontalHeaderLabels(["ID", "Nome", "Estados", "Dias"])
        self.transportadoras_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.transportadoras_table.cellDoubleClicked.connect(self.edit_transportadora)

        layout.addWidget(self.transportadoras_table)

        # Create a button to refresh the table
        self.refresh_button = QPushButton("Atualizar")
        self.refresh_button.clicked.connect(self.populate_transportadoras_table)
        layout.addWidget(self.refresh_button)

        # Create a button to add a new transportadora
        self.add_transportadora_button = QPushButton("Novo")
        self.add_transportadora_button.clicked.connect(self.add_transportadora_window)
        layout.addWidget(self.add_transportadora_button)

        # Set the layout
        self.setLayout(layout)

        # Populate the table with transportadoras
        self.populate_transportadoras_table()

    def populate_transportadoras_table(self):
        # Clear the table
        self.transportadoras_table.setRowCount(0)

        # Get all fields
        self.main_window.cursor.execute("SELECT id, nome, estados, dias FROM transportadora")
        transportadoras_db = self.main_window.cursor.fetchall()

        # Add each transportadora to the table
        for transportadora in transportadoras_db:
            row_position = self.transportadoras_table.rowCount()
            self.transportadoras_table.insertRow(row_position)
            for column, item in enumerate(transportadora):
                self.transportadoras_table.setItem(row_position, column, QTableWidgetItem(str(item)))

    def edit_transportadora(self, row, column):
        # Get the selected transportadora data
        transportadora_data = [self.transportadoras_table.item(row, col).text() for col in range(self.transportadoras_table.columnCount())]

        # Open the edit transportadora dialog
        dialog = EditTransportadoraDialog(transportadora_data, self)
        if dialog.exec_() == QDialog.Accepted:
            self.update_transportadora(dialog.get_transportadora_data())

    def update_transportadora(self, transportadora_data):
        # Update the transportadora in the database
        self.main_window.cursor.execute("""
            UPDATE transportadora 
            SET nome = ?, estados = ?, dias = ? 
            WHERE id = ?
        """, (transportadora_data[1], transportadora_data[2], transportadora_data[3], transportadora_data[0]))
        self.conn.commit()

        # Update the table
        self.populate_transportadoras_table()

    def delete_transportadora(self, transportadora_id):
        # Ask for confirmation before deletion
        reply = QMessageBox.question(self, 'Confirmação', "Tem certeza que deseja apagar esta transportadora?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Delete the transportadora from the database
            self.main_window.cursor.execute("DELETE FROM transportadora WHERE id = ?", (transportadora_id,))
            self.conn.commit()
            # Update the table
            self.populate_transportadoras_table()

    def add_transportadora_window(self):
        # Open the add transportadora dialog
        dialog = AddTransportadoraDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.add_transportadora(dialog.get_transportadora_data())

    def add_transportadora(self, transportadora_data):
        # Add the transportadora to the database
        self.main_window.cursor.execute("""
            INSERT INTO transportadora (nome, estados, dias)
            VALUES (?, ?, ?)
        """, (transportadora_data[1], transportadora_data[2], transportadora_data[3]))
        self.conn.commit()

        # Update the table
        self.populate_transportadoras_table()


class EditTransportadoraDialog(QDialog):
    def __init__(self, transportadora_data, parent=None):
        super().__init__(parent)
        self.transportadora_data = transportadora_data
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()

        self.id = QLineEdit(self.transportadora_data[0])
        self.id.setReadOnly(True)
        layout.addRow("ID:", self.id)

        self.nome = QLineEdit(self.transportadora_data[1])
        layout.addRow("Nome:", self.nome)

        self.estados = QLineEdit(self.transportadora_data[2])
        layout.addRow("Estados:", self.estados)

        self.dias = QLineEdit(self.transportadora_data[3])
        layout.addRow("Dias:", self.dias)

        button_layout = QHBoxLayout()
        self.confirm_button = QPushButton("Confirmar")
        self.confirm_button.clicked.connect(self.accept)
        button_layout.addWidget(self.confirm_button)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addRow(button_layout)
        self.setLayout(layout)

    def get_transportadora_data(self):
        return [
            self.id.text(),
            self.nome.text(),
            self.estados.text(),
            self.dias.text()
        ]


class AddTransportadoraDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()

        self.nome = QLineEdit()
        layout.addRow("Nome:", self.nome)

        self.estados = QLineEdit()
        layout.addRow("Estados:", self.estados)

        self.dias = QLineEdit()
        layout.addRow("Dias:", self.dias)

        button_layout = QHBoxLayout()
        self.confirm_button = QPushButton("Confirmar")
        self.confirm_button.clicked.connect(self.accept)
        button_layout.addWidget(self.confirm_button)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addRow(button_layout)
        self.setLayout(layout)

    def get_transportadora_data(self):
        return [
            None,  # ID will be generated by the database
            self.nome.text(),
            self.estados.text(),
            self.dias.text()
        ]
