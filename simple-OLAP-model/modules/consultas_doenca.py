import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

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

# Mantenha o início do arquivo com as importações e definição do DOENCAS_INTERESSE

def render(data):
    """
    Renderiza a página de Consulta por Doença Específica do Dashboard.
    
    Parâmetros:
    data: Dicionário contendo os dataframes do modelo dimensional
    """
    st.header("Análise por Doença Específica")
    
    # Filtros na barra lateral
    st.sidebar.subheader("Filtros para Consulta")
    
    # Seleção de doença de interesse
    doenca_selecionada = st.sidebar.selectbox(
        "Selecione a doença para análise:",
        list(DOENCAS_INTERESSE.keys())
    )
    
    # Informações sobre a doença selecionada
    info_doenca = DOENCAS_INTERESSE[doenca_selecionada]
    
    # Filtro de período
    anos_disponiveis = sorted(data['dim_tempo']['ANO_CMPT'].unique())
    
    # Seleção de intervalo de anos
    ano_inicial, ano_final = st.sidebar.select_slider(
        "Selecione o intervalo de anos:",
        options=anos_disponiveis,
        value=(min(anos_disponiveis), max(anos_disponiveis))
    )
    
    # Resumo da doença selecionada
    st.subheader(f"Análise de {info_doenca['nome']}")
    
    st.info(f"**Descrição**: {info_doenca['descricao']}")
    st.write(f"**CIDs relacionados**: {', '.join(info_doenca['cids'])}")
    
    # Preparar dados filtrados para a doença e período selecionado
    # Primeiro filtrar pelo período
    fato_filtrado = data['fato'].merge(
        data['dim_tempo'].query(f"ANO_CMPT >= {ano_inicial} and ANO_CMPT <= {ano_final}"),
        on='ID_TEMPO'
    )
    
    # Juntar com dimensão diagnóstico
    df_analise = fato_filtrado.merge(
        data['dim_diagnostico'],
        on='ID_DIAGNOSTICO'
    )
    
    # Filtrar por CIDs da doença selecionada
    # Verifica se cada CID no diagnóstico principal está na lista de CIDs da doença
    df_doenca = df_analise[df_analise['DIAG_PRINC'].str.startswith(tuple(info_doenca['cids']))]
    
    # Se não houver dados disponíveis
    if len(df_doenca) == 0:
        st.warning(f"Não foram encontrados registros para {info_doenca['nome']} no período selecionado.")
        return
    
    # Estatísticas gerais
    st.subheader("Estatísticas Gerais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Total de internações - ALTERADO: N_AIH em vez de ID_INTERNACAO
    total_internacoes = len(df_doenca)
    col1.metric(
        label="Total de Internações", 
        value=f"{total_internacoes:,}"
    )
    
    # Permanência média
    permanencia_media = df_doenca['DIAS_PERMANENCIA'].mean()
    col2.metric(
        label="Permanência Média", 
        value=f"{permanencia_media:.1f} dias"
    )
    
    # Custo total
    custo_total = df_doenca['VAL_TOT'].sum()
    if custo_total >= 1e9:
        valor_formatado = f"R$ {custo_total/1e9:.2f} bi"
    elif custo_total >= 1e6:
        valor_formatado = f"R$ {custo_total/1e6:.2f} mi"
    else:
        valor_formatado = f"R$ {custo_total:,.2f}"
        
    col3.metric(
        label="Custo Total", 
        value=valor_formatado
    )
    
    # Taxa de mortalidade
    taxa_mortalidade = df_doenca['MORTE'].mean() * 100
    col4.metric(
        label="Taxa de Mortalidade", 
        value=f"{taxa_mortalidade:.2f}%"
    )
    
    # Seção 1: Evolução temporal
    st.subheader("Evolução Temporal")
    
    # Agrupar por ano e mês - ALTERADO: N_AIH em vez de ID_INTERNACAO
    df_tempo = df_doenca.groupby(['ANO_CMPT', 'MES_CMPT']).agg(
        total_internacoes=('N_AIH', 'count'),  # Modificado aqui
        custo_total=('VAL_TOT', 'sum'),
        permanencia_media=('DIAS_PERMANENCIA', 'mean'),
        taxa_mortalidade=('MORTE', 'mean')
    ).reset_index()
    
    # Aplicar multiplicação após a agregação
    df_tempo['taxa_mortalidade'] = df_tempo['taxa_mortalidade'] * 100
    
    # Criar coluna de data para visualização
    df_tempo['data'] = pd.to_datetime(
        df_tempo['ANO_CMPT'].astype(str) + '-' + 
        df_tempo['MES_CMPT'].astype(str) + '-01'
    )
    
    # Métrica para visualização temporal
    metrica_tempo = st.radio(
        "Selecione a métrica para análise temporal:",
        ["Internações", "Custo Total", "Permanência Média", "Taxa de Mortalidade"],
        horizontal=True
    )
    
    # Mapear seleção para coluna
    if metrica_tempo == "Internações":
        y_col = 'total_internacoes'
        y_label = 'Total de Internações'
    elif metrica_tempo == "Custo Total":
        y_col = 'custo_total'
        y_label = 'Custo Total (R$)'
    elif metrica_tempo == "Permanência Média":
        y_col = 'permanencia_media'
        y_label = 'Permanência Média (dias)'
    else:  # Taxa de Mortalidade
        y_col = 'taxa_mortalidade'
        y_label = 'Taxa de Mortalidade (%)'
    
    # Gráfico de linha temporal
    fig_tempo = px.line(
        df_tempo.sort_values('data'),
        x='data',
        y=y_col,
        title=f'Evolução de {y_label} para {info_doenca["nome"]}',
        labels={'data': 'Data', y_col: y_label},
        markers=True
    )
    st.plotly_chart(fig_tempo, use_container_width=True)
    
    # Seção 2: Análise por Faixa Etária
    st.subheader("Análise por Faixa Etária")
    
    # Juntar com dimensão paciente
    df_doenca_paciente = df_doenca.merge(
        data['dim_paciente'],
        on='ID_PACIENTE'
    )
    
    # Agrupar por faixa etária e sexo - ALTERADO: N_AIH em vez de ID_INTERNACAO
    df_faixa_etaria = df_doenca_paciente.groupby(['FAIXA_ETARIA', 'SEXO']).agg(
        total_internacoes=('N_AIH', 'count'),  # Modificado aqui
        taxa_mortalidade=('MORTE', 'mean')
    ).reset_index()
    
    # Aplicar multiplicação após a agregação
    df_faixa_etaria['taxa_mortalidade'] = df_faixa_etaria['taxa_mortalidade'] * 100
    
    # Gráfico de barras agrupadas por faixa etária e sexo
    fig_faixa_etaria = px.bar(
        df_faixa_etaria,
        x='FAIXA_ETARIA',
        y='total_internacoes',
        color='SEXO',
        barmode='group',
        title=f'Internações por Faixa Etária e Sexo - {info_doenca["nome"]}',
        labels={
            'FAIXA_ETARIA': 'Faixa Etária', 
            'total_internacoes': 'Total de Internações',
            'SEXO': 'Sexo'
        }
    )
    st.plotly_chart(fig_faixa_etaria, use_container_width=True)
    
    # Seção 3: Distribuição Geográfica
    st.subheader("Distribuição Geográfica")
    
    # Juntar com dimensão localização
    df_doenca_geo = df_doenca.merge(
        data['dim_localizacao'],
        on='ID_LOCALIZACAO'
    )
    
    # Agrupar por UF - ALTERADO: N_AIH em vez de ID_INTERNACAO e UF_RES em vez de UF_ZI
    df_uf = df_doenca_geo.groupby('UF_RES').agg(  # Modificado aqui: UF_RES é o nome correto
        total_internacoes=('N_AIH', 'count'),  # Modificado aqui
        taxa_mortalidade=('MORTE', 'mean')
    ).reset_index()
    
    # Aplicar multiplicação após a agregação
    df_uf['taxa_mortalidade'] = df_uf['taxa_mortalidade'] * 100
    
    # Gráfico de mapa coroplético (se disponível) ou barras
    try:
        fig_mapa = px.choropleth(
            df_uf,
            locations='UF_RES',  # Modificado aqui
            color='total_internacoes',
            scope="south america",
            center={"lat": -15.7801, "lon": -47.9292},
            title=f'Distribuição de {info_doenca["nome"]} por Estado',
            labels={'total_internacoes': 'Total de Internações', 'UF_RES': 'Estado'}  # Modificado aqui
        )
        st.plotly_chart(fig_mapa, use_container_width=True)
    except:
        # Se o mapa falhar, mostrar gráfico de barras
        fig_barras_uf = px.bar(
            df_uf.sort_values('total_internacoes', ascending=False),
            x='UF_RES',  # Modificado aqui
            y='total_internacoes',
            title=f'Internações por {info_doenca["nome"]} por Estado',
            labels={'UF_RES': 'Estado', 'total_internacoes': 'Total de Internações'}  # Modificado aqui
        )
        st.plotly_chart(fig_barras_uf, use_container_width=True)
    
    # Seção 4: Análise de Desfechos
    st.subheader("Análise de Desfechos")
    
    # Distribuição de desfechos
    df_desfechos = df_doenca.groupby('MORTE').agg(
        total=('N_AIH', 'count')  # Modificado aqui
    ).reset_index()
    
    # Adicionar descrições
    df_desfechos['DESFECHO'] = df_desfechos['MORTE'].map({0: 'Alta', 1: 'Óbito'})
    
    # Gráfico de pizza
    fig_desfechos = px.pie(
        df_desfechos,
        values='total',
        names='DESFECHO',
        title=f'Desfechos para {info_doenca["nome"]}',
        color='DESFECHO',
        color_discrete_map={'Alta': 'lightgreen', 'Óbito': 'salmon'}
    )
    st.plotly_chart(fig_desfechos, use_container_width=True)
    
    # Tabela de dados detalhados
    with st.expander("Ver dados detalhados"):
        # Agrupar dados por ano - ALTERADO: N_AIH em vez de ID_INTERNACAO
        df_detalhado = df_doenca.groupby('ANO_CMPT').agg(
            total_internacoes=('N_AIH', 'count'),  # Modificado aqui
            permanencia_media=('DIAS_PERMANENCIA', 'mean'),
            custo_total=('VAL_TOT', 'sum'),
            custo_medio=('VAL_TOT', 'mean'),
            taxa_mortalidade=('MORTE', 'mean')
        ).reset_index()

        # Aplicar multiplicação após a agregação
        df_detalhado['taxa_mortalidade'] = df_detalhado['taxa_mortalidade'] * 100
            
        # Formatar valores
        df_display = df_detalhado.copy()
        df_display['permanencia_media'] = df_display['permanencia_media'].round(2).astype(str) + ' dias'
        df_display['custo_total'] = df_display['custo_total'].apply(lambda x: f"R$ {x:,.2f}")
        df_display['custo_medio'] = df_display['custo_medio'].apply(lambda x: f"R$ {x:,.2f}")
        df_display['taxa_mortalidade'] = df_display['taxa_mortalidade'].round(2).astype(str) + '%'
        
        # Renomear colunas
        df_display = df_display.rename(columns={
            'ANO_CMPT': 'Ano',
            'total_internacoes': 'Total de Internações',
            'permanencia_media': 'Permanência Média',
            'custo_total': 'Custo Total',
            'custo_medio': 'Custo Médio',
            'taxa_mortalidade': 'Taxa de Mortalidade'
        })
        
        st.dataframe(df_display, use_container_width=True)
    
    # Data da última atualização
    st.caption(f"Dados atualizados em: {datetime.now().strftime('%d/%m/%Y')}")