# 静态校验钩子桩字节：按 dllmain.cpp 的 EmitBytes 顺序重建并反汇编
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

code = bytearray()
code += bytes([0x48, 0x83, 0xEC, 0x28])              # sub rsp,0x28
code += bytes([0x48, 0x89, 0x4C, 0x24, 0x20])        # mov [rsp+0x20],rcx
code += bytes([0x48, 0xB8]) + (0x1122334455667788).to_bytes(8, 'little')  # mov rax, <filter>
code += bytes([0xFF, 0xD0])                          # call rax
code += bytes([0x48, 0x8B, 0x4C, 0x24, 0x20])        # mov rcx,[rsp+0x20]
code += bytes([0x48, 0x83, 0xC4, 0x28])              # add rsp,0x28
je_pos = len(code)
code += bytes([0x85, 0xC0, 0x74, 0x06])              # test eax,eax; je +6
code += bytes([0xB8, 0x01, 0x00, 0x00, 0x00, 0xC3])  # mov eax,1; ret
orig_pos = len(code)
code += bytes([0x48, 0xB8]) + (0xDEADBEEFCAFEBABE).to_bytes(8, 'little')  # mov rax, <tramp>
code += bytes([0xFF, 0xE0])                          # jmp rax

print(f"je at +{je_pos:#x}, .orig label at +{orig_pos:#x}")
rel = orig_pos - (je_pos + 4)
print(f"je rel8 = {rel} ({rel:#x})  => 期望 6 -> {'OK' if rel == 6 else 'BUG!'}")

md = Cs(CS_ARCH_X86, CS_MODE_64)
for m in md.disasm(bytes(code), 0x1000):
    mark = ""
    if m.address == 0x1000 + orig_pos:
        mark = "   <== .orig"
    print(f"  {m.address:#x}: {m.mnemonic} {m.op_str}{mark}")

# 跳板验证
tramp = bytearray()
tramp += bytes([0x48, 0x89, 0x5C, 0x24, 0x10])       # mov [rsp+0x10],rbx  (原首 5 字节)
tramp += bytes([0x48, 0xB8]) + (0x7FF6CF5DD8C5).to_bytes(8, 'little')  # mov rax, target+5
tramp += bytes([0xFF, 0xE0])
print("\n--- trampoline ---")
for m in md.disasm(bytes(tramp), 0x2000):
    print(f"  {m.address:#x}: {m.mnemonic} {m.op_str}")
