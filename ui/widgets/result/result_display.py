from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit

class ResultDisplay(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.text_results = QTextEdit(self)
        self.text_results.setReadOnly(True)
        layout.addWidget(self.text_results)
        self.setLayout(layout)

    def update_results(self, pedido):
        self.main_window.cursor.execute("SELECT transportadora, id_cotado, modalidade, valor, tempo, is_default FROM cotado WHERE id_pedido = ?", (pedido,))
        results = self.main_window.cursor.fetchall()
        self.main_window.cursor.execute("SELECT nome_destinatario FROM pedidos WHERE id_pedido = ?", (pedido,))
        cliente = self.main_window.cursor.fetchone()[0]
        self.text_results.clear()
        self.text_results.insertPlainText(f"Resultado(s) para:\n{cliente} - {pedido}\n")
        results_by_transporter = {}
        for transportadora_id, id_cotacao, modalidade, valor, tempo, is_default in results:
            if transportadora_id not in results_by_transporter:
                results_by_transporter[transportadora_id] = {'default': [], 'extra': []}
            if is_default:
                results_by_transporter[transportadora_id]['default'].append((id_cotacao, modalidade, valor, tempo))
            else:
                results_by_transporter[transportadora_id]['extra'].append((id_cotacao, modalidade, valor, tempo))
        for transportadora_id, quotes in results_by_transporter.items():
            self.main_window.cursor.execute("SELECT nome FROM transportadora WHERE id = ?", (transportadora_id,))
            result = self.main_window.cursor.fetchone()
            transportadora_name = result[0] if result is not None else "Desconhecido"
            self.text_results.insertPlainText(f"\n*{transportadora_name}*:\n")
            for id_cotacao, modalidade, valor, tempo in quotes['default']:
                tempo_str = f"{tempo} dia útil.\n" if tempo == 1 else f"{tempo} dias úteis.\n"
                self.text_results.insertPlainText(f"{modalidade}\n{id_cotacao}\nR$ {valor}\n{tempo_str}")
            for id_cotacao, modalidade, valor, tempo in quotes['extra']:
                tempo_str = f"{tempo} dia útil.\n" if tempo == 1 else f"{tempo} dias úteis.\n"
                self.text_results.insertPlainText(f"{modalidade}\nR$ {valor}\n{tempo_str}")
