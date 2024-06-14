from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QDialog, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox, QMessageBox
from PyQt5.QtCore import Qt

class PedidosWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.cursor = self.main_window.cursor
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Create the table to display orders
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(12)
        self.orders_table.setHorizontalHeaderLabels(["ID", "Nome", "CPF Remetente", "CPF Destinatário", "Valor NFe", "CEP", "Estado", "Cidade", "Endereço", "Volume", "Peso", "Medidas"])
        self.orders_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.orders_table.cellDoubleClicked.connect(self.edit_order)

        layout.addWidget(self.orders_table)

        # Create a button to refresh the table
        self.refresh_button = QPushButton("Atualizar")
        self.refresh_button.clicked.connect(self.populate_orders_table)
        layout.addWidget(self.refresh_button)

        # Set the layout
        self.setLayout(layout)

        # Populate the table with orders
        self.populate_orders_table()

    def populate_orders_table(self):
        # Clear the table
        self.orders_table.setRowCount(0)

        # Get all fields
        self.main_window.cursor.execute("SELECT id_pedido, nome_destinatario, cpf_remetente, cpf_destinatario, valor_nfe, cep, estado, cidade, endereco, volume, weight, measures FROM pedidos")
        orders_db = self.main_window.cursor.fetchall()

        # Add each order to the table
        for order in orders_db:
            row_position = self.orders_table.rowCount()
            self.orders_table.insertRow(row_position)
            for column, item in enumerate(order):
                self.orders_table.setItem(row_position, column, QTableWidgetItem(str(item)))

    def edit_order(self, row, column):
        # Get the selected order data
        order_data = [self.orders_table.item(row, col).text() for col in range(self.orders_table.columnCount())]

        # Open the edit order dialog
        dialog = EditOrderDialog(order_data, self)
        if dialog.exec_() == QDialog.Accepted:
            self.update_order(dialog.get_order_data())

    def update_order(self, order_data):
        # Update the order in the database
        self.main_window.cursor.execute("""
            UPDATE pedidos 
            SET nome_destinatario = ?, cpf_remetente = ?, cpf_destinatario = ?, valor_nfe = ?, cep = ?, estado = ?, cidade = ?, endereco = ?, volume = ?, weight = ?, measures = ? 
            WHERE id_pedido = ?
        """, (order_data[1], order_data[2], order_data[3], order_data[4], order_data[5], order_data[6], order_data[7], order_data[8], order_data[9], order_data[10], order_data[11], order_data[0]))
        self.conn.commit()

        # Update the table
        self.populate_orders_table()

    def delete_order(self, order_id):
        # Ask for confirmation before deletion
        reply = QMessageBox.question(self, 'Confirmação', "Tem certeza que deseja apagar este pedido?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Delete the order from the database
            self.main_window.cursor.execute("DELETE FROM pedidos WHERE id_pedido = ?", (order_id,))
            # Delete the associated products from the database
            self.main_window.cursor.execute("DELETE FROM produtos_pedido WHERE id_pedido = ?", (order_id,))
            self.conn.commit()
            # Update the table
            self.populate_orders_table()


class EditOrderDialog(QDialog):
    def __init__(self, order_data, parent=None):
        super().__init__(parent)
        self.order_data = order_data
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()

        self.id_pedido = QLineEdit(self.order_data[0])
        self.id_pedido.setReadOnly(True)
        layout.addRow("ID Pedido:", self.id_pedido)

        self.nome_destinatario = QLineEdit(self.order_data[1])
        layout.addRow("Nome Destinatário:", self.nome_destinatario)

        self.cpf_remetente = QLineEdit(self.order_data[2])
        layout.addRow("CPF Remetente:", self.cpf_remetente)

        self.cpf_destinatario = QLineEdit(self.order_data[3])
        layout.addRow("CPF Destinatário:", self.cpf_destinatario)

        self.valor_nfe = QLineEdit(self.order_data[4])
        layout.addRow("Valor NFe:", self.valor_nfe)

        self.cep = QLineEdit(self.order_data[5])
        layout.addRow("CEP:", self.cep)

        self.estado = QLineEdit(self.order_data[6])
        layout.addRow("Estado:", self.estado)

        self.cidade = QLineEdit(self.order_data[7])
        layout.addRow("Cidade:", self.cidade)

        self.endereco = QLineEdit(self.order_data[8])
        layout.addRow("Endereço:", self.endereco)

        self.volume = QSpinBox()
        self.volume.setValue(int(self.order_data[9]))
        layout.addRow("Volume:", self.volume)

        self.peso = QDoubleSpinBox()
        self.peso.setValue(float(self.order_data[10]))
        layout.addRow("Peso:", self.peso)

        self.medidas = QLineEdit(self.order_data[11])
        layout.addRow("Medidas:", self.medidas)

        button_layout = QHBoxLayout()
        self.confirm_button = QPushButton("Confirmar")
        self.confirm_button.clicked.connect(self.accept)
        button_layout.addWidget(self.confirm_button)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addRow(button_layout)
        self.setLayout(layout)

    def get_order_data(self):
        return [
            self.id_pedido.text(),
            self.nome_destinatario.text(),
            self.cpf_remetente.text(),
            self.cpf_destinatario.text(),
            self.valor_nfe.text(),
            self.cep.text(),
            self.estado.text(),
            self.cidade.text(),
            self.endereco.text(),
            self.volume.value(),
            self.peso.value(),
            self.medidas.text(),
        ]
