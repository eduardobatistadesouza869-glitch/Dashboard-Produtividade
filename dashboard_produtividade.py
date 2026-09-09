import pandas as pd
import streamlit as st
import plotly.express as px
import json
import os

# -----------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO VISUAL ("A elegant and perfect style")
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Gestão de Produtividade Logística",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS personalizada para acabamento premium
st.markdown("""
<style>
    /* Estilo do fundo e fontes */
    .main {
        background-color: #f8f9fa;
    }
    h1, h2, h3 {
        color: #1e293b;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        font-weight: 600;
    }
    
    /* Customização dos Cards / Métricas */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #0f172a !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.88rem !important;
        color: #64748b !important;
        font-weight: 600 !important;
    }
    
    /* Destaques e Alertas */
    .suggestion-box {
        background-color: #f0f9ff;
        border-left: 4px solid #0284c7;
        padding: 10px 14px;
        border-radius: 4px;
        margin-top: 5px;
        margin-bottom: 15px;
        font-size: 0.85rem;
        color: #0369a1;
    }
    .critical-card {
        background-color: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. FUNÇÕES AUXILIARES DE TRATAMENTO DE DADOS
# -----------------------------------------------------------------------------
def converter_duracao_para_horas(duracao_str):
    """
    Converte strings de duração nos formatos HH:MM ou HH:MM:SS para horas em formato decimal.
    Suporta durações maiores que 24 horas.
    """
    if pd.isna(duracao_str) or str(duracao_str).strip() in ["", "nan", "None"]:
        return 0.0
    
    try:
        partes = str(duracao_str).strip().split(":")
        if len(partes) == 2:
            horas = float(partes[0])
            minutos = float(partes[1])
            return horas + (minutos / 60.0)
        elif len(partes) == 3:
            horas = float(partes[0])
            minutos = float(partes[1])
            segundos = float(partes[2])
            return horas + (minutos / 60.0) + (segundos / 3600.0)
        else:
            return 0.0
    except Exception:
        return 0.0

def converter_numero_flexivel(valor):
    """
    Converte um valor numérico vindo da planilha para float, detectando
    automaticamente se o separador decimal é vírgula (formato brasileiro,
    ex: 1.234,56) ou ponto (formato internacional, ex: 1234.56).

    Regras:
    - Se houver vírgula E ponto no mesmo valor: assume formato brasileiro
      com separador de milhar (ponto) e decimal (vírgula) -> "1.234,56" -> 1234.56
    - Se houver apenas vírgula: a vírgula é o separador decimal -> "1234,56" -> 1234.56
    - Se houver apenas ponto (ou nenhum separador): já está no formato
      correto para o Python -> "12.5" -> 12.5 / "1234" -> 1234.0
      (Isso cobre o caso do campo Peso, que vem da planilha usando ponto
      como separador decimal, não como separador de milhar.)
    """
    if pd.isna(valor):
        return 0.0

    texto = str(valor).strip()
    if texto in ["", "nan", "None"]:
        return 0.0

    tem_virgula = "," in texto
    tem_ponto = "." in texto

    try:
        if tem_virgula and tem_ponto:
            texto = texto.replace(".", "").replace(",", ".")
        elif tem_virgula and not tem_ponto:
            texto = texto.replace(",", ".")
        # Se só tem ponto (ou nenhum separador), o valor já está pronto
        # para ser convertido diretamente, sem remover nada.
        return float(texto)
    except Exception:
        return 0.0

CONFIG_PATH = "filtros_salvos.json"

def carregar_config():
    """
    Carrega os filtros salvos anteriormente (período, exclusões e metas manuais)
    de um arquivo local, para que o usuário não precise refazê-los a cada acesso.
    """
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def salvar_config(config):
    """
    Persiste os filtros atuais em disco para reutilização em futuras visitas.
    """
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2, default=str)
    except Exception:
        pass

@st.cache_data(ttl=300)
def carregar_dados_google_sheets(url_planilha):
    """
    Lê a aba 'Página1' diretamente do Google Sheets e realiza o saneamento básico das colunas.
    """
    try:
        # Extrai a chave (ID) da URL
        if "/edit" in url_planilha:
            sheet_id = url_planilha.split("/d/")[1].split("/edit")[0]
        else:
            sheet_id = url_planilha
            
        url_csv = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=P%C3%A1gina1"
        
        df = pd.read_csv(url_csv)
        
        # Mapeamento e normalização flexível das colunas
        colunas_map = {}
        for col in df.columns:
            c_upper = str(col).strip().upper()
            if "NOME" in c_upper:
                colunas_map[col] = "Nome"
            elif "TAREFA" in c_upper:
                colunas_map[col] = "tipo Tarefa"
            elif "PRODUTO" in c_upper or "PROD" in c_upper:
                colunas_map[col] = "Qt Produtos"
            elif "UNIDADE" in c_upper or "UNID" in c_upper:
                colunas_map[col] = "Unidades"
            elif "PESO" in c_upper:
                colunas_map[col] = "Peso"
            elif "VOLUME" in c_upper or "VOL" in c_upper:
                colunas_map[col] = "Volume"
            elif "DURA" in c_upper:
                colunas_map[col] = "Duração"
            elif "DATA" in c_upper:
                colunas_map[col] = "Data"
            elif "RUA" in c_upper:
                colunas_map[col] = "Rua"

        df = df.rename(columns=colunas_map)
        
        # Tratamento de datas
        if "Data" in df.columns:
            df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce")
            
        # Tratamento de valores numéricos (detecta automaticamente vírgula ou ponto como decimal)
        for col_num in ["Qt Produtos", "Unidades", "Peso", "Volume"]:
            if col_num in df.columns:
                df[col_num] = df[col_num].apply(converter_numero_flexivel)
            else:
                df[col_num] = 0

        # Tratamento do tempo
        if "Duração" in df.columns:
            df["Horas_Decimais"] = df["Duração"].apply(converter_duracao_para_horas)
        else:
            df["Horas_Decimais"] = 0.0

        # Limpeza na coluna Nome
        df["Nome"] = df["Nome"].astype(str).str.strip().str.title()
        df = df[df["Nome"].str.upper() != "NAN"]

        return df, None
    except Exception as e:
        return None, f"Erro ao processar dados da planilha: {str(e)}"

# -----------------------------------------------------------------------------
# 3. BARRA LATERAL (FILTROS, EXCLUSÕES E CONFIGURAÇÕES)
# -----------------------------------------------------------------------------
st.sidebar.title("⚙️ Painel de Controle")

URL_PADRAO = "https://docs.google.com/spreadsheets/d/1fzxNS3p6e9UdWFGE49b7Z2IgwnJ2wNWvUWgb2cqDy5M/edit?usp=sharing"

with st.sidebar.expander("🔗 Fonte de Dados", expanded=False):
    url_input = st.text_input("Link do Google Sheets", value=URL_PADRAO)

if st.sidebar.button("🔄 Recarregar Dados"):
    st.cache_data.clear()
    st.rerun()

# Carregamento inicial
df_raw, erro = carregar_dados_google_sheets(url_input)

if erro:
    st.error(f"⚠️ {erro}")
    st.stop()

if df_raw is None or df_raw.empty:
    st.warning("Nenhum dado encontrado na planilha.")
    st.stop()

# Carrega os filtros salvos de visitas anteriores (período, exclusões e metas)
config_salva = carregar_config()

# A exclusão de colaboradores agora é feita individualmente dentro de cada
# aba (Separação / Conferência), pois um operador pode atuar nos dois
# ambientes e a exclusão em um não deve afetar o outro.
df_base = df_raw.copy()

# --- FILTRO DE DATAS ---
st.sidebar.markdown("---")
st.sidebar.subheader("📅 Período de Análise")

data_min_base = df_base["Data"].min()
data_max_base = df_base["Data"].max()

if pd.notna(data_min_base) and pd.notna(data_max_base):
    # Usa o período salvo anteriormente, se ainda estiver dentro do intervalo válido
    data_inicio_padrao = data_min_base.date()
    data_fim_padrao = data_max_base.date()
    try:
        if config_salva.get("data_inicio") and config_salva.get("data_fim"):
            di = pd.to_datetime(config_salva["data_inicio"]).date()
            df_ = pd.to_datetime(config_salva["data_fim"]).date()
            if data_min_base.date() <= di <= data_max_base.date():
                data_inicio_padrao = di
            if data_min_base.date() <= df_ <= data_max_base.date():
                data_fim_padrao = df_
    except Exception:
        pass

    datas_selecionadas = st.sidebar.date_input(
        "Selecione o intervalo:",
        value=(data_inicio_padrao, data_fim_padrao),
        min_value=data_min_base.date(),
        max_value=data_max_base.date()
    )
    if isinstance(datas_selecionadas, tuple) and len(datas_selecionadas) == 2:
        df_filtrado = df_base[
            (df_base["Data"].dt.date >= datas_selecionadas[0]) &
            (df_base["Data"].dt.date <= datas_selecionadas[1])
        ]
        # Salva o período escolhido para a próxima visita
        config_salva["data_inicio"] = str(datas_selecionadas[0])
        config_salva["data_fim"] = str(datas_selecionadas[1])
        salvar_config(config_salva)
    else:
        df_filtrado = df_base
else:
    df_filtrado = df_base

st.sidebar.caption("💾 Os filtros são salvos automaticamente para as próximas visitas.")
if st.sidebar.button("🗑️ Limpar Filtros Salvos"):
    salvar_config({})
    st.sidebar.success("Filtros salvos apagados! Recarregue a página para aplicar os padrões.")
    st.rerun()

# -----------------------------------------------------------------------------
# 4. NAVEGAÇÃO DE AMBIENTES (SEPARAÇÃO VS CONFERÊNCIA)
# -----------------------------------------------------------------------------
st.title("📦 Monitoramento de Produtividade Operacional")

aba_separacao, aba_conferencia = st.tabs([
    "🛒 AMBIENTE DE SEPARAÇÃO (PICKING)", 
    "🔍 AMBIENTE DE CONFERÊNCIA"
])

def processar_ambiente(df_input, termo_busca_tarefa, n_top_sugestao, nome_ambiente, config_salva):
    """
    Filtra os dados por ambiente, calcula a sugestão baseada no TOP N, 
    permite ajuste manual de metas e constrói o dashboard específico.
    """
    # Filtragem por tipo de tarefa
    df_ambiente = df_input[df_input["tipo Tarefa"].astype(str).str.upper().str.contains(termo_busca_tarefa, na=False)].copy()

    if df_ambiente.empty:
        st.info(f"Nenhum registro encontrado para o ambiente de **{nome_ambiente}** no período selecionado.")
        return

    # --- FILTRO DE EXCLUSÃO DE COLABORADORES (específico deste ambiente) ---
    st.markdown(f"#### 🚫 Exclusão de Colaboradores — {nome_ambiente}")
    lista_colaboradores_ambiente = sorted(df_ambiente["Nome"].unique().tolist())

    # Recupera a exclusão salva anteriormente, filtrando apenas nomes que ainda existem
    chave_exclusao = f"excluidos_{nome_ambiente}"
    excluidos_salvos = [
        n for n in config_salva.get(chave_exclusao, []) if n in lista_colaboradores_ambiente
    ]

    excluidos_ambiente = st.multiselect(
        f"Selecione colaboradores a EXCLUIR apenas do ambiente de {nome_ambiente}:",
        options=lista_colaboradores_ambiente,
        default=excluidos_salvos,
        help="Afeta somente este ambiente. Um operador excluído aqui continua aparecendo normalmente na outra aba.",
        key=f"exclusao_{nome_ambiente}"
    )

    # Salva a exclusão escolhida para a próxima visita
    if config_salva.get(chave_exclusao) != excluidos_ambiente:
        config_salva[chave_exclusao] = excluidos_ambiente
        salvar_config(config_salva)

    df_ambiente = df_ambiente[~df_ambiente["Nome"].isin(excluidos_ambiente)].copy()

    if df_ambiente.empty:
        st.info(f"Todos os colaboradores de **{nome_ambiente}** foram excluídos do período selecionado.")
        return

    # Consolidado por Operador
    agrupado = df_ambiente.groupby("Nome").agg(
        Total_Visitas=("Qt Produtos", "sum"),
        Total_Unidades=("Unidades", "sum"),
        Total_Peso=("Peso", "sum"),
        Total_Volume=("Volume", "sum"),
        Tempo_Horas=("Horas_Decimais", "sum")
    ).reset_index()

    # Remove operadores sem registro de tempo para não gerar divisão por zero
    agrupado = agrupado[agrupado["Tempo_Horas"] > 0].copy()

    if agrupado.empty:
        st.warning(f"Existem dados para {nome_ambiente}, mas nenhum operador possui tempo registrado maior que zero.")
        return

    # Cálculo dos KPIs Individuais
    agrupado["UPH"] = (agrupado["Total_Unidades"] / agrupado["Tempo_Horas"]).round(1)
    agrupado["PPH"] = (agrupado["Total_Visitas"] / agrupado["Tempo_Horas"]).round(1)
    agrupado["KPH"] = (agrupado["Total_Peso"] / agrupado["Tempo_Horas"]).round(1)

    # -------------------------------------------------------------------------
    # CÁLCULO DE METAS POR REFERÊNCIA (SUGESTÃO TOP N)
    # -------------------------------------------------------------------------
    top_uph = agrupado.nlargest(n_top_sugestao, "UPH")["UPH"].mean()
    top_pph = agrupado.nlargest(n_top_sugestao, "PPH")["PPH"].mean()
    top_kph = agrupado.nlargest(n_top_sugestao, "KPH")["KPH"].mean()

    sugestao_uph_val = round(top_uph if pd.notna(top_uph) else 100.0, 1)
    sugestao_pph_val = round(top_pph if pd.notna(top_pph) else 30.0, 1)
    sugestao_kph_val = round(top_kph if pd.notna(top_kph) else 100.0, 1)

    # Usa a meta salva anteriormente como valor inicial, se existir; caso contrário, a sugestão automática
    valor_inicial_uph = config_salva.get(f"meta_uph_{nome_ambiente}", sugestao_uph_val)
    valor_inicial_pph = config_salva.get(f"meta_pph_{nome_ambiente}", sugestao_pph_val)
    valor_inicial_kph = config_salva.get(f"meta_kph_{nome_ambiente}", sugestao_kph_val)

    # Bloco de Ajuste de Metas
    st.markdown(f"### 🎯 Definição de Metas — {nome_ambiente}")
    
    col_meta1, col_meta2, col_meta3 = st.columns(3)
    with col_meta1:
        meta_uph_manual = st.number_input(
            f"Meta Manual UPH (Unidades/Hora) - {nome_ambiente}",
            value=float(valor_inicial_uph),
            step=5.0,
            key=f"meta_uph_{nome_ambiente}"
        )
        st.markdown(
            f"<div class='suggestion-box'>💡 <b>Sugestão Automática: {sugestao_uph_val} UPH</b> "
            f"(Média do TOP {n_top_sugestao} de {nome_ambiente})</div>", 
            unsafe_allow_html=True
        )

    with col_meta2:
        meta_pph_manual = st.number_input(
            f"Meta Manual PPH (Visitas/Hora) - {nome_ambiente}",
            value=float(valor_inicial_pph),
            step=2.0,
            key=f"meta_pph_{nome_ambiente}"
        )
        st.markdown(
            f"<div class='suggestion-box'>💡 <b>Sugestão Automática: {sugestao_pph_val} PPH</b> "
            f"(Média do TOP {n_top_sugestao} de {nome_ambiente})</div>", 
            unsafe_allow_html=True
        )

    with col_meta3:
        meta_kph_manual = st.number_input(
            f"Meta Manual KPH (Kg/Hora) - {nome_ambiente}",
            value=float(valor_inicial_kph),
            step=5.0,
            key=f"meta_kph_{nome_ambiente}"
        )
        st.markdown(
            f"<div class='suggestion-box'>💡 <b>Sugestão Automática: {sugestao_kph_val} KPH</b> "
            f"(Média do TOP {n_top_sugestao} de {nome_ambiente})</div>", 
            unsafe_allow_html=True
        )

    # Salva as metas manuais escolhidas para a próxima visita
    if (config_salva.get(f"meta_uph_{nome_ambiente}") != meta_uph_manual or
            config_salva.get(f"meta_pph_{nome_ambiente}") != meta_pph_manual or
            config_salva.get(f"meta_kph_{nome_ambiente}") != meta_kph_manual):
        config_salva[f"meta_uph_{nome_ambiente}"] = meta_uph_manual
        config_salva[f"meta_pph_{nome_ambiente}"] = meta_pph_manual
        config_salva[f"meta_kph_{nome_ambiente}"] = meta_kph_manual
        salvar_config(config_salva)

    # Atingimento e Status
    agrupado["% Meta UPH"] = ((agrupado["UPH"] / meta_uph_manual) * 100).round(1)
    agrupado["% Meta PPH"] = ((agrupado["PPH"] / meta_pph_manual) * 100).round(1)
    agrupado["% Meta KPH"] = ((agrupado["KPH"] / meta_kph_manual) * 100).round(1)

    def aplicar_status(row):
        pct_uph = row["% Meta UPH"]
        pct_pph = row["% Meta PPH"]
        pct_kph = row["% Meta KPH"]

        # CAMINHO NORMAL: mantém a exigência cheia de UPH e PPH, mas o peso
        # (KPH) só precisa atingir 40% da meta — cobre operações com mix de
        # produtos leves, onde o peso naturalmente fica abaixo da meta.
        bateu_normal = pct_uph >= 100 and pct_pph >= 100 and pct_kph >= 40

        # CAMINHO COMPENSADO PELO PESO: se o colaborador bateu a meta de
        # peso (produtos mais pesados que reduzem o ritmo de UPH/PPH), a
        # exigência de UPH e PPH cai para 50% da meta.
        bateu_compensado = pct_kph >= 100 and pct_uph >= 50 and pct_pph >= 50

        if bateu_normal or bateu_compensado:
            return "🟢 Na Meta"

        # Faixa de Atenção: mesma lógica dos dois caminhos, mas com os
        # limiares reduzidos a 80% (mantendo a mesma régua usada no restante
        # do dashboard para "quase batendo a meta").
        quase_normal = pct_uph >= 80 and pct_pph >= 80 and pct_kph >= 32   # 80% de 40%
        quase_compensado = pct_kph >= 80 and pct_uph >= 40 and pct_pph >= 40  # 80% de 50%

        if quase_normal or quase_compensado:
            return "🟡 Atenção"

        return "🔴 Crítico"

    agrupado["Status"] = agrupado.apply(aplicar_status, axis=1)
    agrupado = agrupado.sort_values(by="UPH", ascending=False).reset_index(drop=True)
    agrupado.index += 1

    # -------------------------------------------------------------------------
    # RESUMO DA OPERAÇÃO (METRICS)
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown(f"### 📊 Visão Geral do Período — {nome_ambiente}")

    tot_unid = agrupado["Total_Unidades"].sum()
    tot_visitas = agrupado["Total_Visitas"].sum()
    tot_peso = agrupado["Total_Peso"].sum()
    tot_horas = agrupado["Tempo_Horas"].sum()
    uph_media_eq = round(tot_unid / tot_horas, 1) if tot_horas > 0 else 0
    kph_media_eq = round(tot_peso / tot_horas, 1) if tot_horas > 0 else 0

    c_na_meta = (agrupado["Status"] == "🟢 Na Meta").sum()
    c_atencao = (agrupado["Status"] == "🟡 Atenção").sum()
    c_critico = (agrupado["Status"] == "🔴 Crítico").sum()

    m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
    m1.metric("Unidades Processadas", f"{int(tot_unid):,}")
    m2.metric("Total de Visitas", f"{int(tot_visitas):,}")
    m3.metric("Peso Processado", f"{tot_peso:,.1f} kg")
    m4.metric("Média UPH da Equipe", f"{uph_media_eq} unid/h")
    m5.metric("Média KPH da Equipe", f"{kph_media_eq} kg/h")
    m6.metric("Operadores Ativos", len(agrupado))
    m7.metric("Status da Equipe", f"🟢{c_na_meta} | 🟡{c_atencao} | 🔴{c_critico}")

    # -------------------------------------------------------------------------
    # LEADERBOARD E ALERTAS CRÍTICOS
    # -------------------------------------------------------------------------
    st.markdown("---")
    col_tabela, col_alertas = st.columns([2, 1])

    with col_tabela:
        st.subheader("🏆 Ranking de Colaboradores")
        st.dataframe(
            agrupado[["Status", "Nome", "UPH", "% Meta UPH", "PPH", "% Meta PPH", "KPH", "% Meta KPH", "Total_Unidades", "Total_Peso", "Tempo_Horas"]],
            column_config={
                "Status": st.column_config.TextColumn("Status", width="medium"),
                "Nome": "Colaborador",
                "UPH": st.column_config.NumberColumn("UPH", format="%.1f 📦"),
                "% Meta UPH": st.column_config.ProgressColumn(
                    "% Meta UPH",
                    format="%.1f%%",
                    min_value=0,
                    max_value=150
                ),
                "PPH": st.column_config.NumberColumn("PPH", format="%.1f 🚶"),
                "% Meta PPH": st.column_config.ProgressColumn(
                    "% Meta PPH",
                    format="%.1f%%",
                    min_value=0,
                    max_value=150
                ),
                "KPH": st.column_config.NumberColumn("KPH (kg/h)", format="%.1f ⚖️"),
                "% Meta KPH": st.column_config.ProgressColumn(
                    "% Meta KPH",
                    format="%.1f%%",
                    min_value=0,
                    max_value=150
                ),
                "Total_Peso": st.column_config.NumberColumn("Peso Processado", format="%.1f kg ⚖️"),
                "Tempo_Horas": st.column_config.NumberColumn("Horas Trab.", format="%.1f h"),
            },
            use_container_width=True
        )

    with col_alertas:
        st.subheader("⚠️ Operadores em Zona Crítica")
        df_criticos = agrupado[agrupado["Status"] == "🔴 Crítico"]

        if not df_criticos.empty:
            for _, r in df_criticos.iterrows():
                st.markdown(
                    f"<div class='critical-card'>"
                    f"<b>👤 {r['Nome']}</b><br>"
                    f"• <b>UPH:</b> {r['UPH']} / Meta {meta_uph_manual} ({r['% Meta UPH']}%)<br>"
                    f"• <b>PPH:</b> {r['PPH']} / Meta {meta_pph_manual} ({r['% Meta PPH']}%)<br>"
                    f"• <b>KPH:</b> {r['KPH']} kg/h / Meta {meta_kph_manual} kg/h ({r['% Meta KPH']}%)<br>"
                    f"• <b>Tempo Registrado:</b> {round(r['Tempo_Horas'], 1)}h"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.success("🎉 Excelente! Nenhum operador no ambiente crítico neste período.")

    # -------------------------------------------------------------------------
    # GRÁFICO DE COMPARAÇÃO DE DESEMPENHO
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("📈 Comparativo de Desempenho x Meta")

    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        fig = px.bar(
            agrupado,
            x="Nome",
            y="UPH",
            color="Status",
            color_discrete_map={
                "🟢 Na Meta": "#16a34a",
                "🟡 Atenção": "#eab308",
                "🔴 Crítico": "#dc2626"
            },
            text="UPH",
            title=f"Rendimento Individual de UPH - {nome_ambiente}"
        )
        fig.add_hline(y=meta_uph_manual, line_dash="dash", line_color="#0284c7", annotation_text="Meta UPH")
        fig.update_layout(xaxis_title="Colaborador", yaxis_title="Unidades Por Hora (UPH)", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    with col_graf2:
        fig_peso = px.bar(
            agrupado,
            x="Nome",
            y="KPH",
            color="Status",
            color_discrete_map={
                "🟢 Na Meta": "#16a34a",
                "🟡 Atenção": "#eab308",
                "🔴 Crítico": "#dc2626"
            },
            text="KPH",
            title=f"Rendimento Individual de Peso (KPH) - {nome_ambiente}"
        )
        fig_peso.add_hline(y=meta_kph_manual, line_dash="dash", line_color="#0284c7", annotation_text="Meta KPH")
        fig_peso.update_layout(xaxis_title="Colaborador", yaxis_title="Quilos Por Hora (KPH)", template="plotly_white")
        st.plotly_chart(fig_peso, use_container_width=True)

# Execução das abas separadas
with aba_separacao:
    processar_ambiente(df_filtrado, termo_busca_tarefa="SEPARA", n_top_sugestao=8, nome_ambiente="Separação", config_salva=config_salva)

with aba_conferencia:
    processar_ambiente(df_filtrado, termo_busca_tarefa="CONF", n_top_sugestao=2, nome_ambiente="Conferência", config_salva=config_salva)

# -----------------------------------------------------------------------------
# 5. GLOSSÁRIO OPERACIONAL E EXPLICAÇÕES (RODAPÉ)
# -----------------------------------------------------------------------------
st.markdown("---")
with st.expander("📖 Glossário Operacional e Regras de Cálculo", expanded=False):
    st.markdown("""
    ### Siglas e Conceitos Utilizados no Dashboard

    * **UPH (Units Per Hour / Unidades por Hora):**  
      Mede a taxa de movimentação física de itens. Calculado dividindo a quantidade total de **Unidades** pelo tempo total trabalhado (**Horas Decimais**).
      $$\\text{UPH} = \\frac{\\text{Total de Unidades}}{\\text{Horas Trabalhadas}}$$

    * **PPH (Picks Per Hour / Visitas por Hora):**  
      Mede o ritmo de deslocamento e acesso às posições de estoque (endereços de picking). Calculado dividindo a quantidade de **Qt Produtos (Visitas)** pelo tempo total trabalhado.
      $$\\text{PPH} = \\frac{\\text{Total de Visitas (Qt Produtos)}}{\\text{Horas Trabalhadas}}$$

    * **KPH (Kilos Per Hour / Peso Processado por Hora):**  
      Mede o volume físico (em peso) movimentado pelo colaborador a cada hora trabalhada. Calculado dividindo o **Peso** total processado pelo tempo total trabalhado.
      $$\\text{KPH} = \\frac{\\text{Total de Peso (kg)}}{\\text{Horas Trabalhadas}}$$

    * **Horas Decimais:**  
      Conversão do tempo `HH:MM` para base numérica decimal para permitir cálculos exatos.  
      *(Exemplo: 01h30m equivale a 1.5 horas).*

    * **Sugestão Automática de Meta (TOP N):**  
      * **Ambiente de Separação:** Média aritmética do UPH/PPH/KPH dos **8 melhores colaboradores** do período selecionado.  
      * **Ambiente de Conferência:** Média aritmética do UPH/PPH/KPH dos **2 melhores colaboradores** do período selecionado.

    * **Regra de Compensação por Peso:**  
      Como o mix de produtos varia bastante em peso, um colaborador não precisa necessariamente bater as **3 metas ao mesmo tempo** (UPH, PPH e KPH). O Status é definido pelo melhor dos dois caminhos abaixo:
      * **Caminho Normal:** bate 100% da meta de UPH **e** 100% da meta de PPH — nesse caso, só precisa atingir **40%** da meta de KPH (peso).
      * **Caminho Compensado pelo Peso:** bate 100% da meta de KPH (peso) — nesse caso, só precisa atingir **50%** das metas de UPH e PPH.

    * **Faixas de Status:**  
      * 🟢 **Na Meta:** Atende integralmente a um dos dois caminhos acima (100% do exigido em cada caminho).  
      * 🟡 **Atenção:** Está próximo de um dos dois caminhos, com **80%** dos valores exigidos em cada caminho (ex: UPH ≥ 80% e PPH ≥ 80% e KPH ≥ 32%; ou KPH ≥ 80% e UPH ≥ 40% e PPH ≥ 40%).  
      * 🔴 **Crítico:** Não atinge nem a faixa de Atenção em nenhum dos dois caminhos.
    """)
