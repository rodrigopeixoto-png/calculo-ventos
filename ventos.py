import streamlit as st
import math

# ==========================================
# FUNÇÕES DE CÁLCULO
# ==========================================
def interp_linear(x, x1, x2, y1, y2):
    """Realiza a interpolação linear simples entre dois pontos."""
    if x == x1: return y1
    if x == x2: return y2
    return y1 + ((x - x1) * (y2 - y1) / (x2 - x1))

def obter_cpe_paredes(h_b, a_b):
    """
    Retorna os Cpe globais e laterais baseado na Tabela 4 da NBR 6123.
    """
    # 1. Interpolação para faces de Barlavento e Sotavento
    if h_b <= 0.5:
        c_0 = 0.7; c_90 = 0.7
        d_0 = -0.3 
        b_90 = -0.5 if a_b <= 1 else -0.3 
    elif h_b >= 1.5:
        c_0 = 0.8; c_90 = 0.8
        d_0 = -0.6; b_90 = -0.6
    else:
        c_0 = interp_linear(h_b, 0.5, 1.5, 0.7, 0.8)
        c_90 = c_0
        d_0 = interp_linear(h_b, 0.5, 1.5, -0.3, -0.6)
        b_ref_05 = -0.5 if a_b <= 1 else -0.3
        b_90 = interp_linear(h_b, 0.5, 1.5, b_ref_05, -0.6)
        
    # 2. Definição das zonas laterais (Sucção)
    # Vento 0° (Laterais são A e B)
    if a_b <= 1:
        a1_b1 = -0.8
        a2_b2 = -0.4
        a3_b3 = -0.3 
    elif a_b <= 2:
        a1_b1 = -0.8
        a2_b2 = -0.4
        a3_b3 = -0.2
    else: 
        a1_b1 = -0.8
        a2_b2 = -0.4
        a3_b3 = -0.2 
        
    # Vento 90° (Laterais são C e D)
    if h_b <= 0.5:
        c1_d1 = -0.9
        c2_d2 = -0.5
    elif h_b >= 1.5:
        c1_d1 = -0.9
        c2_d2 = -0.5
    else:
        c1_d1 = -0.9
        c2_d2 = -0.5

    return {
        'vento_0': {
            'Barlavento_C': round(c_0, 2), 
            'Sotavento_D': round(d_0, 2),
            'Lateral_A1_B1': round(a1_b1, 2),
            'Lateral_A2_B2': round(a2_b2, 2),
            'Lateral_A3_B3': round(a3_b3, 2)
        },
        'vento_90': {
            'Barlavento_A': round(c_90, 2), 
            'Sotavento_B': round(b_90, 2),
            'Lateral_C1_D1': round(c1_d1, 2),
            'Lateral_C2_D2': round(c2_d2, 2)
        }
    }

# ==========================================
# CONFIGURAÇÃO INICIAL DA PÁGINA E VARIÁVEIS
# ==========================================
st.set_page_config(page_title="Cálculo de Vento - NBR 6123", layout="wide")
st.title("Cálculo da Força de Ventos em Edificações (NBR 6123)")

abas = st.tabs([
    "Geometria", 
    "Velocidade Básica", 
    "Fator S1", 
    "Fator S2", 
    "Fator S3", 
    "Cálculo e Esforços"
])

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
    
    tipo_telhado = st.radio("Tipo de Cobertura:", ["Duas águas", "Uma água"], horizontal=True)
    st.session_state['tipo_telhado'] = tipo_telhado
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        dim_a = st.number_input("Maior dimensão 'a' (m)", value=24.0, step=1.0)
        dim_b = st.number_input("Menor dimensão 'b' (m)", value=12.0, step=1.0)
    with col2:
        dim_h = st.number_input("Altura do pilar 'h' (m)", value=5.0, step=0.5)
        label_h1 = "Altura da cumeeira 'h1' (m)" if tipo_telhado == "Duas águas" else "Desnível do telhado 'h1' (m)"
        dim_h1 = st.number_input(label_h1, value=1.5, step=0.1)
    with col3:
        dist_porticos = st.number_input("Distância entre pórticos 'p' (m)", value=6.0, step=1.0)
        angulo_beta = st.number_input("Ângulo do telhado 'β' (°)", value=14.0, step=1.0)
    
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
    q = 0.613 * math.pow(vk, 2) 
    
    col_res1, col_res2 = st.columns(2)
    col_res1.metric(label="Velocidade Característica (Vk)", value=f"{vk:.2f} m/s")
    col_res2.metric(label="Pressão Dinâmica (q)", value=f"{q:.2f} N/m²")
    
    st.divider()
    
    st.subheader("Coeficientes de Pressão Externa ($C_{pe}$) - Paredes")
    
    rel_h_b = dim_h / dim_b
    rel_a_b = dim_a / dim_b
    
    st.write(f"- Relação $h/b$: **{rel_h_b:.2f}** | Relação $a/b$: **{rel_a_b:.2f}**")
    
    cpe_paredes = obter_cpe_paredes(rel_h_b, rel_a_b)
    
    col_v0, col_v90 = st.columns(2)
    
    with col_v0:
        st.write("**Vento a 0° (Perpendicular à face a)**")
        st.write(f"Face **C** (Barlavento): **{cpe_paredes['vento_0']['Barlavento_C']}**")
        st.write(f"Face **D** (Sotavento): **{cpe_paredes['vento_0']['Sotavento_D']}**")
        st.write("Zonas Laterais (**A** e **B**):")
        st.info(f"A1/B1 = **{cpe_paredes['vento_0']['Lateral_A1_B1']}** \n\n A2/B2 = **{cpe_paredes['vento_0']['Lateral_A2_B2']}** \n\n A3/B3 = **{cpe_paredes['vento_0']['Lateral_A3_B3']}**")
        
    with col_v90:
        st.write("**Vento a 90° (Perpendicular à face b)**")
        st.write(f"Face **A** (Barlavento): **{cpe_paredes['vento_90']['Barlavento_A']}**")
        st.write(f"Face **B** (Sotavento): **{cpe_paredes['vento_90']['Sotavento_B']}**")
        st.write("Zonas Laterais (**C** e **D**):")
        st.info(f"C1/D1 = **{cpe_paredes['vento_90']['Lateral_C1_D1']}** \n\n C2/D2 = **{cpe_paredes['vento_90']['Lateral_C2_D2']}**")
