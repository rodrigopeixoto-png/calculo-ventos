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
    "Cpe - Paredes/Telhado",
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
    "III - Terrenos planos/ondulados (granjas, subúrbios)": {"A": (0.94, 0.10), "B": (0.94, 0.105), "C": (0.93, 0.115)},
    "IV - Terrenos com muitos obstáculos (zonas urbanas)": {"A": (0.86, 0.12), "B": (0.85, 0.125), "C": (0.84, 0.135)},
    "V - Terrenos com obstáculos altos (centros)": {"A": (0.74, 0.15), "B": (0.73, 0.16), "C": (0.71, 0.17)}
}

if 'altura_z' not in st.session_state:
    st.session_state['altura_z'] = 5.0
if 'maior_dimensao' not in st.session_state:
    st.session_state['maior_dimensao'] = 24.0

# ==========================================
# ABA 1: Geometria
# ==========================================
with abas[0]:
    st.header("Dimensões da Edificação")
    
    col_img, col_dados = st.columns([1, 1])
    
    with col_img:
        # Tenta carregar a imagem, se não encontrar, exibe um aviso
        try:
            st.image("image_6326c1.png", caption="Nomenclatura das dimensões e faces", use_container_width=True)
        except:
            st.warning("Faça o upload do arquivo 'image_6326c1.png' no GitHub para visualizar o esquema.")
            
    with col_dados:
        dim_a = st.number_input("Dimensão 'a' (m)", value=24.0, step=1.0)
        dim_b = st.number_input("Dimensão 'b' (m)", value=12.0, step=1.0)
        dim_h = st.number_input("Altura do pilar 'h' (m)", value=5.0, step=0.5)
        dim_h1 = st.number_input("Altura da cumeeira 'h1' (m)", value=1.5, step=0.1)
        dist_porticos = st.number_input("Distância entre pórticos 'p' (m)", value=6.0, step=1.0)
        angulo_beta = st.number_input("Ângulo do telhado 'β' (°)", value=14.0, step=1.0)
    
    st.session_state['altura_z'] = dim_h + (dim_h1 / 2)
    st.session_state['maior_dimensao'] = max(dim_a, dim_b)

# ==========================================
# ABA 2: Velocidade Básica (V0)
# ==========================================
with abas[1]:
    st.header("Análise das Isopletas de Vento")
    st.write("Verifique a localização da edificação no mapa de isopletas da NBR 6123.")
    
    try:
        st.image("image_6326a3.png", caption="Isopletas da Velocidade Básica (V0) no Brasil (m/s)", use_container_width=True)
    except:
        st.warning("Faça o upload do arquivo 'image_6326a3.png' no GitHub.")
    
    v0 = st.number_input("Insira a Velocidade Básica - V0 (m/s) lida no mapa", value=45.0, step=1.0)

# ==========================================
# ABA 3: Fator Topográfico (S1)
# ==========================================
with abas[2]:
    st.header("Fator Topográfico - S1")
    
    try:
        st.image("image_6323f8.png", caption="Comportamento do vento em Taludes e Morros", use_container_width=True)
    except:
        st.warning("Faça o upload do arquivo 'image_6323f8.png' no GitHub.")
        
    tipo_terreno = st.radio(
        "Selecione o tipo de relevo:",
        ["Terreno plano ou fracamente acidentado (S1 = 1.0)",
         "Taludes e Morros (Calcular)",
         "Vales profundos (S1 = 0.9)"]
    )
    
    s1 = 1.0
    if "plano" in tipo_terreno:
        s1 = 1.0
    elif "Vales" in tipo_terreno:
        s1 = 0.9
    else:
        st.write("Parâmetros do Talude/Morro:")
        angulo_t = st.number_input("Ângulo (º)", value=15.0)
        s1 = st.number_input("Valor calculado de S1 (insira manualmente após analisar o ábaco)", value=1.1, step=0.05)
        
    st.metric(label="Valor Adotado para S1", value=f"{s1:.2f}")

# ==========================================
# ABA 4: Fator de Rugosidade (S2)
# ==========================================
with abas[3]:
    st.header("Fator de Rugosidade e Dimensões - S2")
    
    categoria = st.selectbox("Categoria do Terreno (Rugosidade)", list(s2_params.keys()), index=2)
    
    maior_dim = st.session_state['maior_dimensao']
    if maior_dim <= 20:
        classe_auto = "A"
    elif maior_dim <= 50:
        classe_auto = "B"
    else:
        classe_auto = "C"
        
    st.write(f"Maior dimensão da edificação: **{maior_dim} m**")
    classe = st.selectbox("Classe da Edificação", ["A (≤ 20m)", "B (20m a 50m)", "C (> 50m)"], 
                          index=["A", "B", "C"].index(classe_auto))
    classe_key = classe[0] 
    
    z = st.number_input("Altura (z) para cálculo de S2 (m)", value=st.session_state['altura_z'])
    
    b_val, p_val = s2_params[categoria][classe_key]
    fr = 1.0 
    z_calc = max(z, 5.0) 
    
    s2 = b_val * fr * math.pow((z_calc / 10.0), p_val)
    st.metric(label="Valor Calculado para S2", value=f"{s2:.3f}")

# ==========================================
# ABA 5: Fator Estatístico (S3)
# ==========================================
with abas[4]:
    st.header("Fator Estatístico - S3")
    try:
        st.image("image_632377.png", caption="Tabela de Fatores Estatísticos", use_container_width=True)
    except:
        pass
    
    grupo_s3 = st.radio("Selecione o grupo da edificação:", list(s3_valores.keys()), index=2)
    s3 = s3_valores[grupo_s3]
    st.metric(label="Valor Adotado para S3", value=f"{s3:.2f}")

# ==========================================
# ABA 6: Esquemas Cpe (Paredes e Telhado)
# ==========================================
with abas[5]:
    st.header("Coeficientes de Pressão Externa (Cpe)")
    st.write("Visuais de referência para determinação dos coeficientes externos.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Cpe - Paredes")
        try:
            st.image("image_63233a.png", use_container_width=True)
        except:
            st.warning("Faça o upload do arquivo 'image_63233a.png'.")
            
    with col2:
        st.subheader("Cpe - Telhado")
        try:
            st.image("image_632304.png", use_container_width=True)
        except:
            st.warning("Faça o upload do arquivo 'image_632304.png'.")

# ==========================================
# ABA 7: Resultados e Esforços
# ==========================================
with abas[6]:
    st.header("Velocidade Característica e Pressão Dinâmica")
    
    # Cálculo
    vk = v0 * s1 * s2 * s3
    q = 0.613 * math.pow(vk, 2)
    q_kn = q / 1000.0
    
    col_res1, col_res2 = st.columns(2)
    col_res1.metric(label="Velocidade Característica (Vk)", value=f"{vk:.2f} m/s")
    col_res2.metric(label="Pressão Dinâmica (q)", value=f"{q_kn:.4f} kN/m²", delta=f"{q:.1f} N/m²", delta_color="off")
    
    st.divider()
    
    st.subheader("Combinação de Esforços Resultantes")
    st.write("Para os esforços reais, considera-se a subtração do Cpi em relação ao Cpe para cada elemento.")
    
    try:
        st.image("image_631fd7.png", caption="Exemplos de Combinações de Vento", use_container_width=True)
        st.image("image_631f97.png", caption="Esforços Finais Resultantes", use_container_width=True)
    except:
        st.warning("Faça o upload dos arquivos 'image_631fd7.png' e 'image_631f97.png'.")
