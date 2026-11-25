# Scripts históricos (não fazem parte do sistema)

Movidos para cá na auditoria de 25/11/2026 (achado C7). Ficam só como registro das sondagens da PoC 03.

| Script | O que era | Situação |
|---|---|---|
| `teste_api_rapido.py` | Sondagem do `AgenteOpenAI` (OpenAI, PoC 03) | **Não roda mais**: `geracao.AgenteOpenAI` foi removido na PoC 04A, quando o projeto passou para o Gemini |
| `teste_openrouter.py` | Sondagem com modelos gratuitos do OpenRouter (PoC 03) | **Não roda mais**, pelo mesmo motivo |

O sistema atual usa o Gemini nos especialistas e o Groq (`openai/gpt-oss-120b`) na IA Juiz. Ferramentas vigentes: ver o `README.md` da raiz.
