# 修复 dllmain.cpp：PowerShell 替换导致的行合并（'?' 吞掉了换行）
import io, re, sys

PATH = r"C:\Users\Administrator\Desktop\逆向scumserver\scum-harness\plugin\dllmain.cpp"
raw = open(PATH, "rb").read()
# 去掉 BOM
if raw.startswith(b"\xef\xbb\xbf"):
    raw = raw[3:]
text = raw.decode("utf-8", "surrogateescape")
lines = text.split("\n")

CODE_START = re.compile(r'^(uint|int|size_t|static|struct|return|std|for|if|while|void|uintptr_t|uint8_t|uint32_t|uint64_t|int32_t|char|float|double|bool|UObject|void\*|\{|auto|LONG|DWORD|HANDLE|SIZE_T|unsigned)')

fixed = 0
out = []
for ln in lines:
    stripped = ln
    # 在一行里找 "?" 后面紧跟代码的情况（且前面有注释符号）
    if "?" in ln and "//" in ln:
        # 从右往左找候选 '?'
        for m in reversed(list(re.finditer(r'\?', ln))):
            tail = ln[m.end():]
            # 去掉可能的前导空格后判断是否像代码
            probe = tail.lstrip()
            if probe and CODE_START.match(probe):
                head = ln[:m.start()].rstrip()
                # 保留行内注释：若 head 已有 // 则直接分行
                out.append(head)
                out.append(tail.lstrip())
                fixed += 1
                break
        else:
            out.append(ln)
    else:
        out.append(ln)

open(PATH, "wb").write(b"\xef\xbb\xbf" + "\n".join(out).encode("utf-8", "surrogateescape"))
print(f"split {fixed} merged lines; total lines {len(out)}")
