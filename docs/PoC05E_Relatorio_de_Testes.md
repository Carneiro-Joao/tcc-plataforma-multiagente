# PoC05E — Relatório visual de testes

Ferramenta para rodar a suíte inteira e ver o resultado numa página HTML.

## Como usar (PowerShell, dentro de `aula-ia-backend`)

```
python relatorio_testes.py                 # roda tudo e abre o relatório no navegador
python relatorio_testes.py --sem-abrir     # só grava o arquivo
python relatorio_testes.py --filtro juiz   # só testes cujo identificador contém "juiz"
```

Se `python` não funcionar no Windows, use `py relatorio_testes.py`.

- Os testes são offline: não usam chave de API nem internet.
- O relatório fica em `aula-ia-backend/local/relatorio_testes/relatorio-AAAAMMDD-HHMMSS.html` (pasta ignorada pelo Git). Nunca sobrescreve um anterior.
- Código de saída: 0 = tudo passou; 1 = há falha/erro; 2 = nenhum teste executado ou erro de uso.
- A página é um arquivo único (sem internet, tema claro/escuro), com filtros "Todos / Só problemas / Só ignorados", busca e módulos expansíveis. Módulos com problema abrem sozinhos.
- Módulo que nem consegue ser importado aparece como erro ("Falha ao importar"); nunca some silenciosamente.

## O que o relatório prova e o que não prova

Prova a lógica e os contratos do projeto (validador, integrador, contratos do Juiz, análise de séries). Não prova a qualidade pedagógica dos planos nem o comportamento de um LLM real: isso depende dos ensaios com API e da adjudicação humana.

Alternativa sem o relatório: `python -m unittest discover -s tests -v`.
