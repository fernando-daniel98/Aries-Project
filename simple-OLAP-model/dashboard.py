import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Dashboard SIH/SUS", 
    page_icon="🏥", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Listas de CIDs por doença de interesse
cid10_interesse_sepse = [
    "A021", "A039", "A207", "A217", "A227", "A239", "A241", "A267", 
    "A280", "A282", "A327", "A392", "A393", "A394", "A40", "A400", 
    "A401", "A402", "A403", "A408", "A409", "A41", "A410", "A411", 
    "A412", "A413", "A414", "A415", "A418", "A419", "A427", "B007", 
    "B377", "P352", "P36", "P360", "P361", "P362", "P363", "P364", 
    "P365", "P368", "P369", "P372", "P375"
]

cid10_interesse_pneumonias_bacterianas = [
    "J13", "J14", "J150", "J151", "J152", "J153", "J154", "J155", 
    "J156", "J157", "J158", "J159", "J16", "J160", "J168", "J170", 
    "J178", "J180", "J181", "J182", "J188", "J189", "J851", "P231", 
    "P232", "P233", "P234", "P235", "P236", "P238", "P239", "J860", "J869"
]

cid10_interesse_infeccao_trato_urinario = [
    "N080", "N110", "N111", "N151", "N300", "N301", "N302", "N308", 
    "N340", "N390", "O233", "O234", "O239", "O862", "O863", "P393"
]

# Dicionário com informações sobre as doenças de interesse
DOENCAS_INTERESSE = {
    "Sepse": {
        "nome": "Sepse",
        "cids": cid10_interesse_sepse,
        "descricao": "Infecção generalizada com potencial risco de vida, caracterizada por resposta inflamatória sistêmica."
    },
    "Pneumonia Bacteriana": {
        "nome": "Pneumonia Bacteriana",
        "cids": cid10_interesse_pneumonias_bacterianas,
        "descricao": "Infecção do parênquima pulmonar causada por agentes bacterianos."
    },
    "Infecção do Trato Urinário": {
        "nome": "Infecção do Trato Urinário (ITU)",
        "cids": cid10_interesse_infeccao_trato_urinario,
        "descricao": "Infecção que afeta qualquer parte do sistema urinário, incluindo rins, ureteres, bexiga e uretra."
    }
}

# Função para carregar os dados
@st.cache_data
def carregar_dados():
    """
    Carrega os dados processados do SIH de arquivos CSV.
    Utiliza cache para melhor performance.
    """
    base_dir = r'c:\Users\Fernando\Documents\CEPID - Projeto ARIES\Aries-Project\data\processados\SIH'
    
    fato = pd.read_csv(f'{base_dir}/fato_internacao.csv', sep=';')
    dim_tempo = pd.read_csv(f'{base_dir}/dim_tempo.csv', sep=';')
    dim_paciente = pd.read_csv(f'{base_dir}/dim_paciente.csv', sep=';')
    dim_hospital = pd.read_csv(f'{base_dir}/dim_hospital.csv', sep=';')
    dim_localizacao = pd.read_csv(f'{base_dir}/dim_localizacao.csv', sep=';')
    dim_diagnostico = pd.read_csv(f'{base_dir}/dim_diagnostico.csv', sep=';')
    dim_procedimento = pd.read_csv(f'{base_dir}/dim_procedimento.csv', sep=';')
    
    # Converter datas
    fato['DT_INTER'] = pd.to_datetime(fato['DT_INTER'])
    fato['DT_SAIDA'] = pd.to_datetime(fato['DT_SAIDA'])
    
    return {
        'fato': fato,
        'dim_tempo': dim_tempo,
        'dim_paciente': dim_paciente,
        'dim_hospital': dim_hospital,
        'dim_localizacao': dim_localizacao,
        'dim_diagnostico': dim_diagnostico,
        'dim_procedimento': dim_procedimento
    }

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

# Interface principal
def main():
    """
    Função principal que constrói a interface do dashboard.
    """
    # Título principal
    st.title("🏥 Dashboard de Análise de Internações SUS")
    st.markdown("### Modelo Dimensional OLAP para dados do SIH/SUS")
    
    # Carregar dados
    with st.spinner('Carregando dados...'):
        data = carregar_dados()
    
    # Barra lateral para configurações
    st.sidebar.header("Configurações")
    
    # Menu de navegação
    menu = st.sidebar.radio(
        "Selecione a análise:",
        ["Visão Geral", "Análise Temporal", "Análise Geográfica", 
         "Análise de Diagnósticos", "Análise de Custos", "Análise de Desfechos",
         "Consulta por Doença Específica"]  # Renomeado para refletir a nova funcionalidade
    )
    
    # Estatísticas gerais sempre mostradas no topo
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric(
            label="Total de Internações", 
            value=f"{len(data['fato']):,}"
        )
        
        # Format value based on magnitude (thousands, millions, billions)
        valor_total = data['fato']['VAL_TOT'].sum()
        if valor_total >= 1e9:  # billions
            valor_formatado = f"R$ {valor_total/1e9:.1f} B"
        elif valor_total >= 1e6:  # millions
            valor_formatado = f"R$ {valor_total/1e6:.1f} M"
        elif valor_total >= 1e3:  # thousands
            valor_formatado = f"R$ {valor_total/1e3:.1f} K"
        else:
            valor_formatado = f"R$ {valor_total:.2f}"

        col2.metric(
            label="Valor Total", 
            value=valor_formatado
        )
        
        col3.metric(
            label="Permanência Média", 
            value=f"{data['fato']['DIAS_PERMANENCIA'].mean():.1f} dias"
        )
        
        col4.metric(
            label="Taxa de Mortalidade", 
            value=f"{(data['fato']['MORTE'].mean() * 100):.2f}%"
        )
    
    st.markdown("---")
    
    # Renderizar diferentes seções com base na seleção do menu
    if menu == "Visão Geral":
        st.header("Visão Geral dos Dados")
        
        # Distribuir alguns gráficos na página
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico temporal simplificado
            fig_temporal = analise_temporal(data['fato'], data['dim_tempo'])
            st.plotly_chart(fig_temporal, use_container_width=True)
        
        with col2:
            # Gráfico de desfechos
            fig_desfechos = analise_desfechos(data['fato'], data['dim_paciente'])
            st.plotly_chart(fig_desfechos, use_container_width=True)
            
        # Gráfico de diagnósticos
        fig_diag = analise_diagnosticos(data['fato'], data['dim_diagnostico'])
        st.plotly_chart(fig_diag, use_container_width=True)
        
        # Exibir algumas informações de contexto
        st.markdown("""
        ### Sobre os dados
        
        Este dashboard apresenta análises de internações hospitalares registradas no SIH/SUS.
        O modelo dimensional permite a exploração multidimensional dos dados, facilitando
        a identificação de padrões e tendências nas internações hospitalares.
        
        Use o menu lateral para navegar entre diferentes análises.
        """)
    
    elif menu == "Análise Temporal":
        st.header("Análise Temporal")
        
        # Opções de filtro de período
        st.sidebar.subheader("Filtros de Tempo")
        anos_disponiveis = sorted(data['fato']['DT_INTER'].dt.year.unique())
        ano_selecionado = st.sidebar.selectbox("Selecione o ano:", anos_disponiveis, index=len(anos_disponiveis)-1)
        
        # Filtrar por ano selecionado
        fato_filtrado = data['fato'][data['fato']['DT_INTER'].dt.year == ano_selecionado]
        
        # Gráfico principal temporal
        fig_temporal = analise_temporal(fato_filtrado, data['dim_tempo'])
        st.plotly_chart(fig_temporal, use_container_width=True)
        
        # Gráficos adicionais
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribuição por dia da semana
            fato_filtrado['dia_semana'] = fato_filtrado['DT_INTER'].dt.day_name()
            dias_semana = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            dias_ptbr = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
            
            mapping_dias = dict(zip(dias_semana, dias_ptbr))
            fato_filtrado['dia_semana_ptbr'] = fato_filtrado['dia_semana'].map(mapping_dias)
            
            contagem_dias = fato_filtrado['dia_semana_ptbr'].value_counts().reindex(dias_ptbr)
            
            fig_dias = px.bar(
                x=contagem_dias.index, 
                y=contagem_dias.values,
                title="Internações por Dia da Semana",
                labels={'x': 'Dia da Semana', 'y': 'Número de Internações'}
            )
            st.plotly_chart(fig_dias, use_container_width=True)
            
        with col2:
            # Duração média das internações por mês
            duracao_por_mes = fato_filtrado.groupby(fato_filtrado['DT_INTER'].dt.month).agg(
                permanencia_media=('DIAS_PERMANENCIA', 'mean')
            ).reset_index()
            duracao_por_mes.columns = ['Mês', 'Permanência Média']
            
            # Mapear nomes dos meses
            meses_ptbr = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            duracao_por_mes['Nome Mês'] = duracao_por_mes['Mês'].apply(lambda x: meses_ptbr[x-1])
            
            fig_duracao = px.line(
                duracao_por_mes,
                x='Nome Mês',
                y='Permanência Média',
                title=f"Permanência Média por Mês ({ano_selecionado})",
                markers=True
            )
            
            # Configurar ordem dos meses no eixo X
            fig_duracao.update_layout(
                xaxis = dict(
                    categoryorder = 'array',
                    categoryarray = meses_ptbr
                )
            )
            
            st.plotly_chart(fig_duracao, use_container_width=True)
    
    elif menu == "Análise Geográfica":
        st.header("Análise Geográfica")
        
        # Mapa ou visualização geográfica
        fig_geo = analise_geografica(data['fato'], data['dim_localizacao'])
        st.plotly_chart(fig_geo, use_container_width=True)
        
        # Tabela com dados por UF
        st.subheader("Dados detalhados por UF")
        
        analise_geo = data['fato'].merge(data['dim_localizacao'], on='ID_LOCALIZACAO')
        dados_uf = analise_geo.groupby('UF_RES').agg(
            internacoes=('N_AIH', 'count'),
            valor_total=('VAL_TOT', 'sum'),
            valor_medio=('VAL_TOT', 'mean'),
            permanencia_media=('DIAS_PERMANENCIA', 'mean'),
            mortalidade=('MORTE', 'mean')
        ).reset_index()
        
        # Formatar valores
        dados_uf['valor_total'] = dados_uf['valor_total'].map('R$ {:,.2f}'.format)
        dados_uf['valor_medio'] = dados_uf['valor_medio'].map('R$ {:,.2f}'.format)
        dados_uf['permanencia_media'] = dados_uf['permanencia_media'].map('{:.1f} dias'.format)
        dados_uf['mortalidade'] = (dados_uf['mortalidade'] * 100).map('{:.2f}%'.format)
        
        # Renomear colunas
        dados_uf.columns = ['UF', 'Internações', 'Valor Total', 'Valor Médio', 'Permanência Média', 'Taxa de Mortalidade']
        
        # Exibir tabela
        st.dataframe(dados_uf, use_container_width=True)
    
    elif menu == "Análise de Diagnósticos":
        st.header("Análise de Diagnósticos")
        
        # Gráfico principal de diagnósticos
        fig_diag = analise_diagnosticos(data['fato'], data['dim_diagnostico'])
        st.plotly_chart(fig_diag, use_container_width=True)
        
        # Filtros para análise mais específica
        st.sidebar.subheader("Filtros de Diagnóstico")
        grupos_diagnostico = sorted(data['dim_diagnostico']['GRUPO_DIAG_PRINC'].dropna().unique())
        grupo_selecionado = st.sidebar.selectbox("Selecione o grupo diagnóstico:", grupos_diagnostico)
        
        # Filtrar por grupo diagnóstico
        diagnosticos_filtrados = data['dim_diagnostico'][
            data['dim_diagnostico']['GRUPO_DIAG_PRINC'] == grupo_selecionado
        ]
        fato_filtrado = data['fato'].merge(diagnosticos_filtrados, on='ID_DIAGNOSTICO')
        
        # Análises adicionais
        col1, col2 = st.columns(2)
        
        with col1:
            # Permanência média por diagnóstico no grupo selecionado
            permanencia_por_diag = fato_filtrado.groupby('DIAG_PRINC').agg(
                permanencia_media=('DIAS_PERMANENCIA', 'mean'),
                contagem=('N_AIH', 'count')
            ).reset_index()
            
            # Filtrar apenas os mais frequentes
            top_diags = permanencia_por_diag[permanencia_por_diag['contagem'] > 5].sort_values('contagem', ascending=False).head(10)
            
            fig_perm = px.bar(
                top_diags,
                x='DIAG_PRINC',
                y='permanencia_media',
                title=f"Permanência Média dos Principais Diagnósticos (Grupo {grupo_selecionado})",
                color='contagem',
                labels={'DIAG_PRINC': 'CID', 'permanencia_media': 'Permanência Média (dias)', 'contagem': 'Quantidade'},
                hover_data=['contagem']
            )
            st.plotly_chart(fig_perm, use_container_width=True)
        
        with col2:
            # Taxa de mortalidade por diagnóstico no grupo selecionado
            mortalidade_por_diag = fato_filtrado.groupby('DIAG_PRINC').agg(
                mortes=('MORTE', 'sum'),
                total=('MORTE', 'count')
            ).reset_index()
            mortalidade_por_diag['taxa_mortalidade'] = mortalidade_por_diag['mortes'] / mortalidade_por_diag['total'] * 100
            
            # Filtrar apenas os mais frequentes
            top_mort = mortalidade_por_diag[mortalidade_por_diag['total'] > 5].sort_values('taxa_mortalidade', ascending=False).head(10)
            
            fig_mort = px.bar(
                top_mort,
                x='DIAG_PRINC',
                y='taxa_mortalidade',
                title=f"Taxa de Mortalidade por Diagnóstico (Grupo {grupo_selecionado})",
                color='taxa_mortalidade',
                color_continuous_scale='Reds',
                labels={'DIAG_PRINC': 'CID', 'taxa_mortalidade': 'Taxa de Mortalidade (%)', 'total': 'Quantidade'},
                hover_data=['mortes', 'total']
            )
            st.plotly_chart(fig_mort, use_container_width=True)
    
    elif menu == "Análise de Custos":
        st.header("Análise de Custos")
        
        # Filtros para análise de custos
        st.sidebar.subheader("Filtros de Custos")
        filtrar_por = st.sidebar.selectbox(
            "Analisar custos por:",
            ["Utilização de UTI", "Grupo Diagnóstico", "Faixa Etária"]
        )
        
        if filtrar_por == "Utilização de UTI":
            # Análise por UTI
            fig_custos = analise_custos(data['fato'])
            st.plotly_chart(fig_custos, use_container_width=True)
            
            # Distribuição dos valores
            st.subheader("Distribuição dos valores de internação")
            
            # Criar colunas para os gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                # Histograma de valores (limitado para melhor visualização)
                valores_limitados = data['fato'][data['fato']['VAL_TOT'] < data['fato']['VAL_TOT'].quantile(0.95)]
                
                fig_hist = px.histogram(
                    valores_limitados,
                    x='VAL_TOT',
                    title="Distribuição de Valores (95% percentil)",
                    labels={'VAL_TOT': 'Valor Total (R$)'},
                    nbins=50
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with col2:
                # Distribuição por componente de custo (SH vs SP)
                custos_componentes = data['fato'].agg({
                    'VAL_SH': 'sum',
                    'VAL_SP': 'sum',
                    'VAL_UTI': 'sum',
                    'VAL_TOT': 'sum'
                }).reset_index()
                
                # Transformar para formato longo
                custos_componentes.columns = ['Componente', 'Valor']
                custos_componentes['Componente'] = custos_componentes['Componente'].map({
                    'VAL_SH': 'Serviços Hospitalares',
                    'VAL_SP': 'Serviços Profissionais',
                    'VAL_UTI': 'UTI',
                    'VAL_TOT': 'Total'
                })
                
                # Filtrar apenas os componentes (sem o total)
                custos_componentes = custos_componentes[custos_componentes['Componente'] != 'Total']
                
                fig_comp = px.pie(
                    custos_componentes,
                    values='Valor',
                    names='Componente',
                    title="Composição dos Custos"
                )
                st.plotly_chart(fig_comp, use_container_width=True)
                
        elif filtrar_por == "Grupo Diagnóstico":
            # Análise por grupo diagnóstico
            fig_custos = analise_custos(data['fato'], data['dim_diagnostico'], filtrar=True)
            st.plotly_chart(fig_custos, use_container_width=True)
            
            # Tabela com detalhes por grupo diagnóstico
            analise_diag = data['fato'].merge(data['dim_diagnostico'], on='ID_DIAGNOSTICO')
            custos_por_diag = analise_diag.groupby('GRUPO_DIAG_PRINC').agg(
                valor_total=('VAL_TOT', 'sum'),
                valor_medio=('VAL_TOT', 'mean'),
                permanencia_media=('DIAS_PERMANENCIA', 'mean'),
                internacoes=('N_AIH', 'count')
            ).reset_index().sort_values('valor_total', ascending=False)
            
            # Formatar valores
            custos_por_diag['valor_total'] = custos_por_diag['valor_total'].map('R$ {:,.2f}'.format)
            custos_por_diag['valor_medio'] = custos_por_diag['valor_medio'].map('R$ {:,.2f}'.format)
            custos_por_diag['permanencia_media'] = custos_por_diag['permanencia_media'].map('{:.1f} dias'.format)
            
            # Renomear colunas
            custos_por_diag.columns = ['Grupo CID', 'Valor Total', 'Valor Médio', 'Permanência Média', 'Internações']
            
            # Exibir tabela
            st.dataframe(custos_por_diag, use_container_width=True)
            
        elif filtrar_por == "Faixa Etária":
            # Análise por faixa etária
            analise_idade = data['fato'].merge(data['dim_paciente'], on='ID_PACIENTE')
            
            custos_por_idade = analise_idade.groupby('FAIXA_ETARIA').agg(
                valor_medio=('VAL_TOT', 'mean'),
                permanencia_media=('DIAS_PERMANENCIA', 'mean'),
                internacoes=('N_AIH', 'count')
            ).reset_index()
            
            fig_idade = px.bar(
                custos_por_idade,
                x='FAIXA_ETARIA',
                y='valor_medio',
                title="Valor Médio por Faixa Etária",
                labels={'FAIXA_ETARIA': 'Faixa Etária', 'valor_medio': 'Valor Médio (R$)'},
                color='permanencia_media',
                hover_data=['internacoes', 'permanencia_media']
            )
            st.plotly_chart(fig_idade, use_container_width=True)
            
            # Relação entre permanência e valor médio
            fig_scatter = px.scatter(
                custos_por_idade,
                x='permanencia_media',
                y='valor_medio',
                size='internacoes',
                color='FAIXA_ETARIA',
                title="Relação entre Permanência e Valor por Faixa Etária",
                labels={
                    'permanencia_media': 'Permanência Média (dias)',
                    'valor_medio': 'Valor Médio (R$)',
                    'FAIXA_ETARIA': 'Faixa Etária',
                    'internacoes': 'Número de Internações'
                }
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
    
    elif menu == "Análise de Desfechos":
        st.header("Análise de Desfechos")
        
        # Gráfico principal de taxa de mortalidade
        fig_desfechos = analise_desfechos(data['fato'], data['dim_paciente'])
        st.plotly_chart(fig_desfechos, use_container_width=True)
        
        # Análises adicionais de desfecho
        col1, col2 = st.columns(2)
        
        with col1:
            # Mortalidade por permanência
            mortalidade_permanencia = data['fato'].copy()
            # Criar faixas de permanência
            bins = [0, 1, 3, 7, 14, 30, 100]
            labels = ['1 dia', '2-3 dias', '4-7 dias', '8-14 dias', '15-30 dias', '> 30 dias']
            mortalidade_permanencia['FAIXA_PERMANENCIA'] = pd.cut(
                mortalidade_permanencia['DIAS_PERMANENCIA'], 
                bins=bins, 
                labels=labels,
                include_lowest=True
            )
            
            # Calcular taxa de mortalidade por faixa de permanência
            mort_por_perm = mortalidade_permanencia.groupby('FAIXA_PERMANENCIA').agg(
                mortes=('MORTE', 'sum'),
                total=('MORTE', 'count'),
            ).reset_index()
            mort_por_perm['taxa_mortalidade'] = mort_por_perm['mortes'] / mort_por_perm['total'] * 100
            
            fig_mort_perm = px.bar(
                mort_por_perm,
                x='FAIXA_PERMANENCIA',
                y='taxa_mortalidade',
                title="Taxa de Mortalidade por Tempo de Permanência",
                labels={
                    'FAIXA_PERMANENCIA': 'Tempo de Permanência',
                    'taxa_mortalidade': 'Taxa de Mortalidade (%)'
                },
                color='taxa_mortalidade',
                color_continuous_scale='Reds',
                hover_data=['mortes', 'total']
            )
            st.plotly_chart(fig_mort_perm, use_container_width=True)
        
        with col2:
            # Mortalidade por uso de UTI
            mortalidade_uti = data['fato'].groupby('PASSOU_UTI').agg(
                mortes=('MORTE', 'sum'),
                total=('MORTE', 'count'),
            ).reset_index()
            mortalidade_uti['taxa_mortalidade'] = mortalidade_uti['mortes'] / mortalidade_uti['total'] * 100
            
            fig_mort_uti = px.bar(
                mortalidade_uti,
                x='PASSOU_UTI',
                y='taxa_mortalidade',
                title="Taxa de Mortalidade por Utilização de UTI",
                labels={
                    'PASSOU_UTI': 'Utilizou UTI',
                    'taxa_mortalidade': 'Taxa de Mortalidade (%)'
                },
                color='taxa_mortalidade',
                color_continuous_scale='Reds',
                hover_data=['mortes', 'total']
            )
            # Ajustar rótulos do eixo X
            fig_mort_uti.update_xaxes(
                ticktext=['Não', 'Sim'],
                tickvals=[0, 1]
            )
            st.plotly_chart(fig_mort_uti, use_container_width=True)
        
        # Mortalidade por grupo diagnóstico
        analise_diag = data['fato'].merge(data['dim_diagnostico'], on='ID_DIAGNOSTICO')
        
        mortalidade_diag = analise_diag.groupby('GRUPO_DIAG_PRINC').agg(
            mortes=('MORTE', 'sum'),
            total=('MORTE', 'count'),
        ).reset_index()
        mortalidade_diag['taxa_mortalidade'] = mortalidade_diag['mortes'] / mortalidade_diag['total'] * 100
        
        # Filtrar grupos com número mínimo de casos
        mortalidade_diag = mortalidade_diag[mortalidade_diag['total'] >= 10].sort_values('taxa_mortalidade', ascending=False)
        
        fig_mort_diag = px.bar(
            mortalidade_diag.head(15),
            x='GRUPO_DIAG_PRINC',
            y='taxa_mortalidade',
            title="Taxa de Mortalidade por Grupo Diagnóstico (Top 15)",
            labels={
                'GRUPO_DIAG_PRINC': 'Grupo Diagnóstico',
                'taxa_mortalidade': 'Taxa de Mortalidade (%)'
            },
            color='taxa_mortalidade',
            color_continuous_scale='Reds',
            hover_data=['mortes', 'total']
        )
        st.plotly_chart(fig_mort_diag, use_container_width=True)
    
    elif menu == "Consulta por Doença Específica":
        st.header("Consulta por Doença Específica")
        
        # Seleção da doença de interesse
        doenca_selecionada = st.sidebar.selectbox(
            "Selecione a doença de interesse:",
            list(DOENCAS_INTERESSE.keys())
        )
        
        # Obter informações da doença selecionada
        info_doenca = DOENCAS_INTERESSE[doenca_selecionada]
        lista_cids = info_doenca["cids"]
        
        # Interface para selecionar o período
        st.sidebar.subheader("Filtrar por Período")
        
        # Opções de anos e meses
        anos_disponiveis = sorted(data['fato']['DT_INTER'].dt.year.unique())
        meses = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 
                5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 
                9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
        
        # Selecionar ano e mês
        ano_selecionado = st.sidebar.selectbox("Ano:", anos_disponiveis, index=len(anos_disponiveis)-1)
        mes_selecionado = st.sidebar.selectbox(
            "Mês:", 
            list(meses.keys()),
            format_func=lambda x: meses[x],
            index=1  # Fevereiro
        )
        
        # Informações sobre a doença selecionada
        st.markdown(f"""
        ### Consulta Específica para Casos de {info_doenca['nome']}
        
        {info_doenca['descricao']}
        
        Esta consulta analisa internações relacionadas a {info_doenca['nome']}, conforme os seguintes códigos CID:
        """)
        
        # Exibir a lista de CIDs em formato compacto
        max_cols = 5  # Máximo de colunas para exibição dos CIDs
        cols = st.columns(max_cols)
        for i, cid in enumerate(lista_cids):
            cols[i % max_cols].markdown(f"- **{cid}**")
        
        # Executar consulta
        st.markdown("### Resultados da Consulta")
        
        with st.spinner(f"Executando consulta para {info_doenca['nome']}..."):
            resultado, stats = consulta_especifica_cid(
                data['fato'], 
                data['dim_diagnostico'], 
                data['dim_paciente'], 
                lista_cids,
                ano=ano_selecionado,
                mes=mes_selecionado
            )
        
        # Exibir estatísticas resumidas
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric(
            label="Total de Casos", 
            value=f"{stats['total_registros']:,}"
        )
        
        col2.metric(
            label="Valor Total", 
            value=f"R$ {stats['valor_total']:,.2f}"
        )
        
        col3.metric(
            label="Permanência Média", 
            value=f"{stats['permanencia_media']:.1f} dias"
        )
        
        col4.metric(
            label="Taxa de Mortalidade", 
            value=f"{stats['taxa_mortalidade']:.2f}%"
        )
        
        # Exibir tabela de resultados
        if len(resultado) > 0:
            st.subheader(f"Casos de {info_doenca['nome']} identificados em {meses[mes_selecionado]} de {ano_selecionado}")
            
            # Formatar colunas de data
            resultado['DT_INTER'] = pd.to_datetime(resultado['DT_INTER']).dt.strftime('%d/%m/%Y')
            resultado['DT_SAIDA'] = pd.to_datetime(resultado['DT_SAIDA']).dt.strftime('%d/%m/%Y')
            
            # Formatar valores monetários
            resultado['VAL_TOT'] = resultado['VAL_TOT'].map('R$ {:,.2f}'.format)
            
            # Formatar coluna de morte
            resultado['MORTE'] = resultado['MORTE'].map({0: 'Não', 1: 'Sim'})
            
            # Renomear colunas para melhor visualização
            resultado = resultado.rename(columns={
                'N_AIH': 'AIH',
                'DT_INTER': 'Data Internação',
                'DT_SAIDA': 'Data Saída',
                'DIAS_PERMANENCIA': 'Dias',
                'DIAG_PRINC': 'CID',
                'FAIXA_ETARIA': 'Faixa Etária',
                'DESC_SEXO': 'Sexo',
                'VAL_TOT': 'Valor Total',
                'MORTE': 'Óbito'
            })
            
            # Exibir tabela
            st.dataframe(resultado, use_container_width=True)
            
            # Permitir download dos resultados
            csv = resultado.to_csv(index=False).encode('utf-8')
            filename = f"{doenca_selecionada.lower().replace(' ', '_')}_{ano_selecionado}_{mes_selecionado}.csv"
            st.download_button(
                label="Baixar resultados em CSV",
                data=csv,
                file_name=filename,
                mime="text/csv",
            )
            
            # Gráficos de análise destes casos específicos
            st.subheader(f"Análise dos Casos de {info_doenca['nome']}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribuição por faixa etária
                contagem_faixa = resultado['Faixa Etária'].value_counts().reset_index()
                contagem_faixa.columns = ['Faixa Etária', 'Quantidade']
                
                fig_faixa = px.bar(
                    contagem_faixa,
                    x='Faixa Etária',
                    y='Quantidade',
                    title=f"Distribuição por Faixa Etária - {info_doenca['nome']}",
                    color='Quantidade',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig_faixa, use_container_width=True)
            
            with col2:
                # Distribuição por sexo
                contagem_sexo = resultado['Sexo'].value_counts().reset_index()
                contagem_sexo.columns = ['Sexo', 'Quantidade']
                
                fig_sexo = px.pie(
                    contagem_sexo,
                    values='Quantidade',
                    names='Sexo',
                    title=f"Distribuição por Sexo - {info_doenca['nome']}",
                    hole=0.4
                )
                st.plotly_chart(fig_sexo, use_container_width=True)
            
            # Distribuição de CIDs
            contagem_cid = resultado['CID'].value_counts().reset_index().head(15)
            contagem_cid.columns = ['CID', 'Quantidade']
            
            fig_cid = px.bar(
                contagem_cid,
                x='Quantidade',
                y='CID',
                title=f"CIDs mais frequentes - {info_doenca['nome']}",
                orientation='h',
                color='Quantidade',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig_cid, use_container_width=True)
            
        else:
            st.warning(f"Não foram encontrados casos de {info_doenca['nome']} em {meses[mes_selecionado]} de {ano_selecionado}.")
            st.info("Tente selecionar outro período ou verifique se os dados contêm os CIDs listados.")

# Executar a aplicação
if __name__ == '__main__':
    main()