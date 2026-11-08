"""Núcleo teórico: Gramática Livre de Contexto -> simplificação -> FNC -> CYK.

Representação: dict  variavel -> lista de corpos; cada corpo é uma tupla de símbolos.
A tupla vazia () representa ε. Variáveis são as chaves do dict; o resto é terminal.
"""
from itertools import product

EPS = "ε"


# ------------------------------------------------------------ utilidades
def carregar(dados):
    """Converte o JSON ({"inicial", "producoes": {A: ["( P ) P", "ε"]}}) para a forma interna."""
    prods = {}
    for cab, corpos in dados["producoes"].items():
        prods[cab] = [tuple(s for s in c.split() if s != EPS) for c in corpos]
    return {"inicial": dados["inicial"], "producoes": prods}


def copiar(g):
    return {"inicial": g["inicial"], "producoes": {a: list(c) for a, c in g["producoes"].items()}}


def corpo_str(corpo):
    return " ".join(corpo) if corpo else EPS


def gramatica_str(g):
    """Texto da gramática, com a variável inicial na primeira linha."""
    ordem = [g["inicial"]] + [a for a in g["producoes"] if a != g["inicial"]]
    return "\n".join(f"{a} → " + " | ".join(corpo_str(c) for c in g["producoes"][a])
                     for a in ordem if a in g["producoes"])


def terminais(g):
    return sorted({s for cs in g["producoes"].values() for c in cs for s in c
                   if s not in g["producoes"]})


def _sem_repetidos(lista):
    return list(dict.fromkeys(lista))


# -------------------------------------------------------- simplificação
def novo_inicial(g):
    """Se a variável inicial aparece em algum lado direito, cria S0 → S."""
    ini = g["inicial"]
    if not any(ini in c for cs in g["producoes"].values() for c in cs):
        return g, "A variável inicial não aparece no lado direito: nada a fazer."
    novo = ini + "0"
    while novo in g["producoes"]:
        novo += "'"
    h = {"inicial": novo, "producoes": {novo: [(ini,)], **copiar(g)["producoes"]}}
    return h, f"Criada nova variável inicial {novo} → {ini}."


def anulaveis(g):
    nul, mudou = set(), True
    while mudou:
        mudou = False
        for a, cs in g["producoes"].items():
            if a not in nul and any(all(s in nul for s in c) for c in cs):
                nul.add(a)
                mudou = True
    return nul


def remover_vazias(g):
    """Remove produções ε (mantém S → ε apenas se a inicial for anulável)."""
    nul = anulaveis(g)
    novas = {}
    for a, cs in g["producoes"].items():
        lista = []
        for c in cs:
            # cada símbolo anulável pode ficar ou sair
            opcoes = [((s,), ()) if s in nul else ((s,),) for s in c]
            for escolha in product(*opcoes):
                corpo = tuple(x for parte in escolha for x in parte)
                if corpo or a == g["inicial"]:
                    lista.append(corpo)
        novas[a] = _sem_repetidos(lista)
    if g["inicial"] not in nul:
        novas[g["inicial"]] = [c for c in novas[g["inicial"]] if c]
    txt = "Anuláveis: {" + ", ".join(sorted(nul)) + "}" if nul else "Não há variáveis anuláveis."
    return {"inicial": g["inicial"], "producoes": novas}, txt


def remover_unitarias(g):
    """Remove produções A → B substituindo-as pelas produções não unitárias de B."""
    P = g["producoes"]
    unit = lambda c: len(c) == 1 and c[0] in P
    novas, pares = {}, []
    for a in P:
        fecho, pilha = [a], [a]          # fecho unitário de a (ordem de descoberta)
        while pilha:
            x = pilha.pop()
            for c in P[x]:
                if unit(c) and c[0] not in fecho:
                    fecho.append(c[0])
                    pilha.append(c[0])
        pares += [f"{a} ⇒* {b}" for b in fecho[1:]]
        novas[a] = _sem_repetidos([c for b in fecho for c in P[b] if not unit(c)])
    txt = ("Pares unitários: " + ", ".join(pares)) if pares else "Não há produções unitárias."
    return {"inicial": g["inicial"], "producoes": novas}, txt


def remover_inuteis(g):
    """Remove símbolos que não geram terminais e depois os inalcançáveis."""
    P = g["producoes"]
    gera, mudou = set(), True
    while mudou:
        mudou = False
        for a, cs in P.items():
            if a not in gera and any(all(s not in P or s in gera for s in c) for c in cs):
                gera.add(a)
                mudou = True
    P1 = {a: [c for c in cs if all(s not in P or s in gera for s in c)]
          for a, cs in P.items() if a in gera}
    alc, pilha = {g["inicial"]}, [g["inicial"]]
    while pilha:
        for c in P1.get(pilha.pop(), []):
            for s in c:
                if s in P1 and s not in alc:
                    alc.add(s)
                    pilha.append(s)
    P2 = {a: cs for a, cs in P1.items() if a in alc}
    removidos = [a for a in P if a not in P2]
    txt = ("Removidas: " + ", ".join(removidos)) if removidos else "Não há símbolos inúteis."
    return {"inicial": g["inicial"], "producoes": P2}, txt


# ---------------------------------------------------------------- FNC
def _nome_livre(usados, prefixo):
    i = 1
    while f"{prefixo}{i}" in usados:
        i += 1
    usados.add(f"{prefixo}{i}")
    return f"{prefixo}{i}"


def para_fnc(g, nomes_terminais=None):
    """Recebe gramática simplificada; devolve FNC (A → BC | a, S → ε)."""
    nomes_terminais = dict(nomes_terminais or {})
    P = copiar(g)["producoes"]
    usados = set(P)

    # 1) terminais em corpos de tamanho >= 2 viram variáveis  (T → t)
    var_t = {}
    for a in list(P):
        for i, c in enumerate(P[a]):
            if len(c) >= 2:
                novo = []
                for s in c:
                    if s not in P and s not in var_t.values():
                        if s not in var_t:
                            nome = nomes_terminais.get(s)
                            if not nome or nome in usados:
                                nome = _nome_livre(usados, "T")
                            usados.add(nome)
                            var_t[s] = nome
                        novo.append(var_t[s])
                    else:
                        novo.append(s)
                P[a][i] = tuple(novo)
    for t, v in var_t.items():
        P[v] = [(t,)]
    txt1 = ", ".join(f"{v} → {t}" for t, v in var_t.items()) or "nenhuma"

    # 2) corpos com 3+ variáveis são quebrados; caudas iguais reutilizam a mesma variável
    cauda = {}

    def _ref(simbolos):
        """Variável (ou par) que gera exatamente 'simbolos'."""
        if len(simbolos) == 1:
            return simbolos[0]
        if simbolos not in cauda:
            nome = _nome_livre(usados, "Z")
            cauda[simbolos] = nome
            P[nome] = [(simbolos[0], _ref(simbolos[1:]))]
        return cauda[simbolos]

    for a in list(P):
        P[a] = _sem_repetidos([c if len(c) <= 2 else (c[0], _ref(c[1:])) for c in P[a]])
    txt2 = ", ".join(f"{v} → {' '.join(P[v][0])}  (gera {' '.join(s)})"
                     for s, v in cauda.items()) or "nenhuma"
    return {"inicial": g["inicial"], "producoes": P}, txt1, txt2


def pipeline(g, nomes_terminais=None):
    """Lista de etapas (titulo, explicacao, gramatica) até a FNC."""
    etapas = [("Gramática original", "", g)]
    for titulo, f in [("1. Nova variável inicial", novo_inicial),
                      ("2. Remoção de produções vazias (ε)", remover_vazias),
                      ("3. Remoção de produções unitárias", remover_unitarias),
                      ("4. Remoção de símbolos inúteis", remover_inuteis)]:
        g, txt = f(g)
        etapas.append((titulo, txt, g))
    fnc, t1, t2 = para_fnc(g, nomes_terminais)
    etapas.append(("5. Forma Normal de Chomsky",
                   f"Variáveis para terminais: {t1}.\nVariáveis para quebrar corpos longos: {t2}.",
                   fnc))
    return etapas


def eh_fnc(g):
    P = g["producoes"]
    for a, cs in P.items():
        for c in cs:
            ok = (len(c) == 2 and all(s in P and s != g["inicial"] for s in c)) or \
                 (len(c) == 1 and c[0] not in P) or (len(c) == 0 and a == g["inicial"])
            if not ok:
                return False
    return True


# ---------------------------------------------------------------- CYK
def cyk(g, w):
    """Retorna (aceita, tabela, arvore). tabela[i][j] = {A: backpointer} para w[i:i+j+1].
    Árvore: (simbolo, [filhos]); folhas terminais têm filhos []."""
    P, S, n = g["producoes"], g["inicial"], len(w)
    if n == 0:
        ok = () in P.get(S, [])
        return ok, [], ((S, [(EPS, [])]) if ok else None)
    T = [[{} for _ in range(n - i)] for i in range(n)]
    for i, ch in enumerate(w):
        for a, cs in P.items():
            if (ch,) in cs:
                T[i][0][a] = ch
    for l in range(2, n + 1):                 # comprimento do trecho
        for i in range(n - l + 1):
            for k in range(1, l):             # ponto de corte
                esq, dir_ = T[i][k - 1], T[i + k][l - k - 1]
                for a, cs in P.items():
                    if a in T[i][l - 1]:
                        continue
                    for c in cs:
                        if len(c) == 2 and c[0] in esq and c[1] in dir_:
                            T[i][l - 1][a] = (k, c[0], c[1])
                            break

    def montar(a, i, l):
        bp = T[i][l - 1][a]
        if isinstance(bp, str):
            return (a, [(bp, [])])
        k, b, c = bp
        return (a, [montar(b, i, k), montar(c, i + k, l - k)])

    ok = S in T[0][n - 1]
    return ok, T, (montar(S, 0, n) if ok else None)


def numerar(arvore):
    """Atribui ids aos nós: devolve (raiz_id, nos{id: simbolo}, filhos{id: [ids]})."""
    nos, filhos = {}, {}
    def rec(no):
        i = len(nos)
        nos[i] = no[0]
        filhos[i] = [rec(f) for f in no[1]]
        return i
    return rec(arvore), nos, filhos


def derivacao_esquerda(arvore, variaveis):
    """Passos da derivação mais à esquerda: lista de (forma_sentencial, id_expandido, producao)."""
    raiz, nos, filhos = numerar(arvore)
    forma = [raiz]
    passos = [([nos[raiz]], None, None)]
    while True:
        pos = next((p for p, i in enumerate(forma) if nos[i] in variaveis and filhos[i]), None)
        if pos is None:
            break
        i = forma[pos]
        forma = forma[:pos] + [f for f in filhos[i] if nos[f] != EPS] + forma[pos + 1:]
        prod = f"{nos[i]} → " + " ".join(nos[f] for f in filhos[i])
        passos.append(([nos[x] for x in forma], i, prod))
    return passos, nos, filhos


# ------------------------------------------------------------- entrada
def ler_entrada(texto):
    """Linhas 'sentença ; esperado' (esperado = aceita/rejeita, opcional). '#' é comentário."""
    casos = []
    for linha in texto.splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        sent, _, esp = linha.partition(";")
        sent = sent.strip().replace(" ", "")
        esp = esp.strip().lower()
        casos.append(("" if sent == EPS else sent,
                      None if not esp else esp.startswith("aceit")))
    return casos
