# Arquitetura Técnica — orcha-mcp

## Visão Geral

O `orcha-mcp` implementa o papel de **MCP Host**: uma aplicação que gerencia múltiplos MCP Clients, cada um mantendo uma conexão dedicada com um MCP Server, e coordena um LLM para usar as ferramentas expostas por esses servers.

```
┌─────────────────────────────────────────────────────────────┐
│                        orcha-mcp                            │
│                    (MCP Host / Orchestrator)                │
│                                                             │
│  ┌─────────────┐    ┌──────────────────────────────────┐   │
│  │  CLI Layer  │    │           MCP Host               │   │
│  │  (Typer)    │───▶│  ┌──────────┐  ┌──────────────┐  │   │
│  └─────────────┘    │  │ Client 1 │  │   Client 2   │  │   │
│                     │  └────┬─────┘  └──────┬───────┘  │   │
│  ┌─────────────┐    └───────┼───────────────┼──────────┘   │
│  │  LLM Layer  │            │               │              │
│  │ (Anthropic) │            │               │              │
│  └─────────────┘            │               │              │
└─────────────────────────────┼───────────────┼──────────────┘
                              │               │
                   STDIO      │               │  HTTP
                   (subproc.) │               │  (requests)
                              ▼               ▼
                    ┌──────────────┐  ┌──────────────────┐
                    │  MCP Server  │  │   MCP Server     │
                    │  (local)     │  │   (remoto)       │
                    │  filesystem  │  │   fetch / sentry │
                    └──────────────┘  └──────────────────┘
```

---

## Participantes do Protocolo MCP

O protocolo define três participantes centrais. O `orcha-mcp` implementa os dois primeiros:

| Participante | Papel | Quem implementa no orcha-mcp |
|---|---|---|
| **MCP Host** | Coordena clients e fornece contexto ao LLM | `host.py` — o orquestrador principal |
| **MCP Client** | Mantém uma conexão dedicada com um server | `client.py` — uma instância por server |
| **MCP Server** | Expõe ferramentas, recursos e prompts | Processos externos (filesystem, fetch, etc.) |

---

## Camadas do Protocolo

### Data Layer (JSON-RPC 2.0)

Toda comunicação usa mensagens JSON-RPC 2.0. Existem três tipos:

```json
// Request (espera resposta)
{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}

// Response
{"jsonrpc": "2.0", "id": 1, "result": {"tools": [...]}}

// Notification (sem resposta esperada)
{"jsonrpc": "2.0", "method": "notifications/initialized"}
```

### Transport Layer

Dois mecanismos de transporte suportados:

| Transport | Uso | Como funciona |
|---|---|---|
| **STDIO** | Servers locais (subprocessos) | `stdin`/`stdout` do processo filho |
| **HTTP (Streamable)** | Servers remotos | POST para o endpoint + SSE opcional |

---

## Fluxo de uma Sessão Completa

### 1. Inicialização (Lifecycle)

Quando o `orcha-mcp` inicia, para cada server configurado:

```
Host                          Server
 │                              │
 │── initialize ───────────────▶│  protocolVersion, capabilities do client
 │◀── initialize response ──────│  capabilities do server (tools, resources...)
 │── notifications/initialized ▶│  sinaliza que está pronto
 │                              │
```

**Mensagem real trocada (`--verbose` exibirá isso):**

```json
// → Host envia
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "capabilities": {},
    "clientInfo": {"name": "orcha-mcp", "version": "0.1.0"}
  }
}

// ← Server responde
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2025-06-18",
    "capabilities": {"tools": {"listChanged": true}},
    "serverInfo": {"name": "filesystem", "version": "0.6.2"}
  }
}
```

### 2. Tool Discovery

```
Host                          Server
 │── tools/list ──────────────▶│
 │◀── tools/list response ─────│  array de tools com inputSchema
```

**Mensagem real:**

```json
// → Request
{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}

// ← Response
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "read_file",
        "description": "Read the complete contents of a file",
        "inputSchema": {
          "type": "object",
          "properties": {
            "path": {"type": "string", "description": "File path"}
          },
          "required": ["path"]
        }
      }
    ]
  }
}
```

### 3. Decisão do LLM

O Host monta uma lista unificada de todas as tools de todos os servers e envia ao LLM como parte do contexto:

```python
# Pseudocódigo do que o orcha-mcp faz internamente
tools_for_llm = []
for client in host.clients:
    tools = await client.list_tools()
    for tool in tools:
        tools_for_llm.append({
            "name": f"{client.name}_{tool.name}",  # namespace por server
            "description": tool.description,
            "input_schema": tool.inputSchema
        })

response = await llm.complete(
    messages=[{"role": "user", "content": pergunta}],
    tools=tools_for_llm
)
```

O LLM responde com `tool_use` quando decide usar uma ferramenta:

```json
{
  "role": "assistant",
  "content": [
    {
      "type": "tool_use",
      "id": "toolu_01",
      "name": "filesystem_read_file",
      "input": {"path": "./README.md"}
    }
  ]
}
```

### 4. Tool Execution (Roteamento)

O Host identifica qual server possui a tool pelo prefixo do namespace, e delega ao Client correto:

```
Host                          Client 1 (filesystem)       Server
 │                                │                          │
 │── roteia "filesystem_*" ──────▶│                          │
 │                                │── tools/call ───────────▶│
 │                                │◀── resultado ────────────│
 │◀── conteúdo ──────────────────│                          │
```

**Mensagem real:**

```json
// → Host → Server
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": {"path": "./README.md"}
  }
}

// ← Server → Host
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [{"type": "text", "text": "# orcha-mcp\n..."}]
  }
}
```

### 5. Resposta Final

O resultado é inserido no histórico de mensagens e enviado novamente ao LLM para que ele formule a resposta final ao usuário.

---

## Primitivos MCP

O protocolo define três tipos de primitivos que servers podem expor:

| Primitivo | O que é | Método de descoberta | Método de uso |
|---|---|---|---|
| **Tools** | Funções executáveis (ações) | `tools/list` | `tools/call` |
| **Resources** | Dados/contexto (leitura) | `resources/list` | `resources/read` |
| **Prompts** | Templates reutilizáveis | `prompts/list` | `prompts/get` |

O MVP foca em **Tools**. Resources e Prompts são épicos futuros.

---

## Como OpenCode, Claude Code e Gemini CLI fazem a mesma coisa

Todas essas ferramentas implementam o papel de MCP Host. O que difere entre elas:

| Ferramenta | Runtime | Transport suportado | Config | Observações |
|---|---|---|---|---|
| **OpenCode** | TypeScript/Bun | STDIO + HTTP | `opencode.json` | Suporta OAuth automático para servers remotos |
| **Claude Code** | TypeScript/Node | STDIO + HTTP | `~/.claude/settings.json` | Integrado diretamente ao Anthropic Claude |
| **Gemini CLI** | TypeScript/Node | STDIO + HTTP | `settings.json` | Usa Google Gemini como LLM |
| **orcha-mcp** | Python | STDIO + HTTP | `orcha.json` | Foco educacional: expõe o protocolo raw |

O loop interno é idêntico em todas:
1. Ler config e conectar aos MCP servers configurados
2. Fazer `tools/list` em cada server
3. Montar lista unificada e enviar ao LLM com a pergunta do usuário
4. Interceptar `tool_use` do LLM
5. Rotear para o server correto via `tools/call`
6. Inserir resultado no histórico e repetir até o LLM dar uma resposta final

A diferença do `orcha-mcp` é que a flag `--verbose` expõe cada uma dessas etapas com as mensagens JSON-RPC reais.

---

## Estrutura de Módulos

```
orcha/
├── cli.py          # Entry point (Typer): define comandos list-tools, call, chat
├── config.py       # Lê orcha.json, valida schema, retorna dataclasses
├── host.py         # Orquestrador: inicializa clients, agrega tools, gerencia loop LLM
├── client.py       # MCP Client: lifecycle, tools/list, tools/call para 1 server
├── transport/
│   ├── stdio.py    # Inicia subprocesso, lê/escreve JSON-RPC via stdin/stdout
│   └── http.py     # Faz POST para server remoto, lida com SSE
├── llm/
│   ├── base.py     # Protocol/ABC: interface agnóstica de provider
│   └── anthropic.py# Implementação Anthropic: messages API com tool_use
└── inspector.py    # Formata e printa JSON-RPC no terminal (modo --verbose)
```

### Fluxo de dependências

```
cli.py
  └── host.py
        ├── config.py
        ├── client.py (N instâncias)
        │     └── transport/stdio.py  ou  transport/http.py
        ├── llm/anthropic.py
        └── inspector.py (opcional, ativado por --verbose)
```

---

## Decisões de Design

### Por que Python?

- SDK oficial MCP (`mcp`) tem suporte Python de primeira classe
- `anthropic` SDK Python é maduro e tem suporte nativo a `tool_use`
- `asyncio` lida bem com múltiplas conexões STDIO simultâneas
- Mais fácil de inspecionar e experimentar para aprendizado

### Por que namespace `server_toolname`?

OpenCode e Claude Code registram tools com o nome do server como prefixo para evitar colisões quando múltiplos servers expõem tools com mesmo nome. O `orcha-mcp` segue a mesma convenção.

### Por que `orcha.json` e não `.env` / args?

Seguindo o padrão estabelecido por OpenCode (`opencode.json`), Claude Code (`settings.json`) e outros. Facilita versionar a configuração dos servers junto ao projeto.
