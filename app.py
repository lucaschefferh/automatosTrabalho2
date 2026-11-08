"""GLC -> Forma Normal de Chomsky -> derivação.  Rodar com:  streamlit run app.py

Abas: 1) gramática original e FNC  2) simplificação passo a passo
      3) derivação de uma sentença (árvore)  4) sentenças do arquivo de entrada"""
import json
import time

import pandas as pd
import streamlit as st

from gramatica import (EPS, carregar, pipeline, gramatica_str, terminais, eh_fnc,
                       cyk, derivacao_esquerda, ler_entrada)

st.set_page_config(page_title="GLC → FNC & Derivação", layout="wide")

INTERVALO = 1.0
C_ATIVO, C_FOLHA, C_VAR, C_ARESTA = "#ffd43b", "#b2f2bb", "#d0ebff", "#e03131"


# ------------------------------------------------------------------ DOT
def _q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def arvore_dot(nos, filhos, variaveis, passos, k):
    """Desenha a árvore até o passo k da derivação (nós ainda não expandidos ficam tracejados)."""
    expandidos = [p[1] for p in passos[1:k + 1]]
    ativo = expandidos[-1] if expandidos else None
    visiveis = {0} | {f for i in expandidos for f in filhos[i]}
    linhas = ["digraph { bgcolor=transparent; size=\"10,5.2\"; nodesep=0.2; ranksep=0.3; "
              "node [fontname=Helvetica fontsize=14 shape=circle style=filled width=0.5 "
              "fixedsize=true]; edge [arrowhead=none];"]
    for i in sorted(visiveis):
        s = nos[i]
        if s in variaveis:
            cor = C_ATIVO if i == ativo else C_VAR
            estilo = "filled" if i in expandidos else "filled,dashed"
            larg = 3 if i == ativo else 1
            linhas.append(f"{i} [label={_q(s)} fillcolor={_q(cor)} style={_q(estilo)} "
                          f"penwidth={larg}];")
        else:
            linhas.append(f"{i} [label={_q(s)} shape=box fillcolor={_q(C_FOLHA)}];")
    for i in expandidos:
        for f in filhos[i]:
            cor = C_ARESTA if i == ativo else "black"
            linhas.append(f"{i} -> {f} [color={_q(cor)} penwidth={3 if i == ativo else 1}];")
    return "\n".join(linhas) + "}"


# --------------------------------------------------------------- helpers
@st.cache_data
def preparar(texto_json):
    dados = json.loads(texto_json)
    g = carregar(dados)
    return pipeline(g, dados.get("nomes_terminais"))


def mostrar_gramatica(g):
    st.code(gramatica_str(g), language=None)


def selo(ok):
    return "✅ ACEITA" if ok else "❌ REJEITA"


def mover(chave, delta, n):
    st.session_state[chave] = min(n, max(0, st.session_state[chave] + delta))


def controles(chave, n, sig):
    if st.session_state.get("sig_" + chave) != sig:
        st.session_state[chave] = 0
        st.session_state["sig_" + chave] = sig
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 6])
    c1.button("⏮", key=f"r_{chave}", help="Reiniciar", on_click=mover, args=(chave, -10**6, n))
    c2.button("◀", key=f"a_{chave}", help="Passo anterior", on_click=mover, args=(chave, -1, n))
    c3.button("▶", key=f"p_{chave}", help="Próximo passo", on_click=mover, args=(chave, 1, n))
    play = c4.button("⏵⏵", key=f"pl_{chave}", help="Reproduzir do início", type="primary")
    if n > 0:
        c5.slider("Passo da derivação", 0, n, key=chave)
    return (st.session_state[chave] if n > 0 else 0), play


def painel_derivacao(fnc, w, chave):
    variaveis = fnc["producoes"]
    ok, T, arv = cyk(fnc, w)
    st.markdown(f"### Sentença `{w or EPS}` → **{selo(ok)}**")
    if not ok:
        st.error("Não existe árvore de derivação: a variável inicial "
                 f"**{fnc['inicial']}** não gera a sentença.")
        return
    passos, nos, filhos = derivacao_esquerda(arv, variaveis)
    n = len(passos) - 1
    k, play = controles(chave, n, (w, json.dumps(fnc["producoes"], default=list)))
    c_arv, c_der = st.columns([3, 2])
    area_arv = c_arv.empty()
    area_der = c_der.empty()

    def desenhar(k):
        with area_arv.container(horizontal_alignment="center"):
            st.graphviz_chart(arvore_dot(nos, filhos, variaveis, passos, k), width="content")
        linhas = []
        for j, (forma, _, prod) in enumerate(passos[:k + 1]):
            txt = " ".join(forma) or EPS
            seta = "" if j == 0 else "⇒ "
            regra = f"   [{prod}]" if prod else ""
            linhas.append(f"{seta}{txt}{regra}")
        area_der.code("Derivação mais à esquerda\n\n" + "\n".join(linhas), language=None)

    if play:
        for j in range(n + 1):
            desenhar(j)
            time.sleep(INTERVALO)
    else:
        desenhar(k)


# --------------------------------------------------------------- estado
with open("gramatica.json", encoding="utf-8") as f:
    texto_padrao = f.read()

st.title("Gramática Livre de Contexto → Forma Normal de Chomsky")
st.caption("Exercício 6 — Σ = { (, ), [, ] }: cadeias só de parênteses balanceados "
           "ou só de colchetes balanceados, sem misturar.")

try:
    etapas = preparar(texto_padrao)
except Exception as e:  # JSON inválido etc.
    st.error(f"Gramática inválida: {e}")
    st.stop()

original, fnc = etapas[0][2], etapas[-1][2]
aba1, aba2, aba3, aba4 = st.tabs(["Gramática original e FNC", "Simplificação passo a passo",
                                  "Derivação (árvore)", "Arquivo de entrada"])

# --------------------------------------------------- 1. original x FNC
with aba1:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Gramática original")
        mostrar_gramatica(original)
        st.markdown(f"**Variáveis:** {', '.join(original['producoes'])}  \n"
                    f"**Terminais:** {', '.join(terminais(original))}  \n"
                    f"**Inicial:** {original['inicial']}")
        st.info("**P** gera parênteses balanceados e **C** gera colchetes balanceados. "
                "Como S escolhe só um dos dois, os tipos nunca se misturam.")
    with c2:
        st.subheader("Forma Normal de Chomsky")
        mostrar_gramatica(fnc)
        st.markdown(f"**Variáveis:** {', '.join(fnc['producoes'])}  \n"
                    f"**Está na FNC?** {'Sim ✅' if eh_fnc(fnc) else 'Não ❌'}")
        st.caption("Regras da FNC: A → BC, A → a, e S → ε apenas para a variável inicial "
                   "(que não aparece em nenhum lado direito).")

# ------------------------------------------------------ 2. etapas
with aba2:
    for i, (titulo, txt, g) in enumerate(etapas):
        anterior = gramatica_str(etapas[i - 1][2]) if i else None
        with st.expander(titulo + ("" if i == 0 or gramatica_str(g) != anterior
                                   else "  (sem alterações)"), expanded=True):
            if txt:
                st.markdown(txt.replace("\n", "  \n"))
            mostrar_gramatica(g)

# ------------------------------------------------------ 3. derivação
with aba3:
    w = st.text_input("Sentença (deixe vazio ou digite ε para a cadeia vazia)", "(())")
    w = "" if w.strip() == EPS else w.replace(" ", "")
    painel_derivacao(fnc, w, "passo_manual")

# ------------------------------------------------------ 4. arquivo
with aba4:
    st.caption("Formato: uma sentença por linha (ε = cadeia vazia). "
               "Linhas com `#` são comentários.")
    arq = st.file_uploader("Arquivo de entrada (.txt)", type=["txt"])
    if arq is None:
        st.info("Envie o arquivo de entrada para testar as sentenças.")
        st.stop()
    casos = ler_entrada(arq.getvalue().decode("utf-8"))
    linhas = []
    for s, _ in casos:
        linhas.append({"Sentença": s or EPS, "Resultado": selo(cyk(fnc, s)[0])})
    st.dataframe(pd.DataFrame(linhas), width="stretch", hide_index=True)
