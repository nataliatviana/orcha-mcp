# Backlog — orcha-mcp

> Backlog priorizado em ordem cronológica de implementação, seguindo as sprints definidas em [mvp.md](./mvp.md).
> Histórias do MVP estão marcadas com `[MVP]`. Histórias pós-MVP estão no final do documento.

---

## Épicos

| ID | Nome | Descrição | MVP? |
|----|------|-----------|------|
| E0 | Setup | Bootstrap do projeto: estrutura, tooling, CI | Sim |
| E1 | Core MCP Client | Conexão com servers, lifecycle, capability negotiation | Sim |
| E2 | Configuração | Leitura e validação do `orcha.json` | Sim |
| E3 | Tool Discovery | `tools/list`, exibição formatada | Sim |
| E4 | Tool Execution | `tools/call`, roteamento multi-server, resultado | Sim |
| E5 | Loop LLM | LLM real decide tools, loop até resposta final | Sim |
| E6 | Debug / Inspeção | `--verbose`, `--dry-run`, inspeção do protocolo raw | Sim |
| E7 | Multi-agente | Um agente delega tarefas a sub-agentes via MCP | Não |
| E8 | Resources e Prompts | Primitivos `resources/*` e `prompts/*` do MCP | Não |
| E9 | Comparativo de ferramentas | Side-by-side com OpenCode / Claude Code | Não |

---

## Sprint 0 — Bootstrap

> Objetivo: projeto executável do zero, com tooling configurado e estrutura de pastas definida.

---

### US00 — Setup do projeto `[MVP]`

**Como** desenvolvedor,
**quero** um repositório Python com estrutura de pastas, dependências e tooling configurados,
**para** começar a implementar funcionalidades sem overhead de setup.

**Critérios de aceite:**
- [ ] `pyproject.toml` configurado com `uv`, Python 3.11+, e dependências do MVP (`typer`, `mcp`, `httpx`, `anthropic`, `rich`, `pydantic`)
- [ ] Estrutura de pastas criada:
  ```
  orcha/
    cli.py          # entrypoint Typer
    config/         # leitura e validação do orcha.json
    client/         # MCP client (STDIO + HTTP)
    llm/            # integração Anthropic
    display/        # formatação rich para terminal
  tests/
  docs/
  ```
- [ ] Script `orcha` disponível via `uv run orcha --help` após `uv sync`
- [ ] `ruff` configurado para lint e format
- [ ] `mypy` configurado com `strict = true`
- [ ] `pytest` configurado com `tests/` como diretório raiz
- [ ] Pre-commit hooks configurados (ruff, mypy)
- [ ] `.env.example` com `ANTHROPIC_API_KEY=` documentado
- [ ] `README.md` com instruções mínimas de instalação e uso

**Notas técnicas:**
- Usar `[project.scripts] orcha = "orcha.cli:app"` no `pyproject.toml`
- O `mcp` SDK oficial já abstrai grande parte do transporte; não reinventar a roda

**Definição de Pronto:**
- [ ] `uv sync && uv run orcha --help` funciona sem erros
- [ ] `uv run ruff check .` passa sem warnings
- [ ] `uv run mypy orcha/` passa sem erros
- [ ] `uv run pytest` passa (mesmo que não haja testes ainda, a configuração executa)

---

## Sprint 1 — Fundação

> Objetivo: ler configuração e conectar ao primeiro MCP server via STDIO, com handshake completo.

---

## E2 — Configuração

---

### US01 — Configuração de múltiplos servers via JSON `[MVP]`

**Como** desenvolvedor,
**quero** definir múltiplos MCP servers em um arquivo `orcha.json`,
**para** gerenciar quais servers usar sem alterar o código.

**Critérios de aceite:**
- [ ] O arquivo `orcha.json` é lido da raiz do diretório atual por padrão
- [ ] Suporta múltiplos servers com `type: "local"` (STDIO) e `type: "remote"` (HTTP)
- [ ] Cada server local tem: `command` (lista de strings), `enabled`, `environment` (opcional)
- [ ] Cada server remoto tem: `url`, `enabled`, `headers` (opcional, para Bearer token)
- [ ] A seção `llm` define `provider` e `model`
- [ ] Erros de schema exibem mensagem clara indicando o campo inválido (sem stack trace)
- [ ] Um `orcha.json` ausente exibe mensagem de erro orientando o usuário a criar o arquivo

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
      "enabled": true,
      "environment": {
        "NODE_ENV": "production"
      }
    },
    "fetch": {
      "type": "local",
      "command": ["uvx", "mcp-server-fetch"],
      "enabled": true
    }
  }
}
```

**Notas técnicas:**
- Usar `pydantic` v2 com `model_validator` para validação cross-field (ex: `command` obrigatório se `type=local`)
- Modelo `OrchaConfig` em `orcha/config/schema.py`

**Definição de Pronto:**
- [ ] Critérios de aceite funcionam
- [ ] Teste unitário cobre: config válida, campo ausente, tipo inválido e arquivo ausente
- [ ] Tipagem estática completa no módulo `orcha/config/`
- [ ] Erros exibem mensagem legível no terminal (sem stack trace)

---

### US02 — Variáveis de ambiente por server `[MVP]`

**Como** desenvolvedor,
**quero** definir variáveis de ambiente específicas por server no `orcha.json`,
**para** passar credenciais e configurações sem expô-las globalmente.

**Critérios de aceite:**
- [ ] O campo `environment` aceita um objeto de strings (`Record<str, str>`)
- [ ] As variáveis são **mescladas** com o ambiente do processo pai ao iniciar o subprocesso (não substituem)
- [ ] Variáveis definidas em `environment` têm precedência sobre as do processo pai
- [ ] Nenhuma variável de ambiente é logada ou exibida no terminal por padrão
- [ ] Com `--verbose`, exibe apenas os **nomes** das variáveis injetadas (não os valores)

**Notas técnicas:**
- Passar `env={**os.environ, **server.environment}` ao criar o subprocesso STDIO
- Para servers HTTP, injetar como headers via `Authorization: Bearer <token>` referenciando a var por nome

**Definição de Pronto:**
- [ ] Critérios de aceite funcionam
- [ ] Teste verifica que a variável está disponível no subprocesso
- [ ] Teste verifica que o valor não aparece em nenhuma saída `--verbose`
- [ ] Tipagem estática completa

---

### US03 — Ativar e desativar servers individualmente `[MVP]`

**Como** desenvolvedor,
**quero** desabilitar um server no `orcha.json` sem removê-lo,
**para** testar outros servers de forma isolada.

**Critérios de aceite:**
- [ ] Server com `"enabled": false` não é inicializado em nenhum comando
- [ ] O comando `orcha list-tools` não exibe tools de servers desabilitados
- [ ] Flag `--server <nome>` restringe a operação ao server especificado (ignorando os demais)
- [ ] Erro claro se o nome passado em `--server` não existir no `orcha.json`

**Definição de Pronto:**
- [ ] Critérios de aceite funcionam
- [ ] Teste cobre: server desabilitado não aparece, `--server` filtra corretamente
- [ ] Tipagem estática completa

---

### US04 — Path alternativo de config `[MVP]`

**Como** desenvolvedor,
**quero** passar um caminho alternativo para o arquivo de config,
**para** usar diferentes configurações por projeto ou contexto.

**Critérios de aceite:**
- [ ] Flag `--config <path>` aceita caminho absoluto ou relativo ao diretório atual
- [ ] Erro claro se o arquivo não existir no path especificado
- [ ] A flag está disponível em todos os subcomandos (`list-tools`, `call`, `chat`, `describe`)

**Definição de Pronto:**
- [ ] Critérios de aceite funcionam
- [ ] Teste cobre: path válido, path inexistente
- [ ] Tipagem estática completa

---

## E1 — Core MCP Client

---

### US05 — Conexão STDIO com server local `[MVP]`

**Como** desenvolvedor,
**quero** conectar o orcha-mcp a um MCP server local via STDIO,
**para** ver o ciclo de inicialização JSON-RPC acontecendo entre o host e o server.

**Critérios de aceite:**
- [ ] O orcha-mcp inicia o processo do server como subprocesso usando o `command` do `orcha.json`
- [ ] Envia a mensagem `initialize` com `protocolVersion` e `clientInfo`
- [ ] Recebe a resposta com as capabilities do server e a armazena
- [ ] Envia `notifications/initialized` após receber a resposta do `initialize`
- [ ] A sequência de handshake completa sem erros para o server `@modelcontextprotocol/server-filesystem`

**Notas técnicas:**
- Usar o MCP Python SDK (`mcp.client.stdio.stdio_client`) em vez de implementar o transporte manualmente
- O SDK gerencia o `asyncio.create_subprocess_exec` e a leitura de JSON newline-delimited
- Instanciar `ClientSession` e chamar `session.initialize()`

**Definição de Pronto:**
- [ ] Critérios de aceite funcionam
- [ ] Teste de integração faz handshake com um server real (ou server de teste `server-everything`)
- [ ] Erro ao iniciar o subprocesso (comando não encontrado) exibe mensagem clara
- [ ] Tipagem estática completa

---

### US06 — Encerramento gracioso de conexões `[MVP]`

**Como** desenvolvedor,
**quero** que todas as conexões com MCP servers sejam encerradas corretamente ao finalizar,
**para** evitar processos órfãos e garantir que o lifecycle MCP seja respeitado.

**Critérios de aceite:**
- [ ] Ao finalizar qualquer comando, todos os subprocessos de servers STDIO são encerrados
- [ ] O encerramento aguarda a finalização dos processos com timeout de 5s antes de forçar (`SIGKILL`)
- [ ] `Ctrl+C` (SIGINT) durante qualquer operação aciona o encerramento gracioso antes de sair
- [ ] No modo `--verbose`, exibe mensagem de encerramento para cada server desconectado

**Notas técnicas:**
- Usar context manager (`async with`) do MCP SDK para garantir cleanup automático
- Registrar handler para `SIGINT` e `SIGTERM` que chama o mesmo fluxo de shutdown
- Evitar `ProcessLookupError` ao tentar encerrar processo já finalizado

**Definição de Pronto:**
- [ ] Critérios de aceite funcionam
- [ ] Nenhum processo zumbi detectado após execução de qualquer comando (verificável com `ps`)
- [ ] Tipagem estática completa

---

### US07 — Exibição da capability negotiation `[MVP]`

**Como** desenvolvedor,
**quero** ver no terminal as capabilities negociadas durante o handshake,
**para** entender o que cada server suporta antes de usar suas tools.

**Critérios de aceite:**
- [ ] Ao conectar, exibe um resumo formatado: nome do server, versão do server, capabilities declaradas
- [ ] Com `--verbose`, exibe o JSON-RPC raw completo do `initialize` (request e response)
- [ ] O sumário é exibido antes de qualquer operação subsequente

**Exemplo de output (`orcha list-tools`):**
```
Connected servers:
  filesystem  v0.6.2  tools(listChanged=true)
  fetch       v0.1.0  tools
```

**Notas técnicas:**
- Capabilities disponíveis em `session.server_capabilities` após `initialize()`
- Usar `rich.table.Table` para formatação

**Definição de Pronto:**
- [ ] Critérios de aceite funcionam
- [ ] Teste verifica que nome, versão e capabilities aparecem no output
- [ ] Tipagem estática completa

---

## Sprint 2 — Discovery

> Objetivo: listar e inspecionar tools de todos os servers, com inspeção do protocolo via `--verbose`.

---

## E3 — Tool Discovery

---

### US08 — Listar todas as tools disponíveis `[MVP]`

**Como** desenvolvedor,
**quero** executar `orcha list-tools` e ver todas as ferramentas disponíveis,
**para** saber o que posso pedir ao LLM que ele use.

**Critérios de aceite:**
- [ ] Conecta em todos os servers habilitados e chama `tools/list` em cada um
- [ ] Exibe as tools agrupadas por server
- [ ] Para cada tool: nome com namespace (`<server>_<toolname>`), descrição curta
- [ ] Exibe contagem total de tools ao final
- [ ] Com `--server <nome>`, lista apenas as tools do server especificado

**Exemplo de output:**
```
Server: filesystem (5 tools)
  filesystem_read_file         Read the complete contents of a file
  filesystem_write_file        Create a new file or overwrite an existing file
  filesystem_list_directory    List the contents of a directory
  filesystem_create_directory  Create a new directory
  filesystem_delete_file       Delete a file

Server: fetch (2 tools)
  fetch_fetch                  Fetches a URL from the internet
  fetch_get_robots_txt         Gets the robots.txt file for a domain

Total: 7 tools disponíveis
```

**Notas técnicas:**
- Namespace usa `_` como separador: `<server_name>_<tool_name>`
- Se o nome da tool já contém o nome do server como prefixo, não duplicar
- Usar `session.list_tools()` do MCP SDK

**Definição de Pronto:**
- [ ] Critérios de aceite funcionam
- [ ] Teste de integração com `server-filesystem` valida output esperado
- [ ] Tipagem estática completa
- [ ] `--verbose` exibe JSON-RPC do `tools/list` (coberto por US10)

---

### US09 — Inspecionar o inputSchema de uma tool `[MVP]`

**Como** desenvolvedor,
**quero** ver o `inputSchema` completo de uma tool específica,
**para** entender quais parâmetros ela aceita antes de chamá-la.

**Critérios de aceite:**
- [ ] Comando `orcha describe <tool_name>` exibe o `inputSchema` completo em JSON formatado
- [ ] Indica quais campos são `required` e quais são opcionais (com destaque visual)
- [ ] Aceita nome com namespace (`filesystem_read_file`) ou sem (`read_file` com `--server filesystem`)
- [ ] Erro claro se a tool não for encontrada

**Exemplo de output:**
```
Tool: filesystem_read_file
Description: Read the complete contents of a file from the filesystem.

Input Schema:
  path  (string, required)  Path of the file to read
```

**Definição de Pronto:**
- [ ] Critérios de aceite funcionam
- [ ] Teste verifica output para uma tool conhecida
- [ ] Tipagem estática completa

---

## E6 — Debug / Inspeção

---

### US10 — Flag --verbose global `[MVP]`

**Como** desenvolvedor,
**quero** que qualquer comando aceite `--verbose` / `-v`,
**para** ver o JSON-RPC bruto em qualquer operação sem precisar de um comando especial.

**Critérios de aceite:**
- [ ] `--verbose` funciona em `list-tools`, `call`, `chat` e `describe`
- [ ] Mensagens JSON-RPC são coloridas: azul para requests (→), verde para responses (←), amarelo para notifications
- [ ] O JSON é pretty-printed com indentação de 2 espaços
- [ ] Cada mensagem é prefixada com direção e server: `→ HOST→filesystem` / `← filesystem→HOST`
- [ ] Saída verbose vai para `stderr`, não `stdout`, para não interferir em pipes

**Notas técnicas:**
- Implementar um `VerboseLogger` singleton em `orcha/display/verbose.py` ativado pela flag
- Interceptar mensagens no nível do transport do MCP SDK

**Definição de Pronto:**
- [ ] Critérios de aceite funcionam
- [ ] Teste verifica que `stdout` não contém JSON-RPC (apenas `stderr`)
- [ ] Tipagem estática completa

---

### US11 — Inspecionar o JSON-RPC do tools/list e tools/call `[MVP]`

**Como** desenvolvedor,
**quero** ver o JSON-RPC bruto trocado durante `tools/list` e `tools/call`,
**para** entender exatamente o que o protocolo transfere em cada operação.

**Critérios de aceite:**
- [ ] Com `--verbose` em `list-tools`: imprime a request `tools/list` e a response completa para cada server
- [ ] Com `--verbose` em `call`: imprime a request `tools/call` com os argumentos e a response completa
- [ ] Formata o conteúdo da resposta quando for texto longo (trunca em 500 chars com indicação de truncamento)
- [ ] O JSON é idêntico ao que foi transmitido (sem modificações)

**Definição de Pronto:**
- [ ] Critérios de aceite funcionam
- [ ] Teste verifica que o JSON exibido é válido e contém os campos esperados do protocolo MCP
- [ ] Tipagem estática completa

---

## Sprint 3 — Execution

> Objetivo: executar tools diretamente via CLI, com roteamento automático entre servers.

---

## E4 — Tool Execution

---

### US12 — Executar uma tool diretamente `[MVP]`

**Como** desenvolvedor,
**quero** executar `orcha call <tool_name> --args '<json>'`,
**para** testar uma tool individualmente sem precisar de um LLM decidindo.

**Critérios de aceite:**
- [ ] Aceita o nome da tool com namespace (`filesystem_read_file`)
- [ ] Aceita os argumentos como JSON string via `--args '{...}'`
- [ ] Exibe o resultado formatado no terminal (texto, JSON ou conteúdo binário identificado)
- [ ] Retorna exit code `1` se a tool retornar `isError: true` na resposta MCP
- [ ] Exibe mensagem de erro legível se o JSON passado em `--args` for inválido

**Notas técnicas:**
- Usar `session.call_tool(name, arguments)` do MCP SDK
- Resultado pode ser `TextContent`, `ImageContent` ou `EmbeddedResource`; tratar cada tipo

**Definição de Pronto:**
- [ ] Critérios de aceite funcionam
- [ ] Teste de integração executa `filesystem_read_file` e valida conteúdo retornado
- [ ] `--verbose` exibe JSON-RPC da chamada (coberto por US11)
- [ ] Tipagem estática completa

---

### US13 — Roteamento automático para o server correto `[MVP]`

**Como** desenvolvedor,
**quero** que o orcha-mcp identifique automaticamente qual server possui a tool chamada,
**para** não precisar especificar o server manualmente a cada chamada.

**Critérios de aceite:**
- [ ] O roteamento usa o prefixo do namespace: `filesystem_*` → client `filesystem`
- [ ] Erro claro se a tool não for encontrada em nenhum server conectado
- [ ] Erro claro se houver ambiguidade (mesmo nome de tool em dois servers sem namespace)
- [ ] O mapa de roteamento é construído uma vez na inicialização (não a cada chamada)

**Notas técnicas:**
- Implementar `ToolRouter` em `orcha/client/router.py`
- Índice `Dict[str, ClientSession]` mapeando nome qualificado → session

**Definição de Pronto:**
- [ ] Critérios de aceite funcionam
- [ ] Teste cobre: roteamento correto, tool não encontrada, ambiguidade
- [ ] Tipagem estática completa

---

### US14 — Modo dry-run `[MVP]`

**Como** desenvolvedor,
**quero** usar `--dry-run` para ver o que seria executado sem executar de fato,
**para** validar meu entendimento antes de disparar operações reais.

**Critérios de aceite:**
- [ ] Com `--dry-run`, exibe a mensagem JSON-RPC que seria enviada ao server
- [ ] Não estabelece nenhuma conexão real com servers MCP
- [ ] Não consome créditos de API do LLM
- [ ] Exibe aviso visível de que está em modo dry-run (`[DRY-RUN]` no início do output)
- [ ] Disponível em `call` e `chat`

**Definição de Pronto:**
- [ ] Critérios de aceite funcionam
- [ ] Teste verifica ausência de conexões reais (mock de `stdio_client`)
- [ ] Tipagem estática completa

---

## Sprint 4 — LLM Loop

> Objetivo: integrar o LLM Anthropic com o ciclo MCP completo; adicionar transport HTTP.

---

## E5 — Loop LLM

---

### US15 — Configuração do provider LLM `[MVP]`

**Como** desenvolvedor,
**quero** configurar qual LLM usar no `orcha.json`,
**para** testar com diferentes modelos sem alterar o código.

**Critérios de aceite:**
- [ ] Suporta `provider: "anthropic"` com autenticação via variável de ambiente `ANTHROPIC_API_KEY`
- [ ] `model` é configurável (ex: `claude-3-5-sonnet-20241022`, `claude-3-haiku-20240307`)
- [ ] Erro claro e acionável se `ANTHROPIC_API_KEY` não estiver definida (indicando onde configurar)
- [ ] Erro claro se o modelo especificado não suportar `tool_use`

**Notas técnicas:**
- Instanciar `anthropic.AsyncAnthropic()` em `orcha/llm/anthropic.py`
- Validar presença da API key na inicialização, não na primeira chamada

**Definição de Pronto:**
- [ ] Critérios de aceite funcionam
- [ ] Teste verifica mensagem de erro quando `ANTHROPIC_API_KEY` está ausente
- [ ] Tipagem estática completa

---

### US16 — Chat com uma pergunta única `[MVP]`

**Como** desenvolvedor,
**quero** executar `orcha chat "<pergunta>"`,
**para** ver o ciclo completo: LLM → tool_use → MCP → resultado → resposta final.

**Critérios de aceite:**
- [ ] Conecta aos servers habilitados e descobre as tools antes de chamar o LLM
- [ ] Envia a pergunta ao LLM com a lista completa de tools disponíveis no formato `tool_use`
- [ ] Detecta blocos `tool_use` na resposta do LLM e executa cada tool via MCP
- [ ] Insere o resultado de cada tool como `tool_result` no histórico de mensagens
- [ ] Repete o loop até o LLM retornar uma resposta sem `tool_use` (resposta final)
- [ ] Exibe a resposta final formatada com `rich.markdown`
- [ ] Trata o caso em que o LLM responde diretamente sem acionar nenhuma tool

**Notas técnicas:**
- Loop: `messages` começa com a pergunta do usuário; cada rodada adiciona `assistant` + `user (tool_results)`
- Limit de segurança: máximo de 10 iterações do loop para evitar loops infinitos

**Definição de Pronto:**
- [ ] Critérios de aceite funcionam com `orcha chat "Quais arquivos existem neste diretório?"`
- [ ] Teste de integração valida o ciclo completo (pode usar mock da API Anthropic)
- [ ] Tipagem estática completa
- [ ] Erros da API Anthropic exibem mensagem legível (sem stack trace)

---

### US17 — Exibir cada etapa do loop LLM com --verbose `[MVP]`

**Como** desenvolvedor,
**quero** ver cada etapa do loop de orquestração ao usar `--verbose`,
**para** entender exatamente como o LLM e o protocolo MCP interagem.

**Critérios de aceite:**
- [ ] Exibe a mensagem enviada ao LLM (número de mensagens no histórico, número de tools disponíveis)
- [ ] Exibe a resposta do LLM incluindo o bloco `tool_use` com o nome da tool e os argumentos escolhidos
- [ ] Exibe o JSON-RPC `tools/call` enviado ao MCP server
- [ ] Exibe o JSON-RPC de resposta do server
- [ ] Exibe a mensagem final enviada ao LLM com o resultado da tool
- [ ] Exibe a resposta final do LLM
- [ ] Cada passo é numerado sequencialmente `[STEP N]`

**Exemplo de output (`--verbose`):**
```
[STEP 1] Sending to LLM (claude-3-5-sonnet-20241022)
  → 1 message(s) | 7 tools available

[STEP 2] LLM responded with tool_use
  → Tool: filesystem_read_file
  → Args: {"path": "./README.md"}

[STEP 3] Executing via MCP
  → HOST→filesystem: {"jsonrpc":"2.0","id":3,"method":"tools/call",...}
  ← filesystem→HOST: {"jsonrpc":"2.0","id":3,"result":{"content":[...]}}

[STEP 4] Sending result to LLM
  → 3 message(s) in history

[STEP 5] Final response
O README.md contém informações sobre o projeto orcha-mcp...
```

**Definição de Pronto:**
- [ ] Critérios de aceite funcionam
- [ ] Teste verifica que todos os steps são emitidos para `stderr`
- [ ] Tipagem estática completa

---

## E1 — Core MCP Client (HTTP)

---

### US18 — Conexão HTTP com server remoto `[MVP]`

**Como** desenvolvedor,
**quero** conectar o orcha-mcp a um MCP server remoto via HTTP,
**para** comparar o comportamento entre transport STDIO e HTTP.

**Critérios de aceite:**
- [ ] O orcha-mcp faz POST para a URL do server com a mensagem `initialize`
- [ ] Suporta headers customizados via campo `headers` no `orcha.json` (para autenticação Bearer token)
- [ ] Lida com respostas síncronas (200 JSON) e streaming (SSE — `text/event-stream`)
- [ ] Timeout configurável via campo `timeout` no `orcha.json` (padrão: 30s)
- [ ] Erro claro se a URL não estiver acessível (connection refused, timeout)

**Notas técnicas:**
- Usar `mcp.client.streamable_http.streamablehttp_client` do MCP SDK
- Server remoto configurado com `type: "remote"` e `url` no `orcha.json`
- Testar com `@modelcontextprotocol/server-everything` rodando localmente via HTTP

**Definição de Pronto:**
- [ ] Critérios de aceite funcionam
- [ ] Teste verifica handshake HTTP com server de teste local
- [ ] Tipagem estática completa
- [ ] Erros de rede exibem mensagem orientada a ação (verificar URL, verificar server)

---

## Sprint 5 — Polimento

> Objetivo: chat interativo, sumário de sessão e refinamentos de UX.

---

## E5 — Loop LLM (continuação)

---

### US19 — Chat interativo (REPL) `[MVP]`

**Como** desenvolvedor,
**quero** executar `orcha chat --interactive` e ter uma sessão de chat contínua,
**para** explorar o comportamento do loop MCP em múltiplos turnos de conversa.

**Critérios de aceite:**
- [ ] Abre um loop no terminal com prompt `>`
- [ ] Mantém o histórico completo de mensagens entre turnos da sessão
- [ ] `Ctrl+C` ou comando `/exit` encerram a sessão graciosamente
- [ ] Comando `/clear` limpa o histórico mantendo a sessão e os servers conectados
- [ ] Exibe quantas tools e servers estão ativos no início da sessão
- [ ] Com `--verbose`, o modo verbose persiste em todos os turnos

**Notas técnicas:**
- Usar `prompt_toolkit` ou o `input()` nativo com `readline` para histórico de comandos
- Os servers MCP ficam conectados durante toda a sessão (não reconectam a cada turno)

**Definição de Pronto:**
- [ ] Critérios de aceite funcionam
- [ ] `Ctrl+C` não deixa processos órfãos
- [ ] Tipagem estática completa

---

## E6 — Debug / Inspeção (continuação)

---

### US20 — Sumário de sessão ao encerrar `[MVP]`

**Como** desenvolvedor,
**quero** ver um sumário ao fim de qualquer operação,
**para** ter uma visão geral do que foi feito naquela sessão.

**Critérios de aceite:**
- [ ] Exibe ao encerrar: servers conectados, total de tools descobertas, tools chamadas (nome + contagem), tempo total de execução
- [ ] Com `--verbose`, exibe também a contagem de mensagens JSON-RPC trocadas por server
- [ ] O sumário vai para `stderr` para não interferir em pipes

**Exemplo de output:**
```
─── Session Summary ───────────────────────────────
  Servers:   filesystem, fetch
  Tools:     7 discovered, 2 called
    filesystem_read_file  ×1
    filesystem_list_directory  ×1
  Duration:  3.2s
───────────────────────────────────────────────────
```

**Definição de Pronto:**
- [ ] Critérios de aceite funcionam
- [ ] Tipagem estática completa
- [ ] Sumário aparece mesmo quando a sessão é encerrada por `Ctrl+C`

---

## Pós-MVP

> As histórias abaixo estão fora do escopo da primeira entrega. Ver [mvp.md](./mvp.md) para justificativas.

---

## E7 — Orquestração Multi-Agente

Um agente orquestrador que delega sub-tarefas a agentes especializados via MCP.

---

### US21 — Agente delegando para sub-agente via MCP

**Como** desenvolvedor,
**quero** que um agente orquestrador possa criar e chamar sub-agentes como tools MCP,
**para** entender como a orquestração hierárquica de agentes funciona.

**Critérios de aceite:**
- [ ] O orquestrador pode iniciar um sub-processo `orcha chat` como se fosse um MCP server
- [ ] O sub-agente expõe uma tool `run_task(instruction: string)` via MCP
- [ ] O agente principal pode delegar para o sub-agente e aguardar a resposta
- [ ] O ciclo completo é observável com `--verbose` mostrando os dois níveis de orquestração

---

## E8 — Resources e Prompts

Suporte aos outros primitivos MCP além de Tools.

---

### US22 — Listar e ler Resources

**Como** desenvolvedor,
**quero** executar `orcha list-resources` e `orcha read-resource <uri>`,
**para** explorar o primitivo Resources do MCP.

**Critérios de aceite:**
- [ ] `list-resources` exibe todos os resources disponíveis por server (URI, nome, mimeType)
- [ ] `read-resource <uri>` exibe o conteúdo do resource
- [ ] Com `--verbose`, exibe o JSON-RPC de `resources/list` e `resources/read`

---

### US23 — Listar e usar Prompts

**Como** desenvolvedor,
**quero** executar `orcha list-prompts` e `orcha get-prompt <nome>`,
**para** explorar o primitivo Prompts do MCP e ver como templates são usados.

**Critérios de aceite:**
- [ ] `list-prompts` exibe todos os prompts disponíveis por server (nome, descrição, argumentos)
- [ ] `get-prompt <nome> --args '{...}'` exibe o prompt renderizado com os argumentos fornecidos
- [ ] Com `--verbose`, exibe o JSON-RPC de `prompts/list` e `prompts/get`

---

## E9 — Comparativo entre Ferramentas

Análise comparativa de como OpenCode, Claude Code e Gemini CLI usam o MCP.

---

### US24 — Modo "side-by-side"

**Como** desenvolvedor,
**quero** executar a mesma pergunta no `orcha-mcp` e ver o log de outra ferramenta lado a lado,
**para** comparar as diferenças de implementação entre elas.

**Critérios de aceite:**
- [ ] Flag `--compare <tool>` aceita `opencode` ou `claude-code` como valor
- [ ] Executa a mesma query nas duas ferramentas e exibe os traces JSON-RPC lado a lado
- [ ] Gera um relatório de diferenças (número de round-trips, tools chamadas, latência)

---

## Resumo de Priorização

| História | Épico | Sprint | MVP? | Prioridade |
|----------|-------|--------|------|------------|
| US00 | E0 | 0 | Sim | Alta |
| US01 | E2 | 1 | Sim | Alta |
| US02 | E2 | 1 | Sim | Alta |
| US03 | E2 | 1 | Sim | Alta |
| US04 | E2 | 1 | Sim | Média |
| US05 | E1 | 1 | Sim | Alta |
| US06 | E1 | 1 | Sim | Alta |
| US07 | E1 | 1 | Sim | Alta |
| US08 | E3 | 2 | Sim | Alta |
| US09 | E3 | 2 | Sim | Média |
| US10 | E6 | 2 | Sim | Alta |
| US11 | E6 | 2 | Sim | Alta |
| US12 | E4 | 3 | Sim | Alta |
| US13 | E4 | 3 | Sim | Alta |
| US14 | E4 | 3 | Sim | Média |
| US15 | E5 | 4 | Sim | Alta |
| US16 | E5 | 4 | Sim | Alta |
| US17 | E5 | 4 | Sim | Alta |
| US18 | E1 | 4 | Sim | Alta |
| US19 | E5 | 5 | Sim | Média |
| US20 | E6 | 5 | Sim | Baixa |
| US21 | E7 | — | Não | Alta (futuro) |
| US22 | E8 | — | Não | Média (futuro) |
| US23 | E8 | — | Não | Média (futuro) |
| US24 | E9 | — | Não | Baixa (futuro) |
