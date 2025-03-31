import streamlit as st
import pandas as pd
import plotly.express as px

# Implementamos a função analise_temporal aqui para garantir a compatibilidade com os dados
# Modifique a função analise_temporal para verificar se o merge é necessário:
def analise_temporal(fato, dim_tempo):
    """
    Gera gráfico de análise temporal das internações.
    
    Adaptado para usar os nomes corretos das colunas.
    """
    # Verificar se o DataFrame já tem as colunas necessárias antes de fazer o merge
    if 'ANO_CMPT' in fato.columns and 'MES_CMPT' in fato.columns:
        df_analise = fato  # Usar o DataFrame como está
    else:
        # Juntar com dimensão tempo apenas se as colunas não existirem
        df_analise = fato.merge(dim_tempo, on='ID_TEMPO')
    
    # Agrupar por ano e mês
    df_tempo = df_analise.groupby(['ANO_CMPT', 'MES_CMPT']).agg(
        total_internacoes=('N_AIH', 'count')  # Modificado para usar N_AIH
    ).reset_index()
    
    # Criar coluna de data para visualização
    df_tempo['data'] = pd.to_datetime(
        df_tempo['ANO_CMPT'].astype(str) + '-' + 
        df_tempo['MES_CMPT'].astype(str).str.zfill(2) + '-01'
    )
    
    # Gráfico de linha temporal
    fig = px.line(
        df_tempo.sort_values('data'),
        x='data',
        y='total_internacoes',
        title='Evolução do número de internações ao longo do tempo',
        labels={'data': 'Data', 'total_internacoes': 'Total de Internações'},
        markers=True
    )
    
    return fig

def render(data):
    """
    Renderiza a página de Análise Temporal do Dashboard.
    
    Parâmetros:
    data: Dicionário contendo os dataframes do modelo dimensional
    """
    st.header("Análise Temporal das Internações")
    
    # Filtros na barra lateral para análise temporal
    st.sidebar.subheader("Filtros para Análise Temporal")
    
    # Obter intervalo de anos disponíveis
    anos_disponiveis = sorted(data['dim_tempo']['ANO_CMPT'].unique())
    
    # Seleção de intervalo de anos
    ano_inicial, ano_final = st.sidebar.select_slider(
        "Selecione o intervalo de anos:",
        options=anos_disponiveis,
        value=(min(anos_disponiveis), max(anos_disponiveis))
    )
    
    # Filtrar dados pelo intervalo de tempo selecionado
    fato_filtrado = data['fato'].merge(
        data['dim_tempo'].query(f"ANO_CMPT >= {ano_inicial} and ANO_CMPT <= {ano_final}"),
        on='ID_TEMPO'
    )
    
    # Granularidade temporal
    granularidade = st.sidebar.radio(
        "Granularidade da análise:",
        ["Mensal", "Trimestral", "Anual"]
    )
    
    # Seção 1: Gráfico de evolução temporal
    st.subheader("Evolução das Internações ao Longo do Tempo")
    fig_principal = analise_temporal(fato_filtrado, data['dim_tempo'])
    st.plotly_chart(fig_principal, use_container_width=True)
    
    # Seção 2: Análise comparativa por período
    st.subheader("Análise Comparativa por Período")
    
    # Preparar dados para análise comparativa dependendo da granularidade
    if granularidade == "Mensal":
        df_tempo = data['dim_tempo'].copy()
        df_tempo['PERIODO'] = df_tempo['ANO_CMPT'].astype(str) + "-" + df_tempo['MES_CMPT'].astype(str).str.zfill(2)
        df_tempo['PERIODO_LABEL'] = pd.to_datetime(df_tempo['PERIODO'] + '-01').dt.strftime('%b/%Y')
        group_by = ['ANO_CMPT', 'MES_CMPT', 'PERIODO', 'PERIODO_LABEL']
        x_col = 'PERIODO_LABEL'
        titulo = 'Comparação Mensal'
    elif granularidade == "Trimestral":
        df_tempo = data['dim_tempo'].copy()
        df_tempo['TRIMESTRE'] = ((df_tempo['MES_CMPT'] - 1) // 3) + 1
        df_tempo['PERIODO'] = df_tempo['ANO_CMPT'].astype(str) + "-T" + df_tempo['TRIMESTRE'].astype(str)
        df_tempo['PERIODO_LABEL'] = "T" + df_tempo['TRIMESTRE'].astype(str) + "/" + df_tempo['ANO_CMPT'].astype(str)
        group_by = ['ANO_CMPT', 'TRIMESTRE', 'PERIODO', 'PERIODO_LABEL']
        x_col = 'PERIODO_LABEL'
        titulo = 'Comparação Trimestral'
    else:  # Anual
        df_tempo = data['dim_tempo'].copy()
        df_tempo['PERIODO'] = df_tempo['ANO_CMPT'].astype(str)
        df_tempo['PERIODO_LABEL'] = df_tempo['ANO_CMPT'].astype(str)
        group_by = ['ANO_CMPT', 'PERIODO', 'PERIODO_LABEL']
        x_col = 'PERIODO_LABEL'
        titulo = 'Comparação Anual'
    
    # Filtrar pelos anos selecionados
    df_tempo = df_tempo[(df_tempo['ANO_CMPT'] >= ano_inicial) & (df_tempo['ANO_CMPT'] <= ano_final)]
    
    # Juntar com fato e agrupar
    df_analise = data['fato'].merge(df_tempo, on='ID_TEMPO')
    
    # Modificação principal: usar N_AIH em vez de ID_INTERNACAO
    df_agrupado = df_analise.groupby(group_by).agg(
        total_internacoes=('N_AIH', 'count'),  # Modificado aqui
        permanencia_media=('DIAS_PERMANENCIA', 'mean'),
        custo_medio=('VAL_TOT', 'mean'),
        mortalidade=('MORTE', 'mean')
    ).reset_index()
    
    # Converter mortalidade para percentual
    df_agrupado['mortalidade'] = df_agrupado['mortalidade'] * 100
    
    # Mostrar gráficos comparativos
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de número de internações
        fig_internacoes = px.bar(
            df_agrupado, 
            x=x_col, 
            y='total_internacoes',
            title=f'Número de Internações - {titulo}',
            labels={x_col: 'Período', 'total_internacoes': 'Total de Internações'}
        )
        st.plotly_chart(fig_internacoes, use_container_width=True)
        
        # Gráfico de permanência média
        fig_permanencia = px.bar(
            df_agrupado, 
            x=x_col, 
            y='permanencia_media',
            title=f'Permanência Média - {titulo}',
            labels={x_col: 'Período', 'permanencia_media': 'Dias de Permanência'}
        )
        st.plotly_chart(fig_permanencia, use_container_width=True)
    
    with col2:
        # Gráfico de custo médio
        fig_custo = px.bar(
            df_agrupado, 
            x=x_col, 
            y='custo_medio',
            title=f'Custo Médio - {titulo}',
            labels={x_col: 'Período', 'custo_medio': 'Custo Médio (R$)'},
            color='custo_medio',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_custo, use_container_width=True)
        
        # Gráfico de taxa de mortalidade
        fig_mortalidade = px.line(
            df_agrupado, 
            x=x_col, 
            y='mortalidade',
            title=f'Taxa de Mortalidade - {titulo}',
            labels={x_col: 'Período', 'mortalidade': 'Taxa de Mortalidade (%)'},
            markers=True
        )
        st.plotly_chart(fig_mortalidade, use_container_width=True)
    
    # Tabela de dados
    with st.expander("Ver tabela de dados"):
        # Formatar colunas para exibição
        df_exibicao = df_agrupado.copy()
        df_exibicao['permanencia_media'] = df_exibicao['permanencia_media'].round(2).astype(str) + ' dias'
        df_exibicao['custo_medio'] = 'R$ ' + df_exibicao['custo_medio'].round(2).astype(str)
        df_exibicao['mortalidade'] = df_exibicao['mortalidade'].round(2).astype(str) + '%'
        
        # Renomear colunas para melhor visualização
        df_exibicao = df_exibicao.rename(columns={
            'PERIODO_LABEL': 'Período',
            'total_internacoes': 'Total de Internações',
            'permanencia_media': 'Permanência Média',
            'custo_medio': 'Custo Médio',
            'mortalidade': 'Taxa de Mortalidade'
        })
        
        # Exibir apenas as colunas relevantes
        colunas_exibir = ['Período', 'Total de Internações', 'Permanência Média', 'Custo Médio', 'Taxa de Mortalidade']
        st.dataframe(df_exibicao[colunas_exibir], use_container_width=True)