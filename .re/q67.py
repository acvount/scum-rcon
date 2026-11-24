
import socket, json
def rpc(c, t=180):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
r = rpc("loadclass /Game/ConZ_Files/Blueprints/PlayerControllers/BP_ConZPlayerController.BP_ConZPlayerController_C LoadClassAsset_Blocking")
print("loadclass:", json.dumps({k:v for k,v in r.items() if k!="hex"}, ensure_ascii=False))
if r.get("hex"): print("  hex:", r["hex"][:80])
print("after:", json.dumps(rpc("findobj BP_ConZPlayerController 5"), ensure_ascii=False)[:400])
