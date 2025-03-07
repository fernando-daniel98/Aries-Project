class TabelaCheia:
    def __init__(self, nome_tabela):
        self.nome_tabela = nome_tabela
        self.colunas = [
            'ANO_CMPT', 'MES_CMPT', 'DT_INTER', 'DT_SAIDA', 'CEP', 'MUNIC_RES', 'MUNIC_MOV',
            'CGC_HOSP', 'CNES', 'NASC', 'SEXO', 'IDADE', 'COD_IDADE', 'NACIONAL', 'INSTRU',
            'RACA_COR', 'ETNIA', 'CBOR', 'MORTE', 'UTI_MES_TO', 'MARCA_UTI', 'VAL_UTI',
            'PROC_SOLIC', 'PROC_REA', 'VAL_SH', 'VAL_SP', 'N_AIH', 'VAL_TOT', 'INFEHOSP',
            'DIAG_PRINC', 'DIAG_SECUN', 'DIAGSEC1', 'DIAGSEC2', 'DIAGSEC3', 'DIAGSEC4',
            'DIAGSEC5', 'DIAGSEC6', 'DIAGSEC7', 'DIAGSEC8', 'DIAGSEC9', 'CID_MORTE', 'CID_ASSO'
        ]
        self.tipo_colunas = {
            'ANO_CMPT': sa.VARCHAR(4), 'MES_CMPT': sa.VARCHAR(2), 'DT_INTER': sa.VARCHAR(8),
            'DT_SAIDA': sa.VARCHAR(8), 'CEP': sa.VARCHAR(8), 'MUNIC_RES': sa.VARCHAR(6),
            'MUNIC_MOV': sa.VARCHAR(6), 'CGC_HOSP': sa.VARCHAR(16), 'CNES': sa.VARCHAR(7),
            'NASC': sa.VARCHAR(8), 'SEXO': sa.VARCHAR(1), 'IDADE': sa.NUMERIC(2),
            'COD_IDADE': sa.VARCHAR(1), 'NACIONAL': sa.VARCHAR(3), 'INSTRU': sa.VARCHAR(1),
            'RACA_COR': sa.VARCHAR(2), 'ETNIA': sa.VARCHAR(4), 'CBOR': sa.VARCHAR(6),
            'MORTE': sa.NUMERIC(1), 'UTI_MES_TO': sa.NUMERIC(3), 'MARCA_UTI': sa.VARCHAR(2),
            'VAL_UTI': sa.NUMERIC(9,2), 'PROC_SOLIC': sa.VARCHAR(10), 'PROC_REA': sa.VARCHAR(10),
            'VAL_SH': sa.NUMERIC(13,2), 'VAL_SP': sa.NUMERIC(13,2), 'N_AIH': sa.VARCHAR(13),
            'VAL_TOT': sa.NUMERIC(14,2), 'INFEHOSP': sa.VARCHAR(1), 'DIAG_PRINC': sa.VARCHAR(5),
            'DIAG_SECUN': sa.VARCHAR(5), 'DIAGSEC1': sa.VARCHAR(5), 'DIAGSEC2': sa.VARCHAR(5),
            'DIAGSEC3': sa.VARCHAR(5), 'DIAGSEC4': sa.VARCHAR(5), 'DIAGSEC5': sa.VARCHAR(5),
            'DIAGSEC6': sa.VARCHAR(5), 'DIAGSEC7': sa.VARCHAR(5), 'DIAGSEC8': sa.VARCHAR(5),
            'DIAGSEC9': sa.VARCHAR(5), 'CID_MORTE': sa.VARCHAR(5), 'CID_ASSO': sa.VARCHAR(5)
        }

    def __str__(self):
        return f'Tabela {self.nome_tabela}'

    def __repr__(self):
        return f'TabelaCheia({self.nome_tabela!r})'

    def cria_tabela(self, conn):
        
        metadata = sa.MetaData()
        
        try:
            metadata.reflect(bind=conn)
            
            if self.nome_tabela in metadata.tables:
                print(f'Tabela {self.nome_tabela} já existe.')
                return
            
            colunas = [sa.Column(nome, tipo) for nome, tipo in self.tipo_colunas.items()]
            tabela = sa.Table(self.nome_tabela, metadata, *colunas)
            tabela.create(conn)  # Remove o "with conn.begin()"
            print(f'Tabela {self.nome_tabela} criada com sucesso.')
        except sa.exc.SQLAlchemyError as e:
            print(f"Falha ao criar tabela: {str(e)}")
            if conn.in_transaction():  # Adiciona rollback condicional
                conn.rollback()


    def insere_dados(self, df: pd.DataFrame, conn):
        df.to_sql(self.nome_tabela, conn, if_exists='append', index=False, dtype=self.tipo_colunas)
        print(f'Dados inseridos na tabela {self.nome_tabela}.')

    def remove_tabela(self, conn):
        metadata = sa.MetaData(bind=conn)
        metadata.reflect()

        if self.nome_tabela not in metadata.tables:
            print(f'Tabela {self.nome_tabela} não existe.')
            return

        sa.Table(self.nome_tabela, metadata).drop(conn)
        print(f'Tabela {self.nome_tabela} removida com sucesso.')

class Dimensoes:
    def __init__(self, dimensao):
        self.lista_dimensoes = {
            'Dimensão Tempo': ['ANO_CMPT', 'MES_CMPT', 'DT_INTER', 'DT_SAIDA'],
            'Dimensão Localização': ['CEP', 'MUNIC_RES', 'MUNIC_MOV'],
            'Dimensão Hospital': ['CGC_HOSP', 'CNES'],
            'Dimensão Paciente': ['NASC', 'SEXO', 'IDADE', 'COD_IDADE', 'NACIONAL', 
                                  'INSTRU', 'RACA_COR', 'ETNIA', 'CBOR', 'MORTE'],
            'Dimensão UTI': ['UTI_MES_TO', 'MARCA_UTI', 'VAL_UTI'],
            'Dimensão Procedimento': ['PROC_SOLIC', 'PROC_REA', 'VAL_SH', 'VAL_SP', 
                                      'N_AIH', 'VAL_TOT', 'INFEHOSP'],
            'Dimensão Diagnóstico': ['DIAG_PRINC', 'DIAG_SECUN', 'DIAGSEC1', 'DIAGSEC2', 
                                     'DIAGSEC3', 'DIAGSEC4', 'DIAGSEC5', 'DIAGSEC6', 
                                     'DIAGSEC7', 'DIAGSEC8', 'DIAGSEC9', 'CID_MORTE', 'CID_ASSO']
        }
        
        if dimensao not in self.lista_dimensoes:
            raise ValueError('Dimensão inválida.')
        
        self.dimensao = dimensao
        self.colunas = self.lista_dimensoes[dimensao]

    def __str__(self):
        return f'Tabela de {self.dimensao}'
    
    def get_dimensao(self):
        return self.dimensao
    
    def get_colunas(self):
        return self.colunas
    
    def insere_dados(self, df, conn, namedb):
        """ Insere os dados da dimensão no banco de dados """
        if self.dimensao not in self.lista_dimensoes:
            raise ValueError('Essa tabela não é de dimensão conhecida.')

        dtype_map = {
            'VARCHAR': lambda x: sa.VARCHAR(x),
            'NUMERIC': lambda x, y=0: sa.NUMERIC(x, y)
        }
        
        tipos = {
            'Dimensão Tempo': {'ANO_CMPT': ('VARCHAR', 4), 'MES_CMPT': ('VARCHAR', 2),
                               'DT_INTER': ('VARCHAR', 8), 'DT_SAIDA': ('VARCHAR', 8)},
            'Dimensão Localização': {'CEP': ('VARCHAR', 8), 'MUNIC_RES': ('VARCHAR', 6),
                                     'MUNIC_MOV': ('VARCHAR', 6)},
            'Dimensão Hospital': {'CGC_HOSP': ('VARCHAR', 16), 'CNES': ('VARCHAR', 7)},
            'Dimensão Paciente': {'NASC': ('VARCHAR', 8), 'SEXO': ('VARCHAR', 1),
                                  'IDADE': ('NUMERIC', 2), 'COD_IDADE': ('VARCHAR', 1),
                                  'NACIONAL': ('VARCHAR', 3), 'INSTRU': ('VARCHAR', 1),
                                  'RACA_COR': ('VARCHAR', 2), 'ETNIA': ('VARCHAR', 4),
                                  'CBOR': ('VARCHAR', 6), 'MORTE': ('NUMERIC', 1)},
            'Dimensão UTI': {'UTI_MES_TO': ('NUMERIC', 3), 'MARCA_UTI': ('VARCHAR', 2),
                             'VAL_UTI': ('NUMERIC', 9, 2)},
            'Dimensão Procedimento': {'PROC_SOLIC': ('VARCHAR', 10), 'PROC_REA': ('VARCHAR', 10),
                                      'VAL_SH': ('NUMERIC', 13, 2), 'VAL_SP': ('NUMERIC', 13, 2),
                                      'N_AIH': ('VARCHAR', 13), 'VAL_TOT': ('NUMERIC', 14, 2),
                                      'INFEHOSP': ('VARCHAR', 1)},
            'Dimensão Diagnóstico': {'DIAG_PRINC': ('VARCHAR', 4), 'DIAG_SECUN': ('VARCHAR', 4),
                                     'DIAGSEC1': ('VARCHAR', 4), 'DIAGSEC2': ('VARCHAR', 4),
                                     'DIAGSEC3': ('VARCHAR', 4), 'DIAGSEC4': ('VARCHAR', 4),
                                     'DIAGSEC5': ('VARCHAR', 4), 'DIAGSEC6': ('VARCHAR', 4),
                                     'DIAGSEC7': ('VARCHAR', 4), 'DIAGSEC8': ('VARCHAR', 4),
                                     'DIAGSEC9': ('VARCHAR', 4), 'CID_MORTE': ('VARCHAR', 4),
                                     'CID_ASSO': ('VARCHAR', 4)}
        }

        df.to_sql(namedb, conn, if_exists='append', index=False, dtype={
            col: dtype_map[tipo[0]](*tipo[1:]) for col, tipo in tipos[self.dimensao].items()
        })
    
    def cria_tabela(self, conn, namedb):
        """ Cria a tabela no banco de dados se não existir """
        metadata = sa.MetaData()
        metadata.reflect(bind=conn)
        
        if namedb in metadata.tables:
            print(f'Tabela {namedb} já existe.')
            return
        
        tipos = {
            'Dimensão Tempo': [('ANO_CMPT', sa.VARCHAR(4)), ('MES_CMPT', sa.VARCHAR(2)),
                               ('DT_INTER', sa.VARCHAR(8)), ('DT_SAIDA', sa.VARCHAR(8))],
            'Dimensão Localização': [('CEP', sa.VARCHAR(8)), ('MUNIC_RES', sa.VARCHAR(6)),
                                     ('MUNIC_MOV', sa.VARCHAR(6))],
            'Dimensão Hospital': [('CGC_HOSP', sa.VARCHAR(16)), ('CNES', sa.VARCHAR(7))],
            'Dimensão Paciente': [('NASC', sa.VARCHAR(8)), ('SEXO', sa.VARCHAR(1)),
                                  ('IDADE', sa.NUMERIC(2)), ('COD_IDADE', sa.VARCHAR(1)),
                                  ('NACIONAL', sa.VARCHAR(3)), ('INSTRU', sa.VARCHAR(1)),
                                  ('RACA_COR', sa.VARCHAR(2)), ('ETNIA', sa.VARCHAR(4)),
                                  ('CBOR', sa.VARCHAR(6)), ('MORTE', sa.NUMERIC(1))],
        }
        
        tabela = sa.Table(
            namedb, sa.MetaData(),
            *[sa.Column(col, tipo) for col, tipo in tipos[self.dimensao]]
        )
        
        tabela.create(conn)
        print(f'Tabela {namedb} criada com sucesso.')

