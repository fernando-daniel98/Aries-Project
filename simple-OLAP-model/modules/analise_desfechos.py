import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def render(data):
    """
    Renderiza a página de Análise de Desfechos do Dashboard.
    
    Parâmetros:
    data: Dicionário contendo os dataframes do modelo dimensional
    """
    st.header("Análise de Desfechos Clínicos")
    
    # Filtros na barra lateral
    st.sidebar.subheader("Filtros para Análise de Desfechos")
    
    # Filtro de período
    anos_disponiveis = sorted(data['dim_tempo']['ANO_CMPT'].unique())
    
    # Seleção de intervalo de anos
    ano_inicial, ano_final = st.sidebar.select_slider(
        "Selecione o intervalo de anos:",
        options=anos_disponiveis,
        value=(min(anos_disponiveis), max(anos_disponiveis))
    )
    
    # Filtro de dimensão para análise
    dimensao_analise = st.sidebar.selectbox(
        "Dimensão para análise:",
        ["Diagnósticos", "Hospitais", "Regiões", "Faixa Etária"]
    )
    
    # Filtrar dados pelo intervalo de tempo selecionado
    fato_filtrado = data['fato'].merge(
        data['dim_tempo'].query(f"ANO_CMPT >= {ano_inicial} and ANO_CMPT <= {ano_final}"),
        on='ID_TEMPO'
    )
    
    # Estatísticas gerais de desfechos
    st.subheader("Estatísticas Gerais de Desfechos")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Taxa de mortalidade geral
    taxa_mortalidade = fato_filtrado['MORTE'].mean() * 100
    
    col1.metric(
        label="Taxa de Mortalidade", 
        value=f"{taxa_mortalidade:.2f}%"
    )
    
    # Tempo médio de permanência
    tempo_medio = fato_filtrado['DIAS_PERMANENCIA'].mean()
    col2.metric(
        label="Permanência Média", 
        value=f"{tempo_medio:.2f} dias"
    )
    
    # Total de óbitos
    total_obitos = int(fato_filtrado['MORTE'].sum())
    col3.metric(
        label="Total de Óbitos", 
        value=f"{total_obitos:,}"
    )
    
    # Total de internações
    total_internacoes = len(fato_filtrado)
    col4.metric(
        label="Total de Internações", 
        value=f"{total_internacoes:,}"
    )
    
    # Seção 1: Evolução temporal dos desfechos
    st.subheader("Evolução Temporal dos Desfechos")
    
    # Agrupar por ano e mês - MODIFICADO: N_AIH em vez de ID_INTERNACAO
    df_desfecho_tempo = fato_filtrado.groupby(['ANO_CMPT', 'MES_CMPT']).agg(
        taxa_mortalidade=('MORTE', 'mean'),
        tempo_permanencia=('DIAS_PERMANENCIA', 'mean'),
        total_internacoes=('N_AIH', 'count'),  # Modificado aqui
        total_obitos=('MORTE', 'sum')
    ).reset_index()
    
    # Converter taxa de mortalidade para percentual
    df_desfecho_tempo['taxa_mortalidade'] = df_desfecho_tempo['taxa_mortalidade'] * 100
    
    # Criar coluna de data para melhor visualização
    df_desfecho_tempo['data'] = pd.to_datetime(
        df_desfecho_tempo['ANO_CMPT'].astype(str) + '-' + 
        df_desfecho_tempo['MES_CMPT'].astype(str) + '-01'
    )
    
    # Seleção da métrica para o gráfico temporal
    metrica_tempo = st.radio(
        "Selecione a métrica para visualização:",
        ["Taxa de Mortalidade", "Tempo Médio de Permanência", "Total de Óbitos"],
        horizontal=True
    )
    
    # Mapear seleção para coluna correspondente
    if metrica_tempo == "Taxa de Mortalidade":
        y_col = 'taxa_mortalidade'
        y_label = 'Taxa de Mortalidade (%)'
    elif metrica_tempo == "Tempo Médio de Permanência":
        y_col = 'tempo_permanencia'
        y_label = 'Tempo Médio (dias)'
    else:
        y_col = 'total_obitos'
        y_label = 'Total de Óbitos'
    
    # Gráfico de linha temporal
    fig_tempo = px.line(
        df_desfecho_tempo.sort_values('data'),
        x='data',
        y=y_col,
        title=f'Evolução de {metrica_tempo} ao longo do tempo',
        labels={'data': 'Data', y_col: y_label},
        markers=True
    )
    
    # Ajustar layout se for taxa de mortalidade para começar em zero
    if metrica_tempo == "Taxa de Mortalidade":
        fig_tempo.update_layout(yaxis=dict(range=[0, max(df_desfecho_tempo['taxa_mortalidade']) * 1.1]))
    
    st.plotly_chart(fig_tempo, use_container_width=True)
    
    # Seção 2: Análise por dimensão selecionada
    st.subheader(f"Análise de Desfechos por {dimensao_analise}")
    
    # Preparar dados conforme dimensão selecionada
    if dimensao_analise == "Diagnósticos":
        # Juntar com dimensão diagnóstico
        df_analise = fato_filtrado.merge(
            data['dim_diagnostico'],
            on='ID_DIAGNOSTICO'
        )
        # Criar categorias de CID (primeiros 3 caracteres)
        df_analise['CATEGORIA_CID'] = df_analise['DIAG_PRINC'].str[:3]
        group_col = 'CATEGORIA_CID'
        col_name = 'Categoria CID'
        
    elif dimensao_analise == "Hospitais":
        # Juntar com dimensão hospital
        df_analise = fato_filtrado.merge(
            data['dim_hospital'],
            on='ID_HOSPITAL'
        )
        # Modificado para usar CNES em vez de NOME_HOSPITAL
        group_col = 'CNES'
        col_name = 'Hospital'
        
    elif dimensao_analise == "Regiões":
        # Juntar com dimensão localização
        df_analise = fato_filtrado.merge(
            data['dim_localizacao'],
            on='ID_LOCALIZACAO'
        )
        # Modificado: UF_RES em vez de UF_ZI
        group_col = 'UF_RES'
        col_name = 'Estado'
        
    else:  # Faixa Etária
        # Juntar com dimensão paciente
        df_analise = fato_filtrado.merge(
            data['dim_paciente'],
            on='ID_PACIENTE'
        )
        group_col = 'FAIXA_ETARIA'
        col_name = 'Faixa Etária'
    
    # Agrupar por dimensão selecionada
    try:
        df_desfecho_dim = df_analise.groupby(group_col).agg(
            taxa_mortalidade=('MORTE', 'mean'),
            tempo_permanencia=('DIAS_PERMANENCIA', 'mean'),
            total_internacoes=('N_AIH', 'count'),  # Modificado aqui
            total_obitos=('MORTE', 'sum')
        ).reset_index()
        
        # Converter taxa de mortalidade para percentual
        df_desfecho_dim['taxa_mortalidade'] = df_desfecho_dim['taxa_mortalidade'] * 100
        
        # Filtrar para apenas itens com número mínimo de internações (para relevância estatística)
        min_internacoes = 10
        df_desfecho_dim = df_desfecho_dim[df_desfecho_dim['total_internacoes'] >= min_internacoes]
        
        # Top N itens para visualização
        top_n = st.slider(f"Número de {dimensao_analise.lower()} a exibir:", min_value=5, max_value=20, value=10)
        
        # Variável de análise
        var_analise = st.selectbox(
            "Variável para análise:",
            ["Taxa de Mortalidade", "Tempo de Permanência", "Total de Óbitos"]
        )
        
        # Mapear seleção para coluna
        if var_analise == "Taxa de Mortalidade":
            col_var = 'taxa_mortalidade'
            formato = '{:.2f}%'
        elif var_analise == "Tempo de Permanência":
            col_var = 'tempo_permanencia'
            formato = '{:.2f} dias'
        else:  # Total de Óbitos
            col_var = 'total_obitos'
            formato = '{:,}'
        
        # Ordenar e pegar top N
        df_top = df_desfecho_dim.sort_values(col_var, ascending=False).head(top_n)
        
        # Gráfico de barras
        fig_top = px.bar(
            df_top,
            x=group_col,
            y=col_var,
            title=f'Top {top_n} {dimensao_analise} por {var_analise}',
            labels={group_col: col_name, col_var: var_analise},
            color=col_var,
            text_auto=True
        )
        
        # Ajustar layout para melhor visualização
        fig_top.update_layout(
            xaxis_tickangle=-45,
            yaxis=dict(title=var_analise)
        )
        
        st.plotly_chart(fig_top, use_container_width=True)
        
        # Seção 3: Análise de distribuição de tempo de permanência
        st.subheader("Distribuição do Tempo de Permanência")
        
        # Histograma de tempo de permanência
        fig_hist = px.histogram(
            fato_filtrado,
            x='DIAS_PERMANENCIA',
            nbins=30,
            title='Distribuição do Tempo de Permanência',
            labels={'DIAS_PERMANENCIA': 'Dias de Permanência', 'count': 'Frequência'},
            marginal='box'  # Adiciona um boxplot na margem
        )
        
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Seção 4: Análise específica de mortalidade
        st.subheader("Análise Detalhada de Mortalidade")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Taxa de mortalidade por sexo
            # Modificado: usar DESC_SEXO em vez de SEXO
            if 'DESC_SEXO' in df_analise.columns:
                df_mortalidade_sexo = df_analise.groupby('DESC_SEXO').agg(
                    taxa_mortalidade=('MORTE', 'mean'),
                    total_internacoes=('N_AIH', 'count')  # Modificado aqui
                ).reset_index()
                
                df_mortalidade_sexo['taxa_mortalidade'] = df_mortalidade_sexo['taxa_mortalidade'] * 100
                
                fig_sexo = px.bar(
                    df_mortalidade_sexo,
                    x='DESC_SEXO',  # Modificado aqui
                    y='taxa_mortalidade',
                    title='Taxa de Mortalidade por Sexo',
                    labels={'DESC_SEXO': 'Sexo', 'taxa_mortalidade': 'Taxa de Mortalidade (%)'},  # Modificado aqui
                    text_auto='.2f',
                    color='taxa_mortalidade'
                )
                st.plotly_chart(fig_sexo, use_container_width=True)
        
        with col2:
            # Taxa de mortalidade por faixa etária (se disponível)
            if 'FAIXA_ETARIA' in df_analise.columns:
                df_mortalidade_idade = df_analise.groupby('FAIXA_ETARIA').agg(
                    taxa_mortalidade=('MORTE', 'mean'),
                    total_internacoes=('N_AIH', 'count')  # Modificado aqui
                ).reset_index()
                
                df_mortalidade_idade['taxa_mortalidade'] = df_mortalidade_idade['taxa_mortalidade'] * 100
                
                fig_idade = px.bar(
                    df_mortalidade_idade,
                    x='FAIXA_ETARIA',
                    y='taxa_mortalidade',
                    title='Taxa de Mortalidade por Faixa Etária',
                    labels={'FAIXA_ETARIA': 'Faixa Etária', 'taxa_mortalidade': 'Taxa de Mortalidade (%)'},
                    text_auto='.2f',
                    color='taxa_mortalidade'
                )
                st.plotly_chart(fig_idade, use_container_width=True)
        
        # Tabela detalhada
        with st.expander("Ver tabela detalhada de desfechos"):
            # Formatar colunas para exibição
            df_display = df_desfecho_dim.copy()
            df_display['taxa_mortalidade'] = df_display['taxa_mortalidade'].round(2).astype(str) + ' %'
            df_display['tempo_permanencia'] = df_display['tempo_permanencia'].round(2).astype(str) + ' dias'
            
            # Renomear colunas
            df_display = df_display.rename(columns={
                group_col: col_name,
                'taxa_mortalidade': 'Taxa de Mortalidade',
                'tempo_permanencia': 'Tempo Médio de Permanência',
                'total_internacoes': 'Total de Internações',
                'total_obitos': 'Total de Óbitos'
            })
            
            # Ordenar por taxa de mortalidade
            df_display = df_display.sort_values('Taxa de Mortalidade', ascending=False)
            
            st.dataframe(df_display, use_container_width=True)
            
    except Exception as e:
        st.error(f"Erro ao processar dados para {dimensao_analise}: {str(e)}")
        st.info("Verifique se as colunas necessárias estão disponíveis nos dados.")
        
    # Seção 5: Comparativo de desfechos
    st.subheader("Comparativo de Desfechos")
    
    # Seleção das dimensões para comparativo
    dimensao_x = st.selectbox(
        "Selecione a primeira dimensão:",
        ["Diagnóstico", "Hospital", "Região", "Faixa Etária"],
        key="dim_x"
    )
    
    dimensao_y = st.selectbox(
        "Selecione a segunda dimensão:",
        ["Diagnóstico", "Hospital", "Região", "Faixa Etária"],
        key="dim_y",
        index=3  # Padrão para Faixa Etária se disponível
    )
    
    # Verificar se as dimensões são diferentes
    if dimensao_x != dimensao_y:
        try:
            # Preparar os dados para as dimensões selecionadas
            df_comparativo = fato_filtrado.copy()
            
            # Juntar com as dimensões necessárias
            dimensoes = [dimensao_x, dimensao_y]
            
            for dim in dimensoes:
                if dim == "Diagnóstico":
                    df_comparativo = df_comparativo.merge(
                        data['dim_diagnostico'],
                        on='ID_DIAGNOSTICO'
                    )
                    df_comparativo['CATEGORIA_CID'] = df_comparativo['DIAG_PRINC'].str[:3]
                
                elif dim == "Hospital":
                    df_comparativo = df_comparativo.merge(
                        data['dim_hospital'],
                        on='ID_HOSPITAL'
                    )
                
                elif dim == "Região":
                    df_comparativo = df_comparativo.merge(
                        data['dim_localizacao'],
                        on='ID_LOCALIZACAO'
                    )
                
                elif dim == "Faixa Etária":
                    df_comparativo = df_comparativo.merge(
                        data['dim_paciente'],
                        on='ID_PACIENTE'
                    )
            
            # Mapear dimensões para colunas - MODIFICADO
            mapeamento_colunas = {
                "Diagnóstico": 'CATEGORIA_CID',
                "Hospital": 'CNES',  # Modificado de NOME_HOSPITAL para CNES
                "Região": 'UF_RES',  # Modificado de UF_ZI para UF_RES
                "Faixa Etária": 'FAIXA_ETARIA'
            }
            
            col_x = mapeamento_colunas.get(dimensao_x)
            col_y = mapeamento_colunas.get(dimensao_y)
            
            # Filtrar para os valores mais frequentes para não sobrecarregar o gráfico
            valores_x = df_comparativo[col_x].value_counts().head(5).index.tolist()
            valores_y = df_comparativo[col_y].value_counts().head(5).index.tolist()
            
            df_filtered = df_comparativo[
                (df_comparativo[col_x].isin(valores_x)) & 
                (df_comparativo[col_y].isin(valores_y))
            ]
            
            # Agrupar por ambas dimensões
            df_heatmap = df_filtered.groupby([col_x, col_y]).agg(
                taxa_mortalidade=('MORTE', 'mean'),
                total_internacoes=('N_AIH', 'count')  # Modificado aqui
            ).reset_index()
            
            # Converter para percentual
            df_heatmap['taxa_mortalidade'] = df_heatmap['taxa_mortalidade'] * 100
            
            # Criar heatmap
            fig_heatmap = px.density_heatmap(
                df_heatmap,
                x=col_x,
                y=col_y,
                z='taxa_mortalidade',
                title=f'Taxa de Mortalidade por {dimensao_x} e {dimensao_y}',
                labels={
                    col_x: dimensao_x,
                    col_y: dimensao_y,
                    'taxa_mortalidade': 'Taxa de Mortalidade (%)'
                },
                text_auto='.2f',
                color_continuous_scale='RdYlGn_r'  # Escala de vermelho (alto) para verde (baixo)
            )
            
            st.plotly_chart(fig_heatmap, use_container_width=True)
            
        except Exception as e:
            st.error(f"Erro ao gerar heatmap comparativo: {str(e)}")
            st.info("Verifique se as dimensões selecionadas possuem dados suficientes.")
    else:
        st.warning("Por favor, selecione dimensões diferentes para o comparativo.")