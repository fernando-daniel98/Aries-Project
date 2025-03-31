import pandas as pd
import plotly.express as px

# Função para filtrar por CID específico
def filtrar_por_cid(df_diagnostico, lista_cids):
    """
    Filtra os diagnósticos que contêm os CIDs especificados.
    
    Parâmetros:
    df_diagnostico: DataFrame da dimensão diagnóstico
    lista_cids: Lista de códigos CID a serem filtrados
    
    Retorno:
    DataFrame filtrado apenas com os IDs de diagnóstico que correspondem aos CIDs
    """
    # Padronizar os CIDs da lista removendo pontos
    lista_cids_padronizados = [cid.replace(".", "") for cid in lista_cids]
    
    # Filtrar diagnósticos que correspondem à lista
    mask = df_diagnostico['DIAG_PRINC'].isin(lista_cids_padronizados)
    
    # Lista de todas as colunas possíveis de diagnóstico
    colunas_diagnostico = ['DIAG_SECUN', 'CID_ASSO', 'CID_MORTE', 
                          'DIAGSEC1', 'DIAGSEC2', 'DIAGSEC3', 'DIAGSEC4', 
                          'DIAGSEC5', 'DIAGSEC6', 'DIAGSEC7', 'DIAGSEC8', 'DIAGSEC9']
    
    # Verificar cada coluna de diagnóstico no DataFrame
    for col in colunas_diagnostico:
        if col in df_diagnostico.columns:
            mask = mask | df_diagnostico[col].isin(lista_cids_padronizados)
    
    return df_diagnostico[mask]

# Função para análise temporal
def analise_temporal(df_fato, df_tempo):
    """
    Realiza análise temporal das internações.
    
    Parâmetros:
    df_fato: DataFrame da tabela de fatos
    df_tempo: DataFrame da dimensão tempo
    
    Retorno:
    Gráfico de linha mostrando a evolução temporal das internações
    """
    analise = df_fato.merge(df_tempo, on='ID_TEMPO')
    
    # Criar uma série temporal com competência ANO/MÊS
    serie_temporal = analise.groupby(['ANO_CMPT', 'MES_CMPT']).size().reset_index(name='quantidade')
    serie_temporal['periodo'] = pd.to_datetime(serie_temporal['ANO_CMPT'].astype(str) + '-' + 
                                              serie_temporal['MES_CMPT'].astype(str).str.zfill(2) + '-01')
    
    # Plotar com plotly para interatividade
    fig = px.line(
        serie_temporal, 
        x='periodo', 
        y='quantidade',
        title='Evolução do Número de Internações',
        labels={'periodo': 'Período', 'quantidade': 'Número de Internações'},
        markers=True
    )
    
    # Melhorar formatação do eixo X
    fig.update_xaxes(
        dtick="M1",
        tickformat="%b\n%Y",
        ticklabelmode="period"
    )
    
    return fig

# Função para análise geográfica
def analise_geografica(df_fato, df_localizacao):
    """
    Realiza análise geográfica das internações por UF.
    
    Parâmetros:
    df_fato: DataFrame da tabela de fatos
    df_localizacao: DataFrame da dimensão localização
    
    Retorno:
    Gráfico de barras com a distribuição de internações por UF
    """
    analise = df_fato.merge(df_localizacao, on='ID_LOCALIZACAO')
    
    # Distribuição por UF
    por_uf = analise.groupby('UF_RES').agg(
        qtd_internacoes=('N_AIH', 'count'),
        valor_total=('VAL_TOT', 'sum'),
        valor_medio=('VAL_TOT', 'mean')
    ).reset_index().sort_values('qtd_internacoes', ascending=False)
    
    # Plotar com plotly
    fig = px.bar(
        por_uf,
        x='UF_RES',
        y='qtd_internacoes',
        title='Distribuição de Internações por UF de Residência',
        labels={'UF_RES': 'UF', 'qtd_internacoes': 'Número de Internações'},
        color='valor_medio',
        color_continuous_scale='Viridis',
        hover_data=['valor_total', 'valor_medio']
    )
    
    return fig

# Função para análise de diagnósticos
def analise_diagnosticos(df_fato, df_diagnostico):
    """
    Analisa a distribuição de diagnósticos principais.
    
    Parâmetros:
    df_fato: DataFrame da tabela de fatos
    df_diagnostico: DataFrame da dimensão diagnóstico
    
    Retorno:
    Gráfico de barras com os principais diagnósticos
    """
    analise = df_fato.merge(df_diagnostico, on='ID_DIAGNOSTICO')
    
    # Top 15 diagnósticos
    top_diagnosticos = analise['DIAG_PRINC'].value_counts().reset_index().head(15)
    top_diagnosticos.columns = ['CID', 'Quantidade']
    
    # Plotar com plotly
    fig = px.bar(
        top_diagnosticos,
        x='Quantidade',
        y='CID',
        title='Top 15 Diagnósticos Principais',
        labels={'Quantidade': 'Número de Internações', 'CID': 'Código CID'},
        orientation='h'
    )
    
    return fig

# Função para análise de custos
def analise_custos(df_fato, df_diagnostico=None, filtrar=False):
    """
    Analisa os custos das internações.
    
    Parâmetros:
    df_fato: DataFrame da tabela de fatos
    df_diagnostico: DataFrame da dimensão diagnóstico (opcional)
    filtrar: Indica se deve filtrar por diagnóstico
    
    Retorno:
    Gráfico de barras com os custos médios
    """
    if filtrar and df_diagnostico is not None:
        analise = df_fato.merge(df_diagnostico, on='ID_DIAGNOSTICO')
        grupo_por = 'GRUPO_DIAG_PRINC'
        titulo = 'Custo Médio por Grupo de Diagnóstico'
        x_label = 'Grupo Diagnóstico'
    else:
        analise = df_fato
        grupo_por = 'PASSOU_UTI'
        titulo = 'Custo Médio por Utilização de UTI'
        x_label = 'Passou por UTI'
    
    # Calcular custo médio
    custos = analise.groupby(grupo_por).agg(
        custo_medio=('VAL_TOT', 'mean'),
        dias_permanencia=('DIAS_PERMANENCIA', 'mean'),
        qtd=('N_AIH', 'count')
    ).reset_index()
    
    # Plotar com plotly
    fig = px.bar(
        custos,
        x=grupo_por,
        y='custo_medio',
        title=titulo,
        labels={grupo_por: x_label, 'custo_medio': 'Custo Médio (R$)'},
        color='dias_permanencia',
        hover_data=['qtd', 'dias_permanencia']
    )
    
    return fig

# Função para análise de desfechos
def analise_desfechos(df_fato, df_paciente):
    """
    Analisa os desfechos das internações (mortalidade).
    
    Parâmetros:
    df_fato: DataFrame da tabela de fatos
    df_paciente: DataFrame da dimensão paciente
    
    Retorno:
    Gráfico de barras com taxas de mortalidade por faixa etária
    """
    analise = df_fato.merge(df_paciente, on='ID_PACIENTE')
    
    # Calcular taxa de mortalidade por faixa etária
    mortalidade = analise.groupby('FAIXA_ETARIA').agg(
        mortes=('MORTE', 'sum'),
        total=('MORTE', 'count')
    ).reset_index()
    
    mortalidade['taxa_mortalidade'] = mortalidade['mortes'] / mortalidade['total'] * 100
    
    # Plotar com plotly
    fig = px.bar(
        mortalidade,
        x='FAIXA_ETARIA',
        y='taxa_mortalidade',
        title='Taxa de Mortalidade por Faixa Etária',
        labels={'FAIXA_ETARIA': 'Faixa Etária', 'taxa_mortalidade': 'Taxa de Mortalidade (%)'},
        color='taxa_mortalidade',
        color_continuous_scale='Reds',
        hover_data=['mortes', 'total']
    )
    
    return fig

# Função para consulta por CIDs específicos
def consulta_especifica_cid(df_fato, df_diagnostico, df_paciente, lista_cids, ano=None, mes=None):
    """
    Realiza uma consulta específica por CIDs de interesse.
    
    Parâmetros:
    df_fato: DataFrame da tabela de fatos
    df_diagnostico: DataFrame da dimensão diagnóstico
    df_paciente: DataFrame da dimensão paciente
    lista_cids: Lista de CIDs para filtrar
    ano: Ano específico para filtrar (opcional)
    mes: Mês específico para filtrar (opcional)
    
    Retorno:
    DataFrame com os resultados da consulta
    """
    
    # Filtrar os diagnósticos pelos CIDs de interesse
    diagnosticos_filtrados = filtrar_por_cid(df_diagnostico, lista_cids)
    
    # Juntar com a tabela de fatos
    resultado = df_fato.merge(diagnosticos_filtrados, on='ID_DIAGNOSTICO')
    
    # Removendo duplicatas baseado no ID único de internação
    resultado = resultado.drop_duplicates(subset=['N_AIH'])
    
    # Adicionar dados do paciente
    resultado = resultado.merge(df_paciente, on='ID_PACIENTE')
    
    # Filtrar por período específico, se informado
    if ano is not None:
        resultado = resultado[resultado['DT_INTER'].dt.year == ano]
    
    if mes is not None:
        resultado = resultado[resultado['DT_INTER'].dt.month == mes]
    
    # Selecionar colunas relevantes
    cols = ['N_AIH', 'DT_INTER', 'DT_SAIDA', 'DIAS_PERMANENCIA', 'DIAG_PRINC', 
            'FAIXA_ETARIA', 'DESC_SEXO', 'VAL_TOT', 'MORTE']
    
    if 'DESC_RACA_COR' in resultado.columns:
        cols.append('DESC_RACA_COR')
    
    resultado_final = resultado[cols].copy()
    
    # Adicionar algumas estatísticas agregadas
    stats = {
        'total_registros': len(resultado_final),
        'valor_total': resultado_final['VAL_TOT'].sum(),
        'permanencia_media': resultado_final['DIAS_PERMANENCIA'].mean(),
        'taxa_mortalidade': resultado_final['MORTE'].mean() * 100
    }
    
    return resultado_final, stats