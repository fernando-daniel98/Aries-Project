import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def render(data):
    """
    Renderiza a página de Análise de Custos do Dashboard.
    
    Parâmetros:
    data: Dicionário contendo os dataframes do modelo dimensional
    """
    st.header("Análise de Custos das Internações")
    
    st.sidebar.subheader("Filtros para Análise de Custos")
    
    anos_disponiveis = sorted(data['dim_tempo']['ANO_CMPT'].unique())
    
    ano_inicial, ano_final = st.sidebar.select_slider(
        "Selecione o intervalo de anos:",
        options=anos_disponiveis,
        value=(min(anos_disponiveis), max(anos_disponiveis))
    )
    
    dimensao_analise = st.sidebar.selectbox(
        "Dimensão para análise:",
        ["Diagnósticos", "Hospitais", "Regiões", "Procedimentos", "Faixa Etária"]
    )
    
    fato_filtrado = data['fato'].merge(
        data['dim_tempo'].query(f"ANO_CMPT >= {ano_inicial} and ANO_CMPT <= {ano_final}"),
        on='ID_TEMPO'
    )
    
    st.subheader("Estatísticas Gerais de Custos")
    
    col1, col2, col3, col4 = st.columns(4)
    
    custo_total = fato_filtrado['VAL_TOT'].sum()
    if custo_total >= 1e9:
        valor_formatado = f"R$ {custo_total/1e9:.2f} bi"
    elif custo_total >= 1e6:
        valor_formatado = f"R$ {custo_total/1e6:.2f} mi"
    else:
        valor_formatado = f"R$ {custo_total:,.2f}"
        
    col1.metric(
        label="Custo Total", 
        value=valor_formatado
    )
    
    custo_medio = fato_filtrado['VAL_TOT'].mean()
    col2.metric(
        label="Custo Médio por Internação", 
        value=f"R$ {custo_medio:,.2f}"
    )
    
    dias_validos = fato_filtrado[fato_filtrado['DIAS_PERMANENCIA'] > 0]
    if len(dias_validos) > 0:
        custo_por_dia = dias_validos['VAL_TOT'].sum() / dias_validos['DIAS_PERMANENCIA'].sum()
    else:
        custo_por_dia = 0
    
    col3.metric(
        label="Custo Médio por Dia", 
        value=f"R$ {custo_por_dia:,.2f}"
    )
    
    total_internacoes = len(fato_filtrado)
    col4.metric(
        label="Total de Internações", 
        value=f"{total_internacoes:,}"
    )
    
    st.subheader("Evolução Temporal dos Custos")
    
    df_custos_tempo = fato_filtrado.groupby(['ANO_CMPT', 'MES_CMPT']).agg(
        custo_total=('VAL_TOT', 'sum'),
        custo_medio=('VAL_TOT', 'mean'),
        total_internacoes=('N_AIH', 'count')
    ).reset_index()
    
    df_custos_tempo['data'] = pd.to_datetime(
        df_custos_tempo['ANO_CMPT'].astype(str) + '-' + 
        df_custos_tempo['MES_CMPT'].astype(str) + '-01'
    )
    
    metrica_tempo = st.radio(
        "Selecione a métrica para visualização:",
        ["Custo Total", "Custo Médio por Internação", "Total de Internações"],
        horizontal=True
    )
    
    if metrica_tempo == "Custo Total":
        y_col = 'custo_total'
        y_label = 'Custo Total (R$)'
    elif metrica_tempo == "Custo Médio por Internação":
        y_col = 'custo_medio'
        y_label = 'Custo Médio (R$)'
    else:
        y_col = 'total_internacoes'
        y_label = 'Total de Internações'
    
    fig_tempo = px.line(
        df_custos_tempo.sort_values('data'),
        x='data',
        y=y_col,
        title=f'Evolução de {metrica_tempo} ao longo do tempo',
        labels={'data': 'Data', y_col: y_label},
        markers=True
    )
    st.plotly_chart(fig_tempo, use_container_width=True)
    
    st.subheader(f"Análise de Custos por {dimensao_analise}")
    
    if dimensao_analise == "Diagnósticos":
        df_analise = fato_filtrado.merge(
            data['dim_diagnostico'],
            on='ID_DIAGNOSTICO'
        )
        df_analise['CATEGORIA_CID'] = df_analise['DIAG_PRINC'].str[:3]
        group_col = 'CATEGORIA_CID'
        col_name = 'Categoria CID'
        
    elif dimensao_analise == "Hospitais":
        df_analise = fato_filtrado.merge(
            data['dim_hospital'],
            on='ID_HOSPITAL'
        )
        group_col = 'CNES'
        col_name = 'Hospital'
        
    elif dimensao_analise == "Regiões":
        df_analise = fato_filtrado.merge(
            data['dim_localizacao'],
            on='ID_LOCALIZACAO'
        )
        group_col = 'UF_RES'
        col_name = 'Estado'
        
    elif dimensao_analise == "Procedimentos":
        df_analise = fato_filtrado.merge(
            data['dim_procedimento'],
            on='ID_PROCEDIMENTO'
        )
        group_col = 'PROC_REA'
        col_name = 'Procedimento'
        
    else:  # Faixa Etária
        df_analise = fato_filtrado.merge(
            data['dim_paciente'],
            on='ID_PACIENTE'
        )
        group_col = 'FAIXA_ETARIA'
        col_name = 'Faixa Etária'
    
    try:
        df_custos_dim = df_analise.groupby(group_col).agg(
            custo_total=('VAL_TOT', 'sum'),
            custo_medio=('VAL_TOT', 'mean'),
            total_internacoes=('N_AIH', 'count'),
            permanencia_media=('DIAS_PERMANENCIA', 'mean')
        ).reset_index()
        
        df_custos_dim['dias_totais'] = df_custos_dim['total_internacoes'] * df_custos_dim['permanencia_media']
        df_custos_dim['custo_por_dia'] = df_custos_dim.apply(
            lambda x: x['custo_total'] / x['dias_totais'] if x['dias_totais'] > 0 else 0, 
            axis=1
        )
        
        top_n = st.slider(f"Número de {dimensao_analise.lower()} a exibir:", min_value=5, max_value=20, value=10)
        
        var_analise = st.selectbox(
            "Variável para análise:",
            ["Custo Total", "Custo Médio por Internação", "Custo por Dia de Permanência"]
        )
        
        if var_analise == "Custo Total":
            col_var = 'custo_total'
            formato = 'R$ {:,.2f}'
        elif var_analise == "Custo Médio por Internação":
            col_var = 'custo_medio'
            formato = 'R$ {:,.2f}'
        else:  # Custo por Dia
            col_var = 'custo_por_dia'
            formato = 'R$ {:,.2f}'
        
        df_top = df_custos_dim.sort_values(col_var, ascending=False).head(top_n)
        
        fig_top = px.bar(
            df_top,
            x=group_col,
            y=col_var,
            title=f'Top {top_n} {dimensao_analise} por {var_analise}',
            labels={group_col: col_name, col_var: var_analise},
            color=col_var,
            text_auto='.2s'
        )
        
        fig_top.update_layout(
            xaxis_tickangle=-45,
            yaxis=dict(title=var_analise)
        )
        
        st.plotly_chart(fig_top, use_container_width=True)
        
        st.subheader("Distribuição dos Custos")
        
        fig_hist = px.histogram(
            fato_filtrado,
            x='VAL_TOT',
            nbins=50,
            title='Distribuição dos Custos por Internação',
            labels={'VAL_TOT': 'Custo (R$)', 'count': 'Frequência'}
        )
        
        st.plotly_chart(fig_hist, use_container_width=True)
        
        fig_box = px.box(
            df_analise,
            x='ANO_CMPT',
            y='VAL_TOT',
            title='Distribuição dos Custos por Ano',
            labels={'ANO_CMPT': 'Ano', 'VAL_TOT': 'Custo (R$)'}
        )
        
        st.plotly_chart(fig_box, use_container_width=True)
        
        with st.expander("Ver tabela detalhada de custos"):
            if 'dias_totais' in df_custos_dim.columns:
                df_custos_dim = df_custos_dim.drop(columns=['dias_totais'])
                
            df_display = df_custos_dim.copy()
            df_display['custo_total'] = df_display['custo_total'].apply(lambda x: f"R$ {x:,.2f}")
            df_display['custo_medio'] = df_display['custo_medio'].apply(lambda x: f"R$ {x:,.2f}")
            df_display['custo_por_dia'] = df_display['custo_por_dia'].apply(lambda x: f"R$ {x:,.2f}")
            df_display['permanencia_media'] = df_display['permanencia_media'].round(2).astype(str) + " dias"
            
            df_display = df_display.rename(columns={
                group_col: col_name,
                'custo_total': 'Custo Total',
                'custo_medio': 'Custo Médio por Internação',
                'custo_por_dia': 'Custo por Dia',
                'total_internacoes': 'Total de Internações',
                'permanencia_media': 'Permanência Média'
            })
            
            df_display = df_display.sort_values('Custo Total', ascending=False)
            
            st.dataframe(df_display, use_container_width=True)
            
    except Exception as e:
        st.error(f"Erro ao processar dados para {dimensao_analise}: {str(e)}")
        st.info("Verifique se as colunas necessárias estão disponíveis nos dados.")