from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox, QApplication, QScrollArea
from ui.widgets.cotar.mercos import Mercos
from ui.widgets.cotar.cepaberto import CepAberto

class CotarWidget(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.conn = main_window.conn
        self.cursor = main_window.cursor
        self.session = main_window.session
        self.mercos = Mercos(self.session, self.cursor, self.main_window)
        self.cepaberto = CepAberto()
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        entry_layout = QHBoxLayout()
        self.entry_id = QLineEdit(self)
        self.entry_id.setPlaceholderText("Enter order ID")
        self.button_check = QPushButton("Buscar", self)
        self.button_check.clicked.connect(self.check_quote)

        entry_layout.addWidget(self.entry_id)
        entry_layout.addWidget(self.button_check)
        main_layout.addLayout(entry_layout)

        self.entry_id.returnPressed.connect(self.button_check.click)

        # Scroll area for results
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget(self.scroll_area)
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)

        button_layout = QHBoxLayout()
        self.copy_button = QPushButton("Copiar(tudo)", self)
        self.copy_button.clicked.connect(self.copy_quote)
        self.copy_pedido_info_button = QPushButton("Copiar(cotação)", self)
        self.copy_pedido_info_button.clicked.connect(self.copy_pedido_info)

        button_layout.addWidget(self.copy_button)
        button_layout.addWidget(self.copy_pedido_info_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def check_quote(self):
        id_pedido = self.entry_id.text()
        if not id_pedido:
            QMessageBox.critical(self, "Erro", "Por favor, insira um ID de pedido.")
            return

        self.cursor.execute("SELECT * FROM pedidos WHERE id_pedido = ?", (id_pedido,))
        pedido = self.cursor.fetchone()

        if pedido is None:
            try:
                order_info = self.mercos.get_order_info(id_pedido)
                self.cursor.execute('''
                    INSERT OR REPLACE INTO pedidos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', order_info[:12])  # Inserir apenas os 12 primeiros valores
                self.conn.commit()
                pedido = order_info
            except ValueError as e:
                QMessageBox.critical(self, "Erro", str(e))
                return

        self.display_quote(id_pedido)
        self.main_window.result_widget.check_order(id_pedido)

    def display_quote(self, id_pedido):
        self.cursor.execute("SELECT * FROM pedidos WHERE id_pedido = ?", (id_pedido,))
        pedido = self.cursor.fetchone()

        if not pedido:
            raise ValueError(f"No order found with id {id_pedido}")

        # Clear previous content
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        nome_destinatario, cpf_remetente, cpf_destinatario, valor_nfe, cep, estado, cidade, endereco, volume, weight, measures = pedido[1:]
        self.cursor.execute("SELECT nome, quantidade FROM produtos_pedido JOIN produtos ON produtos_pedido.id_produto = produtos.id_produto WHERE id_pedido = ?", (id_pedido,))
        produtos_qtde = self.cursor.fetchall()
        produtos = [produto for produto, _ in produtos_qtde]
        qtde = [qtde for _, qtde in produtos_qtde]

        self.add_label(f"{' '.join(nome_destinatario.split())} - {id_pedido}", is_bold=True)
        self.add_label("Produto(s):")
        for produto, quantidade in zip(produtos, qtde):
            self.add_label(f"* {produto} - {quantidade}")

        self.add_label(f"\n{id_pedido}")
        self.add_label(f"*CPF/CNPJ Remetente:* {cpf_remetente}")
        self.add_label(f"*Nome Destinatário:* {nome_destinatario}")
        self.add_label(f"*CPF/CNPJ Destinatário:* {cpf_destinatario}")
        self.add_label(f"*Pagante:* CIF")
        self.add_label(f"*Valor da NFe:* {valor_nfe}")
        self.add_label(f"*CEP:* {cep}")
        self.add_label(f"*Estado:* {estado}")
        self.add_label(f"*Cidade:* {cidade}")
        self.add_label(f"*Endereço:* {endereco}")
        self.add_label(f"*Volumes:* {volume}")
        self.add_label(f"*Peso:* {weight:.2f} kg")
        self.add_label(f"*Medidas:*")
        self.add_label(f"* {measures}")
        self.add_label(f"*Obs:* Material plástico, em caixa.")

        self.cursor.execute("SELECT nome FROM transportadora WHERE id IN (SELECT id_transportadora FROM pedidos_transportadoras WHERE id_pedido = ?)", (id_pedido,))
        transportadoras = self.cursor.fetchall()
        self.add_label("\nTransportadoras que atendem o pedido:")
        for transportadora in transportadoras:
            self.add_label(f"* {transportadora[0]}")

    def add_label(self, text, is_bold=False):
        label = QLabel(text)
        if is_bold:
            label.setStyleSheet("font-weight: bold")
        self.scroll_layout.addWidget(label)

    def update_textbox(self, text):
        self.textbox.clear()
        self.textbox.setPlainText(text)

    def copy_quote(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.main_window.quotes[self.main_window.current_quote])

    def copy_pedido_info(self):
        id_pedido = self.entry_id.text()

        if 0 <= self.main_window.current_quote < len(self.main_window.quotes):
            quote = self.main_window.quotes[self.main_window.current_quote]
            lines = quote.split("\n")

            try:
                start_index = next(i for i, line in enumerate(lines) if line.startswith(f"{id_pedido}"))
                end_index = next(i for i, line in enumerate(lines) if line.startswith("*Obs:* Material plástico, em caixa.")) + 1
                pedido_info = "\n".join(lines[start_index:end_index])

                clipboard = QApplication.clipboard()
                clipboard.setText(pedido_info)
            except StopIteration:
                QMessageBox.critical(self, "Erro", "Não foi possível encontrar a informação completa do pedido.")
        else:
            QMessageBox.critical(self, "Erro", "Não há cotação atual para copiar.")