from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea, QFrame, QLabel, QMessageBox
from PyQt5.QtCore import Qt
from ui.widgets.result.quote_form import QuoteForm
from ui.widgets.result.result_display import ResultDisplay
import base64
import http.client
import json
import os
import re

class ResultWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.cursor = self.main_window.conn.cursor()
        self.current_order_id = None
        self.entry_widgets = {}
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        self.label_info = QLabel("Para ver os resultados de uma cotação, na aba 'Cotar'\ninsira o ID do pedido e clique em 'Buscar'.", self)
        self.label_info.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.label_info)

        self.frame_buttons_cotado = QFrame(self)
        button_layout = QHBoxLayout(self.frame_buttons_cotado)

        self.button_add = QPushButton("Adicionar", self)
        self.button_add.clicked.connect(self.create_extra_form)

        self.button_braspress = QPushButton("Braspress", self)
        self.button_braspress.clicked.connect(lambda: self.api_braspress(self.current_order_id))

        self.button_melhor_envio = QPushButton("Melhor Envio", self)
        self.button_melhor_envio.clicked.connect(lambda: self.api_melhor_envio(self.current_order_id))

        self.button_voltar = QPushButton("Voltar", self)

        button_layout.addWidget(self.button_add)
        button_layout.addWidget(self.button_braspress)
        button_layout.addWidget(self.button_melhor_envio)
        button_layout.addWidget(self.button_voltar)

        main_layout.addWidget(self.frame_buttons_cotado)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget(self.scroll_area)
        self.scroll_area.setWidget(self.scroll_content)

        self.scroll_layout = QVBoxLayout(self.scroll_content)
        main_layout.addWidget(self.scroll_area)

        self.result_display = ResultDisplay(self.main_window)
        main_layout.addWidget(self.result_display)

        self.setLayout(main_layout)

    def update_results(self, text):
        self.result_display.update_results(text)

    def check_order(self, order_id):
        self.current_order_id = order_id

        if hasattr(self, 'label_info'):
            self.label_info.deleteLater()
            del self.label_info

        if order_id is not None:
            self.main_window.cursor.execute("SELECT * FROM cotado WHERE id_pedido = ?", (order_id,))
            if self.main_window.cursor.fetchone() is not None:
                pass
        else:
            self.show_message("Info", "Nenhum pedido encontrado para este cliente.")
            return

        for widget in self.scroll_layout.children():
            widget.deleteLater()

        self.entry_widgets = {}

        self.main_window.cursor.execute("SELECT id_transportadora FROM pedidos_transportadoras WHERE id_pedido = ?", (order_id,))
        standard_transporters = [transportador[0] for transportador in self.main_window.cursor.fetchall()]

        self.main_window.cursor.execute("SELECT * FROM cotado WHERE id_pedido = ?", (order_id,))
        all_cotacoes = self.main_window.cursor.fetchall()

        default_cotacoes = [cotacao for cotacao in all_cotacoes if cotacao[1] in standard_transporters and cotacao[6] == 1]
        extra_cotacoes = [cotacao for cotacao in all_cotacoes if cotacao[1] in standard_transporters and cotacao[6] == 0]

        # Inicializar `i` antes do loop
        i = 0
        for i, transporter in enumerate(standard_transporters):
            cotacao = next((c for c in default_cotacoes if c[1] == transporter), None)
            self.create_quote_form(i, cotacao or (order_id, transporter, '', '', '', ''), is_default=True, all_cotacoes=all_cotacoes)

        extra_cotacoes += [cotacao for cotacao in all_cotacoes if cotacao[1] not in standard_transporters]

        for j, cotacao in enumerate(extra_cotacoes, start=i+1):
            self.create_quote_form(j, cotacao, is_default=False)

        self.update_results(order_id)

    def create_quote_form(self, index, cotacao, is_default, all_cotacoes=None):
        quote_form = QuoteForm(self.main_window, cotacao, index, is_default, all_cotacoes)
        self.scroll_layout.addWidget(quote_form)

    def create_extra_form(self):
        if self.current_order_id:
            i = len(self.entry_widgets)
            self.create_quote_form(i, (self.current_order_id, '', '', '', '', ''), is_default=False)

    def show_message(self, title, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()

    def api_braspress(self, order_id):
        id_pedido = order_id

        self.main_window.cursor.execute("SELECT * FROM cotado WHERE id_pedido = ? AND transportadora = ?", (id_pedido, 1))
        existing_quote = self.main_window.cursor.fetchone()

        if existing_quote is not None:
            proceed = QMessageBox.question(self, "Cotação existente", "Já existe uma cotação para este pedido. Deseja prosseguir mesmo assim?", QMessageBox.Yes | QMessageBox.No)
            if proceed == QMessageBox.No:
                return

        self.main_window.cursor.execute("SELECT cpf_remetente FROM pedidos WHERE id_pedido = ?", (id_pedido,))
        result = self.main_window.cursor.fetchone()

        if result is None:
            self.show_message("Erro", "CPF/CNPJ Remetente: não encontrado para o pedido atual.")
            return None

        cpf_remetente = re.sub(r'\D', '', result[0])

        self.main_window.cursor.execute("SELECT * FROM pedidos WHERE id_pedido = ?", (id_pedido,))
        order_data = self.main_window.cursor.fetchone()

        if order_data is None:
            self.show_message("Erro", f"Pedido {id_pedido} não encontrado.")
            return

        if cpf_remetente == os.getenv('CNPJ_1'):
            user = os.getenv('USUARIO_1')
            password = os.getenv('SENHA_1')
        elif cpf_remetente == os.getenv('CNPJ_2'):
            user = os.getenv('USUARIO_2')
            password = os.getenv('SENHA_2')
        else:
            self.show_message("Erro", f"CNPJ remetente {cpf_remetente} não encontrado no arquivo .env.")
            return

        credentials = base64.b64encode(f'{user}:{password}'.encode('utf-8')).decode('utf-8')

        headers = {
            'Authorization': 'Basic ' + credentials,
            'Content-Type': 'application/json',
        }

        id_pedido = order_data[0]
        cpf_remetente = int(re.sub(r'\D', '', order_data[2]))
        cpf_destinatario = int(re.sub(r'\D', '', order_data[3]))
        valor_nfe = float(order_data[4].replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.'))
        cep = int(re.sub(r'\D', '', order_data[5]))
        volume = order_data[9]
        weight = order_data[10]
        measures = order_data[11]

        comprimento, largura, altura = [float(dim.strip())/100 for dim in measures.split('x')]

        data = {
            'cnpjRemetente': cpf_remetente,
            'cnpjDestinatario': cpf_destinatario,
            'modal': 'R',
            'tipoFrete': "1",
            'cepOrigem': 95840000,
            'cepDestino': cep,
            'vlrMercadoria': valor_nfe,
            'peso': weight,
            'volumes': volume,
            'cubagem': [
                {
                    'altura': altura,
                    'largura': largura,
                    'comprimento': comprimento,
                    'volumes': volume
                }
            ]
        }

        conn = http.client.HTTPSConnection("api.braspress.com")
        conn.request("POST", "/v1/cotacao/calcular/json", body=json.dumps(data), headers=headers)
        response = conn.getresponse()

        if response.status == 200:
            response_data = json.loads(response.read().decode())
            valor = response_data['totalFrete']
            tempo = response_data['prazo']
            id_cotado = response_data['id']

            QMessageBox.information(self, "Cotação", f"Valor: {valor}\nTempo: {tempo}\nNúmero: {id_cotado}")

            self.main_window.cursor.execute("INSERT INTO cotado (id_pedido, transportadora, modalidade, valor, tempo, id_cotado, is_default) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (id_pedido, 1, 'Rodoviário', valor, tempo, id_cotado, 1))
            self.conn.commit()

            self.update_results(id_pedido)
            self.check_order(id_pedido)
        else:
            QMessageBox.critical(self, "Erro", f"Erro {response.status}\nText:\n{response.read().decode()}")

        conn.close()
    