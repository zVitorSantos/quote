from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QDialog, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox, QMessageBox, QLabel
from PyQt5.QtCore import Qt
import math

class ProdutosWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.cursor = self.main_window.cursor
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Create the table to display products
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(5)
        self.products_table.setHorizontalHeaderLabels(["ID", "Nome", "Peso (g)", "Medidas (cm)", "Qtde/vol"])
        self.products_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.products_table.cellDoubleClicked.connect(self.edit_product)

        layout.addWidget(self.products_table)

        # Create a button to refresh the table
        self.refresh_button = QPushButton("Atualizar")
        self.refresh_button.clicked.connect(self.populate_products_table)
        layout.addWidget(self.refresh_button)

        # Create a button to add a new product
        self.add_product_button = QPushButton("Novo")
        self.add_product_button.clicked.connect(self.add_product_window)
        layout.addWidget(self.add_product_button)

        # Create the calculator frame
        self.calculator_frame = QWidget()
        self.calculator_layout = QVBoxLayout(self.calculator_frame)
        self.calculadora(self.calculator_layout)
        layout.addWidget(self.calculator_frame)

        # Set the layout
        self.setLayout(layout)

        # Populate the table with products
        self.populate_products_table()

    def populate_products_table(self):
        # Clear the table
        self.products_table.setRowCount(0)

        # Get all fields
        self.main_window.cursor.execute("SELECT id_produto, nome, peso, medidas, qtde_vol FROM produtos")
        products_db = self.main_window.cursor.fetchall()

        # Add each product to the table
        for product in products_db:
            row_position = self.products_table.rowCount()
            self.products_table.insertRow(row_position)
            for column, item in enumerate(product):
                self.products_table.setItem(row_position, column, QTableWidgetItem(str(item)))

    def edit_product(self, row, column):
        # Get the selected product data
        product_data = [self.products_table.item(row, col).text() for col in range(self.products_table.columnCount())]

        # Open the edit product dialog
        dialog = EditProductDialog(product_data, self)
        if dialog.exec_() == QDialog.Accepted:
            self.update_product(dialog.get_product_data())

    def update_product(self, product_data):
        # Update the product in the database
        self.main_window.cursor.execute("""
            UPDATE produtos 
            SET nome = ?, peso = ?, medidas = ?, qtde_vol = ? 
            WHERE id_produto = ?
        """, (product_data[1], product_data[2], product_data[3], product_data[4], product_data[0]))
        self.conn.commit()

        # Update the table
        self.populate_products_table()

    def delete_product(self, product_id):
        # Ask for confirmation before deletion
        reply = QMessageBox.question(self, 'Confirmação', "Tem certeza que deseja apagar este produto?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Delete the product from the database
            self.main_window.cursor.execute("DELETE FROM produtos WHERE id_produto = ?", (product_id,))
            self.conn.commit()
            # Update the table
            self.populate_products_table()

    def add_product_window(self):
        # Open the add product dialog
        dialog = AddProductDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.add_product(dialog.get_product_data())

    def add_product(self, product_data):
        # Add the product to the database
        self.main_window.cursor.execute("""
            INSERT INTO produtos (nome, peso, medidas, qtde_vol)
            VALUES (?, ?, ?, ?)
        """, (product_data[1], product_data[2], product_data[3], product_data[4]))
        self.conn.commit()

        # Update the table
        self.populate_products_table()

    def calculadora(self, layout):
        self.product_entries = []
        self.current_row = 1

        button_layout = QHBoxLayout()
        self.add_product_button = QPushButton("Adicionar")
        self.add_product_button.clicked.connect(self.add_product_entries)
        button_layout.addWidget(self.add_product_button)

        self.remove_product_button = QPushButton("Remover")
        self.remove_product_button.clicked.connect(self.remove_product_entries)
        button_layout.addWidget(self.remove_product_button)

        layout.addLayout(button_layout)

        self.add_product_entries()

        # Create the total weight and volumes entries
        self.weight_label = QLabel("Peso Total em kg")
        layout.addWidget(self.weight_label)
        self.weight_entry = QLineEdit()
        layout.addWidget(self.weight_entry)

        self.volumes_label = QLabel("Volumes Totais")
        layout.addWidget(self.volumes_label)
        self.volumes_entry = QLineEdit()
        layout.addWidget(self.volumes_entry)

        self.calculate_button = QPushButton("Calcular")
        self.calculate_button.clicked.connect(self.calculate)
        layout.addWidget(self.calculate_button)

    def add_product_entries(self):
        row_layout = QHBoxLayout()
        
        product_id_entry = QLineEdit()
        product_id_entry.setPlaceholderText("ID")
        row_layout.addWidget(product_id_entry)

        product_name_entry = QLineEdit()
        product_name_entry.setPlaceholderText("Nome")
        row_layout.addWidget(product_name_entry)

        product_weight_entry = QLineEdit()
        product_weight_entry.setPlaceholderText("Peso(Kg)")
        row_layout.addWidget(product_weight_entry)

        quantity_entry = QLineEdit()
        quantity_entry.setPlaceholderText("Qtde.")
        row_layout.addWidget(quantity_entry)

        products_per_volume_entry = QLineEdit()
        products_per_volume_entry.setPlaceholderText("Qtde. p/Vol.")
        row_layout.addWidget(products_per_volume_entry)

        self.calculator_layout.insertLayout(self.current_row, row_layout)
        self.product_entries.append([product_id_entry, product_name_entry, product_weight_entry, quantity_entry, products_per_volume_entry])

        self.current_row += 1

    def remove_product_entries(self):
        if len(self.product_entries) > 1:
            last_row = self.product_entries.pop()
            for widget in last_row:
                widget.deleteLater()
            self.current_row -= 1

    def calculate(self):
        total_weight = 0
        total_volumes = 0

        for product_entry in self.product_entries:
            if any(entry.text() == "" for entry in product_entry):
                QMessageBox.warning(self, "Informações faltando", "Por favor, preencha todas as informações do produto antes de calcular.")
                return

            product_weight = float(product_entry[2].text())
            quantity = float(product_entry[3].text())

            total_weight += product_weight * quantity

            products_per_volume = int(product_entry[4].text())
            volumes = quantity / products_per_volume

            if volumes % 1 > 0.15:
                volumes = math.ceil(volumes)
            else:
                volumes = math.floor(volumes)

            total_volumes += volumes

        self.weight_entry.setText(str(round(total_weight, 2)))
        self.volumes_entry.setText(str(total_volumes))


class EditProductDialog(QDialog):
    def __init__(self, product_data, parent=None):
        super().__init__(parent)
        self.product_data = product_data
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()

        self.id_produto = QLineEdit(self.product_data[0])
        self.id_produto.setReadOnly(True)
        layout.addRow("ID:", self.id_produto)

        self.nome = QLineEdit(self.product_data[1])
        layout.addRow("Nome:", self.nome)

        self.peso = QLineEdit(self.product_data[2])
        layout.addRow("Peso:", self.peso)

        self.medidas = QLineEdit(self.product_data[3])
        layout.addRow("Medidas:", self.medidas)

        self.qtde_vol = QLineEdit(self.product_data[4])
        layout.addRow("Qtde/vol:", self.qtde_vol)

        button_layout = QHBoxLayout()
        self.confirm_button = QPushButton("Confirmar")
        self.confirm_button.clicked.connect(self.accept)
        button_layout.addWidget(self.confirm_button)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addRow(button_layout)
        self.setLayout(layout)

    def get_product_data(self):
        return [
            self.id_produto.text(),
            self.nome.text(),
            self.peso.text(),
            self.medidas.text(),
            self.qtde_vol.text()
        ]


class AddProductDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()

        self.nome = QLineEdit()
        layout.addRow("Nome:", self.nome)

        self.peso = QLineEdit()
        layout.addRow("Peso:", self.peso)

        self.medidas = QLineEdit()
        layout.addRow("Medidas:", self.medidas)

        self.qtde_vol = QLineEdit()
        layout.addRow("Qtde/vol:", self.qtde_vol)

        button_layout = QHBoxLayout()
        self.confirm_button = QPushButton("Confirmar")
        self.confirm_button.clicked.connect(self.accept)
        button_layout.addWidget(self.confirm_button)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addRow(button_layout)
        self.setLayout(layout)

    def get_product_data(self):
        return [
            None,  # ID will be generated by the database
            self.nome.text(),
            self.peso.text(),
            self.medidas.text(),
            self.qtde_vol.text()
        ]
