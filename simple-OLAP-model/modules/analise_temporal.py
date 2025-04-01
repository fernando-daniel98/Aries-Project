import streamlit as st
import pandas as pd
import plotly.express as px

def analise_temporal(fato, dim_tempo):
    """
    Gera gráfico de análise temporal das internações.
    
    Adaptado para usar os nomes corretos das colunas.
    """
    if 'ANO_CMPT' in fato.columns and 'MES_CMPT' in fato.columns:
        df_analise = fato  # Usar o DataFrame como está
    else:
        df_analise = fato.merge(dim_tempo, on='ID_TEMPO')
    
    df_tempo = df_analise.groupby(['ANO_CMPT', 'MES_CMPT']).agg(
        total_internacoes=('N_AIH', 'count')
    ).reset_index()
    
    df_tempo['data'] = pd.to_datetime(
        df_tempo['ANO_CMPT'].astype(str) + '-' + 
        df_tempo['MES_CMPT'].astype(str).str.zfill(2) + '-01'
    )
    
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
    
    st.sidebar.subheader("Filtros para Análise Temporal")
    
    anos_disponiveis = sorted(data['dim_tempo']['ANO_CMPT'].unique())
    
    ano_inicial, ano_final = st.sidebar.select_slider(
        "Selecione o intervalo de anos:",
        options=anos_disponiveis,
        value=(min(anos_disponiveis), max(anos_disponiveis))
    )
    
    fato_filtrado = data['fato'].merge(
        data['dim_tempo'].query(f"ANO_CMPT >= {ano_inicial} and ANO_CMPT <= {ano_final}"),
        on='ID_TEMPO'
    )
    
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
    else:
        df_tempo = data['dim_tempo'].copy()
        df_tempo['PERIODO'] = df_tempo['ANO_CMPT'].astype(str)
        df_tempo['PERIODO_LABEL'] = df_tempo['ANO_CMPT'].astype(str)
        group_by = ['ANO_CMPT', 'PERIODO', 'PERIODO_LABEL']
        x_col = 'PERIODO_LABEL'
        titulo = 'Comparação Anual'
    

    df_tempo = df_tempo[(df_tempo['ANO_CMPT'] >= ano_inicial) & (df_tempo['ANO_CMPT'] <= ano_final)]
    

    df_analise = data['fato'].merge(df_tempo, on='ID_TEMPO')
    
    df_agrupado = df_analise.groupby(group_by).agg(
        total_internacoes=('N_AIH', 'count'),
        permanencia_media=('DIAS_PERMANENCIA', 'mean'),
        custo_medio=('VAL_TOT', 'mean'),
        mortalidade=('MORTE', 'mean')
    ).reset_index()
    

    df_agrupado['mortalidade'] = df_agrupado['mortalidade'] * 100
    

    col1, col2 = st.columns(2)
    
    with col1:

        fig_internacoes = px.bar(
            df_agrupado, 
            x=x_col, 
            y='total_internacoes',
            title=f'Número de Internações - {titulo}',
            labels={x_col: 'Período', 'total_internacoes': 'Total de Internações'}
        )
        st.plotly_chart(fig_internacoes, use_container_width=True)
        

        fig_permanencia = px.bar(
            df_agrupado, 
            x=x_col, 
            y='permanencia_media',
            title=f'Permanência Média - {titulo}',
            labels={x_col: 'Período', 'permanencia_media': 'Dias de Permanência'}
        )
        st.plotly_chart(fig_permanencia, use_container_width=True)
    
    with col2:

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
        

        fig_mortalidade = px.line(
            df_agrupado, 
            x=x_col, 
            y='mortalidade',
            title=f'Taxa de Mortalidade - {titulo}',
            labels={x_col: 'Período', 'mortalidade': 'Taxa de Mortalidade (%)'},
            markers=True
        )
        st.plotly_chart(fig_mortalidade, use_container_width=True)
    

    with st.expander("Ver tabela de dados"):

        df_exibicao = df_agrupado.copy()
        df_exibicao['permanencia_media'] = df_exibicao['permanencia_media'].round(2).astype(str) + ' dias'
        df_exibicao['custo_medio'] = 'R$ ' + df_exibicao['custo_medio'].round(2).astype(str)
        df_exibicao['mortalidade'] = df_exibicao['mortalidade'].round(2).astype(str) + '%'
        
        df_exibicao = df_exibicao.rename(columns={
            'PERIODO_LABEL': 'Período',
            'total_internacoes': 'Total de Internações',
            'permanencia_media': 'Permanência Média',
            'custo_medio': 'Custo Médio',
            'mortalidade': 'Taxa de Mortalidade'
        })
        
        colunas_exibir = ['Período', 'Total de Internações', 'Permanência Média', 'Custo Médio', 'Taxa de Mortalidade']
        st.dataframe(df_exibicao[colunas_exibir], use_container_width=True)