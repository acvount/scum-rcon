# probe_slots.py — 计算每个 vtable 槽位的可挂载 patch 尺寸，逐槽位 tickprobe，识别 Tick
import json, socket, struct, sys, time
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

HOST, PORT = "127.0.0.1", 17880

def send(cmd, timeout=90):
    with socket.create_connection((HOST, PORT), timeout=timeout) as s:
        s.sendall((cmd + "\n").encode()); buf = b""
        while not buf.endswith(b"\n"):
            c = s.recv(65536)
            if not c: break
            buf += c
    return json.loads(buf.decode("utf-8", "replace").strip())

def raw(a, ln):
    r = send(f"raw {a:x} {ln}")
    if not r.get("ok"):
        raise RuntimeError(f"raw @{a:#x} failed: {r}")
    return bytes.fromhex(r["hex"])

md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

_CTRL = ("jmp", "call", "loop", "jrcxz", "jecxz")   # 控制流重定位危险
try:
    from capstone.x86 import X86_OP_MEM, X86_REG_RIP
    def _is_rip_rel(m):
        return any(op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP for op in m.operands)
except Exception:
    def _is_rip_rel(m):
        return "rip" in m.op_str or m.mnemonic in _CTRL

def patch_size(f):
    """返回能覆盖完整指令且无 rip 相对操作数/控制流的 patch 尺寸（14..32），不可挂载返回 None"""
    code = raw(f, 40)
    insns = list(md.disasm(code, f))
    cov = 0
    for m in insns:
        if m.address - f != cov:  # 不连续（对齐/解码失败）
            break
        if m.mnemonic.startswith("j") or m.mnemonic in _CTRL or _is_rip_rel(m):
            return None
        cov += m.size
        if cov >= 14:
            return cov if cov <= 32 else None
    return None

def main():
    wait_slots = sys.argv[1:] if len(sys.argv) > 1 else None
    st = send("stat")
    if not st.get("ready"):
        print("harness not ready:", st); return
    r = send("findvt GameEngine 78 96")
    if not r.get("ok"):
        print("findvt failed:", r); return
    slots = {s["i"]: int(s["a"]) for s in r["slots"]}  # findvt 输出十进制
    rows = []
    for i in sorted(slots):
        if wait_slots and str(i) not in wait_slots:
            continue
        f = slots[i]
        psz = patch_size(f)
        if psz is None:
            rows.append((i, f, None, None)); continue
        pr = send(f"tickprobe {i} {psz} 2500")
        rows.append((i, f, psz, pr))
    print(f"{'slot':>4} {'rva':>10} {'psz':>4} {'count':>6} {'deltas':>28} {'rdxs':>14} {'tids':>14}")
    for i, f, psz, pr in rows:
        if psz is None:
            print(f"{i:>4} {f & 0xffffffff:>#10x} {'--':>4}  SKIP (rip-rel/unpatchable)")
            continue
        d = ",".join(str(x)[:6] for x in pr.get("deltas", []))
        rx = ",".join(str(x) for x in pr.get("rdxs", []))
        ti = ",".join(str(x) for x in pr.get("tids", []))
        print(f"{i:>4} {f & 0xffffffff:>#10x} {psz:>4} {pr.get('count', '?'):>6} {d:>28} {rx:>14} {ti:>14}")

if __name__ == "__main__":
    main()
