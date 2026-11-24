; vthooks.asm — 游戏线程 hook 核心（每 hook 点一个独立 stub 携带记录指针）
; stub 布局（C 侧 MakeStub 生成，RWX）:
;   48 B8 <rec64>          mov rax, rec
;   49 BB <core64>         mov r11, core
;   41 FF E3               jmp r11
; 核心约定：进入时 rax = 记录指针；采样/派发完成后 jmp [rax + trampolineOffset]

EXTERN LoadTaskInvokeC:PROC
EXTERN __imp_GetCurrentThreadId:QWORD

.CODE

; ProbeRec: +0x00 state +0x08 count +0x10 nDelta +0x14 deltas[8]
;           +0x38 nRdx +0x3C rdxs[8] +0x60 nTid +0x64 tids[4] +0x78 trampoline
ProbeHookCore PROC
    sub     rsp, 38h
    mov     qword ptr [rsp+28h], rcx
    mov     qword ptr [rsp+30h], rdx
    mov     qword ptr [rsp+18h], r8
    mov     qword ptr [rsp+20h], r9
    mov     qword ptr [rsp+10h], rax
    cmp     dword ptr [rax], 1
    jne     ProbeDone
    lock inc dword ptr [rax+8]
    mov     r10d, dword ptr [rax+10h]
    cmp     r10d, 8
    jge     ProbeNoDelta
    movss   dword ptr [rax+14h+r10*4], xmm0
    inc     dword ptr [rax+10h]
ProbeNoDelta:
    mov     r10d, dword ptr [rax+38h]
    cmp     r10d, 8
    jge     ProbeNoRdx
    mov     dword ptr [rax+3Ch+r10*4], edx
    inc     dword ptr [rax+38h]
ProbeNoRdx:
    mov     r10d, dword ptr [rax+60h]
    cmp     r10d, 4
    jge     ProbeDone
    call    qword ptr [__imp_GetCurrentThreadId]
    mov     r11, qword ptr [rsp+10h]
    mov     r10d, dword ptr [r11+60h]
    mov     dword ptr [r11+64h+r10*4], eax
    inc     dword ptr [r11+60h]
    mov     rax, r11
ProbeDone:
    mov     rcx, qword ptr [rsp+28h]
    mov     rdx, qword ptr [rsp+30h]
    mov     r8,  qword ptr [rsp+18h]
    mov     r9,  qword ptr [rsp+20h]
    add     rsp, 38h
    jmp     qword ptr [rax+78h]
ProbeHookCore ENDP

; LoadRec: +0x00 state +0x04 pad +0x08 ctx +0x10 expectedTid +0x14 result
;          +0x18 classPtr +0x20 trampoline
LoadHookCore PROC
    sub     rsp, 38h
    mov     qword ptr [rsp+28h], rcx
    mov     qword ptr [rsp+30h], rdx
    mov     qword ptr [rsp+18h], r8
    mov     qword ptr [rsp+20h], r9
    mov     qword ptr [rsp+10h], rax
    mov     r10d, 1
    lock xadd dword ptr [rax], r10d
    test    r10d, r10d
    jne     LoadPassthru
    mov     r10d, dword ptr [rax+10h]
    test    r10d, r10d
    je      LoadRunTask
    call    qword ptr [__imp_GetCurrentThreadId]
    mov     r11, qword ptr [rsp+10h]
    cmp     eax, dword ptr [r11+10h]
    je      LoadRunTask2
    mov     dword ptr [r11], 0
    mov     rax, r11
    jmp     LoadExit
LoadRunTask2:
    mov     rax, r11
LoadRunTask:
    call    LoadTaskInvokeC
    mov     rax, qword ptr [rsp+10h]
LoadExit:
    mov     rcx, qword ptr [rsp+28h]
    mov     rdx, qword ptr [rsp+30h]
    mov     r8,  qword ptr [rsp+18h]
    mov     r9,  qword ptr [rsp+20h]
    add     rsp, 38h
    jmp     qword ptr [rax+20h]
LoadPassthru:
    mov     rcx, qword ptr [rsp+28h]
    mov     rdx, qword ptr [rsp+30h]
    mov     r8,  qword ptr [rsp+18h]
    mov     r9,  qword ptr [rsp+20h]
    add     rsp, 38h
    jmp     qword ptr [rax+20h]
LoadHookCore ENDP

END
