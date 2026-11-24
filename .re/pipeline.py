# 完整流水线：probe → gtload → desc → gtcall BroadcastChatLine → 验证
import json, socket, struct, sys
S = socket.create_connection(("127.0.0.1", 17880), timeout=180)
def send(cmd):
    S.sendall((cmd + "\n").encode()); buf = b""
    while not buf.endswith(b"\n"):
        c = S.recv(1 << 22)
        if not c: break
        buf += c
    return json.loads(buf.decode("utf-8", "replace").strip())

pr = send("tickprobe 87 19 2500")
tid = pr["tids"][0] if pr.get("tids") else 0
print("tid:", tid)
r = send(f'gtload "/Game/ConZ_Files/Blueprints/PlayerControllers/BP_ConZPlayerController.BP_ConZPlayerController_C" 86 14 {tid} GameEngine 1')
print("gtload:", json.dumps(r, ensure_ascii=False))
d = send("desc BroadcastChatLine")
print("desc:", json.dumps(d, ensure_ascii=False)[:600])
# 找 World 实例
w = send("findinst World 5")
print("findinst World:", json.dumps(w, ensure_ascii=False)[:300])
# 调用广播
msg = "[YG-TEST] 服务器外部接入测试消息 hello-from-harness"
c = send(f'gtcall BroadcastChatLine o:0x{int(w["items"][0]["addr"], 16):x} s:{msg} i:0')
print("gtcall:", json.dumps(c, ensure_ascii=False))
S.close()
