"""
Programa para Cálculo da Força de Ventos em Edificações 
Baseado na norma brasileira NBR 6123.
Desenvolvido em Python utilizando Streamlit para a interface web 
e Matplotlib para a geração dos diagramas de esforços.
"""

import streamlit as st
import math
import matplotlib.pyplot as plt

# ==========================================
# 1. FUNÇÕES MATEMÁTICAS E DE INTERPOLAÇÃO
# ==========================================

def interp_linear(x, x1, x2, y1, y2):
    """
    Realiza a interpolação linear simples entre dois pontos conhecidos.
    Utilizada quando as dimensões geométricas (h/b, a/b) ou ângulos 
    caem entre os valores tabelados na norma.
    """
    if x == x1: return y1
    if x == x2: return y2
    return y1 + ((x - x1) * (y2 - y1) / (x2 - x1))

def interpolar_telhado(beta, dict_valores):
    """
    Busca o valor exato na tabela do telhado ou interpola linearmente.
    Trata casos complexos da NBR 6123 onde um mesmo ângulo possui 
    duas situações de cálculo (tuplas), calculando a interpolação para ambas.
    """
    angulos = sorted(list(dict_valores.keys()))
    
    # Se o ângulo digitado for exato ao da tabela, retorna direto
    if beta in angulos: 
        return dict_valores[beta]
    
    # Se estiver entre dois ângulos da tabela, interpola
    for i in range(len(angulos)-1):
        if angulos[i] < beta < angulos[i+1]:
            a1, a2 = angulos[i], angulos[i+1]
            val1, val2 = dict_valores[a1], dict_valores[a2]
            
            # Caso a norma preveja duas situações (sucção e pressão) para o ângulo
            if isinstance(val1, tuple) and isinstance(val2, tuple):
                v_min = interp_linear(beta, a1, a2, val1[0], val2[0])
                v_max = interp_linear(beta, a1, a2, val1[1], val2[1])
                return (round(v_min, 2), round(v_max, 2))
            
            # Se a transição muda de tipo abruptamente (ex: de tupla para float)
            elif isinstance(val1, tuple) or isinstance(val2, tuple):
                return val1 
            
            # Interpolação normal para valores únicos
            else:
                return round(interp_linear(beta, a1, a2, val1, val2), 2)
                
    # Extrapolação caso o ângulo seja menor que o mínimo ou maior que o máximo tabelado
    if beta <= angulos[0]: return dict_valores[angulos[0]]
    if beta >= angulos[-1]: return dict_valores[angulos[-1]]

# ==========================================
# 2. FUNÇÕES DA NBR 6123 (Cálculo de Cpe)
# ==========================================

def obter_cpe_paredes(h_b, a_b):
    """
    Calcula os Coeficientes de Pressão Externa (Cpe) para as paredes 
    de acordo com a Tabela 4 da NBR 6123.
    Retorna um dicionário dividido por 'Vento a 0°' e 'Vento a 90°'.
    """
    # Avaliação da relação h/b para as faces perpendiculares ao vento (Barlavento/Sotavento)
    if h_b <= 0.5:
        c_0 = 0.7; c_90 = 0.7; d_0 = -0.3; b_90 = -0.5 if a_b <= 1 else -0.3 
    elif h_b >= 1.5:
        c_0 = 0.8; c_90 = 0.8; d_0 = -0.6; b_90 = -0.6
    else:
        # Se 0.5 < h/b < 1.5, exige interpolação linear
        c_0 = interp_linear(h_b, 0.5, 1.5, 0.7, 0.8); c_90 = c_0
        d_0 = interp_linear(h_b, 0.5, 1.5, -0.3, -0.6)
        b_ref = -0.5 if a_b <= 1 else -0.3
        b_90 = interp_linear(h_b, 0.5, 1.5, b_ref, -0.6)
        
    # Zonas laterais (A1, B1, etc.) sofrem sucção dependendo da relação a/b
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

def obter_cpe_telhado_duas_aguas(h_b, beta):
    """
    Calcula os Coeficientes de Pressão Externa para telhados de DUAS ÁGUAS
    conforme a Tabela 5 da NBR 6123.
    """
    # Zonas E, G, F, H, I, J para vento a 0°
    v0_eg = {5: -0.8, 10: -0.8, 15: -0.8, 20: -0.9, 30: -1.0, 45: -1.2, 60: -1.2}
    v0_fh = {5: -0.6, 10: -0.6, 15: -0.6, 20: -0.7, 30: -0.8, 45: -0.9, 60: -1.0}
    v0_ij = {5: -0.2, 10: -0.2, 15: -0.2, 20: -0.3, 30: -0.4, 45: -0.4, 60: -0.4}
    
    # Vento a 90° depende da relação h/b
    if h_b <= 0.5:
        v90_ef = {5: -0.9, 10: (-1.1, -0.3), 15: (-1.0, 0.2), 20: (-0.7, 0.3), 30: (-0.3, 0.5), 45: 0.6, 60: 0.7}
        v90_gh = {5: -0.4, 10: -0.4, 15: -0.4, 20: -0.4, 30: -0.4, 45: -0.5, 60: -0.6}
    elif h_b >= 1.5:
        v90_ef = {5: -1.3, 10: -1.3, 15: (-1.3, -0.2), 20: (-1.1, 0.0), 30: (-0.7, 0.3), 45: 0.6, 60: 0.7}
        v90_gh = {5: -0.6, 10: -0.6, 15: -0.6, 20: -0.6, 30: -0.6, 45: -0.6, 60: -0.6}
    else: # Simplificação de segurança para h/b entre 0.5 e 1.5
        v90_ef = {5: -0.9, 10: (-1.1, -0.3), 15: (-1.0, 0.2), 20: (-0.7, 0.3), 30: (-0.3, 0.5), 45: 0.6, 60: 0.7}
        v90_gh = {5: -0.4, 10: -0.4, 15: -0.4, 20: -0.4, 30: -0.4, 45: -0.5, 60: -0.6}
        
    return {
        '0': {'EG': interpolar_telhado(beta, v0_eg), 'FH': interpolar_telhado(beta, v0_fh), 'IJ': interpolar_telhado(beta, v0_ij)},
        '90': {'EF': interpolar_telhado(beta, v90_ef), 'GH': interpolar_telhado(beta, v90_gh)}
    }

def obter_cpe_telhado_uma_agua(h_b, beta):
    """
    Calcula os Coeficientes de Pressão Externa para telhados de UMA ÁGUA
    conforme a Tabela 8 da NBR 6123.
    """
    v0_h = {5: -1.0, 10: -1.0, 15: -0.9, 20: -0.8, 30: -0.8}
    v0_i = {5: -0.5, 10: -0.5, 15: -0.5, 20: -0.6, 30: -0.6}
    v0_j = {5: -0.5, 10: -0.5, 15: -0.5, 20: -0.6, 30: -0.6}
    v0_l = {5: -0.3, 10: -0.3, 15: -0.3, 20: -0.4, 30: -0.4}

    v90_h = {5: -0.9, 10: -1.0, 15: -1.0, 20: -1.0, 30: -1.0}
    v90_i = {5: -0.8, 10: -0.8, 15: -0.8, 20: -0.8, 30: -0.8}
    v90_j = {5: -0.4, 10: -0.4, 15: -0.4, 20: -0.4, 30: -0.4}
    v90_l = {5: -0.4, 10: -0.4, 15: -0.4, 20: -0.4, 30: -0.4}
    
    return {
        '0': {
            'H': interpolar_telhado(beta, v0_h), 'I': interpolar_telhado(beta, v0_i),
            'J': interpolar_telhado(beta, v0_j), 'L': interpolar_telhado(beta, v0_l)
        },
        '90': {
            'H': interpolar_telhado(beta, v90_h), 'I': interpolar_telhado(beta, v90_i),
            'J': interpolar_telhado(beta, v90_j), 'L': interpolar_telhado(beta, v90_l)
        }
    }

def calc_res_val(cpe, cpi, q):
    """
    Calcula a pressão estática final: Delta_p = q * (Cpe - Cpi).
    Retorna formato numérico (float) para os gráficos.
    """
    if isinstance(cpe, tuple):
        return q * (cpe[0] - cpi) # Adota a primeira situação (geralmente mais crítica para sucção)
    return q * (cpe - cpi)

# ==========================================
# 3. GERADOR DE DIAGRAMAS (Matplotlib)
# ==========================================

def desenhar_carga(ax, x1, y1, x2, y2, val, arrow_len, label=""):
    """
    Função auxiliar geométrica para desenhar cargas distribuídas 
    (setas perpendiculares à superfície selecionada).
    """
    if val == 0: return
    
    # Encontra o ponto médio e o comprimento da face
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    
    # Calcula o Vetor Normal Unitário (apontando para fora num traçado horário)
    nx, ny = -dy / length, dx / length
    cor = "#ef4444" if val < 0 else "#3b82f6" # Vermelho (Sucção), Azul (Pressão)
    
    # Desenha 3 setas distribuídas pela face
    for i in [0.2, 0.5, 0.8]:
        px, py = x1 + dx * i, y1 + dy * i
        
        if val < 0: # Sucção (Seta empurra para fora)
            start = (px, py)
            end = (px + nx * arrow_len, py + ny * arrow_len)
        else: # Pressão (Seta entra na face)
            start = (px + nx * arrow_len, py + ny * arrow_len)
            end = (px, py)
            
        ax.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle="->", color=cor, lw=1.5))
        
    # Adiciona a caixa de texto com o valor no centro da distribuição de setas
    ax.text(cx + nx * arrow_len * 1.5, cy + ny * arrow_len * 1.5, f"{val:.1f}",
            ha='center', va='center', fontsize=9, color=cor, weight="bold", 
            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))
    
    if label:
        ax.text(cx - nx * arrow_len * 0.5, cy - ny * arrow_len * 0.5, label, 
                ha='center', va='center', fontsize=8, color="black")

def plot_diagrama_esforcos(dim_b, dim_h, dim_h1, p_esq, p_dir, p_tesq, p_tdir, titulo, is_vento_90=True, tipo_telhado="Duas águas"):
    """
    Renderiza o corte transversal da edificação com os esforços aplicados.
    """
    fig, ax = plt.subplots(figsize=(6, 4))
    arrow_len = max(dim_b, dim_h + dim_h1) * 0.15 # Tamanho dinâmico das setas

    # Desenho da edificação (Duas Águas ou Uma Água)
    if tipo_telhado == "Duas águas":
        x = [0, 0, dim_b/2, dim_b, dim_b]
        y = [0, dim_h, dim_h + dim_h1, dim_h, 0]
        ax.plot(x, y, color='black', linewidth=2)
        ax.fill_between([0, dim_b], [0, 0], [dim_h, dim_h], color='#f1f5f9')
        ax.fill_between([0, dim_b/2, dim_b], [dim_h, dim_h+dim_h1, dim_h], [dim_h, dim_h, dim_h], color='#e2e8f0')

        # Chamadas para desenhar cargas nas 4 faces visíveis
        l_esq = "Face A" if is_vento_90 else "Face C"
        desenhar_carga(ax, 0, 0, 0, dim_h, p_esq, arrow_len, l_esq)
        l_tesq = "Zonas E/F" if is_vento_90 else "Zonas E/G"
        desenhar_carga(ax, 0, dim_h, dim_b/2, dim_h + dim_h1, p_tesq, arrow_len, l_tesq)
        l_tdir = "Zonas G/H" if is_vento_90 else "Zonas F/H"
        desenhar_carga(ax, dim_b/2, dim_h + dim_h1, dim_b, dim_h, p_tdir, arrow_len, l_tdir)
        l_dir = "Face B" if is_vento_90 else "Face D"
        desenhar_carga(ax, dim_b, dim_h, dim_b, 0, p_dir, arrow_len, l_dir)
    else: 
        x = [0, 0, dim_b, dim_b, 0]
        y = [0, dim_h, dim_h + dim_h1, 0, 0]
        ax.plot(x[:4] + [0], y[:4] + [0], color='black', linewidth=2)
        ax.fill_between([0, dim_b], [0, 0], [dim_h, dim_h], color='#f1f5f9')
        ax.fill_between([0, dim_b], [dim_h, dim_h+dim_h1], [dim_h, dim_h], color='#e2e8f0')

        l_esq = "Face A" if is_vento_90 else "Face C"
        desenhar_carga(ax, 0, 0, 0, dim_h, p_esq, arrow_len, l_esq)
        l_t = "Zonas H/I" if is_vento_90 else "Zonas H/L"
        desenhar_carga(ax, 0, dim_h, dim_b, dim_h + dim_h1, p_tesq, arrow_len, l_t)
        l_dir = "Face B" if is_vento_90 else "Face D"
        desenhar_carga(ax, dim_b, dim_h + dim_h1, dim_b, 0, p_dir, arrow_len, l_dir)

    # Identificadores Visuais da direção do Vento (Dimensões Refinadas)
    if is_vento_90:
        # Seta do vento 90 graus: Mais delicada e levemente mais afastada
        ax.annotate("Vento", xy=(-arrow_len * 2.2, dim_h/2), xytext=(-arrow_len * 3.6, dim_h/2),
                    arrowprops=dict(facecolor='black', shrink=0.05, width=1.0, headwidth=5),
                    va='center', ha='right', weight='bold', fontsize=9)
    else:
        # Caixa do vento 0 graus: Reduzida em padding e fonte
        ax.text(dim_b/2, dim_h/2, "Vento Entrando\n(0°)",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="black", alpha=0.8, lw=0.8),
                color="black", weight="bold", ha='center', va='center', fontsize=7.5)

    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(titulo, pad=20, fontweight='bold', fontsize=14)
    ax.set_xlim(-dim_b*0.8, dim_b*1.8) # Margens extras laterais
    ax.set_ylim(0, dim_h + dim_h1 + dim_b*0.4) # Margem extra superior
    
    return fig

# ==========================================
# 4. INTERFACE GRÁFICA (Streamlit)
# ==========================================

st.set_page_config(page_title="Ventos NBR 6123", layout="wide")

# --- BARRA LATERAL (ENTRADAS DE DADOS) ---
with st.sidebar:
    st.header("Parâmetros de Entrada")
    
    st.subheader("1. Geometria")
    tipo_telhado = st.selectbox("Cobertura", ["Duas águas", "Uma água"])
    dim_a = st.number_input("Maior dim. em planta 'a' (m)", value=24.0)
    dim_b = st.number_input("Menor dim. em planta 'b' (m)", value=12.0)
    dim_h = st.number_input("Altura do pilar 'h' (m)", value=5.0)
    dim_h1 = st.number_input("Altura da cumeeira/desnível 'h1' (m)", value=1.5)
    angulo_beta = st.number_input("Ângulo do telhado 'β' (°)", value=14.0)
    
    st.subheader("2. Fatores de Vento")
    
    with st.expander("Visualizar Mapa V0"):
        try: st.image("isopletas.png", use_container_width=True)
        except: st.warning("Faça o upload de 'isopletas.png'")
            
    v0 = st.number_input("Veloc. Básica V0 (m/s)", value=45.0)
    s1 = st.number_input("Fator Topográfico S1", value=1.0)
    
    s2_categorias = ["I - Superfícies lisas", "II - Terrenos abertos", "III - Planos c/ obstáculos", "IV - Numerosos obstáculos", "V - Obstáculos altos"]
    s2_params = [(1.10, 0.06), (1.00, 0.085), (0.94, 0.10), (0.86, 0.12), (0.74, 0.15)]
    idx_cat = st.selectbox("Categoria S2", range(len(s2_categorias)), format_func=lambda x: s2_categorias[x], index=2)
    
    s3_valores = [1.10, 1.00, 0.95, 0.88, 0.83]
    s3_labels = ["1 - Hospitais/Bombeiros", "2 - Hotéis/Comércio", "3 - Indústria/Depósitos", "4 - Vedações", "5 - Temporárias"]
    idx_s3 = st.selectbox("Grupo S3", range(len(s3_labels)), format_func=lambda x: s3_labels[x], index=2)

    st.subheader("3. Pressão Interna (Cpi)")
    cpi_positivo = st.number_input("Cpi (Condição Positiva)", value=0.2)
    cpi_negativo = st.number_input("Cpi (Condição Negativa)", value=-0.3)

# --- PROCESSAMENTO DOS DADOS ---
# Fator S2 é ajustado dependendo da altura da edificação
altura_z = dim_h + (dim_h1 / 2.0)
z_calc = max(altura_z, 5.0) # A norma limita altura mínima de cálculo em z=5m
b_val, p_val = s2_params[idx_cat]
s2 = b_val * 1.0 * math.pow((z_calc / 10.0), p_val)
s3 = s3_valores[idx_s3]

# Cálculo da Pressão Dinâmica q = 0.613 * Vk²
vk = v0 * s1 * s2 * s3
q = 0.613 * math.pow(vk, 2)

# Determinação das proporções exigidas nas tabelas
rel_h_b = dim_h / dim_b
rel_a_b = dim_a / dim_b

# Chamada das funções que recuperam Cpe
cpe_paredes = obter_cpe_paredes(rel_h_b, rel_a_b)
if tipo_telhado == "Duas águas":
    cpe_telhado = obter_cpe_telhado_duas_aguas(rel_h_b, angulo_beta)
else:
    cpe_telhado = obter_cpe_telhado_uma_agua(rel_h_b, angulo_beta)

# --- TELA PRINCIPAL (EXIBIÇÃO DE RESULTADOS) ---
st.title("Forças de Vento - NBR 6123")
st.markdown("Cálculo estruturado das forças estáticas devidas ao vento em edificações retangulares.")

st.header("1. Pressão Dinâmica")
col1, col2, col3 = st.columns(3)
col1.metric("Velocidade Característica (Vk)", f"{vk:.2f} m/s")
col2.metric("Pressão Dinâmica (q)", f"{q:.2f} N/m²")
col3.metric("Fatores Utilizados", f"S1={s1:.2f} | S2={s2:.2f} | S3={s3:.2f}")

st.divider()

st.header("2. Coeficientes de Pressão Externa (Cpe)")
col_p, col_t = st.columns(2)

with col_p:
    st.subheader("Paredes")
    with st.expander("Ver Imagem da Norma (Paredes)"):
        try: st.image("cpe_paredes.png", use_container_width=True)
        except: st.warning("Faça upload de 'cpe_paredes.png'")

    st.write("**Vento a 0°**")
    st.write(f"- Face C (Frente): {cpe_paredes['0']['C']} | Face D (Fundos): {cpe_paredes['0']['D']}")
    st.write(f"- Laterais A/B: Z1= {cpe_paredes['0']['A1_B1']} | Z2= {cpe_paredes['0']['A2_B2']} | Z3= {cpe_paredes['0']['A3_B3']}")
    
    st.write("**Vento a 90°**")
    st.write(f"- Face A (Frente): {cpe_paredes['90']['A']} | Face B (Fundos): {cpe_paredes['90']['B']}")
    st.write(f"- Laterais C/D: Z1= {cpe_paredes['90']['C1_D1']} | Z2= {cpe_paredes['90']['C2_D2']}")

with col_t:
    st.subheader("Telhado")
    if tipo_telhado == "Duas águas":
        with st.expander("Ver Imagem da Norma (Duas Águas)"):
            try: st.image("cpe_telhado_2_aguas.png", use_container_width=True)
            except: st.warning("Faça upload de 'cpe_telhado_2_aguas.png'")
                
        st.write("**Vento a 0°**")
        st.write(f"- E/G: {cpe_telhado['0']['EG']} | F/H: {cpe_telhado['0']['FH']} | I/J: {cpe_telhado['0']['IJ']}")
        st.write("**Vento a 90°**")
        st.write(f"- Barlavento (E/F): {cpe_telhado['90']['EF']} *(Verificar Situações)*")
        st.write(f"- Sotavento (G/H): {cpe_telhado['90']['GH']}")
    else:
        with st.expander("Ver Imagem da Norma (Uma Água)"):
            try: st.image("cpe_telhado_1_agua.png", use_container_width=True)
            except: st.warning("Faça upload de 'cpe_telhado_1_agua.png'")
        
        st.write("**Vento a 0°**")
        st.write(f"- Zonas H: {cpe_telhado['0']['H']} | Zonas I: {cpe_telhado['0']['I']}")
        st.write(f"- Zonas J: {cpe_telhado['0']['J']} | Zonas L: {cpe_telhado['0']['L']}")
        st.write("**Vento a 90°**")
        st.write(f"- Zonas H: {cpe_telhado['90']['H']} | Zonas I: {cpe_telhado['90']['I']}")
        st.write(f"- Zonas J: {cpe_telhado['90']['J']} | Zonas L: {cpe_telhado['90']['L']}")

st.divider()

st.header("3. Esforços Resultantes Finais (Δp)")
st.markdown("As setas representam o sentido real da força. **Vermelho indica Sucção** (empurrando para fora) e **Azul indica Pressão** (empurrando para dentro). Valores em **N/m²**.")

# Exibição dividida em abas para cada situação de Pressão Interna (Cpi)
abas_result = st.tabs([f"Combinação 1 (Cpi = {cpi_positivo})", f"Combinação 2 (Cpi = {cpi_negativo})"])

# Plotagem Combinação 1 (Cpi Positivo)
with abas_result[0]:
    col_graf_0, col_graf_90 = st.columns(2)
    
    with col_graf_0:
        v0_pesq = calc_res_val(cpe_paredes['0']['C'], cpi_positivo, q)
        v0_pdir = calc_res_val(cpe_paredes['0']['D'], cpi_positivo, q)
        
        if tipo_telhado == "Duas águas":
            v0_tesq = calc_res_val(cpe_telhado['0']['EG'], cpi_positivo, q)
            v0_tdir = calc_res_val(cpe_telhado['0']['FH'], cpi_positivo, q)
        else:
            v0_tesq = calc_res_val(cpe_telhado['0']['H'], cpi_positivo, q) 
            v0_tdir = 0 
            
        fig_0 = plot_diagrama_esforcos(dim_b, dim_h, dim_h1, v0_pesq, v0_pdir, v0_tesq, v0_tdir, "Vento a 0°", is_vento_90=False, tipo_telhado=tipo_telhado)
        st.pyplot(fig_0)
        
    with col_graf_90:
        v90_pesq = calc_res_val(cpe_paredes['90']['A'], cpi_positivo, q)
        v90_pdir = calc_res_val(cpe_paredes['90']['B'], cpi_positivo, q)
        
        if tipo_telhado == "Duas águas":
            v90_tesq = calc_res_val(cpe_telhado['90']['EF'], cpi_positivo, q)
            v90_tdir = calc_res_val(cpe_telhado['90']['GH'], cpi_positivo, q)
        else:
            v90_tesq = calc_res_val(cpe_telhado['90']['H'], cpi_positivo, q)
            v90_tdir = 0
            
        fig_90 = plot_diagrama_esforcos(dim_b, dim_h, dim_h1, v90_pesq, v90_pdir, v90_tesq, v90_tdir, "Vento a 90°", is_vento_90=True, tipo_telhado=tipo_telhado)
        st.pyplot(fig_90)

# Plotagem Combinação 2 (Cpi Negativo)
with abas_result[1]:
    col_graf_0_c2, col_graf_90_c2 = st.columns(2)
    
    with col_graf_0_c2:
        v0_pesq_c2 = calc_res_val(cpe_paredes['0']['C'], cpi_negativo, q)
        v0_pdir_c2 = calc_res_val(cpe_paredes['0']['D'], cpi_negativo, q)
        
        if tipo_telhado == "Duas águas":
            v0_tesq_c2 = calc_res_val(cpe_telhado['0']['EG'], cpi_negativo, q)
            v0_tdir_c2 = calc_res_val(cpe_telhado['0']['FH'], cpi_negativo, q)
        else:
            v0_tesq_c2 = calc_res_val(cpe_telhado['0']['H'], cpi_negativo, q) 
            v0_tdir_c2 = 0
            
        fig_0_c2 = plot_diagrama_esforcos(dim_b, dim_h, dim_h1, v0_pesq_c2, v0_pdir_c2, v0_tesq_c2, v0_tdir_c2, "Vento a 0°", is_vento_90=False, tipo_telhado=tipo_telhado)
        st.pyplot(fig_0_c2)
        
    with col_graf_90_c2:
        v90_pesq_c2 = calc_res_val(cpe_paredes['90']['A'], cpi_negativo, q)
        v90_pdir_c2 = calc_res_val(cpe_paredes['90']['B'], cpi_negativo, q)
        
        if tipo_telhado == "Duas águas":
            v90_tesq_c2 = calc_res_val(cpe_telhado['90']['EF'], cpi_negativo, q)
            v90_tdir_c2 = calc_res_val(cpe_telhado['90']['GH'], cpi_negativo, q)
        else:
            v90_tesq_c2 = calc_res_val(cpe_telhado['90']['H'], cpi_negativo, q) 
            v90_tdir_c2 = 0
            
        fig_90_c2 = plot_diagrama_esforcos(dim_b, dim_h, dim_h1, v90_pesq_c2, v90_pdir_c2, v90_tesq_c2, v90_tdir_c2, "Vento a 90°", is_vento_90=True, tipo_telhado=tipo_telhado)
        st.pyplot(fig_90_c2)
