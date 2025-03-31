import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

# Tema visual
TEMA = {
    'mapa': px.colors.sequential.Blues,  # Alterado para Blues em vez de Viridis
    'barras': '#2ecc71',
    'linha': '#e74c3c'
}

# Dicionário para mapear códigos de UF para nomes e siglas
UFS = {
    11: {'nome': 'Rondônia', 'sigla': 'RO'},
    12: {'nome': 'Acre', 'sigla': 'AC'},
    13: {'nome': 'Amazonas', 'sigla': 'AM'},
    14: {'nome': 'Roraima', 'sigla': 'RR'},
    15: {'nome': 'Pará', 'sigla': 'PA'},
    16: {'nome': 'Amapá', 'sigla': 'AP'},
    17: {'nome': 'Tocantins', 'sigla': 'TO'},
    21: {'nome': 'Maranhão', 'sigla': 'MA'},
    22: {'nome': 'Piauí', 'sigla': 'PI'},
    23: {'nome': 'Ceará', 'sigla': 'CE'},
    24: {'nome': 'Rio Grande do Norte', 'sigla': 'RN'},
    25: {'nome': 'Paraíba', 'sigla': 'PB'},
    26: {'nome': 'Pernambuco', 'sigla': 'PE'},
    27: {'nome': 'Alagoas', 'sigla': 'AL'},
    28: {'nome': 'Sergipe', 'sigla': 'SE'},
    29: {'nome': 'Bahia', 'sigla': 'BA'},
    31: {'nome': 'Minas Gerais', 'sigla': 'MG'},
    32: {'nome': 'Espírito Santo', 'sigla': 'ES'},
    33: {'nome': 'Rio de Janeiro', 'sigla': 'RJ'},
    35: {'nome': 'São Paulo', 'sigla': 'SP'},
    41: {'nome': 'Paraná', 'sigla': 'PR'},
    42: {'nome': 'Santa Catarina', 'sigla': 'SC'},
    43: {'nome': 'Rio Grande do Sul', 'sigla': 'RS'},
    50: {'nome': 'Mato Grosso do Sul', 'sigla': 'MS'},
    51: {'nome': 'Mato Grosso', 'sigla': 'MT'},
    52: {'nome': 'Goiás', 'sigla': 'GO'},
    53: {'nome': 'Distrito Federal', 'sigla': 'DF'}
}

def render(data):
    """Dashboard de Análise Geográfica"""
    st.header("🏥 Análise Geográfica de Internações", divider='rainbow')
    
    # ========== SIDEBAR ==========
    with st.sidebar:
        # Filtro de ano
        anos_disponiveis = sorted(data['dim_tempo']['ANO_CMPT'].unique())
        ano_selecionado = st.selectbox("Ano:", anos_disponiveis, index=len(anos_disponiveis)-1)
        
        # Filtro de nível geográfico
        nivel_geografico = st.radio(
            "Nível de análise:",
            ["Estado", "Município"]
        )
        
        # Se for análise por município, permitir filtrar por UF
        uf_filtro = None
        if nivel_geografico == "Município":
            # Obter lista de UFs disponíveis nos dados
            ufs_disponiveis = data['dim_localizacao']['UF_RES'].unique()
            # Converter códigos para nomes de UF
            opcoes_uf = {
                (UFS.get(uf, {}).get('nome', f'UF {uf}')): uf 
                for uf in ufs_disponiveis if uf in UFS
            }
            
            if opcoes_uf:
                uf_selecionada = st.selectbox(
                    "Estado para análise municipal:",
                    list(opcoes_uf.keys())
                )
                uf_filtro = opcoes_uf.get(uf_selecionada)

    # ========== PROCESSAMENTO ==========
    # Filtrar por ano
    df_filtrado = (
        data['fato']
        .merge(data['dim_tempo'][data['dim_tempo']['ANO_CMPT'] == ano_selecionado], on='ID_TEMPO')
        .merge(data['dim_localizacao'], on='ID_LOCALIZACAO')
    )
    
    # Aplicar filtro adicional por UF se estiver analisando municípios
    if nivel_geografico == "Município" and uf_filtro is not None:
        df_filtrado = df_filtrado[df_filtrado['UF_RES'] == uf_filtro]
    
    # Definir coluna de agrupamento e nome baseado no nível
    if nivel_geografico == "Estado":
        # Converter códigos de UF para nomes
        df_filtrado['nome_uf'] = df_filtrado['UF_RES'].apply(
            lambda x: UFS.get(x, {}).get('nome', f'UF {x}')
        )
        df_filtrado['sigla_uf'] = df_filtrado['UF_RES'].apply(
            lambda x: UFS.get(x, {}).get('sigla', str(x))
        )
        group_col = 'nome_uf'
        location_col = 'sigla_uf'  # Para o mapa, usamos a sigla
        col_name = 'Estado'
    else:
        # Para municípios, usar o código do município
        # Ideal seria converter para nomes, mas depende dos dados disponíveis
        group_col = 'MUNIC_RES'
        location_col = 'MUNIC_RES'
        col_name = 'Município'
    
    # Agregar dados
    df_geo = df_filtrado.groupby(group_col).agg(
        total_internacoes=('N_AIH', 'count'),
        custo_total=('VAL_TOT', 'sum'),
        permanencia_media=('DIAS_PERMANENCIA', 'mean'),
        mortalidade=('MORTE', 'mean')
    ).reset_index()
    
    # Adicionar coluna de localização para o mapa
    if nivel_geografico == "Estado":
        df_geo['location'] = df_filtrado.groupby(group_col)['sigla_uf'].first().reset_index()['sigla_uf']
    else:
        df_geo['location'] = df_geo[group_col]
    
    # Converter taxa para percentual
    df_geo['mortalidade'] = df_geo['mortalidade'] * 100

    # ========== VISUALIZAÇÃO ==========
    # Seção 1: Mapa ou Gráfico de Barras
    st.subheader(f"Distribuição de Internações por {nivel_geografico} em {ano_selecionado}")
    
    # Criar visualização específica por nível
    if nivel_geografico == "Estado":
        try:
            # Mapa do Brasil simplificado
            fig = px.choropleth(
                df_geo,
                locations='location',  # Usando sigla do estado
                locationmode='ISO-3',  # Um pouco incompatível com siglas BR, mas funciona
                color='total_internacoes',
                color_continuous_scale=TEMA['mapa'],
                scope="south america",
                title=f"Total de Internações por Estado ({ano_selecionado})",
                labels={
                    'total_internacoes': 'Total de Internações',
                    'location': 'Estado'
                }
            )
            
            # Configurar aparência do mapa
            fig.update_geos(
                showcountries=False,
                showcoastlines=True,
                showland=True,
                fitbounds="locations",
                visible=False,
                landcolor='lightgray'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Erro ao criar mapa: {str(e)}")
            # Fallback para gráfico de barras
            usar_barras = True
        
    else:  # Município - sempre usar barras
        usar_barras = True
    
    # Se não conseguir criar o mapa ou for análise municipal, usar gráfico de barras
    if nivel_geografico != "Estado" or 'usar_barras' in locals():
        # Mostrar apenas os top 15 para não ficar sobrecarregado
        df_top = df_geo.sort_values('total_internacoes', ascending=False).head(15)
        
        fig = px.bar(
            df_top,
            x=group_col,
            y='total_internacoes',
            color='total_internacoes',
            color_continuous_scale=TEMA['mapa'],
            title=f"Top 15 {nivel_geografico}s com Maior Número de Internações ({ano_selecionado})",
            labels={
                group_col: col_name,
                'total_internacoes': 'Total de Internações'
            }
        )
        
        # Ajustar para melhor visualização
        fig.update_layout(xaxis_tickangle=-45)
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Seção 2: Análise Detalhada
    st.subheader(f"Análise Detalhada por {nivel_geografico}")
    
    # Selecionar local para análise detalhada
    locais_disponiveis = df_geo.sort_values('total_internacoes', ascending=False)[group_col].tolist()
    
    if locais_disponiveis:
        local_selecionado = st.selectbox(
            f"Selecione um {nivel_geografico.lower()} para detalhes:",
            locais_disponiveis
        )
        
        # Obter dados do local selecionado
        dados = df_geo[df_geo[group_col] == local_selecionado].iloc[0]
        
        # Exibir métricas principais
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Internações", f"{int(dados['total_internacoes']):,}")
        col2.metric("Custo Total", f"R$ {dados['custo_total']:,.2f}")
        col3.metric("Permanência Média", f"{dados['permanencia_media']:.1f} dias")
        col4.metric("Taxa de Mortalidade", f"{dados['mortalidade']:.2f}%")
        
        # Se tivermos dados detalhados, mostrar análise adicional
        if nivel_geografico == "Estado" and len(df_filtrado) > 0:
            st.subheader(f"Principais Municípios de {local_selecionado}")
            
            # Filtrar para o estado selecionado
            codigo_uf = next((uf for uf, info in UFS.items() if info['nome'] == local_selecionado), None)
            
            if codigo_uf:
                df_municipios = df_filtrado[df_filtrado['UF_RES'] == codigo_uf]
                
                # Agrupar por município
                df_mun = df_municipios.groupby('MUNIC_RES').agg(
                    total_internacoes=('N_AIH', 'count'),
                    custo_total=('VAL_TOT', 'sum')
                ).reset_index()
                
                # Mostrar top 10 municípios
                df_top_mun = df_mun.sort_values('total_internacoes', ascending=False).head(10)
                
                fig = px.bar(
                    df_top_mun,
                    x='MUNIC_RES',
                    y='total_internacoes',
                    color='total_internacoes',
                    title=f"Top 10 Municípios de {local_selecionado} por Internações",
                    labels={
                        'MUNIC_RES': 'Código do Município',
                        'total_internacoes': 'Total de Internações'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)

    # Tabela detalhada
    with st.expander("Ver tabela de dados completa"):
        # Formatar colunas para exibição
        df_display = df_geo.copy()
        df_display['permanencia_media'] = df_display['permanencia_media'].round(2).astype(str) + ' dias'
        df_display['custo_total'] = df_display['custo_total'].apply(lambda x: f"R$ {x:,.2f}")
        df_display['mortalidade'] = df_display['mortalidade'].round(2).astype(str) + '%'
        
        # Renomear colunas
        df_display = df_display.rename(columns={
            group_col: col_name,
            'total_internacoes': 'Total de Internações',
            'custo_total': 'Custo Total',
            'permanencia_media': 'Permanência Média',
            'mortalidade': 'Taxa de Mortalidade'
        }).drop(columns=['location'])  # Remover coluna auxiliar
        
        st.dataframe(df_display, use_container_width=True)

if __name__ == "__main__":
    # Para teste individual do módulo
    from dados import carregar_dados
    render(carregar_dados())