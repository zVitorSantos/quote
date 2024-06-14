from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QComboBox, QLabel, QFrame, QMessageBox
from PyQt5.QtCore import Qt

class QuoteForm(QWidget):
    def __init__(self, main_window, cotacao, index, is_default, all_cotacoes=None):
        super().__init__()
        self.main_window = main_window
        self.cotacao = cotacao
        self.index = index
        self.is_default = is_default
        self.all_cotacoes = all_cotacoes
        self.entry_widgets = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        transportadora_name = ""
        id_pedido = None

        if self.is_default and self.cotacao is not None:
            id_pedido, transportadora_id, _, _, _, _, *_ = self.cotacao
            transportadora_name = self.get_transportadora_name(transportadora_id)
            if transportadora_name is not None:
                try:
                    transportadora_id = self.get_transportadora_id(transportadora_name)
                except ValueError:
                    print("ID do pedido inválido: {}".format(id_pedido))
                except Exception as e:
                    print("Erro ao acessar o banco de dados:", e)

        transportadora_widget = None
        if self.is_default:
            label_transportadora = QLabel(transportadora_name)
            label_transportadora.setAlignment(Qt.AlignCenter)
            layout.addWidget(label_transportadora)
            transportadora_widget = label_transportadora
        else:
            transportadora_var = QComboBox()
            transportadora_var.addItems(self.get_transportadora_list())
            layout.addWidget(transportadora_var)
            transportadora_widget = transportadora_var
            transportadora_var.currentIndexChanged.connect(self.update_transportadora_id)

        combobox_modalidade = QComboBox()
        combobox_modalidade.addItems(self.main_window.modalidades)
        layout.addWidget(combobox_modalidade)

        entry_valor = QLineEdit()
        entry_valor.setPlaceholderText("Insira o valor")  # Adiciona o placeholder
        layout.addWidget(entry_valor)

        entry_tempo = QLineEdit()
        entry_tempo.setPlaceholderText("Insira o tempo")  # Adiciona o placeholder
        layout.addWidget(entry_tempo)

        entry_id_cotacao = QLineEdit()
        entry_id_cotacao.setPlaceholderText("Insira o código da cotação")  # Adiciona o placeholder
        layout.addWidget(entry_id_cotacao)

        if self.cotacao is not None:
            _, transportadora_id, modalidade, valor, tempo, id_cotacao, *_ = self.cotacao
            transportadora_id = self.get_transportadora_id(transportadora_name)
            if isinstance(transportadora_widget, QComboBox):
                transportadora_widget.setCurrentText(transportadora_name)
            combobox_modalidade.setCurrentText(modalidade)
            entry_valor.setText(valor)
            entry_tempo.setText(tempo)
            entry_id_cotacao.setText(id_cotacao)

        transportadora_id = self.get_transportadora_id(transportadora_name)
        self.entry_widgets = {
            'pedido': id_pedido,
            'transportadora': transportadora_id,
            'modalidade': combobox_modalidade,
            'valor': entry_valor,
            'tempo': entry_tempo,
            'id_cotacao': entry_id_cotacao,
            'default': self.is_default
        }

        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        layout.addWidget(button_frame)

        button_submit = QPushButton("Enviar")
        button_submit.clicked.connect(lambda: self.submit_form(id_pedido))
        button_layout.addWidget(button_submit)

        button_delete = QPushButton("Apagar")
        button_delete.clicked.connect(lambda: self.delete_form(id_pedido))
        button_layout.addWidget(button_delete)

        self.setLayout(layout)

    def update_transportadora_id(self):
        transportadora_name = self.transportadora_var.currentText()
        self.main_window.cursor.execute("SELECT id FROM transportadora WHERE nome = ?", (transportadora_name,))
        result = self.main_window.cursor.fetchone()
        if result is not None:
            transportadora_id = result[0]
            if self.index in self.entry_widgets:
                self.entry_widgets[self.index]['transportadora'] = transportadora_id
            else:
                print(f"Formulário para a transportadora {self.index} não foi criado.")
        else:
            print(f"Transportadora '{transportadora_name}' não encontrada no banco de dados.")
            transportadora_id = None
            if self.index in self.entry_widgets:
                self.entry_widgets[self.index]['transportadora'] = transportadora_id

    def submit_form(self, pedido):
        widgets = self.entry_widgets
        transportadora_id = widgets['transportadora']
        id_cotado = widgets['id_cotacao'].text()
        is_default = widgets['default']
        modalidade = widgets['modalidade'].currentText()
        valor = widgets['valor'].text()
        tempo = widgets['tempo'].text()
        pedido = widgets['pedido']

        self.main_window.cursor.execute("SELECT * FROM cotado WHERE id_pedido = ? AND transportadora = ? AND modalidade = ?", (pedido, transportadora_id, modalidade))
        if self.main_window.cursor.fetchone() is not None:
            self.show_message("Informação", "Já existe uma cotação para esta transportadora com esta modalidade")
            return

        self.main_window.cursor.execute("SELECT * FROM cotado WHERE id_pedido = ? AND transportadora = ? AND modalidade = ?", (pedido, transportadora_id, modalidade))
        if self.main_window.cursor.fetchone() is not None:
            self.main_window.cursor.execute("UPDATE cotado SET modalidade = ?, valor = ?, tempo = ?, id_cotado = ?, is_default = ? WHERE id_pedido = ? AND transportadora = ? AND modalidade = ?",
                                (modalidade, valor, tempo, id_cotado, is_default, pedido, transportadora_id, modalidade))
        else:
            self.main_window.cursor.execute("INSERT INTO cotado (id_pedido, transportadora, modalidade, valor, tempo, id_cotado, is_default) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (pedido, transportadora_id, modalidade, valor, tempo, id_cotado, is_default))
        self.main_window.conn.commit()
        self.main_window.result_widget.update_results(pedido)

    def delete_form(self, pedido):
        widgets = self.entry_widgets
        transportadora_id = widgets['transportadora']
        if transportadora_id is None:
            print(f"ID da transportadora para o formulário não foi definido.")
            return

        self.main_window.cursor.execute("SELECT * FROM cotado WHERE id_pedido = ? AND transportadora = ?", (pedido, transportadora_id))
        if self.main_window.cursor.fetchone() is None:
            self.show_message("Informação", "Não há nada salvo para ser excluído.")
            return

        self.main_window.cursor.execute("DELETE FROM cotado WHERE id_pedido = ? AND transportadora = ?", (pedido, transportadora_id))
        self.main_window.conn.commit()
        widgets['modalidade'].setCurrentText('')
        widgets['valor'].clear()
        widgets['tempo'].clear()
        widgets['id_cotacao'].clear()
        self.main_window.result_widget.update_results(pedido)

    def get_transportadora_list(self):
        self.main_window.cursor.execute("SELECT nome FROM transportadora")
        return [row[0] for row in self.main_window.cursor.fetchall()]

    def get_transportadora_id(self, transportadora_name):
        if transportadora_name:
            self.main_window.cursor.execute("SELECT id FROM transportadora WHERE nome = ?", (transportadora_name,))
            result = self.main_window.cursor.fetchone()
            if result is not None:
                return result[0]
            else:
                print(f"Transportadora '{transportadora_name}' não encontrada no banco de dados.")
                return None
        else:
            return None

    def get_transportadora_name(self, transportadora_id):
        self.main_window.cursor.execute("SELECT nome FROM transportadora WHERE id = ?", (transportadora_id,))
        result = self.main_window.cursor.fetchone()
        if result is not None:
            return result[0]
        else:
            print(f"Transportadora com ID '{transportadora_id}' não encontrada no banco de dados.")
            return None

    def show_message(self, title, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()
