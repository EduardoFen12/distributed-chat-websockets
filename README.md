# Trabalho de Sistemas Distribuídos
## Chat em Tempo Real — WebSockets, Salas e Privilégios

---

## Descrição
Sistema de chat em tempo real implementado com WebSockets (RFC 6455). O servidor gerencia múltiplas salas de forma isolada, controla privilégios de administrador e realiza limpeza automática de conexões encerradas.

---

## Arquivos
- **`servidor.py`**: Servidor assíncrono Python (`asyncio` + `websockets`).
- **`index.html`**: Frontend completo (HTML + CSS + JavaScript puro).

---

## Dependências
- Python 3.8+
- Biblioteca `websockets`:

```bash
pip install websockets
