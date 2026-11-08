# GLC → Forma Normal de Chomsky → Derivação (Exercício 6)

Σ = { (, ), [, ] }: cadeias formadas **só por parênteses balanceados** ou **só por colchetes
balanceados**, sem misturar os dois tipos.

## Gramática original

```
S → P | C
P → ( P ) P | ε
C → [ C ] C | ε
```

## Forma Normal de Chomsky (gerada pelo programa)

```
S → ε | A Z1 | A Z3 | A Z2 | A B | D Z4 | D Z6 | D Z5 | D E
P → A Z1 | A Z3 | A Z2 | A B
C → D Z4 | D Z6 | D Z5 | D E
A → (    B → )    D → [    E → ]
Z1 → P Z2   Z2 → B P   Z3 → P B
Z4 → C Z5   Z5 → E C   Z6 → C E
```

Etapas: nova variável inicial (não precisou) → remoção de ε (anuláveis {S, P, C}) →
remoção de unitárias (S ⇒* P, S ⇒* C) → remoção de inúteis (nenhum) → FNC.

## Como executar

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Abas

1. **Gramática original e FNC** lado a lado.
2. **Simplificação passo a passo**: a gramática depois de cada etapa.
3. **Derivação (árvore)**: digite uma sentença; o algoritmo CYK decide se ela pertence à
   linguagem e monta a árvore de derivação, mostrada passo a passo (derivação mais à esquerda).
4. **Arquivo de entrada**: envie o `entrada.txt` pelo botão de upload; o programa testa todas as sentenças
   e mostra se cada uma é aceita ou rejeitada.

## Arquivos

| Arquivo | Função |
|---|---|
| `app.py` | Interface Streamlit e desenho da árvore (DOT/Graphviz) |
| `gramatica.py` | Simplificação, conversão para FNC, CYK e derivação mais à esquerda |
| `gramatica.json` | Gramática original |
| `entrada.txt` | Sentenças de aceite/rejeite do enunciado (`sentença ; aceita/rejeita`) |
