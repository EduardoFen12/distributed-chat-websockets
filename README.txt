================================================================================
  Trabalho de Sistemas Distribuídos
  Chat em Tempo Real — WebSockets, Salas e Privilégios
================================================================================

DESCRIÇÃO
---------
Sistema de chat em tempo real implementado com WebSockets (RFC 6455).
O servidor gerencia múltiplas salas de forma isolada, controla privilégios
de administrador e realiza limpeza automática de conexões encerradas.

--------------------------------------------------------------------------------

ARQUIVOS
--------
  servidor.py   → Servidor assíncrono Python (asyncio + websockets)
  index.html    → Frontend completo (HTML + CSS + JavaScript puro)

--------------------------------------------------------------------------------

DEPENDÊNCIAS
------------
  Python 3.8+
  Biblioteca websockets:

    pip install websockets

  Nenhuma dependência de frontend (sem npm, sem frameworks).

--------------------------------------------------------------------------------

COMO EXECUTAR
-------------
  1. Inicie o servidor em um terminal:

       python servidor.py

     Saída esperada:
       Servidor rodando em ws://localhost:8080

  2. Abra o arquivo index.html no navegador.
     Recomendado: abrir múltiplas abas para simular vários clientes.

  3. Preencha seu nome e a sala desejada, depois clique em "Conectar".

--------------------------------------------------------------------------------

PROTOCOLO DE MENSAGENS
-----------------------
  Toda comunicação usa JSON. Cada mensagem possui um campo "type".

  Cliente → Servidor:

    Login:
      { "type": "login", "user": "Alice", "room": "geral", "isAdmin": false }

    Mensagem para a sala:
      { "type": "message", "text": "Olá pessoal!" }

    Broadcast de admin (todas as salas):
      { "type": "admin_broadcast", "text": "Servidor reiniciando em 5 min." }

  Servidor → Cliente:

    Mensagem de sala:
      { "type": "message", "user": "Alice", "text": "...", "style": "normal" }

    Broadcast de admin:
      { "type": "admin_broadcast", "user": "ADMIN_Carlos", "text": "...", "style": "admin" }

    Mensagem de sistema:
      { "type": "system", "text": "Alice entrou na sala." }

    Erro:
      { "type": "error", "text": "Acesso negado." }

--------------------------------------------------------------------------------

PRIVILÉGIOS DE ADMIN
--------------------
  Para entrar como administrador, inclua "ADMIN" no nome de usuário.
  Exemplos: ADMIN, ADMIN_Joao, Carlos_ADMIN

  Admins podem usar o botão "Broadcast" para enviar mensagens para TODAS
  as salas simultaneamente. Clientes comuns que tentarem enviar
  "admin_broadcast" diretamente recebem uma mensagem de erro.

--------------------------------------------------------------------------------

FUNCIONALIDADES IMPLEMENTADAS
------------------------------
  [✓] Salas isoladas — mensagens não vazam entre salas diferentes
  [✓] Identificação de usuário por sessão WebSocket
  [✓] Controle de acesso — admin_broadcast restrito a admins autenticados
  [✓] Resiliência — JSON malformado não derruba o servidor
  [✓] Garbage Collection — sockets removidos dos dicionários ao desconectar
  [✓] Remoção automática de salas vazias

--------------------------------------------------------------------------------

ESTRUTURA INTERNA DO SERVIDOR
------------------------------
  rooms  → dict: { "nome_da_sala": set(websockets) }
  admins → set: { websocket, websocket, ... }

  A 5-tupla de cada conexão (IP origem, porta origem, IP destino, porta
  destino, protocolo) é gerenciada pelo próprio objeto websocket do Python,
  que age como identificador único de cada cliente.

--------------------------------------------------------------------------------

LIMITAÇÕES CONHECIDAS / ESCALABILIDADE
---------------------------------------
  Este servidor é adequado para fins didáticos e cargas leves (~100 clientes).
  Para escala maior, os principais gargalos são:

  - Estado em memória: o dict "rooms" não é compartilhado entre processos.
    Solução de produção: Redis Pub/Sub.

  - CPU única: asyncio usa apenas 1 núcleo (limitação do GIL do Python).
    Solução de produção: múltiplos workers com gunicorn + uvicorn.

  - Broadcast sequencial: envio para N clientes ocorre em loop.
    Solução: asyncio.gather() para envios paralelos.

  Estimativa de capacidade com o código atual:
    Até  ~100 clientes  → sem problemas
    Até ~1.000 clientes → funcional, broadcast lento
    Acima de 10.000    → necessário redesenho com Redis + múltiplos workers

================================================================================