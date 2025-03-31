import streamlit as st
import pandas as pd
import plotly.express as px

def render(data):
    """Análise de Diagnósticos - Versão Corrigida"""
    st.header("📊 Análise de Diagnósticos", divider='rainbow')
    
    # ===== [Sidebar] =====
    with st.sidebar:
        st.subheader("⚙️ Filtros")
        
        # Filtro de ano único para simplificar
        ano_selecionado = st.selectbox(
            "Selecione o ano:",
            sorted(data['dim_tempo']['ANO_CMPT'].unique()),
            index=0
        )
    
    # ===== [Processamento] =====
    # Filtrar e mesclar dados com tratamento de duplicatas
    df = (
        data['fato']
        .merge(data['dim_tempo'][data['dim_tempo']['ANO_CMPT'] == ano_selecionado], on='ID_TEMPO')
        .merge(data['dim_diagnostico'], on='ID_DIAGNOSTICO')
        .drop_duplicates(subset=['N_AIH', 'DIAG_PRINC'])  # Chave única por internação-diagnóstico
    )
    
    # ===== [Análise Principal] =====
    st.subheader("🔍 Diagnósticos Mais Frequentes")
    
    # Contagem única por internação
    diagnosticos = df.groupby('DIAG_PRINC').agg(
        internacoes=('N_AIH', 'nunique'),  # Contagem DISTINCT
        custo_total=('VAL_TOT', 'sum'),
        mortalidade=('MORTE', 'mean')
    ).reset_index().sort_values('internacoes', ascending=False)
    
    # Seleção de top N
    top_n = st.slider("Quantidade de diagnósticos a exibir:", 5, 50, 10)
    df_top = diagnosticos.head(top_n)
    
    # Gráfico corrigido
    fig = px.bar(
        df_top,
        x='DIAG_PRINC',
        y='internacoes',
        labels={'DIAG_PRINC': 'Código CID-10', 'internacoes': 'Internações Únicas'},
        color='internacoes',
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # ===== [Análise Detalhada] =====
    st.subheader("📈 Detalhes por Diagnóstico")
    
    if not df_top.empty:
        cid_selecionado = st.selectbox(
            "Selecione um diagnóstico:",
            df_top['DIAG_PRINC'].tolist()
        )
        
        dados = df[df['DIAG_PRINC'] == cid_selecionado].agg({
            'N_AIH': 'nunique',
            'DIAS_PERMANENCIA': 'mean',
            'VAL_TOT': ['sum', 'mean'],
            'MORTE': 'mean'
        }).squeeze()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Internações Únicas", f"{dados.get(('N_AIH', 'nunique'), 0):,}")
        col2.metric("Custo Total (R$)", f"{dados.get(('VAL_TOT', 'sum'), 0):,.2f}")
        col3.metric("Mortalidade (%)", f"{dados.get(('MORTE', 'mean'), 0)*100:.2f}%")
        col4.metric("Permanência Média", f"{dados.get(('DIAS_PERMANENCIA', 'mean'), 0):.1f} dias")