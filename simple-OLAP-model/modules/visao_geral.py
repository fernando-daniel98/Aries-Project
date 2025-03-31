import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Reimplementação das funções necessárias para usar os nomes de colunas corretos
def analise_temporal(fato, dim_tempo):
    """
    Gera gráfico de análise temporal das internações.
    
    Adaptado para usar N_AIH em vez de ID_INTERNACAO.
    """
    # Juntar com dimensão tempo
    df_analise = fato.merge(dim_tempo, on='ID_TEMPO')
    
    # Agrupar por ano e mês
    df_tempo = df_analise.groupby(['ANO_CMPT', 'MES_CMPT']).agg(
        total_internacoes=('N_AIH', 'count')  # Modificado para usar N_AIH
    ).reset_index()
    
    # Criar coluna de data para visualização
    df_tempo['data'] = pd.to_datetime(
        df_tempo['ANO_CMPT'].astype(str) + '-' + 
        df_tempo['MES_CMPT'].astype(str) + '-01'
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

def analise_desfechos(fato, dim_paciente):
    """
    Gera gráfico de análise de desfechos por faixa etária.
    
    Adaptado para usar N_AIH em vez de ID_INTERNACAO e o esquema correto de faixa etária.
    """
    # Juntar com dimensão paciente
    df_analise = fato.merge(dim_paciente, on='ID_PACIENTE')
    
    # Agrupar por faixa etária
    df_desfechos = df_analise.groupby('FAIXA_ETARIA').agg(
        total_internacoes=('N_AIH', 'count'),  # Modificado para usar N_AIH
        taxa_mortalidade=('MORTE', 'mean')
    ).reset_index()
    
    # Converter taxa para percentual
    df_desfechos['taxa_mortalidade'] = df_desfechos['taxa_mortalidade'] * 100
    
    # Ordenar faixas etárias corretamente
    ordem_faixas = ['< 1 ano', '1-4 anos', '5-11 anos', '12-17 anos', '18-29 anos', '30-59 anos', '60-79 anos', '≥ 80 anos']
    # Filtrar apenas faixas existentes nos dados
    faixas_existentes = [faixa for faixa in ordem_faixas if faixa in df_desfechos['FAIXA_ETARIA'].unique()]
    
    # Gráfico de barras
    fig = px.bar(
        df_desfechos,
        x='FAIXA_ETARIA',
        y='taxa_mortalidade',
        title='Taxa de mortalidade por faixa etária',
        labels={'FAIXA_ETARIA': 'Faixa Etária', 'taxa_mortalidade': 'Taxa de Mortalidade (%)'},
        category_orders={'FAIXA_ETARIA': faixas_existentes}  # Ordenar faixas
    )
    
    return fig

def analise_diagnosticos(fato, dim_diagnostico):
    """
    Gera gráfico dos diagnósticos mais frequentes.
    
    Adaptado para usar N_AIH em vez de ID_INTERNACAO e DIAG_PRINC para o CID.
    """
    # Juntar com dimensão diagnóstico
    df_analise = fato.merge(dim_diagnostico, on='ID_DIAGNOSTICO')
    
    # Extrair categoria do CID (primeiros 3 caracteres)
    df_analise['CATEGORIA_CID'] = df_analise['DIAG_PRINC'].str[:3]
    
    # Agrupar por categoria
    df_diag = df_analise.groupby('CATEGORIA_CID').agg(
        total_internacoes=('N_AIH', 'count')  # Modificado para usar N_AIH
    ).reset_index()
    
    # Top 10 diagnósticos
    top_diags = df_diag.sort_values('total_internacoes', ascending=False).head(10)
    
    # Gráfico de barras horizontais
    fig = px.bar(
        top_diags,
        y='CATEGORIA_CID',
        x='total_internacoes',
        title='Top 10 categorias de diagnóstico (CID)',
        labels={'CATEGORIA_CID': 'Categoria CID', 'total_internacoes': 'Total de Internações'},
        orientation='h'
    )
    
    return fig

def render(data):
    """
    Renderiza a página de Visão Geral do Dashboard.
    
    Parâmetros:
    data: Dicionário contendo os dataframes do modelo dimensional
    """
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
    
    # Mostrar informações sobre as dimensões disponíveis
    with st.expander("Dimensões disponíveis para análise"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Tempo")
            st.write(f"• Anos: {', '.join(map(str, sorted(data['dim_tempo']['ANO_CMPT'].unique())))}")
            
            st.markdown("#### Paciente")
            st.write(f"• Faixas etárias: {', '.join(sorted(data['dim_paciente']['FAIXA_ETARIA'].unique()))}")
            st.write(f"• Sexo: {', '.join(sorted(data['dim_paciente']['DESC_SEXO'].unique()))}")
        
        with col2:
            st.markdown("#### Localização")
            
            uf_dict = {
                11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA', 16: 'AP', 17: 'TO',
                21: 'MA', 22: 'PI', 23: 'CE', 24: 'RN', 25: 'PB', 26: 'PE', 27: 'AL',
                28: 'SE', 29: 'BA', 31: 'MG', 32: 'ES', 33: 'RJ', 35: 'SP', 41: 'PR',
                42: 'SC', 43: 'RS', 50: 'MS', 51: 'MT', 52: 'GO', 53: 'DF'
            }
            
            ufs = [uf_dict.get(int(uf), str(uf)) for uf in sorted(data['dim_localizacao']['UF_RES'].unique())]
            st.write(f"• Estados: {', '.join(ufs)}")
            
            st.markdown("#### Hospitais")
            st.write(f"• Total de hospitais: {len(data['dim_hospital']['ID_HOSPITAL'].unique())}")