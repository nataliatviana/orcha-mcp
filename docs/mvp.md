# Escopo do MVP — orcha-mcp

> Este documento define o que entra na primeira versão entregável do `orcha-mcp`.
> Para o backlog completo (incluindo itens pós-MVP), veja [backlog.md](./backlog.md).

---

## Objetivo do MVP

Entregar uma CLI Python funcional que:

1. Conecta a **múltiplos MCP servers** (local STDIO + remoto HTTP) configurados via `orcha.json`
2. **Descobre ferramentas** (`tools/list`) e as exibe formatadas no terminal
3. **Executa ferramentas** (`tools/call`) diretamente via CLI
4. Integra um **LLM real** (Anthropic Claude) que decide quais ferramentas usar
5. **Expõe o protocolo** JSON-RPC bruto em cada etapa com flag `--verbose`

O MVP deve ser suficiente para que um desenvolvedor entenda, de forma prática e observável, como o ciclo MCP funciona de ponta a ponta.

---

## O que está INCLUÍDO no MVP

### Comandos CLI

| Comando | Descrição |
|---------|-----------|
| `orcha list-tools` | Lista todas as tools de todos os servers habilitados |
| `orcha describe <tool>` | Exibe o `inputSchema` completo de uma tool |
| `orcha call <tool> --args '<json>'` | Executa uma tool diretamente, sem LLM |
| `orcha chat "<pergunta>"` | Ciclo completo: LLM → tool_use → MCP → resultado |
| `orcha chat --interactive` | REPL de chat com histórico mantido entre turnos |

### Flags globais

| Flag | Comportamento |
|------|---------------|
| `--verbose` / `-v` | Exibe JSON-RPC bruto formatado em cada step |
| `--dry-run` | Mostra o que seria feito sem executar |
| `--config <path>` | Usa arquivo de config alternativo |
| `--server <nome>` | Restringe a operação a um server específico |

### Configuração (`orcha.json`)

- Suporte a `type: "local"` (STDIO) e `type: "remote"` (HTTP)
- Campo `enabled` por server (true/false)
- Campo `environment` para vars de ambiente por server
- Configuração do provider LLM (`provider`, `model`)

### Transports

- **STDIO**: servidores locais iniciados como subprocesso
- **HTTP (Streamable)**: servidores remotos via POST + SSE

### LLM

- Provider: **Anthropic Claude** via `ANTHROPIC_API_KEY`
- Modelos suportados: qualquer modelo Claude com suporte a `tool_use`
- Loop de orquestração: múltiplas rodadas até resposta final

---

## O que está FORA do MVP

| Item | Motivo |
|------|--------|
| TUI interativa | Adiciona complexidade de UI sem valor didático imediato |
| Primitivos Resources | Fora do foco inicial (tools são o core do MCP) |
| Primitivos Prompts | Fora do foco inicial |
| Orquestração multi-agente | Épico E7, pós-MVP |
| Múltiplos providers LLM (OpenAI, Gemini) | Complexidade desnecessária no MVP; Anthropic tem o melhor suporte a tool_use |
| OAuth automático para servers remotos | Servers remotos do MVP usarão Bearer token simples |
| Registry de MCP servers públicos | Configuração manual é suficiente para aprendizado |

---

## Histórias de Usuário do MVP

Referência completa no [backlog.md](./backlog.md). Resumo:

| ID | Descrição | Prioridade |
|----|-----------|------------|
| US01 | Conexão STDIO com server local | Alta |
| US02 | Conexão HTTP com server remoto | Alta |
| US03 | Exibição da capability negotiation | Alta |
| US04 | Configuração de múltiplos servers via JSON | Alta |
| US05 | Ativar/desativar servers individualmente | Alta |
| US06 | Path alternativo de config | Média |
| US07 | Listar todas as tools disponíveis | Alta |
| US08 | Inspecionar JSON-RPC do tools/list | Alta |
| US09 | Inspecionar inputSchema de uma tool | Média |
| US10 | Executar uma tool diretamente | Alta |
| US11 | Roteamento automático para o server correto | Alta |
| US12 | Inspecionar JSON-RPC do tools/call | Alta |
| US13 | Modo dry-run | Média |
| US14 | Chat com uma pergunta única | Alta |
| US15 | Exibir cada etapa do loop LLM com --verbose | Alta |
| US16 | Configuração do provider LLM | Alta |
| US17 | Chat interativo (REPL) | Média |
| US18 | Flag --verbose global | Alta |
| US19 | Sumário de sessão ao encerrar | Baixa |

---

## Critérios de Aceite do MVP

O MVP está completo quando todos os cenários abaixo funcionarem:

### Cenário 1 — Descoberta de ferramentas

```bash
orcha list-tools --verbose
```

**Esperado:**
- O terminal exibe o JSON-RPC `initialize` (request + response) para cada server
- O terminal exibe o JSON-RPC `tools/list` (request + response) para cada server
- Uma lista formatada de todas as tools, agrupadas por server, é exibida ao final

---

### Cenário 2 — Execução direta de tool

```bash
orcha call filesystem_read_file --args '{"path": "./README.md"}' --verbose
```

**Esperado:**
- O JSON-RPC `tools/call` enviado ao server é exibido
- O JSON-RPC de resposta do server é exibido
- O conteúdo do arquivo é exibido como resultado

---

### Cenário 3 — Chat com orquestração LLM

```bash
orcha chat "Quais arquivos existem neste diretório?" --verbose
```

**Esperado:**
- O terminal exibe a mensagem enviada ao LLM (com lista de tools)
- O terminal exibe a resposta do LLM com `tool_use` (nome da tool + argumentos)
- O terminal exibe o JSON-RPC `tools/call` enviado ao MCP server
- O terminal exibe a resposta do MCP server
- O terminal exibe a resposta final do LLM com base no resultado

---

### Cenário 4 — Configuração mínima

Com o seguinte `orcha.json`:

```json
{
  "llm": {
    "provider": "anthropic",
    "model": "claude-3-5-sonnet-20241022"
  },
  "mcp_servers": {
    "filesystem": {
      "type": "local",
      "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "."],
      "enabled": true
    }
  }
}
```

Todos os comandos acima funcionam sem mais configuração além de `ANTHROPIC_API_KEY`.

---

### Cenário 5 — Server desabilitado não aparece

Com `"enabled": false` em um server:

```bash
orcha list-tools
```

**Esperado:**
- O server desabilitado não aparece na listagem
- Nenhuma conexão é feita com aquele server

---

## Stack Técnica

| Componente | Tecnologia |
|-----------|-----------|
| Runtime | Python 3.11+ |
| CLI | [Typer](https://typer.tiangolo.com/) |
| MCP SDK | [mcp](https://github.com/modelcontextprotocol/python-sdk) (oficial Anthropic) |
| HTTP client | [httpx](https://www.python-httpx.org/) (async) |
| LLM | [anthropic](https://github.com/anthropic/anthropic-sdk-python) Python SDK |
| Formatação terminal | [rich](https://github.com/Textualize/rich) |
| Validação de config | [pydantic](https://docs.pydantic.dev/) v2 |
| Gerenciador de pacotes | [uv](https://docs.astral.sh/uv/) (recomendado) |

---

## Dependências de Desenvolvimento

```toml
# pyproject.toml (dependências principais)
[project]
requires-python = ">=3.11"
dependencies = [
    "typer>=0.12",
    "mcp>=1.0",
    "httpx>=0.27",
    "anthropic>=0.34",
    "rich>=13.0",
    "pydantic>=2.0",
]

[project.scripts]
orcha = "orcha.cli:app"
```

---

## MCP Servers recomendados para desenvolvimento

Para desenvolver e testar o MVP localmente, os seguintes servers são suficientes e não requerem autenticação externa:

| Server | Instalação | O que faz |
|--------|-----------|-----------|
| `@modelcontextprotocol/server-filesystem` | `npx -y @modelcontextprotocol/server-filesystem <path>` | Lê, escreve e lista arquivos |
| `mcp-server-fetch` | `uvx mcp-server-fetch` | Faz fetch de URLs da internet |
| `@modelcontextprotocol/server-everything` | `npx -y @modelcontextprotocol/server-everything` | Server de teste com múltiplos tipos de tools |

---

## Sequência de Desenvolvimento Sugerida

Para implementar o MVP de forma incremental, seguindo o backlog:

```
Sprint 1 — Fundação
  E2: Config (US04, US05, US06)
  E1: MCP Client STDIO (US01, US03)

Sprint 2 — Discovery
  E3: Tool Discovery (US07, US08, US09)
  E6: --verbose (US18)

Sprint 3 — Execution
  E4: Tool Execution (US10, US11, US12, US13)

Sprint 4 — LLM Loop
  E5: Loop LLM (US14, US15, US16)
  E1: HTTP Transport (US02)

Sprint 5 — Polimento
  E5: Chat interativo (US17)
  E6: Sumário de sessão (US19)
```

---

## Definição de Pronto (DoD)

Uma história de usuário está **pronta** quando:

- [ ] O comportamento descrito nos critérios de aceite funciona
- [ ] A flag `--verbose` exibe as mensagens JSON-RPC relevantes para aquela operação
- [ ] Erros são tratados com mensagens claras no terminal (sem stack trace exposto ao usuário)
- [ ] O código tem tipagem estática (type hints Python)
- [ ] Existe ao menos um teste para o caminho feliz
