import pandas as pd
from conectando_bd import conecting_database, desconecting_database

# Configuração do Banco
USER = "postgres"
PASSWORD = "dan313852*"
HOST = "localhost"
PORT = "5432"
DATABASE = "seu_banco"

def transform_data():
    print("Iniciando transformação dos dados...")

    engine = conecting_database(USER, PASSWORD, HOST, PORT, DATABASE)
    if engine is None:
        print("Falha na conexão com o banco. Encerrando...")
        return

    query = "SELECT * FROM stage_sihsus"
    df = pd.read_sql(query, engine)

    df = df.dropna()
    df["valor"] = df["valor"].astype(float).round(2)  # Converter para float e arredondar
    df["data_procedimento"] = pd.to_datetime(df["data_procedimento"])
    df.rename(columns={"cod_paciente": "id_paciente"}, inplace=True)

    df.to_sql("dados_transformados", engine, if_exists="replace", index=False, method="multi", chunksize=10000)
    print("Transformação concluída e dados inseridos na tabela final.")

    desconecting_database(engine)

if __name__ == "__main__":
    transform_data()
