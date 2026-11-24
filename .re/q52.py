
import socket, json
def rpc(c, t=180):
    s=socket.create_connection(("127.0.0.1",17880),timeout=t)
    s.sendall((c+"\n").encode()); b=b""
    while not b.endswith(b"\n"):
        d=s.recv(1<<20)
        if not d: break
        b+=d
    return json.loads(b.decode("utf-8","replace"))
r = rpc("strtest 77 KismetStringLibrary")
hexs = r.get("hex","")
abc = "ABC".encode('utf-16-le') in bytes.fromhex(hexs) if hexs else False
print("strtest77:", json.dumps({k:v for k,v in r.items() if k!="hex"}, ensure_ascii=False), "ABC=", abc)
if hexs: print("  hex:", hexs[:96])
r = rpc("loadclass /Game/ConZ_Files/Blueprints/PlayerControllers/BP_ConZPlayerController.BP_ConZPlayerController_C LoadClassAsset_Blocking VoiceChatComponent")
print("loadclass:", json.dumps({k:v for k,v in r.items() if k!="hex"}, ensure_ascii=False))
print("after:", json.dumps(rpc("findobj BP_ConZPlayerController 5"), ensure_ascii=False)[:300])
