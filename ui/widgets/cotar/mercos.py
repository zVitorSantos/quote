import os
from bs4 import BeautifulSoup
import PyPDF2
import re
from fuzzywuzzy import fuzz
import math
from PyQt5.QtWidgets import QMessageBox
from io import BytesIO

class Mercos:
    def __init__(self, session, cursor, main_window):
        self.session = session
        self.cursor = cursor
        self.main_window = main_window

    def login(self):
        username = os.getenv("usuario")
        password = os.getenv("senha")
        login_url = "https://app.mercos.com/login"
        payload = {
            "usuario": username,
            "senha": password
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = self.session.post(login_url, data=payload, headers=headers)
        if response.status_code != 200:
            raise ValueError("Login failed")

    def get_order_info(self, entry_id):
        self.login()
        order_status, soup = self.get_order_details(entry_id)
        if order_status == "Cancelado":
            raise ValueError("Pedido Cancelado")
        elif order_status in ["Concluído", "Em orçamento"]:
            order_link_element = soup.find('div', {'class': 'link-pedido'}).find('a')
            if order_link_element is None:
                raise ValueError("Não foi possível encontrar o link do pedido.")
            pdf_link = order_link_element.get('href').replace('detalhar', 'pdf')
            pdf_content = self.download_order_pdf(pdf_link)
            order_info = self.extract_order_info(entry_id, pdf_content)
            return order_info
        else:
            raise ValueError("O status do pedido é desconhecido.")

    def get_order_details(self, entry_id):
        order_details_url = f"https://app.mercos.com/359524/pedidos/?tipo_pesquisa=0&texto={entry_id}"
        response = self.session.get(order_details_url)
        if "Tela de login</h1>" in response.text:
            self.login()
            response = self.session.get(order_details_url)
        if response.status_code != 200:
            raise ValueError(f"Request failed with status {response.status_code}")
        soup = BeautifulSoup(response.text, 'html.parser')
        if soup.find('p', string='Não foi encontrado nenhum pedido.') is not None:
            raise ValueError(f"No order found with id {entry_id}")
        order_status_elements = soup.find_all('span', {'class': 'badge-pedido'})
        if not order_status_elements:
            raise ValueError("Cannot find order status")
        order_status = order_status_elements[-1].text.strip()
        return order_status, soup

    def download_order_pdf(self, pdf_link):
        base_url = 'https://app.mercos.com'
        pdf_link = base_url + pdf_link
        response = self.session.get(pdf_link)
        if response.status_code != 200:
            raise ValueError("Download failed")
        return response.content

    def extract_order_info(self, id_pedido, file_content):
        pdf = PyPDF2.PdfReader(BytesIO(file_content))
        text = pdf.pages[0].extract_text()

        produtos, qtde = self.extract_products_info(id_pedido, text)
        nome_destinatario, cpf_remetente, cpf_destinatario, endereco, cep, cidade, estado, valor_nfe = self.extract_personal_info(text)
        volume, peso, medidas = self.calc_volume_peso(produtos, qtde)

        necessary_fields = [
            nome_destinatario, cpf_remetente, cpf_destinatario, valor_nfe, cep, estado, cidade, endereco, volume, peso, medidas
        ]
        friendly_field_names = {
            "nome_destinatario": "Nome do Destinatário",
            "cpf_remetente": "CPF do Remetente",
            "cpf_destinatario": "CPF do Destinatário",
            "valor_nfe": "Valor da NFe",
            "cep": "CEP",
            "estado": "Estado",
            "cidade": "Cidade",
            "endereco": "Endereço",
            "volume": "Volume",
            "peso": "Peso",
            "measures": "Medidas"
        }

        missing_fields = [friendly_field_names[field] for field, value in zip(friendly_field_names.keys(), necessary_fields) if not value]
        if missing_fields:
            QMessageBox.critical(self.main_window, "Erro", f"Campos necessários faltando:\n{', '.join(missing_fields)}")
            return

        transportadoras = self.get_transportadoras(estado)
        for transportadora in transportadoras:
            id_transportadora, _ = transportadora
            self.cursor.execute('SELECT * FROM pedidos_transportadoras WHERE id_pedido = ? AND id_transportadora = ?', (id_pedido, id_transportadora))
            if not self.cursor.fetchone():
                self.cursor.execute('INSERT INTO pedidos_transportadoras (id_pedido, id_transportadora) VALUES (?, ?)', (id_pedido, id_transportadora))

        self.cursor.execute('''
            INSERT OR REPLACE INTO pedidos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (id_pedido, nome_destinatario, cpf_remetente, cpf_destinatario, valor_nfe, cep, estado, cidade, endereco, volume, peso, medidas))

        self.main_window.conn.commit()

        return id_pedido, nome_destinatario, cpf_remetente, cpf_destinatario, valor_nfe, cep, estado, cidade, endereco, volume, peso, medidas, produtos, qtde

    def extract_products_info(self, id_pedido, text):
        lines = text.split('\n')
        produtos, qtde = [], []
        self.cursor.execute("SELECT id_produto, nome FROM produtos")
        produtos_db = self.cursor.fetchall()
        produtos_db.sort(key=lambda x: len(x[1]), reverse=True)

        for i in range(len(lines)):
            if lines[i].strip() == '-':
                produto = re.sub(r' - \d{11,}', ' ', lines[i + 1]).strip()
                quantidade = None
                for j in range(i + 2, len(lines)):
                    line = lines[j].strip()
                    if line.isdigit() and not lines[j - 1].strip().isdigit() and len(line) != 13:
                        quantidade = line
                        break
                    if not line.isdigit() or len(line) != 13:
                        produto += ' ' + line
                produto = produto.replace("-", "").strip()
                produtos.append(produto)
                qtde.append(quantidade if quantidade and len(quantidade) <= 10 else '0')

                id_produto = next((id for id, nome in produtos_db if nome in produto), None)
                if id_produto:
                    self.cursor.execute('SELECT * FROM produtos_pedido WHERE id_pedido = ? AND id_produto = ?', (id_pedido, id_produto))
                    if not self.cursor.fetchone():
                        self.cursor.execute('INSERT INTO produtos_pedido (id_pedido, id_produto, quantidade) VALUES (?, ?, ?)', (id_pedido, id_produto, quantidade))

        return produtos, qtde

    def extract_personal_info(self, text):
        patterns = {
            'nome_destinatario': r'Cliente:\n([^\n]+)',
            'cpf_remetente': r'(maggiore|brilha natal|verytel)',
            'endereco': r'Endereço:\n([^\n]+)',
            'cidade': r'Cidade:\n([^\n]+)',
            'estado': r'Estado:\n([^\n]+)',
            'valor_nfe': r'Valor total:\n([^\n]+)|Valor total em produtos:\n([^\n]+)',
            'cpf_destinatario': r'\d{3}\.\d{3}\.\d{3}-\d{2}|\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}',
            'cep': r'\d{5}-\d{3}'
        }

        def extract(pattern, text, group=1):
            match = re.search(pattern, text)
            if match:
                return match.group(group) if match.lastindex and group <= match.lastindex else match.group(0)
            return None

        nome_destinatario = extract(patterns['nome_destinatario'], text)
        endereco = extract(patterns['endereco'], text)
        cidade = extract(patterns['cidade'], text)
        estado = extract(patterns['estado'], text)
        valor_nfe = extract(patterns['valor_nfe'], text, 1) or extract(patterns['valor_nfe'], text, 2)
        cpf_destinatario = extract(patterns['cpf_destinatario'], text)
        cep = extract(patterns['cep'], text)
        if cep:
            cep = cep.replace('-', '')
            if not cidade or not estado:
                cidade, estado = self.main_window.cepaberto.get_location(cep)

        empresa = text.lower()
        if 'maggiore' in empresa:
            cpf_remetente = '24.914.470/0001-29'
        elif 'brilha natal' in empresa:
            cpf_remetente = '00.699.893/0001-05'
        elif 'verytel' in empresa:
            cpf_remetente = '21.214.067/0001-07'
        else:
            cpf_remetente = 'Indefinida'

        return nome_destinatario, cpf_remetente, cpf_destinatario, endereco, cep, cidade, estado, valor_nfe

    def get_transportadoras(self, estado):
        estado = self.main_window.state_abbreviations.get(estado, estado)
        if estado:
            self.cursor.execute('SELECT id, nome FROM transportadora WHERE estados LIKE ?', ('%' + estado + '%',))
        else:
            QMessageBox.critical(self.main_window, "Erro", "Estado is None")
        return self.cursor.fetchall()

    def calc_volume_peso(self, produtos, qtde):
        total_volume, total_weight, medidas = 0, 0, None
        unknown_products = []

        self.cursor.execute("SELECT id_produto, nome, peso, medidas, qtde_vol FROM produtos")
        produtos_db = self.cursor.fetchall()

        for produto, quantidade in zip(produtos, qtde):
            quantidade = int(quantidade)
            best_match_info = max(
                ((id_produto_db, nome_db, peso_db, medidas_db, unidades_por_volume_db)
                 for id_produto_db, nome_db, peso_db, medidas_db, unidades_por_volume_db in produtos_db
                 if any(keyword in produto.lower() for keyword in nome_db.lower().split())),
                key=lambda x: fuzz.ratio(produto.lower(), x[1].lower()), default=None)

            if best_match_info:
                _, nome_db, peso_db, medidas_db, unidades_por_volume_db = best_match_info
                if nome_db.lower() in produto.lower():
                    volume = math.ceil(quantidade / unidades_por_volume_db)
                    weight = quantidade * peso_db
                    total_volume += volume
                    total_weight += weight
                    medidas = medidas_db or medidas
                else:
                    unknown_products.append(produto)
            else:
                unknown_products.append(produto)

        return total_volume, total_weight, medidas
