class DatabaseInitializer:
    def __init__(self, conn):
        self.conn = conn
        self.cursor = self.conn.cursor()
        self.create_database()
        self.add_default_values()

    def create_database(self):
        # Check if the database is empty
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = self.cursor.fetchall()
        if len(tables) == 0:
            # List of CREATE TABLE statements
            tables = [
                """
                CREATE TABLE pedidos (
                    id_pedido TEXT PRIMARY KEY,
                    nome_destinatario TEXT,    
                    cpf_remetente TEXT,        
                    cpf_destinatario TEXT,     
                    valor_nfe TEXT,
                    cep TEXT,
                    estado TEXT,
                    cidade TEXT,
                    endereco TEXT,
                    volume INTEGER,
                    weight REAL,
                    measures TEXT
                )
                """,
                """
                CREATE TABLE transportadora (
                    id INTEGER PRIMARY KEY,
                    nome TEXT,
                    estados TEXT,
                    dias TEXT
                )
                """,
                """
                CREATE TABLE pedidos_transportadoras (
                    id_pedido TEXT,
                    id_transportadora INTEGER,
                    FOREIGN KEY (id_pedido) REFERENCES pedidos (id_pedido),
                    FOREIGN KEY (id_transportadora) REFERENCES transportadora (id),
                    PRIMARY KEY (id_pedido, id_transportadora)
                )
                """,
                """
                CREATE TABLE cotado (
                    id_pedido TEXT,
                    transportadora INTEGER,
                    modalidade TEXT,
                    valor REAL,
                    tempo INTEGER,
                    id_cotado TEXT,
                    is_default INTEGER,
                    UNIQUE(id_pedido, transportadora, modalidade)
                )
                """,
                """
                CREATE TABLE produtos_pedido (
                    id INTEGER PRIMARY KEY,
                    id_pedido TEXT,
                    id_produto INTEGER,
                    quantidade INTEGER,
                    FOREIGN KEY(id_pedido) REFERENCES pedidos(id_pedido),
                    FOREIGN KEY(id_produto) REFERENCES produtos(id_produto)
                )
                """,
                """
                CREATE TABLE produtos (
                    id_produto INTEGER PRIMARY KEY,
                    nome TEXT,
                    peso REAL,
                    medidas TEXT,
                    qtde_vol INTEGER
                )
                """
            ]

            # Execute each CREATE TABLE statement
            for table in tables:
                self.cursor.execute(table)

    def add_default_values(self):
        # Check if the transportadora table is empty
        self.cursor.execute("SELECT COUNT(*) FROM transportadora")
        if self.cursor.fetchone()[0] == 0:
            transportadoras = [
                (1, "Braspress", "AC,AL,AP,AM,BA,CE,DF,ES,GO,MA,MT,MS,MG,PA,PB,PR,PE,PI,RJ,RN,RS,RO,RR,SC,SP,SE,TO", "Terça,Quinta"),
                (2, "Sevex", "AC,AL,AP,AM,BA,CE,DF,ES,GO,MA,MT,MS,MG,PA,PB,PR,PE,PI,RJ,RN,RS,RO,RR,SC,SP,SE,TO", "Segunda,Terça,Quarta,Quinta,Sexta"),
                (3, "Rodonaves C", "AC,AM,DF,ES,GO,MT,MS,MG,PA,PR,RJ,RS,SC,SP,TO", "Quarta"),
                (4, "Rodonaves NH", "AC,AM,DF,ES,GO,MT,MS,MG,PA,PR,RJ,RS,SC,SP,TO", "Quarta"),
                (5, "Transito", "AC,AL,AP,AM,BA,CE,DF,ES,GO,MA,MT,MS,MG,PA,PB,PR,PE,PI,RJ,RN,RS,RO,RR,SC,SP,SE,TO", "Segunda,Quarta,Sexta"),
                (6, "São Miguel", "PR,RS,SC", "Quarta"),
                (7, "Leomar", "MG,PR,RS,SC,SP", "Segunda,Terça,Quarta,Quinta,Sexta"),
                (8, "Transduarte", "MG,RS,SC,SP", "Terça,Quarta,Sexta"),
                (9, "Mengue", "MG,PR,RS,SC,SP", "Quarta"),
                (10, "VitLog", "AC,AM,AP,DF,GO,MS,MT,PA,RO,RR,TO", "Segunda,Terça,Quarta,Quinta,Sexta")
            ]

            # Insert each transportadora into the transportadora table
            for transportadora in transportadoras:
                self.cursor.execute("INSERT INTO transportadora VALUES (?, ?, ?, ?)", transportadora)

        # Check if the produtos table is empty
        self.cursor.execute("SELECT COUNT(*) FROM produtos")
        if self.cursor.fetchone()[0] == 0:
            produtos = [
                (1, "SOUSPLAT PETIT ORLANDO", 0.15, "35 x 24 x 35", 40),
                (2, "SOUSPLAT PETIT FLORAL", 0.154, "35 x 24 x 35", 40),
                (3, "SOUSPLAT ORLANDO", 0.29, "35 x 24 x 35", 30),
                (4, "SOUSPLAT SATURNO", 0.266, "35 x 24 x 35", 40),
                (5, "SOUSPLAT LISO", 0.225, "35 x 24 x 35", 40),
                (6, "SOUSPLAT TRADICIONAL", 0.286, "35 x 24 x 35", 40),
                (7, "SOUSPLAT CARVALHO", 0.202, "35 x 24 x 35", 40),
                (8, "SOUSPLAT ARABESCO", 0.25, "35 x 24 x 35", 40),
                (9, "SOUSPLAT TRANÇADO", 0.25, "35 x 24 x 35", 40),
                (10, "SOUSPLAT GARDEN", 0.232, "35 x 24 x 35", 40),
                (11, "SOUSPLAT VERSALHES", 0.232, "35 x 24 x 35", 40)
            ]

            # Insert each produto into the produtos table
            for produto in produtos:
                self.cursor.execute("INSERT INTO produtos VALUES (?, ?, ?, ?, ?)", produto)

        self.conn.commit()
