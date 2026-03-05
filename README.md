# orcha-mcp

Um orquestrador de agentes MCP construído para aprendizado — mostra em detalhes como ferramentas como OpenCode, Claude Code e Gemini CLI se comunicam com MCP servers por debaixo dos panos.

## O que é isso?

`orcha-mcp` é uma CLI Python que atua como **MCP Host**: conecta-se a múltiplos MCP servers (locais via STDIO ou remotos via HTTP), descobre suas ferramentas, e orquestra um LLM real (Anthropic Claude) para decidir quais ferramentas chamar em resposta a uma pergunta.

O diferencial é **transparência total**: cada mensagem JSON-RPC trocada entre o host, os clients e os servers é exposta no terminal — exatamente o que OpenCode e Claude Code fazem em background, mas que normalmente fica invisível ao usuário.

```
Você pergunta algo
       ↓
  orcha-mcp (MCP Host)
       ↓ envia histórico + lista de tools
  LLM (Claude/OpenAI)
       ↓ responde com tool_use
  orcha-mcp roteia para o MCP Client correto
       ↓ JSON-RPC tools/call
  MCP Server (filesystem, fetch, etc.)
       ↓ retorna resultado
  orcha-mcp injeta resultado no histórico
       ↓
  LLM responde ao usuário
```

## Por que isso importa para aprendizado?

O MCP é o "cabo USB-C" do mundo de IA: um protocolo aberto que permite qualquer LLM usar qualquer ferramenta de forma padronizada. Entender como ele funciona dá base para:

- Construir seus próprios MCP servers
- Entender como agentes de IA tomam decisões sobre ferramentas
- Depurar problemas em pipelines de agentes
- Comparar abordagens entre diferentes ferramentas (OpenCode, Claude Code, Gemini CLI)

## Instalação

```bash
# Requires Python 3.11+
git clone https://github.com/seu-usuario/orcha-mcp
cd orcha-mcp

# Install dependencies (production + dev)
uv sync

# Set up your API key
cp .env.example .env
# Edit .env and fill in ANTHROPIC_API_KEY

# Install pre-commit hooks (once per clone)
uv run pre-commit install
```

Verify everything is working:

```bash
uv run orcha --help
uv run ruff check .
uv run mypy orcha/
uv run pytest
```

## Configuração rápida

Crie um arquivo `orcha.json` na raiz do projeto:

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
    },
    "fetch": {
      "type": "local",
      "command": ["uvx", "mcp-server-fetch"],
      "enabled": true
    }
  }
}
```

Adicione sua chave de API:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Comandos

### Listar ferramentas disponíveis

```bash
orcha list-tools
```

Descobre e exibe todas as tools de todos os servers configurados.

```bash
orcha list-tools --verbose
```

Exibe também o JSON-RPC bruto trocado durante o `initialize` e o `tools/list`.

### Executar uma ferramenta diretamente

```bash
orcha call filesystem_read_file --args '{"path": "./README.md"}'
```

Executa uma tool diretamente, sem passar pelo LLM.

```bash
orcha call filesystem_read_file --args '{"path": "./README.md"}' --verbose
```

Exibe o JSON-RPC do `tools/call` e da resposta.

### Chat com orquestração

```bash
orcha chat "Quais arquivos existem neste diretório?"
```

Inicia um ciclo completo: envia a pergunta ao LLM, que decide quais tools usar, o orquestrador as executa via MCP, e o LLM responde com base nos resultados.

```bash
orcha chat "Quais arquivos existem neste diretório?" --verbose
```

Exibe cada etapa do protocolo: mensagem ao LLM, tool_use escolhida, JSON-RPC enviado ao server, resultado, e resposta final.

### Chat interativo (modo REPL)

```bash
orcha chat --interactive
```

Abre um loop de conversa contínuo no terminal.

## Flags globais

| Flag | Descrição |
|------|-----------|
| `--verbose` / `-v` | Exibe o JSON-RPC bruto em cada passo |
| `--dry-run` | Mostra o que seria feito sem executar |
| `--config <path>` | Usa um arquivo de config alternativo (padrão: `./orcha.json`) |
| `--server <nome>` | Restringe a operação a um server específico |

## Estrutura do projeto

```
orcha-mcp/
├── orcha/
│   ├── __init__.py
│   ├── cli.py              # Entry point da CLI (Click/Typer)
│   ├── config.py           # Leitura e validação do orcha.json
│   ├── host.py             # MCP Host — gerencia múltiplos clients
│   ├── client.py           # MCP Client — conexão com um server
│   ├── transport/
│   │   ├── stdio.py        # Transport STDIO (processos locais)
│   │   └── http.py         # Transport HTTP (servers remotos)
│   ├── llm/
│   │   ├── base.py         # Interface comum para providers LLM
│   │   └── anthropic.py    # Integração com Anthropic Claude
│   └── inspector.py        # Formatação e exibição do JSON-RPC no terminal
├── docs/
│   ├── architecture.md     # Arquitetura técnica detalhada
│   ├── backlog.md          # Backlog do projeto
│   └── mvp.md              # Escopo do MVP
├── examples/
│   └── orcha.json          # Configuração de exemplo
├── tests/
├── orcha.json              # Config do projeto (gitignore a sua se tiver secrets)
├── .env.example
├── .pre-commit-config.yaml
├── pyproject.toml
└── README.md
```

## Documentação

- [Arquitetura técnica](docs/architecture.md) — como o protocolo MCP funciona e como o orcha-mcp se posiciona
- [Backlog](docs/backlog.md) — épicos e histórias de usuário priorizadas
- [Escopo do MVP](docs/mvp.md) — o que está incluído na primeira versão e critérios de aceite

## Referências

- [Model Context Protocol — Spec oficial](https://modelcontextprotocol.io)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Reference Servers](https://github.com/modelcontextprotocol/servers)
- [OpenCode — como usa MCP](https://opencode.ai/docs/mcp-servers/)
- [Claude Code](https://www.anthropic.com/claude-code)
