import json
import urllib.request
from datetime import datetime
import zoneinfo
import streamlit as st

st.set_page_config(
    page_title="Calculadora de Importação", page_icon="📦", layout="centered"
)


# --- FUNÇÃO PARA BUSCAR COTAÇÕES EM TEMPO REAL COM FALLBACK ---
@st.cache_data(ttl=21600)  # Cache de 6 horas (21600 segundos)
def buscar_cotacoes():
    tz = zoneinfo.ZoneInfo("America/Sao_Paulo")
    horario_atualizacao = datetime.now(tz).strftime("%H:%M - %d/%m/%Y")

    cotacoes = {
        "JPY": 0.033,
        "USD": 5.70,
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

        url_usd = "https://open.er-api.com/v6/latest/USD"
        req_usd = urllib.request.Request(
            url_usd, headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req_usd, timeout=5) as response:
            data = json.loads(response.read().decode())
            cotacoes["USD"] = float(data["rates"]["BRL"])

        return cotacoes
    except Exception:
        pass  # Se falhar, tenta a API secundária

    # Tentativa 2: AwesomeAPI (Secundária)
    try:
        url_awesome = "https://economia.awesomeapi.com.br/last/JPY-BRL,USD-BRL"
        req_awesome = urllib.request.Request(
            url_awesome, headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req_awesome, timeout=5) as response:
            data = json.loads(response.read().decode())
            cotacoes["JPY"] = float(data["JPYBRL"]["bid"])
            cotacoes["USD"] = float(data["USDBRL"]["bid"])

        return cotacoes
    except Exception:
        st.warning(
            "⚠️ Não foi possível obter o câmbio em tempo real. A utilizar valores padrão."
        )

    return cotacoes


cotacoes = buscar_cotacoes()

st.title("📦 Calculadora de Importação & Frete")

# Painel no topo com avisos e cotações
st.caption(
    f"ℹ️ O câmbio é atualizado automaticamente a cada 6 horas. **Última atualização:** {cotacoes['ultima_atualizacao']}"
)

col_cot1, col_cot2 = st.columns(2)
col_cot1.metric("Cotação JPY/BRL (Iene)", f"R$ {cotacoes['JPY']:.4f}")
col_cot2.metric("Cotação USD/BRL (Dólar)", f"R$ {cotacoes['USD']:.2f}")

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["Japão", "Japão DHL", "Frete 2026", "Shopee"])

# --- ABA JAPÃO ---
with tab1:
    st.header("Cálculo Japão (Correios / SAL / EMS)")

    col1, col2 = st.columns(2)
    with col1:
        valor_iene = st.number_input(
            "Valor em Iene (¥)",
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

    valor_produto_brl = valor_iene * cotacao_iene
    frete_brl = st.number_input(
        "Frete em Reais (R$)",
        min_value=0.0,
        value=0.0,
        step=5.0,
        key="j_frete",
    )

    valor_aduaneiro = valor_produto_brl + frete_brl
    imposto_importacao = valor_aduaneiro * 0.60
    total = valor_aduaneiro + imposto_importacao

    st.markdown("---")
    st.subheader("Resumo do Cálculo")

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Valor Produto (R$)", f"R$ {valor_produto_brl:.2f}")
    col_b.metric("Imposto Importação (60%)", f"R$ {imposto_importacao:.2f}")
    col_c.metric("Custo Total", f"R$ {total:.2f}")

# --- ABA JAPÃO DHL ---
with tab2:
    st.header("Cálculo Japão (Courier / DHL)")

    col1, col2 = st.columns(2)
    with col1:
        valor_iene_dhl = st.number_input(
            "Valor em Iene (¥)",
            min_value=0.0,
            value=5000.0,
            step=100.0,
            key="dhl_iene",
        )
    with col2:
        cotacao_iene_dhl = st.number_input(
            "Cotação Iene x Real (R$)",
            min_value=0.0001,
            value=cotacoes["JPY"],
            format="%.4f",
            key="dhl_cot",
        )

    valor_produto_dhl = valor_iene_dhl * cotacao_iene_dhl
    frete_dhl = st.number_input(
        "Frete DHL em Reais (R$)",
        min_value=0.0,
        value=0.0,
        step=5.0,
        key="dhl_frete",
    )

    valor_aduaneiro_dhl = valor_produto_dhl + frete_dhl
    imposto_importacao_dhl = valor_aduaneiro_dhl * 0.60
    total_dhl = valor_aduaneiro_dhl + imposto_importacao_dhl

    st.markdown("---")
    st.subheader("Resumo do Cálculo DHL")

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Valor Produto (R$)", f"R$ {valor_produto_dhl:.2f}")
    col_b.metric("Imposto Importação (60%)", f"R$ {imposto_importacao_dhl:.2f}")
    col_c.metric("Custo Total", f"R$ {total_dhl:.2f}")

# --- ABA FRETE 2026 ---
with tab3:
    st.header("Estimativa de Frete 2026")

    cotacao_iene_frete = st.number_input(
        "Cotação do Iene Hoje (R$)",
        min_value=0.0001,
        value=cotacoes["JPY"],
        format="%.4f",
        key="f_cot",
    )

    col1, col2 = st.columns(2)
    with col1:
        peso_g = st.number_input(
            "Peso estimado (gramas)",
            min_value=0,
            value=470,
            step=50,
            key="f_peso",
        )
    with col2:
        frete_iene = st.number_input(
            "Valor do Frete em Ienes (¥)",
            min_value=0.0,
            value=2613.0,
            step=50.0,
            key="f_iene",
        )

    frete_brl_calc = frete_iene * cotacao_iene_frete

    st.markdown("---")
    st.metric("Valor do Frete Convertido", f"R$ {frete_brl_calc:.2f}")

# --- ABA SHOPEE ---
with tab4:
    st.header("Cálculo Shopee / Remessa Conforme")

    dolar_hoje = st.number_input(
        "Cotação Dólar (R$)",
        min_value=0.0,
        value=cotacoes["USD"],
        format="%.2f",
        key="sh_dolar",
    )

    col1, col2 = st.columns(2)
    with col1:
        prod_shopee = st.number_input(
            "Valor do Produto (R$)",
            min_value=0.0,
            value=0.0,
            step=10.0,
            key="sh_prod",
        )
    with col2:
        frete_shopee = st.number_input(
            "Frete (R$)", min_value=0.0, value=0.0, step=5.0, key="sh_frete"
        )

    aliquota_icms = st.number_input(
        "Alíquota ICMS",
        min_value=0.0,
        max_value=1.0,
        value=0.17,
        format="%.2f",
        key="sh_icms_rate",
    )
    despacho_postal = st.number_input(
        "Despacho Postal (R$)",
        min_value=0.0,
        value=0.0,
        step=1.0,
        key="sh_despacho",
    )

    valor_aduaneiro_sh = prod_shopee + frete_shopee
    imposto_imp_sh = 0.0
    icms_sh = (valor_aduaneiro_sh + imposto_imp_sh) * aliquota_icms
    total_shopee = (
        valor_aduaneiro_sh + imposto_imp_sh + icms_sh + despacho_postal
    )

    st.markdown("---")
    st.subheader("Resumo do Cálculo Shopee")

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Valor Aduaneiro", f"R$ {valor_aduaneiro_sh:.2f}")
    col_b.metric("ICMS", f"R$ {icms_sh:.2f}")
    col_c.metric("Custo Total", f"R$ {total_shopee:.2f}")
