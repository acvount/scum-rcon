
import socket, json
def rpc(c, t=180):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
print("hookpe on:", json.dumps(rpc("hookpe on"), ensure_ascii=False))
r = rpc("loadbp /Game/ConZ_Files/Blueprints/PlayerControllers/BP_ConZPlayerController.BP_ConZPlayerController_C")
print("loadbp:", json.dumps(r, ensure_ascii=False))
print("alive:", json.dumps(rpc("stat"), ensure_ascii=False)[:160])
print("after:", json.dumps(rpc("findobj BP_ConZPlayerController 5"), ensure_ascii=False)[:400])
print("chat:", json.dumps(rpc("funcs Chat_Server 200"), ensure_ascii=False)[:600])
