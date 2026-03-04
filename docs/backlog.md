# Backlog — orcha-mcp

> Backlog priorizado por épicos. Histórias do MVP estão marcadas com `[MVP]`.
> Leia o [escopo do MVP](./mvp.md) para entender o que entra na primeira entrega.

---

## Épicos

| ID | Nome | Descrição | MVP? |
|----|------|-----------|------|
| E1 | Core MCP Client | Conexão com servers, lifecycle, capability negotiation | Sim |
| E2 | Configuração | Leitura e validação do `orcha.json` | Sim |
| E3 | Tool Discovery | `tools/list`, exibição formatada, logs JSON-RPC | Sim |
| E4 | Tool Execution | `tools/call`, roteamento multi-server, resultado | Sim |
| E5 | Loop LLM | LLM real decide tools, loop até resposta final | Sim |
| E6 | Debug / Inspeção | `--verbose`, `--dry-run`, inspeção do protocolo raw | Sim |
| E7 | Multi-agente | Um agente delega tarefas a sub-agentes via MCP | Não |
| E8 | Resources e Prompts | Primitivos `resources/*` e `prompts/*` do MCP | Não |
| E9 | Comparativo de ferramentas | Side-by-side com OpenCode / Claude Code | Não |

---

## E1 — Core MCP Client

Implementação do MCP Client com lifecycle completo: inicialização, capability negotiation e encerramento de conexão.

---

### US01 — Conexão STDIO com server local

**Como** desenvolvedor,
**quero** conectar o orcha-mcp a um MCP server local via STDIO,
**para** ver o ciclo de inicialização JSON-RPC acontecendo entre o host e o server.

**Critérios de aceite:**
- [ ] O orcha-mcp inicia o processo do server como subprocesso
- [ ] Envia a mensagem `initialize` com `protocolVersion` e `clientInfo`
- [ ] Recebe a resposta com as capabilities do server
- [ ] Envia `notifications/initialized`
- [ ] A conexão é encerrada graciosamente com `notifications/cancelled` ao finalizar

**Notas técnicas:**
- Usar `asyncio.create_subprocess_exec` com pipes em `stdin`/`stdout`
- O server é iniciado com o `command` definido em `orcha.json`
- Leitura de mensagens via newline-delimited JSON

---

### US02 — Conexão HTTP com server remoto

**Como** desenvolvedor,
**quero** conectar o orcha-mcp a um MCP server remoto via HTTP,
**para** comparar o comportamento entre transport STDIO e HTTP.

**Critérios de aceite:**
- [ ] O orcha-mcp faz POST para a URL do server com a mensagem `initialize`
- [ ] Suporta headers customizados (para autenticação via Bearer token)
- [ ] Lida com respostas síncronas (200 JSON) e assíncronas (SSE)
- [ ] Timeout configurável (padrão: 10s)

**Notas técnicas:**
- Usar `httpx` com suporte a async
- Server remoto configurado com `type: "remote"` e `url` no `orcha.json`

---

### US03 — Exibição da capability negotiation

**Como** desenvolvedor,
**quero** ver no terminal as capabilities negociadas durante o handshake,
**para** entender o que cada server suporta antes de usar suas tools.

**Critérios de aceite:**
- [ ] Ao conectar, exibe um resumo formatado: nome do server, versão, capabilities
- [ ] Com `--verbose`, exibe o JSON-RPC raw completo do initialize/response

**Exemplo de output (`orcha list-tools`):**
```
✓ filesystem  v0.6.2  tools(listChanged=true)
✓ fetch       v0.1.0  tools
```

---

## E2 — Configuração

Leitura, validação e gerenciamento do arquivo `orcha.json`.

---

### US04 — Configuração de múltiplos servers via JSON

**Como** desenvolvedor,
**quero** definir múltiplos MCP servers em um arquivo `orcha.json`,
**para** gerenciar quais servers usar sem alterar o código.

**Critérios de aceite:**
- [ ] O arquivo `orcha.json` é lido da raiz do diretório atual por padrão
- [ ] Suporta múltiplos servers com `type: "local"` e `type: "remote"`
- [ ] Cada server tem: `command` (local) ou `url` (remoto), `enabled`, `environment`
- [ ] Erros de schema exibem mensagem clara indicando o campo inválido

**Exemplo de `orcha.json`:**
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

---

### US05 — Ativar e desativar servers individualmente

**Como** desenvolvedor,
**quero** desabilitar um server no `orcha.json` sem removê-lo,
**para** testar outros servers de forma isolada.

**Critérios de aceite:**
- [ ] Server com `"enabled": false` não é inicializado
- [ ] O comando `orcha list-tools` não exibe tools de servers desabilitados
- [ ] Flag `--server <nome>` restringe a operação ao server especificado

---

### US06 — Path alternativo de config

**Como** desenvolvedor,
**quero** passar um caminho alternativo para o arquivo de config,
**para** usar diferentes configurações por projeto ou contexto.

**Critérios de aceite:**
- [ ] Flag `--config <path>` aceita caminho absoluto ou relativo
- [ ] Erro claro se o arquivo não existir no path especificado

---

## E3 — Tool Discovery

Descoberta e exibição das ferramentas disponíveis em todos os servers conectados.

---

### US07 — Listar todas as tools disponíveis

**Como** desenvolvedor,
**quero** executar `orcha list-tools` e ver todas as ferramentas disponíveis,
**para** saber o que posso pedir ao LLM que ele use.

**Critérios de aceite:**
- [ ] Conecta em todos os servers habilitados
- [ ] Exibe as tools agrupadas por server
- [ ] Para cada tool: nome com namespace (`server_toolname`), descrição curta
- [ ] Exibe contagem total de tools ao final

**Exemplo de output:**
```
Server: filesystem (5 tools)
  filesystem_read_file      Read the complete contents of a file
  filesystem_write_file     Create a new file or overwrite an existing file
  filesystem_list_directory List the contents of a directory
  filesystem_create_directory  Create a new directory
  filesystem_delete_file    Delete a file

Server: fetch (2 tools)
  fetch_fetch               Fetches a URL from the internet
  fetch_get_robots_txt      Gets the robots.txt file for a domain

Total: 7 tools disponíveis
```

---

### US08 — Inspecionar o JSON-RPC do tools/list

**Como** desenvolvedor,
**quero** ver o JSON-RPC bruto trocado durante o `tools/list`,
**para** entender exatamente o que o protocolo transfere nessa etapa.

**Critérios de aceite:**
- [ ] Com `--verbose`, imprime a mensagem `tools/list` enviada e a resposta completa
- [ ] O JSON é formatado (pretty-print) e com destaque sintático (cores) no terminal
- [ ] Cada mensagem é prefixada com direção: `→ HOST→SERVER` ou `← SERVER→HOST`

---

### US09 — Inspecionar o inputSchema de uma tool

**Como** desenvolvedor,
**quero** ver o `inputSchema` completo de uma tool específica,
**para** entender quais parâmetros ela aceita antes de chamá-la.

**Critérios de aceite:**
- [ ] Comando `orcha describe <tool_name>` exibe o inputSchema completo em JSON
- [ ] Indica quais campos são `required` e quais são opcionais

---

## E4 — Tool Execution

Execução direta de tools via CLI, sem passar pelo LLM.

---

### US10 — Executar uma tool diretamente

**Como** desenvolvedor,
**quero** executar `orcha call <tool_name> --args '<json>'`,
**para** testar uma tool individualmente sem precisar de um LLM decidindo.

**Critérios de aceite:**
- [ ] Aceita o nome da tool com namespace (`filesystem_read_file`)
- [ ] Aceita os argumentos como JSON string via `--args`
- [ ] Exibe o resultado formatado no terminal
- [ ] Retorna código de saída 1 se a tool retornar erro

---

### US11 — Roteamento automático para o server correto

**Como** desenvolvedor,
**quero** que o orcha-mcp identifique automaticamente qual server possui a tool chamada,
**para** não precisar especificar o server manualmente a cada chamada.

**Critérios de aceite:**
- [ ] O roteamento é feito pelo prefixo do namespace (`filesystem_*` → client `filesystem`)
- [ ] Erro claro se a tool não for encontrada em nenhum server
- [ ] Erro claro se houver ambiguidade (tool com mesmo nome em dois servers — apenas sem namespace)

---

### US12 — Inspecionar o JSON-RPC do tools/call

**Como** desenvolvedor,
**quero** ver o JSON-RPC bruto do `tools/call` e da resposta,
**para** entender exatamente o que é enviado ao server e o que ele retorna.

**Critérios de aceite:**
- [ ] Com `--verbose`, imprime a request `tools/call` e a response completa
- [ ] Formata o conteúdo da resposta (especialmente se for texto longo)

---

### US13 — Modo dry-run

**Como** desenvolvedor,
**quero** usar `--dry-run` para ver o que seria executado sem executar de fato,
**para** validar meu entendimento antes de disparar operações reais.

**Critérios de aceite:**
- [ ] Com `--dry-run`, exibe a mensagem JSON-RPC que seria enviada
- [ ] Não faz nenhuma conexão real com servers
- [ ] Exibe aviso claro de que está em modo dry-run

---

## E5 — Loop LLM

Integração com LLM real para orquestração completa: o LLM decide as tools, o orquestrador as executa, e o LLM responde com base nos resultados.

---

### US14 — Chat com uma pergunta única

**Como** desenvolvedor,
**quero** executar `orcha chat "<pergunta>"`,
**para** ver o ciclo completo: LLM → tool_use → MCP → resultado → resposta.

**Critérios de aceite:**
- [ ] Conecta aos servers habilitados e descobre as tools
- [ ] Envia a pergunta ao LLM com a lista de tools disponíveis
- [ ] Detecta `tool_use` na resposta do LLM
- [ ] Executa a tool via MCP e insere o resultado no histórico
- [ ] Repete até o LLM dar uma resposta final (sem mais `tool_use`)
- [ ] Exibe a resposta final formatada no terminal

---

### US15 — Exibir cada etapa do loop LLM com --verbose

**Como** desenvolvedor,
**quero** ver cada etapa do loop de orquestração ao usar `--verbose`,
**para** entender exatamente como o LLM e o protocolo MCP interagem.

**Critérios de aceite:**
- [ ] Exibe a mensagem enviada ao LLM (com lista de tools)
- [ ] Exibe a resposta do LLM (incluindo o `tool_use` com os argumentos escolhidos)
- [ ] Exibe o JSON-RPC `tools/call` enviado ao server
- [ ] Exibe o JSON-RPC de resposta do server
- [ ] Exibe a mensagem final enviada ao LLM com o resultado da tool
- [ ] Exibe a resposta final do LLM

**Exemplo de output (`--verbose`):**

```
[STEP 1] Enviando ao LLM (claude-3-5-sonnet-20241022)
  → 1 mensagem(s) no histórico | 7 tools disponíveis

[STEP 2] LLM respondeu com tool_use
  → Tool: filesystem_read_file
  → Args: {"path": "./README.md"}

[STEP 3] Executando via MCP
  → HOST→SERVER: {"jsonrpc":"2.0","id":3,"method":"tools/call",...}
  ← SERVER→HOST: {"jsonrpc":"2.0","id":3,"result":{"content":[...]}}

[STEP 4] Enviando resultado ao LLM
  → 3 mensagem(s) no histórico

[STEP 5] Resposta final
O README.md contém informações sobre o projeto orcha-mcp...
```

---

### US16 — Configuração do provider LLM

**Como** desenvolvedor,
**quero** configurar qual LLM usar no `orcha.json`,
**para** testar com diferentes modelos sem alterar o código.

**Critérios de aceite:**
- [ ] Suporta `provider: "anthropic"` com autenticação via `ANTHROPIC_API_KEY`
- [ ] `model` é configurável (ex: `claude-3-5-sonnet-20241022`, `claude-3-haiku-20240307`)
- [ ] Erro claro se a variável de ambiente da API key não estiver definida

---

### US17 — Chat interativo (REPL)

**Como** desenvolvedor,
**quero** executar `orcha chat --interactive` e ter uma sessão de chat contínua,
**para** explorar o comportamento do loop MCP em múltiplos turnos de conversa.

**Critérios de aceite:**
- [ ] Abre um loop no terminal com prompt `>`
- [ ] Mantém o histórico de mensagens entre turnos
- [ ] `Ctrl+C` encerra a sessão graciosamente
- [ ] Exibe quantas tools e servers estão ativos no início da sessão

---

## E6 — Debug / Inspeção

Ferramentas transversais para inspeção do protocolo, ativas em todos os comandos via flags.

---

### US18 — Flag --verbose global

**Como** desenvolvedor,
**quero** que qualquer comando aceite `--verbose` / `-v`,
**para** ver o JSON-RPC bruto em qualquer operação sem precisar de um comando especial.

**Critérios de aceite:**
- [ ] `--verbose` funciona em `list-tools`, `call`, `chat` e `describe`
- [ ] Mensagens são coloridas: azul para requests, verde para responses, amarelo para notifications
- [ ] O JSON é pretty-printed com indentação de 2 espaços

---

### US19 — Sumário de sessão ao encerrar

**Como** desenvolvedor,
**quero** ver um sumário ao fim de qualquer operação,
**para** ter uma visão geral do que foi feito naquela sessão.

**Critérios de aceite:**
- [ ] Exibe: servers conectados, total de tools descobertas, tools chamadas, tempo total
- [ ] Com `--verbose`, exibe contagem de mensagens JSON-RPC trocadas por server

---

## E7 — Orquestração Multi-Agente *(pós-MVP)*

Um agente orquestrador que delega sub-tarefas a agentes especializados.

---

### US20 — Agente delegando para sub-agente via MCP

**Como** desenvolvedor,
**quero** que um agente orquestrador possa criar e chamar sub-agentes como tools MCP,
**para** entender como a orquestração hierárquica de agentes funciona.

**Critérios de aceite:**
- [ ] O orquestrador pode iniciar um sub-processo `orcha chat` como se fosse um MCP server
- [ ] O sub-agente expõe uma tool `run_task(instruction: string)` via MCP
- [ ] O agente principal pode delegar para o sub-agente e aguardar a resposta

---

## E8 — Resources e Prompts *(pós-MVP)*

Suporte aos outros primitivos MCP além de Tools.

---

### US21 — Listar e ler Resources

**Como** desenvolvedor,
**quero** executar `orcha list-resources` e `orcha read-resource <uri>`,
**para** explorar o primitivo Resources do MCP.

---

### US22 — Listar e usar Prompts

**Como** desenvolvedor,
**quero** executar `orcha list-prompts` e `orcha get-prompt <nome>`,
**para** explorar o primitivo Prompts do MCP e ver como templates são usados.

---

## E9 — Comparativo entre Ferramentas *(pós-MVP)*

Análise comparativa de como OpenCode, Claude Code e Gemini CLI usam o MCP.

---

### US23 — Modo "side-by-side"

**Como** desenvolvedor,
**quero** executar a mesma pergunta no `orcha-mcp` e ver o log de outra ferramenta lado a lado,
**para** comparar as diferenças de implementação entre elas.

---

## Resumo de Priorização

| História | Épico | MVP? | Prioridade |
|----------|-------|------|------------|
| US01 | E1 | Sim | Alta |
| US02 | E1 | Sim | Alta |
| US03 | E1 | Sim | Alta |
| US04 | E2 | Sim | Alta |
| US05 | E2 | Sim | Alta |
| US06 | E2 | Sim | Média |
| US07 | E3 | Sim | Alta |
| US08 | E3 | Sim | Alta |
| US09 | E3 | Sim | Média |
| US10 | E4 | Sim | Alta |
| US11 | E4 | Sim | Alta |
| US12 | E4 | Sim | Alta |
| US13 | E4 | Sim | Média |
| US14 | E5 | Sim | Alta |
| US15 | E5 | Sim | Alta |
| US16 | E5 | Sim | Alta |
| US17 | E5 | Sim | Média |
| US18 | E6 | Sim | Alta |
| US19 | E6 | Sim | Baixa |
| US20 | E7 | Não | Alta (futuro) |
| US21 | E8 | Não | Média (futuro) |
| US22 | E8 | Não | Média (futuro) |
| US23 | E9 | Não | Baixa (futuro) |
