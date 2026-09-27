import json
import urllib.request
from datetime import datetime
import zoneinfo
import streamlit as st

st.set_page_config(
    page_title="Calculadora de Importação", page_icon="📦", layout="centered"
)


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
        pass  # Se falhar, tenta a API secundária

    # Tentativa 2: AwesomeAPI (Secundária)
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

# Painel no topo com avisos e cotações
st.caption(
    f"ℹ️ O câmbio é atualizado automaticamente a cada 6 horas. **Última atualização:** {cotacoes['ultima_atualizacao']}"
)

st.metric("Cotação JPY/BRL (Iene)", f"R$ {cotacoes['JPY']:.4f}")

st.markdown("---")

tab1, tab2 = st.tabs(["Japão", "Frete 2026"])

# --- ABA JAPÃO ---
with tab1:
    st.header("Cálculo Detalhado - Japão")

    # Inputs principais
    col1, col2 = st.columns(2)
    with col1:
        valor_iene = st.number_input(
            "Valor do Produto em Iene (¥)",
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

    col3, col4 = st.columns(2)
    with col3:
        frete_brl = st.number_input(
            "Frete em Reais (R$)",
            min_value=0.0,
            value=0.0,
            step=5.0,
            key="j_frete",
        )
    with col4:
        despacho_postal = st.number_input(
            "Despacho Postal dos Correios (R$)",
            min_value=0.0,
            value=18.10,
            step=1.0,
            key="j_despacho",
        )

    aliquota_icms = st.number_input(
        "Alíquota ICMS (%)",
        min_value=0.0,
        max_value=100.0,
        value=17.0,
        step=1.0,
        key="j_icms_rate",
    ) / 100.0

    # --- MEMÓRIA DE CÁLCULO ---
    valor_produto_brl = valor_iene * cotacao_iene
    valor_aduaneiro = valor_produto_brl + frete_brl
    imposto_importacao = valor_aduaneiro * 0.60  # 60%

    # Cálculo do ICMS por dentro (Base = (Valor Aduaneiro + II) / (1 - Alíquota))
    if (1 - aliquota_icms) > 0:
        base_icms = (valor_aduaneiro + imposto_importacao) / (1 - aliquota_icms)
        valor_icms = base_icms * aliquota_icms
    else:
        base_icms = 0.0
        valor_icms = 0.0

    total_impostos = imposto_importacao + valor_icms + despacho_postal
    total_geral = valor_produto_brl + frete_brl + total_impostos

    st.markdown("---")
    st.subheader("📊 Detalhamento dos Impostos e Taxas")

    # Exibição dos itens
    col_det1, col_det2, col_det3 = st.columns(3)
    col_det1.metric("Valor Produto", f"R$ {valor_produto_brl:.2f}")
    col_det2.metric("Frete (R$)", f"R$ {frete_brl:.2f}")
    col_det3.metric("Valor Aduaneiro Total", f"R$ {valor_aduaneiro:.2f}")

    col_tax1, col_tax2, col_tax3 = st.columns(3)
    col_tax1.metric("Imposto de Importação (60%)", f"R$ {imposto_importacao:.2f}")
    col_tax2.metric(f"ICMS ({aliquota_icms*100:.0f}%)", f"R$ {valor_icms:.2f}")
    col_tax3.metric("Despacho Postal", f"R$ {despacho_postal:.2f}")

    st.markdown("---")
    st.subheader("💰 Resumo Final")

    res_a, res_b = st.columns(2)
    res_a.metric("Total de Impostos e Taxas", f"R$ {total_impostos:.2f}")
    res_b.metric("TOTAL GERAL DA COMPRA", f"R$ {total_geral:.2f}")

    with st.expander("🔍 Ver memória de cálculo (fórmulas)"):
        st.write(f"- **Valor do Produto (R$):** ¥ {valor_iene:.2f} × R$ {cotacao_iene:.4f} = **R$ {valor_produto_brl:.2f}**")
        st.write(f"- **Imposto de Importação (60%):** R$ {valor_aduaneiro:.2f} × 60% = **R$ {imposto_importacao:.2f}**")
        st.write(f"- **Base de Cálculo ICMS:** (R$ {valor_aduaneiro:.2f} + R$ {imposto_importacao:.2f}) ÷ (1 - {aliquota_icms:.2f}) = **R$ {base_icms:.2f}**")
        st.write(f"- **Valor ICMS:** R$ {base_icms:.2f} × {aliquota_icms*100:.0f}% = **R$ {valor_icms:.2f}**")
        st.write(f"- **Total a Pagar de Impostos:** R$ {imposto_importacao:.2f} + R$ {valor_icms:.2f} + R$ {despacho_postal:.2f} = **R$ {total_impostos:.2f}**")

# --- ABA FRETE 2026 ---
with tab2:
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
