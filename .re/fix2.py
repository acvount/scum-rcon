# 精确修复 dllmain.cpp 的合并/断行错误
PATH = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\plugin\dllmain.cpp"
raw = open(PATH, "rb").read()
if raw.startswith(b"\xef\xbb\xbf"):
    raw = raw[3:]
text = raw.decode("utf-8", "surrogateescape")
lines = text.split("\n")

fixed = []

def patch(idx, new_lines):
    lines[idx:idx+1] = new_lines
    fixed.append(idx + 1)

i = 0
while i < len(lines):
    ln = lines[i]
    # 1) break; 行里被塞进了 prop 赋值
    if "== 0) break;" in ln and "prop = *(uint64_t*)" in ln:
        cut = ln.index("prop = *(uint64_t*)")
        head = ln[:cut].rstrip()
        tail = ln[cut:]
        lines[i:i+1] = [head, "        " + tail]
        fixed.append(i+1)
        i += 1
        continue
    # 2) 裸的 {EX_LocalVariable(...)} → 变成注释
    if ln.strip() == "{EX_LocalVariable(0x00), FProperty*}":
        lines[i:i+1] = ["    //   {EX_LocalVariable(0x00), FProperty*}"]
        fixed.append(i+1)
        i += 1
        continue
    # 3) 顶格的 codebuf 声明 → 加缩进
    if ln.startswith("uint8_t codebuf[256]"):
        lines[i:i+1] = ["    " + ln]
        fixed.append(i+1)
        i += 1
        continue
    # 4) 裸 float32 行
    if ln.strip() == "float32":
        lines[i:i+1] = ["            // 3 x float32"]
        fixed.append(i+1)
        i += 1
        continue
    # 5) 'float 解析...' 残行
    if ln.startswith("float ") and "std::string floats" not in ln and len(ln) < 40:
        lines[i:i+1] = ["    // parse as floats (coordinate return values)"]
        fixed.append(i+1)
        i += 1
        continue
    # 6) 裸 {i, addr, nameId, ...} 行
    if ln.strip() == "{i, addr, nameId, nameNum, classId}":
        lines[i:i+1] = ["// returns {i, addr, nameId, nameNum, classId}"]
        fixed.append(i+1)
        i += 1
        continue
    # 7) 顶格的 if (a.size() < 2) return ... usage: findclass
    if ln.startswith('if (a.size() < 2) return') and "findclass" in ln:
        lines[i:i+1] = ["    " + ln]
        fixed.append(i+1)
        i += 1
        continue
    # 8) kMaxDist 声明被注释吞掉
    if "const uintptr_t kMaxDist" in ln and ln.lstrip().startswith("//") is False and not ln.startswith("    const"):
        pos = ln.index("const uintptr_t kMaxDist")
        head = ln[:pos].rstrip()
        tail = ln[pos:]
        lines[i:i+1] = [head, "    " + tail]
        fixed.append(i+1)
        i += 1
        continue
    i += 1

open(PATH, "wb").write(b"\xef\xbb\xbf" + "\n".join(lines).encode("utf-8", "surrogateescape"))
print("patched lines:", fixed)
