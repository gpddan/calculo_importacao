import json
import math
import urllib.request
from datetime import datetime
import zoneinfo
import streamlit as st

st.set_page_config(
    page_title="Calculadora de Importação", page_icon="📦", layout="centered"
)


# --- FUNÇÃO DE CÁLCULO DE FRETE POR PESO (1227 + 346.5 A CADA 100G) ---
def calcular_frete_por_peso(peso_g):
    if peso_g <= 0:
        return 0.0
    incrementos = math.ceil(peso_g / 100.0) - 1
    return 1227.0 + (incrementos * 346.5)


# --- FUNÇÃO PARA BUSCAR COTAÇÕES EM TEMPO REAL COM FALLBACK ---
@st.cache_data(ttl=21600)  # Cache de 6 horas
def buscar_cotacoes():
    tz = zoneinfo.ZoneInfo("America/Sao_Paulo")
    horario_atualizacao = datetime.now(tz).strftime("%H:%M - %d/%m/%Y")

    cotacoes = {
        "JPY": 0.033,
        "ultima_atualizacao": horario_atualizacao,
    }

    # Tentativa 1: ExchangeRate-API
    try:
        url_jpy = "https://open.er-api.com/v6/latest/JPY"
        req_jpy = urllib.request.Request(
            url_jpy, headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req_jpy, timeout=5) as response:
            data = json.loads(response.read().decode())
            cotacoes["JPY"] = float(data["rates"]["BRL"])

        return cotacoes
    except Exception:
        pass

    # Tentativa 2: AwesomeAPI
    try:
        url_awesome = "https://economia.awesomeapi.com.br/last/JPY-BRL"
        req_awesome = urllib.request.Request(
            url_awesome, headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req_awesome, timeout=5) as response:
            data = json.loads(response.read().decode())
            cotacoes["JPY"] = float(data["JPYBRL"]["bid"])

        return cotacoes
    except Exception:
        st.warning(
            "⚠️ Não foi possível obter o câmbio em tempo real. A utilizar valor padrão."
        )

    return cotacoes


cotacoes = buscar_cotacoes()

st.title("📦 Calculadora de Importação & Frete")

# Painel de câmbio
st.caption(
    f"ℹ️ O câmbio é atualizado automaticamente a cada 6 horas. **Última atualização:** {cotacoes['ultima_atualizacao']}"
)
st.metric("Cotação JPY/BRL (Iene)", f"R$ {cotacoes['JPY']:.4f}")

st.markdown("---")

tab1, tab2 = st.tabs(["Japão (Calculadora Completa)", "Tabela de Frete por Peso"])

# --- ABA JAPÃO ---
with tab1:
    st.header("Cálculo Detalhado - Importação Japão")

    # Cotação e Produto
    col1, col2 = st.columns(2)
    with col1:
        valor_iene = st.number_input(
            "Valor do Produto (¥)",
            min_value=0.0,
            value=4400.0,
            step=100.0,
            key="j_iene",
        )
    with col2:
        cotacao_iene = st.number_input(
            "Cotação Iene x Real (R$)",
            min_value=0.0001,
            value=cotacoes["JPY"],
            format="%.4f",
            key="j_cot",
        )

    # Taxa Buyee e Frete no Japão
    col3, col4 = st.columns(2)
    with col3:
        taxa_buyee_jpy = st.number_input(
            "Taxa Buyee (¥)",
            min_value=0.0,
            value=500.0,
            step=50.0,
            key="j_buyee",
            help="Taxa de serviço da Buyee (NÃO incide imposto de importação).",
        )
    with col4:
        frete_japao_jpy = st.number_input(
            "Frete Doméstico no Japão (¥)",
            min_value=0.0,
            value=0.0,
            step=50.0,
            key="j_frete_jp",
            help="Frete dentro do Japão até o armazém (NÃO incide imposto de importação).",
        )

    st.markdown("---")
    st.subheader("✈️ Envio Internacional")

    # Seleção de tipo de frete e método de inserção (Peso vs Valor Direto)
    col5, col6 = st.columns(2)
    with col5:
        tipo_frete = st.selectbox(
            "Tipo de Frete Internacional",
            options=[
                "Air Packet / Small Packet / Collis / Prime Express (Sem imposto no frete)",
                "EMS (Incide imposto sobre o frete)",
            ],
            key="j_tipo_frete",
        )
    with col6:
        modo_entrada_frete = st.radio(
            "Como deseja informar o frete internacional?",
            options=["Calcular por Peso (g)", "Digitar Valor em Ienes (¥)"],
            horizontal=True,
            key="j_modo_frete",
        )

    # Lógica dinâmica para Peso ou Valor Direto
    if modo_entrada_frete == "Calcular por Peso (g)":
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            peso_j_g = st.number_input(
                "Peso estimado do pacote (gramas)",
                min_value=0,
                value=470,
                step=50,
                key="j_peso_g",
            )
        frete_intl_jpy = calcular_frete_por_peso(peso_j_g)
        with col_p2:
            st.metric(
                "Frete Internacional Calculado",
                f"¥ {frete_intl_jpy:,.2f}",
                help="¥ 1.227 para os primeiros 100g + ¥ 346,50 a cada 100g adicionais.",
            )
    else:
        peso_j_g = 0
        frete_intl_jpy = st.number_input(
            "Valor do Frete Internacional (¥)",
            min_value=0.0,
            value=2613.0,
            step=50.0,
            key="j_frete_intl_manual",
        )

    # Taxas Aduaneiras e Correios
    col7, col8 = st.columns(2)
    with col7:
        despacho_postal = st.number_input(
            "Despacho Postal Correios (R$)",
            min_value=0.0,
            value=18.10,
            step=1.0,
            key="j_despacho",
        )
    with col8:
        aliquota_icms = (
            st.number_input(
                "Alíquota ICMS (%)",
                min_value=0.0,
                max_value=100.0,
                value=17.0,
                step=1.0,
                key="j_icms_rate",
            )
            / 100.0
        )

    # --- PROCESSAMENTO DOS CÁLCULOS ---
    valor_prod_brl = valor_iene * cotacao_iene
    taxa_buyee_brl = taxa_buyee_jpy * cotacao_iene
    frete_japao_brl = frete_japao_jpy * cotacao_iene
    frete_intl_brl = frete_intl_jpy * cotacao_iene

    incide_imposto_frete = "EMS" in tipo_frete

    if incide_imposto_frete:
        valor_tributavel = valor_prod_brl + frete_intl_brl
    else:
        valor_tributavel = valor_prod_brl

    imposto_importacao = valor_tributavel * 0.60

    if (1 - aliquota_icms) > 0:
        base_icms = (valor_tributavel + imposto_importacao) / (
            1 - aliquota_icms
        )
        valor_icms = base_icms * aliquota_icms
    else:
        base_icms = 0.0
        valor_icms = 0.0

    total_impostos = imposto_importacao + valor_icms + despacho_postal
    total_geral = (
        valor_prod_brl
        + taxa_buyee_brl
        + frete_japao_brl
        + frete_intl_brl
        + total_impostos
    )

    st.markdown("---")
    st.subheader("📊 Resumo Visual dos Custos")

    c1, c2, c3 = st.columns(3)
    c1.metric("Produto (R$)", f"R$ {valor_prod_brl:.2f}")
    c2.metric(
        "Serviços Japão (Buyee + Frete JP)",
        f"R$ {taxa_buyee_brl + frete_japao_brl:.2f}",
    )
    c3.metric(
        "Base Tributável (Aduana)",
        f"R$ {valor_tributavel:.2f}",
        help="Valor sobre o qual incidem os 60% de imposto.",
    )

    st.markdown("---")
    st.subheader("🏛️ Impostos e Taxas Brasil")

    t1, t2, t3 = st.columns(3)
    t1.metric("Imposto de Importação (60%)", f"R$ {imposto_importacao:.2f}")
    t2.metric(f"ICMS ({aliquota_icms*100:.0f}%)", f"R$ {valor_icms:.2f}")
    t3.metric("Despacho Postal", f"R$ {despacho_postal:.2f}")

    st.markdown("---")
    res_a, res_b = st.columns(2)
    res_a.metric("Total de Impostos/Taxas", f"R$ {total_impostos:.2f}")
    res_b.metric("TOTAL GERAL DA COMPRA", f"R$ {total_geral:.2f}")

    with st.expander("🔍 Ver memória de cálculo (fórmulas)"):
        st.write(
            f"- **Produto:** ¥ {valor_iene:.2f} = **R$ {valor_prod_brl:.2f}**"
        )
        st.write(
            f"- **Taxa Buyee:** ¥ {taxa_buyee_jpy:.2f} = **R$ {taxa_buyee_brl:.2f}** *(Isenta de tributos aduaneiros)*"
        )
        st.write(
            f"- **Frete Japão (Doméstico):** ¥ {frete_japao_jpy:.2f} = **R$ {frete_japao_brl:.2f}** *(Isento de tributos aduaneiros)*"
        )
        frete_origem_txt = f"{peso_j_g}g" if modo_entrada_frete == "Calcular por Peso (g)" else "manual"
        st.write(
            f"- **Frete Internacional ({frete_origem_txt}):** ¥ {frete_intl_jpy:.2f} = **R$ {frete_intl_brl:.2f}** *({'Tributado' if incide_imposto_frete else 'Isento de tributos aduaneiros'})*"
        )
        st.write(
            f"- **Base Tributável:** R$ {valor_tributavel:.2f} *(Produto {'+ Frete Intl' if incide_imposto_frete else ''})*"
        )
        st.write(
            f"- **Imposto de Importação (60%):** R$ {valor_tributavel:.2f} × 60% = **R$ {imposto_importacao:.2f}**"
        )
        st.write(
            f"- **Base ICMS:** (R$ {valor_tributavel:.2f} + R$ {imposto_importacao:.2f}) ÷ (1 - {aliquota_icms:.2f}) = **R$ {base_icms:.2f}**"
        )
        st.write(
            f"- **Valor ICMS:** R$ {base_icms:.2f} × {aliquota_icms*100:.0f}% = **R$ {valor_icms:.2f}**"
        )

# --- ABA 2: CONSULTA RÁPIDA DE FRETE ---
with tab2:
    st.header("Tabela Rápida de Frete por Peso")

    cotacao_iene_frete = st.number_input(
        "Cotação do Iene Hoje (R$)",
        min_value=0.0001,
        value=cotacoes["JPY"],
        format="%.4f",
        key="f_cot",
    )

    peso_g = st.number_input(
        "Peso estimado (gramas)",
        min_value=0,
        value=470,
        step=50,
        key="f_peso",
    )

    frete_calc_iene = calcular_frete_por_peso(peso_g)
    frete_calc_brl = frete_calc_iene * cotacao_iene_frete

    st.markdown("---")
    col_f1, col_f2 = st.columns(2)
    col_f1.metric("Valor do Frete em Ienes", f"¥ {frete_calc_iene:,.2f}")
    col_f2.metric("Valor do Frete Convertido", f"R$ {frete_calc_brl:.2f}")

    st.caption("ℹ️ Regra da tabela: ¥ 1.227 até 100g + ¥ 346,50 para cada 100g adicionais.")
