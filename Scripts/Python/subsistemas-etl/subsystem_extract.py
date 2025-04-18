import time
import schedule
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
from conectando_bd import conecting_database, desconecting_database
from download_dados import downloadDadosSIHSUSparquet

# Configurações do Banco
USER = "postgres"
PASSWORD = "123,258D"
HOST = "localhost"
PORT = "5432"
DATABASE = "extract_test"

def obter_periodo_atual():
    data_atual = datetime.now()
    
    if data_atual.month == 1:
        mes_anterior = 12
        ano = data_atual.year - 1
    else:
        mes_anterior = data_atual.month - 1
        ano = data_atual.year
    
    return [ano], [mes_anterior]

# Configuração dos dados a serem baixados
GRUPO = 'RD'
UF = 'SP'
ANO, MES = obter_periodo_atual()
STAGE_PATH = "data/brutos/SIH/parquet"

# Função para extrair e carregar os dados no stage
def extract_and_load():
    print(f"Baixando dados para: Ano {ANO}, Mês {MES}")
    
    caminho_atual = f"{STAGE_PATH}\\{ANO[0]}"
    
    engine = conecting_database(USER, PASSWORD, HOST, PORT, DATABASE)
    if engine is None:
        print("Falha na conexão com o banco.")
        return

    download_parquet_files = downloadDadosSIHSUSparquet(GRUPO, 
        UF, ANO, MES, caminho_atual)
    
    df = download_parquet_files.to_dataframe()
        
    df.to_sql("stage_sihsus", engine, if_exists="append", 
        index=False, method="multi", chunksize=10000)

    desconecting_database(engine)
    print("Processo concluído!")

# Agendar a execução automática a cada X unidades de tempo.
schedule.every().minute.do(extract_and_load)

while True:
    schedule.run_pending()
    
    # Checa a cada 1 minuto
    time.sleep(60)  
