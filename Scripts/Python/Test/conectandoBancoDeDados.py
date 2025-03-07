from sqlalchemy import create_engine

def conecting_database(user, password, host, port, data_base):
    # URL de conexão
    url = f"postgresql://{user}:{password}@{host}:{port}/{data_base}"

    # Criar o engine
    engine = create_engine(url, isolation_level="AUTOCOMMIT")

    # Teste a conexão
    try:
        connection = engine.connect()
        print("Conexão bem-sucedida!")
    except Exception as e:
        print(f"Erro ao conectar: {e}")
        return None
    return connection

def desconecting_database(connection):
    connection.close()
    print("Conexão fechada!")
