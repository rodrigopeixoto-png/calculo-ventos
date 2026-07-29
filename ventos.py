import streamlit as st
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ==========================================
# FUNÇÕES DE CÁLCULO E INTERPOLAÇÃO
# ==========================================
def interp_linear(x, x1, x2, y1, y2):
    if x == x1: return y1
    if x == x2: return y2
    return y1 + ((x - x1) * (y2 - y1) / (x2 - x1))

def obter_cpe_paredes(h_b, a_b):
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
    angulos = sorted(list(dict_valores.keys()))
    if beta in angulos: return dict_valores[beta]
    
    for i in range(len(angulos)-1):
        if angulos[i] < beta < angulos[i+1]:
            a1, a2 = angulos[i], angulos[i+1]
            val1, val2 = dict_valores[a1], dict_valores[a2]
            
            if isinstance(val1, tuple) and isinstance(val2, tuple):
                v_min = interp_linear(beta, a1, a2, val1[0], val2[0])
                v_max = interp_linear(beta, a1, a2, val1[1], val2[1])
                return (round(v_min, 2), round(v_max, 2))
            elif isinstance(val1, tuple) or isinstance(val2, tuple):
                return val1 
            else:
                return round(interp_linear(beta, a1, a2, val1, val2), 2)
                
    if beta <= angulos[0]: return dict_valores[angulos[0]]
    if beta >= angulos[-1]: return dict_valores[angulos[-1]]

def obter_cpe_telhado_duas_aguas(h_b, beta):
    v0_eg = {5: -0.8, 10: -0.8, 15: -0.8, 20: -0.9, 30: -1.0, 45: -1.2, 60: -1.2}
    v0_fh = {5: -0.6, 10: -0.6, 15: -0.6, 20: -0.7, 30: -0.8, 45: -0.9, 60: -1.0}
    v0_ij = {5: -0.2, 10: -0.2, 15: -0.2, 20: -0.3, 30: -0.4, 45: -0.4, 60: -0.4}
    
    if h_b <= 0.5:
        v90_ef = {5: -0.9, 10: (-1.1, -0.3), 15: (-1.0, 0.2), 20: (-0.7, 0.3), 30: (-0.3, 0.5), 45: 0.6, 60: 0.7}
        v90_gh = {5: -0.4, 10: -0.4, 15: -0.4, 20: -0.4, 30: -0.4, 45: -0.5, 60: -0.6}
    elif h_b >= 1.5:
        v90_ef = {5: -1.3, 10: -1.3, 15: (-1.3, -0.2), 20: (-1.1, 0.0), 30: (-0.7, 0.3), 45: 0.6, 60: 0.7}
        v90_gh = {5: -0.6, 10: -0.6, 15: -0.6, 20: -0.6, 30: -0.6, 45: -0.6, 60: -0.6}
    else:
        v90_ef = {5: -0.9, 10: (-1.1, -0.3), 15: (-1.0, 0.2), 20: (-0.7, 0.3), 30: (-0.3, 0.5), 45: 0.6, 60: 0.7}
        v90_gh = {5: -0.4, 10: -0.4, 15: -0.4, 20: -0.4, 30: -0.4, 45: -0.5, 60: -0.6}
        
    return {
        '0': {'EG': interpolar_telhado(beta, v0_eg), 'FH': interpolar_telhado(beta, v0_fh), 'IJ': interpolar_telhado(beta, v0_ij)},
        '90': {'EF': interpolar_telhado(beta, v90_ef), 'GH': interpolar_telhado(beta, v90_gh)}
    }

def calcular_resultante(cpe, cpi, q):
    if isinstance(cpe, tuple):
        r1 = q * (cpe[0] - cpi)
        r2 = q * (cpe[1] - cpi)
        return f"**{r1:.2f}** ou **{r2:.2f}**"
    else:
        return f"**{(q * (cpe - cpi)):.2f}**"

# ==========================================
# GERADOR DE GRÁFICOS (MATPLOTLIB)
# ==========================================
def plot_esquema_vento(dim_a, dim_b):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    
    # Desenho Vento a 0°
    ax1.add_patch(patches.Rectangle((0, 0), dim_a, dim_b, fill=True, color='#e2e8f0', ec='black'))
    ax1.set_xlim(-dim_a*0.3, dim_a*1.3)
    ax1.set_ylim(-dim_b*0.5, dim_b*1.5)
    
    ax1.text(dim_a/2, -dim_b*0.1, 'Face C', va='top', ha='center', color='#1d4ed8', fontweight='bold', fontsize=10)
    ax1.text(dim_a/2, dim_b*1.1, 'Face D', va='bottom', ha='center', color='#b91c1c', fontweight='bold', fontsize=10)
    ax1.text(-dim_a*0.05, dim_b/2, 'Face A', va='center', ha='right', fontsize=9)
    ax1.text(dim_a*1.05, dim_b/2, 'Face B', va='center', ha='left', fontsize=9)
    
    # Seta do vento 0° (Vem de baixo para cima)
    ax1.arrow(dim_a/2, -dim_b*0.4, 0, dim_b*0.2, head_width=dim_a*0.05, head_length=dim_b*0.08, fc='#1d4ed8', ec='#1d4ed8')
    ax1.set_title("Vento a 0°", fontweight='bold')
    ax1.axis('off')
    
    # Desenho Vento a 90°
    ax2.add_patch(patches.Rectangle((0, 0), dim_a, dim_b, fill=True, color='#e2e8f0', ec='black'))
    ax2.set_xlim(-dim_a*0.3, dim_a*1.3)
    ax2.set_ylim(-dim_b*0.5, dim_b*1.5)
    
    ax2.text(dim_a/2, -dim_b*0.1, 'Face C', va='top', ha='center', fontsize=9)
    ax2.text(dim_a/2, dim_b*1.1, 'Face D', va='bottom', ha='center', fontsize=9)
    ax2.text(-dim_a*0.05, dim_b/2, 'Face A', va='center', ha='right', color='#1d4ed8', fontweight='bold', fontsize=10)
    ax2.text(dim_a*1.05, dim_b/2, 'Face B', va='center', ha='left', color='#b91c1c', fontweight='bold', fontsize=10)
    
    # Seta do vento 90° (Vem da esquerda para a direita)
    ax2.arrow(-dim_a*0.25, dim_b/2, dim_a*0.15, 0, head_width=dim_b*0.08, head_length=dim_a*0.05, fc='#1d4ed8', ec='#1d4ed8')
    ax2.set_title("Vento a 90°", fontweight='bold')
    ax2.axis('off')
    
    return fig

# ==========================================
# INTERFACE STREAMLIT
# ==========================================
st.set_page_config(page_title="Ventos NBR 6123", layout="wide")

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
    s2_params = [(1.10, 0.06), (1.00, 0.085), (0.94, 0.10), (0.86, 0.12), (0.74, 0.15)]
    idx_cat = st.selectbox("Categoria S2", range(len(s2_categorias)), format_func=lambda x: s2_categorias[x], index=2)
    
    s3_valores = [1.10, 1.00, 0.95, 0.88, 0.83]
    s3_labels = ["1 - Hospitais/Bombeiros", "2 - Hotéis/Comércio", "3 - Indústria/Depósitos", "4 - Vedações", "5 - Temporárias"]
    idx_s3 = st.selectbox("Grupo S3", range(len(s3_labels)), format_func=lambda x: s3_labels[x], index=2)

    st.subheader("3. Pressão Interna (Cpi)")
    st.markdown("Insira os limites de $C_{pi}$ para cálculo das combinações:")
    cpi_positivo = st.number_input("Cpi (Condição Positiva)", value=0.2)
    cpi_negativo = st.number_input("Cpi (Condição Negativa)", value=-0.3)

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

# --- TELA PRINCIPAL ---
st.title("Forças de Vento - NBR 6123")
st.markdown("Cálculo estruturado das forças estáticas devidas ao vento em edificações retangulares.")

st.header("1. Esquema da Edificação e Pressão Dinâmica")
# Exibe o gráfico gerado com Matplotlib
fig_esquema = plot_esquema_vento(dim_a, dim_b)
st.pyplot(fig_esquema)

col1, col2, col3 = st.columns(3)
col1.metric("Velocidade Característica (Vk)", f"{vk:.2f} m/s")
col2.metric("Pressão Dinâmica (q)", f"{q:.2f} N/m²")
col3.metric("Fatores Utilizados", f"S1={s1:.2f} | S2={s2:.2f} | S3={s3:.2f}")

st.divider()

st.header("2. Coeficientes de Pressão Externa ($C_{pe}$)")
col_p, col_t = st.columns(2)

with col_p:
    st.subheader("Paredes")
    st.write("**Vento a 0°**")
    st.write(f"- Face C (Frente): {cpe_paredes['0']['C']} | Face D (Fundos): {cpe_paredes['0']['D']}")
    st.write("**Vento a 90°**")
    st.write(f"- Face A (Frente): {cpe_paredes['90']['A']} | Face B (Fundos): {cpe_paredes['90']['B']}")

with col_t:
    st.subheader("Telhado")
    if tipo_telhado == "Duas águas":
        st.write("**Vento a 0°**")
        st.write(f"- E/G: {cpe_telhado['0']['EG']} | F/H: {cpe_telhado['0']['FH']}")
        st.write("**Vento a 90°**")
        st.write(f"- Barlavento (E/F): {cpe_telhado['90']['EF']}")
        st.write(f"- Sotavento (G/H): {cpe_telhado['90']['GH']}")

st.divider()

st.header("3. Esforços Resultantes Finais ($\Delta p$)")
st.markdown("A equação aplicada para o cálculo das faces é $\Delta p = q \times (C_{pe} - C_{pi})$. Valores expressos em **$\text{N/m}^2$**.")

abas_result = st.tabs([f"Combinação 1 (Cpi = {cpi_positivo})", f"Combinação 2 (Cpi = {cpi_negativo})"])

with abas_result[0]:
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown("### Vento a 0°")
        st.write(f"- **Parede C (Barlavento):** {calcular_resultante(cpe_paredes['0']['C'], cpi_positivo, q)}")
        st.write(f"- **Parede D (Sotavento):** {calcular_resultante(cpe_paredes['0']['D'], cpi_positivo, q)}")
        st.write(f"- **Telhado (Zonas E/G):** {calcular_resultante(cpe_telhado['0']['EG'], cpi_positivo, q)}")
    with col_r2:
        st.markdown("### Vento a 90°")
        st.write(f"- **Parede A (Barlavento):** {calcular_resultante(cpe_paredes['90']['A'], cpi_positivo, q)}")
        st.write(f"- **Parede B (Sotavento):** {calcular_resultante(cpe_paredes['90']['B'], cpi_positivo, q)}")
        st.write(f"- **Telhado (Zonas E/F):** {calcular_resultante(cpe_telhado['90']['EF'], cpi_positivo, q)}")

with abas_result[1]:
    col_r3, col_r4 = st.columns(2)
    with col_r3:
        st.markdown("### Vento a 0°")
        st.write(f"- **Parede C (Barlavento):** {calcular_resultante(cpe_paredes['0']['C'], cpi_negativo, q)}")
        st.write(f"- **Parede D (Sotavento):** {calcular_resultante(cpe_paredes['0']['D'], cpi_negativo, q)}")
        st.write(f"- **Telhado (Zonas E/G):** {calcular_resultante(cpe_telhado['0']['EG'], cpi_negativo, q)}")
    with col_r4:
        st.markdown("### Vento a 90°")
        st.write(f"- **Parede A (Barlavento):** {calcular_resultante(cpe_paredes['90']['A'], cpi_negativo, q)}")
        st.write(f"- **Parede B (Sotavento):** {calcular_resultante(cpe_paredes['90']['B'], cpi_negativo, q)}")
        st.write(f"- **Telhado (Zonas E/F):** {calcular_resultante(cpe_telhado['90']['EF'], cpi_negativo, q)}")
