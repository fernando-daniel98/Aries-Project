from pysus.ftp.databases.sih import SIH
import pandas as pd

# Função que recebe um grupo, uma uf, um ano, um mês e um path e retorna uma lista de arquivos baixados em parquet
def downloadDadosSIHSUSparquet(grupo, uf, ano, mes, path):
    sih = SIH().load()
    
    files = sih.get_files(grupo, uf, ano, mes)
        
    downloads = sih.download(files, local_dir=path)
    
    # return downloads

# Função que recebe uma lista de parquet e retorna uma lista de DataFrames
def downloadDadosSIHSUScsv(downloadParquet, path):
    dfs = []
    
    for parquet in downloadParquet:
        df = pd.read_parquet(parquet)
        dfs.append(df)
        
    for df in dfs:
        df.to_csv(f'{path}/{df}.csv', sep=';', encoding = 'ISO-8859-1', index=False)
        

# grupo = 'RD'
# uf = 'SP'
# ano = [2015]
# mes = [2]
# path = '/home/ferdanielinux/desktop-linux/scripts-python/proj-aries/Dados/parquet/teste'

# download = downloadDadosSIHSUS(grupo, uf, ano, mes, path)