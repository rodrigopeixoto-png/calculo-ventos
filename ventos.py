import streamlit as st
import math

# ==========================================
# FUNÇÕES DE CÁLCULO E INTERPOLAÇÃO
# ==========================================
def interp_linear(x, x1, x2, y1, y2):
    if x == x1: return y1
    if x == x2: return y2
    return y1 + ((x - x1) * (y2 - y1) / (x2 - x1))

def obter_cpe_paredes(h_b, a_b):
    """Calcula os coeficientes das paredes conforme Tabela 4 da NBR 6123."""
    if h_b <= 0.5:
        c_0 = 0.7; c_90 = 0.7; d_0 = -0.3; b_90 = -0.5 if a_b <= 1 else -0.3 
    elif h_b >= 1.5:
        c_0 = 0.8; c_90 = 0.8; d_0 = -0.6; b_90 = -0.6
    else:
        c_0 = interp_linear(h_b, 0.5, 1.5, 0.7, 0.8); c_90 = c_0
        d_0 = interp_linear(h_b, 0.5, 1.5, -0.3, -0.6)
        b_ref = -0.5 if a_b <= 1 else -0.3
        b_90 = interp_linear(h_b, 0.5, 1.5, b_ref, -0.6)
        
    if a_b <= 1:
        a1_b1 = -0.8; a2_b2 = -0.4; a3_b3 = -0.3 
    elif a_b <= 2:
        a1_b1 = -0.8; a2_b2 = -0.4; a3_b3 = -0.2
    else: 
        a1_b1 = -0.8; a2_b2 = -0.4; a3_b3 = -0.2 
        
    c1_d1 = -0.9; c2_d2 = -0.5
    
    return {
        '0': {'C': round(c_0, 2), 'D': round(d_0, 2), 'A1_B1': a1_b1, 'A2_B2': a2_b2, 'A3_B3': a3_b3},
        '90': {'A': round(c_90, 2), 'B': round(b_90, 2), 'C1_D1': c1_d1, 'C2_D2': c2_d2}
    }

def interpolar_telhado(beta, dict_valores):
    """Busca o valor exato ou interpola linearmente baseado no ângulo."""
    angulos = sorted(list(dict_valores.keys()))
    if beta in angulos:
        return dict_valores[beta]
    
    # Encontra os ângulos mais próximos
    for i in range(len(angulos)-1):
        if angulos[i] < beta < angulos[i+1]:
            a1, a2 = angulos[i], angulos[i+1]
            val1, val2 = dict_valores[a1], dict_valores[a2]
            
            # Se a norma dá dois valores para o mesmo ângulo (tuplas), interpolamos ambos
            if isinstance(val1, tuple) and isinstance(val2, tuple):
                v_min = interp_linear(beta, a1, a2, val1[0], val2[0])
                v_max = interp_linear(beta, a1, a2, val1[1], val2[1])
                return (round(v_min, 2), round(v_max, 2))
            elif isinstance(val1, tuple) or isinstance(val2, tuple):
                return val1 # Simplificação se mudar de tipo abruptamente
            else:
                return round(interp_linear(beta, a1, a2, val1, val2), 2)
                
    # Extrapolação simples para valores fora da tabela
    if beta <= angulos[0]: return dict_valores[angulos[0]]
    if beta >= angulos[-1]: return dict_valores[angulos[-1]]

def obter_cpe_telhado_duas_aguas(h_b, beta):
    """Mapeamento da Tabela 5 da NBR 6123 para Duas Águas."""
    # Vento a 0° (independe de h/b na tabela, depende do ângulo)
    v0_eg = {5: -0.8, 10: -0.8, 15: -0.8, 20: -0.9, 30: -1.0, 45: -1.2, 60: -1.2}
    v0_fh = {5: -0.6, 10: -0.6, 15: -0.6, 20: -0.7, 30: -0.8, 45: -0.9, 60: -1.0}
    v0_ij = {5: -0.2, 10: -0.2, 15: -0.2, 20: -0.3, 30: -0.4, 45: -0.4, 60: -0.4}
    
    # Vento a 90° (Depende de h/b. Usaremos h/b <= 0.5 como base inicial)
    if h_b <= 0.5:
        v90_ef = {5: -0.9, 10: (-1.1, -0.3), 15: (-1.0, 0.2), 20: (-0.7, 0.3), 30: (-0.3, 0.5), 45: 0.6, 60: 0.7}
        v90_gh = {5: -0.4, 10: -0.4, 15: -0.4, 20: -0.4, 30: -0.4, 45: -0.5, 60: -0.6}
    elif h_b >= 1.5:
        v90_ef = {5: -1.3, 10: -1.3, 15: (-1.3, -0.2), 20: (-1.1, 0.0), 30: (-0.7, 0.3), 45: 0.6, 60: 0.7}
        v90_gh = {5: -0.6, 10: -0.6, 15: -0.6, 20: -0.6, 30: -0.6, 45: -0.6, 60: -0.6}
    else:
        # Simplificação: para valores entre 0.5 e 1.5, assume-se a média mais crítica ou interpola.
        # Para fins didáticos deste app, manteremos a relação <= 0.5 se for menor que 1.0.
        v90_ef = {5: -0.9, 10: (-1.1, -0.3), 15: (-1.0, 0.2), 20: (-0.7, 0.3), 30: (-0.3, 0.5), 45: 0.6, 60: 0.7}
        v90_gh = {5: -0.4, 10: -0.4, 15: -0.4, 20: -0.4, 30: -0.4, 45: -0.5, 60: -0.6}
        
    return {
        '0': {
            'EG': interpolar_telhado(beta, v0_eg),
            'FH': interpolar_telhado(beta, v0_fh),
            'IJ': interpolar_telhado(beta, v0_ij)
        },
        '90': {
            'EF': interpolar_telhado(beta, v90_ef),
            'GH': interpolar_telhado(beta, v90_gh)
        }
    }

# ==========================================
# INTERFACE STREAMLIT (LAYOUT ATUALIZADO)
# ==========================================
st.set_page_config(page_title="Ventos NBR 6123", layout="wide")

# --- BARRA LATERAL (INPUTS) ---
with st.sidebar:
    st.header("Parâmetros de Entrada")
    
    st.subheader("1. Geometria")
    tipo_telhado = st.selectbox("Cobertura", ["Duas águas", "Uma água"])
    dim_a = st.number_input("Maior dim. em planta 'a' (m)", value=24.0)
    dim_b = st.number_input("Menor dim. em planta 'b' (m)", value=12.0)
    dim_h = st.number_input("Altura do pilar 'h' (m)", value=5.0)
    dim_h1 = st.number_input("Altura da cumeeira 'h1' (m)", value=1.5)
    angulo_beta = st.number_input("Ângulo do telhado 'β' (°)", value=14.0)
    
    st.subheader("2. Fatores de Vento")
    v0 = st.number_input("Veloc. Básica V0 (m/s)", value=45.0)
    s1 = st.number_input("Fator Topográfico S1", value=1.0)
    
    s2_categorias = ["I - Superfícies lisas", "II - Terrenos abertos", "III - Planos c/ obstáculos", "IV - Numerosos obstáculos", "V - Obstáculos altos"]
    s2_params = [(1.10, 0.06), (1.00, 0.085), (0.94, 0.10), (0.86, 0.12), (0.74, 0.15)] # Simplificado para Classe B
    idx_cat = st.selectbox("Categoria S2", range(len(s2_categorias)), format_func=lambda x: s2_categorias[x], index=2)
    
    s3_valores = [1.10, 1.00, 0.95, 0.88, 0.83]
    s3_labels = ["1 - Hospitais/Bombeiros", "2 - Hotéis/Comércio", "3 - Indústria/Depósitos", "4 - Vedações", "5 - Temporárias"]
    idx_s3 = st.selectbox("Grupo S3", range(len(s3_labels)), format_func=lambda x: s3_labels[x], index=2)

# --- PROCESSAMENTO ---
altura_z = dim_h + (dim_h1 / 2.0)
z_calc = max(altura_z, 5.0)
b_val, p_val = s2_params[idx_cat]
s2 = b_val * 1.0 * math.pow((z_calc / 10.0), p_val)
s3 = s3_valores[idx_s3]

vk = v0 * s1 * s2 * s3
q = 0.613 * math.pow(vk, 2)

rel_h_b = dim_h / dim_b
rel_a_b = dim_a / dim_b
cpe_paredes = obter_cpe_paredes(rel_h_b, rel_a_b)
cpe_telhado = obter_cpe_telhado_duas_aguas(rel_h_b, angulo_beta)

# --- TELA PRINCIPAL (OUTPUTS) ---
st.title("Forças de Vento - NBR 6123")
st.markdown("Cálculo estruturado dos coeficientes de pressão externa para edificações retangulares.")

st.header("1. Pressão Dinâmica")
col1, col2, col3 = st.columns(3)
col1.metric("Velocidade Característica (Vk)", f"{vk:.2f} m/s")
col2.metric("Pressão Dinâmica (q)", f"{q:.2f} N/m²")
col3.metric("Fatores Utilizados", f"S1={s1:.2f} | S2={s2:.2f} | S3={s3:.2f}")

st.divider()

st.header("2. Coeficientes de Pressão Externa - Paredes")
st.write(f"Relações geométricas: **h/b = {rel_h_b:.2f}** | **a/b = {rel_a_b:.2f}**")

tabela_paredes = st.columns(2)
with tabela_paredes[0]:
    st.subheader("Vento a 0°")
    st.write(f"- **Barlavento (Face C):** {cpe_paredes['0']['C']}")
    st.write(f"- **Sotavento (Face D):** {cpe_paredes['0']['D']}")
    st.write(f"- **Laterais A/B:** Z1= {cpe_paredes['0']['A1_B1']} | Z2= {cpe_paredes['0']['A2_B2']} | Z3= {cpe_paredes['0']['A3_B3']}")

with tabela_paredes[1]:
    st.subheader("Vento a 90°")
    st.write(f"- **Barlavento (Face A):** {cpe_paredes['90']['A']}")
    st.write(f"- **Sotavento (Face B):** {cpe_paredes['90']['B']}")
    st.write(f"- **Laterais C/D:** Z1= {cpe_paredes['90']['C1_D1']} | Z2= {cpe_paredes['90']['C2_D2']}")

st.divider()

st.header("3. Coeficientes de Pressão Externa - Telhado")
st.write(f"Cobertura: **{tipo_telhado}** | Ângulo: **{angulo_beta}°**")

if tipo_telhado == "Duas águas":
    tabela_telhado = st.columns(2)
    with tabela_telhado[0]:
        st.subheader("Vento a 0°")
        st.write(f"- **Bordas (E, G):** {cpe_telhado['0']['EG']}")
        st.write(f"- **Centro (F, H):** {cpe_telhado['0']['FH']}")
        st.write(f"- **Fundo (I, J):** {cpe_telhado['0']['IJ']}")
    
    with tabela_telhado[1]:
        st.subheader("Vento a 90°")
        ef_val = cpe_telhado['90']['EF']
        gh_val = cpe_telhado['90']['GH']
        st.write(f"- **Barlavento (E, F):** {ef_val} " + ("*(Verificar as 2 situações de cálculo)*" if isinstance(ef_val, tuple) else ""))
        st.write(f"- **Sotavento (G, H):** {gh_val}")
else:
    st.info("A lógica detalhada para telhado de uma água pode ser implementada seguindo a mesma estrutura interpoladora.")
