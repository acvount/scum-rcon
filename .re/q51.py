
import socket, json
def rpc(c, t=180):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
for ctx in ["VoiceChatComponent", "KismetSystemLibrary"]:
    for fn in ["LoadClassAsset_Blocking", "LoadAsset_Blocking"]:
        r = rpc("loadclass /Game/ConZ_Files/Blueprints/PlayerControllers/BP_ConZPlayerController.BP_ConZPlayerController_C %s %s" % (fn, ctx))
        print(ctx, fn, "->", json.dumps({k:v for k,v in r.items() if k!="hex"}, ensure_ascii=False))
print("after:", json.dumps(rpc("findobj BP_ConZPlayerController 5"), ensure_ascii=False)[:300])
