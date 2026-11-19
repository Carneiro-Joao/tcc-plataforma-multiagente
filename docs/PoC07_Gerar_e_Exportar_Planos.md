# PoC07 — Gerar planos reais (Gemini) e exportá-los para revisão

Objetivo: gerar alguns planos com a IA de verdade, olhar a qualidade e guardá-los como **casos congelados** (servem depois ao Juiz).
Os planos de IA são **evidência provisória**: n pequeno, sem afirmação de qualidade antes da revisão humana.

## 1. Chave de API (nunca no chat, em arquivo ou no Git)
Duas formas, na janela do CMD que vai rodar o app:

- **Recomendada:** `--pedir-chave` — o programa pergunta a chave com entrada oculta (nada aparece na tela) e **não salva**.
- Ou: `set GEMINI_API_KEY=sua_chave` na **mesma janela** (só vale nela; ao fechar, some). Não use `setx` (grava no Windows).

## 2. Subir o app com a IA
```
cd aula-ia-backend
python app.py --modo lexical --gerador ia --ipv4 --pedir-chave --abrir
```
Modelo padrão: `gemini-3.5-flash-lite` (`--modelo` troca). Cada plano faz 6 chamadas (5 especialistas + avaliação em duas etapas) e pode levar
alguns minutos; indisponibilidade 503 é repetida até 2 vezes (`--repeticoes-503`). Feche qualquer `app.py` antigo antes (porta ocupada = código velho).
Os dados ficam em `local/consultas.sqlite3` (fora do Git).

**Limite diário (proteção de gasto):** com `--gerador ia`, o app aceita no máximo **5 gerações por dia** (data local), contando
tentativas com falha e "Gerar outra versão", pois todas gastam chamadas. Ao atingir, a tela mostra o aviso e nenhuma chamada é feita.
Ao iniciar, o terminal mostra `Limite: 5 planos com IA por dia; usados hoje: N.` Para mudar: `--limite-diario 8`; `--limite-diario 0`
desliga (não recomendado). O modo demonstração não conta nem é limitado. Isso complementa, e não substitui, o limite de gasto na conta do Google.

## 3. Gerar os planos
Sugestão de 4 combinações para ter variedade (tema × tipo × recursos):

| Tema | Tipo | Recursos |
|---|---|---|
| ordenação | Computação desplugada | quadro e pincel, material impresso |
| recursão | Aula prática | computadores |
| privacidade de dados pessoais | Aula teórica | quadro e pincel, projetor |
| fake news | Projeto | celulares, internet |

Em cada um: Consultar habilidades → escolher e confirmar → Gerar plano. Aprovar é opcional; um plano `rascunho` também é exportado.
Se algum tema voltar sem habilidade (fora da BNCC do 8º ano), tudo bem: anote, é um achado.

## 4. Exportar
```
python exportar_planos.py
```
Gera `local/planos_ia/<tema>_r<revisão>_<id>.json` para cada plano real e lista o que foi pulado, com motivo (demonstração, falha, plano que
viola o contrato, credencial no texto). Abre o banco só para leitura e nunca sobrescreve. Envie os arquivos para revisão.

## Limites
- A checagem de credencial é por padrão (`AIza…`, `gsk_…`, `sk-…`) e pelo `sanitizar` do Juiz (chave do Groq no ambiente); não prova ausência de segredos.
- Plano gerado não é validado pedagogicamente: o validador só confere o contrato. Falha técnica (503, 429) é registrada à parte e não conta como plano.
