import streamlit as st
import math

# Configuração inicial da página
st.set_page_config(page_title="Cálculo de Vento - NBR 6123", layout="wide")
st.title("Cálculo da Força de Ventos em Edificações (NBR 6123)")

# Criação das abas
abas = st.tabs([
    "Geometria", 
    "Velocidade Básica", 
    "Fator S1", 
    "Fator S2", 
    "Fator S3", 
    "Cálculo e Esforços"
])

# --- Dicionários de Dados da NBR 6123 ---
s3_valores = {
    "1 - Hospitais, quartéis, centrais de comunicação": 1.10,
    "2 - Hotéis, residências, comércio com alta ocupação": 1.00,
    "3 - Instalações industriais, depósitos (baixa ocupação)": 0.95,
    "4 - Vedações (telhas, vidros, painéis)": 0.88,
    "5 - Edificações temporárias": 0.83
}

s2_params = {
    "I - Superfícies lisas (mar, lagos)": {"A": (1.10, 0.06), "B": (1.11, 0.065), "C": (1.12, 0.07)},
    "II - Terrenos abertos (fazendas, aeroportos)": {"A": (1.00, 0.085), "B": (1.00, 0.09), "C": (1.00, 0.10)},
    "III - Terrenos planos/ondulados com obstáculos (granjas, subúrbios)": {"A": (0.94, 0.10), "B": (0.94, 0.105), "C": (0.93, 0.115)},
    "IV - Terrenos com muitos obstáculos (zonas urbanas)": {"A": (0.86, 0.12), "B": (0.85, 0.125), "C": (0.84, 0.135)},
    "V - Terrenos com obstáculos altos (centros de grandes cidades)": {"A": (0.74, 0.15), "B": (0.73, 0.16), "C": (0.71, 0.17)}
}

# Inicialização de variáveis globais
if 'altura_z' not in st.session_state:
    st.session_state['altura_z'] = 5.0
if 'maior_dimensao' not in st.session_state:
    st.session_state['maior_dimensao'] = 24.0
if 'tipo_telhado' not in st.session_state:
    st.session_state['tipo_telhado'] = "Duas águas"

# ==========================================
# ABA 1: Geometria
# ==========================================
with abas[0]:
    st.header("Dimensões da Edificação")
    
    # Adicionado o seletor de tipo de cobertura
    tipo_telhado = st.radio("Tipo de Cobertura:", ["Duas águas", "Uma água"], horizontal=True)
    st.session_state['tipo_telhado'] = tipo_telhado
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        dim_a = st.number_input("Maior dimensão 'a' (m)", value=24.0, step=1.0)
        dim_b = st.number_input("Menor dimensão 'b' (m)", value=12.0, step=1.0)
    with col2:
        dim_h = st.number_input("Altura do pilar 'h' (m)", value=5.0, step=0.5)
        
        # O rótulo muda de acordo com o tipo de telhado escolhido
        label_h1 = "Altura da cumeeira 'h1' (m)" if tipo_telhado == "Duas águas" else "Desnível do telhado 'h1' (m)"
        dim_h1 = st.number_input(label_h1, value=1.5, step=0.1)
        
    with col3:
        dist_porticos = st.number_input("Distância entre pórticos 'p' (m)", value=6.0, step=1.0)
        angulo_beta = st.number_input("Ângulo do telhado 'β' (°)", value=14.0, step=1.0)
    
    # Atualiza variáveis globais
    st.session_state['altura_z'] = dim_h + (dim_h1 / 2.0) 
    st.session_state['maior_dimensao'] = max(dim_a, dim_b)

# ==========================================
# ABA 2, 3, 4 e 5 (V0, S1, S2, S3)
# ==========================================
with abas[1]:
    st.header("Análise das Isopletas de Vento")
    v0 = st.number_input("Velocidade Básica - V0 (m/s)", value=45.0, step=1.0)

with abas[2]:
    st.header("Fator Topográfico - S1")
    s1 = st.number_input("Valor de S1", value=1.0, step=0.05)

with abas[3]:
    st.header("Fator de Rugosidade e Dimensões - S2")
    categoria = st.selectbox("Categoria do Terreno", list(s2_params.keys()), index=2)
    
    maior_dim = st.session_state['maior_dimensao']
    if maior_dim <= 20: classe_auto = "A"
    elif maior_dim <= 50: classe_auto = "B"
    else: classe_auto = "C"
        
    classe = st.selectbox("Classe da Edificação", ["A (≤ 20m)", "B (20m a 50m)", "C (> 50m)"], index=["A", "B", "C"].index(classe_auto))
    
    z_calc = max(st.session_state['altura_z'], 5.0) 
    b_val, p_val = s2_params[categoria][classe[0]]
    s2 = b_val * 1.0 * math.pow((z_calc / 10.0), p_val)
    st.metric("S2 Calculado", f"{s2:.3f}")

with abas[4]:
    st.header("Fator Estatístico - S3")
    grupo_s3 = st.radio("Selecione o grupo:", list(s3_valores.keys()), index=2)
    s3 = s3_valores[grupo_s3]

# ==========================================
# ABA 6: Resultados, Cpe, Cpi e Esforços
# ==========================================
with abas[5]:
    st.header("Velocidade Característica e Pressão Dinâmica")
    
    vk = v0 * s1 * s2 * s3
    q = 0.613 * math.pow(vk, 2) # N/m²
    
    col_res1, col_res2 = st.columns(2)
    col_res1.metric(label="Velocidade Característica (Vk)", value=f"{vk:.2f} m/s")
    col_res2.metric(label="Pressão Dinâmica (q)", value=f"{q:.2f} N/m²")
    
    st.divider()
    
    st.subheader("Coeficientes de Pressão Externa (Paredes)")
    
    rel_h_b = dim_h / dim_b
    rel_a_b = dim_a / dim_b
    
    st.write(f"**Geometria Base:**")
    st.write(f"- Cobertura: **{st.session_state['tipo_telhado']}**")
    st.write(f"- Relação h/b: **{rel_h_b:.2f}**")
    st.write(f"- Relação a/b: **{rel_a_b:.2f}**")
    
    st.info("Abaixo, iremos implementar a lógica das tabelas da NBR 6123 com base nestas relações.")
    
    col_coef1, col_coef2 = st.columns(2)
    with col_coef1:
        cpe = st.number_input("Cpe - Exemplo", value=-0.80, step=0.1)
    with col_coef2:
        cpi = st.number_input("Cpi - Exemplo", value=0.20, step=0.1)
        
    pressao_resultante = q * (cpe - cpi)
    
    st.success(f"Pressão Resultante na Face: **{pressao_resultante:.2f} N/m²**")
