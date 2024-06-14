import os
import requests

class CepAberto:
    def __init__(self):
        self.token = os.getenv('TOKEN_CEP')
        self.headers = {'Authorization': f'Token token={self.token}'}

    def get_address_by_cep(self, cep):
        url = f"https://www.cepaberto.com/api/v3/cep?cep={cep}"
        response = requests.get(url, headers=self.headers)
        data = response.json()
        cidade = data['cidade']['nome'] if 'cidade' in data and 'nome' in data['cidade'] else None
        estado_sigla = data['estado']['sigla'] if 'estado' in data and 'sigla' in data['estado'] else None
        estado = self.state_names.get(estado_sigla, estado_sigla)
        return cidade, estado
