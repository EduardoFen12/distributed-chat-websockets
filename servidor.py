import asyncio
import websockets
import json

# =============================================================================
# ESTRUTURA DE DADOS DO SISTEMA
# =============================================================================
# rooms: dicionário que mapeia nome_da_sala -> set de websockets conectados
# Exemplo: { "sala1": {ws_alice, ws_bob}, "sala2": {ws_carlos} }
rooms = {}

# admins: set com os websockets que têm privilégios de administrador
# Usamos o próprio objeto websocket como chave, pois ele é único por conexão
admins = set()


# =============================================================================
# HANDLER PRINCIPAL — chamado para cada nova conexão WebSocket
# =============================================================================
async def handler(websocket):
    # Variáveis de estado LOCAL desta conexão (cada cliente tem o seu)
    current_room = None   # sala em que este cliente está
    user_name = "Anônimo" # nome do usuário (preenchido no login)

    try:
        # Loop que fica lendo mensagens enquanto o cliente estiver conectado
        async for message in websocket:
            try:
                # Toda mensagem chega como string JSON — desserializamos aqui
                data = json.loads(message)
                msg_type = data.get("type")

                # ------------------------------------------------------------------
                # TODO 1: LÓGICA DE LOGIN
                # ------------------------------------------------------------------
                # O cliente envia: { "type": "login", "user": "...", "room": "...", "isAdmin": bool }
                if msg_type == "login":
                    user_name = data.get("user", "Anônimo")
                    room_name = data.get("room", "geral")

                    # Salva qual sala este websocket pertence
                    current_room = room_name

                    # Garante que a sala existe no dicionário, criando um set vazio se necessário
                    if current_room not in rooms:
                        rooms[current_room] = set()

                    # Adiciona este websocket à sala
                    rooms[current_room].add(websocket)

                    # Se o cliente declarou ser admin, adiciona ao set de admins
                    if data.get("isAdmin", False):
                        admins.add(websocket)

                    print(f"[LOGIN] {user_name} entrou na sala '{current_room}'" +
                          (" [ADMIN]" if websocket in admins else ""))

                    # Confirma o login para o próprio cliente
                    await websocket.send(json.dumps({
                        "type": "system",
                        "text": f"Bem-vindo(a), {user_name}! Você está na sala '{current_room}'."
                    }))

                    # Avisa os OUTROS na sala que alguém entrou
                    await broadcast_sala(current_room, {
                        "type": "system",
                        "text": f"{user_name} entrou na sala."
                    }, excluir=websocket)

                # ------------------------------------------------------------------
                # TODO 2: MENSAGEM DE SALA (restrita — só vai para quem está na mesma sala)
                # ------------------------------------------------------------------
                # O cliente envia: { "type": "message", "text": "..." }
                elif msg_type == "message":
                    if current_room is None:
                        # Cliente tentou falar sem ter feito login ainda
                        await websocket.send(json.dumps({
                            "type": "error",
                            "text": "Você precisa fazer login antes de enviar mensagens."
                        }))
                        continue

                    texto = data.get("text", "")
                    print(f"[MSG] {user_name} em '{current_room}': {texto}")

                    # Monta o payload e envia para TODOS na mesma sala (inclusive o remetente,
                    # para ele ver a própria mensagem confirmada pelo servidor)
                    await broadcast_sala(current_room, {
                        "type": "message",
                        "user": user_name,
                        "text": texto,
                        "room": current_room,
                        "style": "normal"
                    })

                # ------------------------------------------------------------------
                # TODO 3: COMANDO DE ADMIN — envia para TODAS as salas
                # ------------------------------------------------------------------
                # O cliente envia: { "type": "admin_broadcast", "text": "..." }
                elif msg_type == "admin_broadcast":
                    if websocket not in admins:
                        # Impostor! Avisa apenas o próprio remetente
                        await websocket.send(json.dumps({
                            "type": "error",
                            "text": "Acesso negado. Você não tem privilégios de admin."
                        }))
                        print(f"[ALERTA] {user_name} tentou usar admin_broadcast sem permissão!")
                    else:
                        texto = data.get("text", "")
                        print(f"[ADMIN BROADCAST] {user_name}: {texto}")

                        # Percorre TODAS as salas e envia para TODOS os clientes
                        for sala, clientes in rooms.items():
                            for cliente in clientes:
                                try:
                                    await cliente.send(json.dumps({
                                        "type": "admin_broadcast",
                                        "user": user_name,
                                        "text": texto,
                                        "style": "admin"  # frontend usa isso para destacar
                                    }))
                                except websockets.exceptions.ConnectionClosed:
                                    pass  # cliente desconectou entre um envio e outro

                else:
                    print(f"[AVISO] Tipo de mensagem desconhecido: '{msg_type}'")

            except json.JSONDecodeError:
                # TODO implícito do enunciado: nunca deixar o servidor cair com JSON ruim
                print(f"[ERRO] {user_name} enviou dados inválidos (JSON malformado).")
                await websocket.send(json.dumps({
                    "type": "error",
                    "text": "Mensagem inválida (JSON malformado)."
                }))
                continue  # Continua o loop normalmente

    except websockets.exceptions.ConnectionClosed:
        # Navegador fechado ou conexão perdida — tratado no finally
        pass

    except Exception as e:
        print(f"[ERRO INESPERADO] {e}")

    finally:
        # ------------------------------------------------------------------
        # TODO 4: GARBAGE COLLECTION — limpa o websocket ao desconectar
        # ------------------------------------------------------------------
        # Remove o websocket da sala atual para não vazar memória
        if current_room and current_room in rooms:
            rooms[current_room].discard(websocket)  # discard não lança erro se não existir

            # Se a sala ficou vazia, remove ela também do dicionário
            if not rooms[current_room]:
                del rooms[current_room]
                print(f"[GC] Sala '{current_room}' removida (sem clientes).")
            else:
                # Avisa os que ficaram que este usuário saiu
                await broadcast_sala(current_room, {
                    "type": "system",
                    "text": f"{user_name} saiu da sala."
                })

        # Remove dos admins caso estivesse lá
        admins.discard(websocket)

        print(f"[DESCONEXÃO] {user_name} desconectou.")


# =============================================================================
# FUNÇÃO AUXILIAR: envia para todos de uma sala (com opção de excluir um socket)
# =============================================================================
async def broadcast_sala(room_name, payload, excluir=None):
    """Envia `payload` (dict) para todos os clientes da sala `room_name`.
    Se `excluir` for informado, pula aquele websocket específico.
    """
    if room_name not in rooms:
        return

    mensagem = json.dumps(payload)

    # Iteramos sobre uma CÓPIA do set para evitar erros se ele mudar durante o loop
    for cliente in rooms[room_name].copy():
        if cliente == excluir:
            continue
        try:
            await cliente.send(mensagem)
        except websockets.exceptions.ConnectionClosed:
            pass  # cliente já desconectou, será limpo no seu próprio finally


# =============================================================================
# PONTO DE ENTRADA
# =============================================================================
async def main():
    # 0.0.0.0 = aceita conexões de qualquer interface de rede (obrigatório pelo enunciado)
    async with websockets.serve(handler, "0.0.0.0", 8080):
        print("Servidor rodando em ws://localhost:8080")
        await asyncio.Future()  # mantém o servidor rodando indefinidamente

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
