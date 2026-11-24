// reflect.cpp — UFunction 参数解析 + ProcessEvent 调用（含偏移自校准）
#include "ue.h"
#include <algorithm>
#include <cstring>
#include <ctype.h>

namespace ue {

// ---------------- FProperty 链读取（多候选评分） ----------------
struct ChainScore { int ok = 0; int32_t parmsSize = 0; };

static bool ReadNameAt(void* p, int off, std::string& out) {
    FName n = *(FName*)((uint8_t*)p + off);
    if (n.ComparisonIndex <= 0) return false;
    std::string s = FNameToString(n);
    if (s.empty() || s.size() > 128) return false;
    for (char c : s) {
        if (!(isalnum((unsigned char)c) || c == '_')) return false;
    }
    out = s;
    return true;
}

// 候选偏移组合；对每个组合跑一遍链，选最自洽的结果
struct LayoutCand { int offName; int offSize; int offOffset; };

static bool BuildProps(UFunction* fn, const LayoutCand& lc,
                       std::vector<PropertyInfo>& out, int32_t parmsSize,
                       ChainScore& score) {
    out.clear();
    void* props = *(void**)((uint8_t*)fn + g_flayout.offChildProps);
    if (!props) return false;
    void* cur = props;
    int guard = 0;
    int32_t lastOffset = -1;
    while (cur && guard++ < 64) {
        PropertyInfo pi;
        if (!ReadNameAt(cur, lc.offName, pi.name)) { score.ok = -1; return false; }
        int32_t esz = *(int32_t*)((uint8_t*)cur + lc.offSize);
        int32_t off = *(int32_t*)((uint8_t*)cur + lc.offOffset);
        if (esz <= 0 || esz > 4096) return false;
        if (off < 0 || (parmsSize > 0 && off + esz > parmsSize + 32)) return false;
        if (off < lastOffset) return false;
        pi.prop = (FProperty*)cur;
        pi.size = esz;
        pi.offset = off;
        pi.type = "?";
        pi.structName = "";
        out.push_back(pi);
        lastOffset = off;
        score.ok++;
        cur = *(void**)((uint8_t*)cur + 0x20); // FField::Next @0x20（实测）
    }
    return !out.empty();
}

bool DescribeFunction(UFunction* fn, FunctionInfo& out) {
    if (!fn) return false;
    out.fn = fn;
    out.name = GetObjectName((UObject*)fn);
    out.fullName = GetFullPath((UObject*)fn);
    out.params.clear();

    int32_t parmsSize = *(uint16_t*)((uint8_t*)fn + g_flayout.offParmsSize);
    if (parmsSize <= 0 || parmsSize > 8192) parmsSize = 0;
    out.parmsSize = parmsSize;

    const LayoutCand cands[] = {
        { 0x28, 0x3C, 0x4C },   // 实测：FField Name@0x28, FProperty ElementSize@0x3C, Offset_Internal@0x4C
        { 0x18, 0x2C, 0x3C },   // 默认（UE5）
        { 0x18, 0x2C, 0x40 },
        { 0x18, 0x30, 0x44 },
        { 0x10, 0x24, 0x34 },
        { 0x20, 0x34, 0x44 },
    };
    int bestScore = -1;
    std::vector<PropertyInfo> best;
    for (auto& lc : cands) {
        ChainScore sc;
        std::vector<PropertyInfo> props;
        if (BuildProps(fn, lc, props, parmsSize, sc) && sc.ok > bestScore) {
            bestScore = sc.ok;
            best = props;
        }
    }
    out.params = best;
    return !best.empty() || parmsSize > 0;
}

// ---------------- 参数写入 ----------------
static void WriteFString(uint8_t* dst, const std::wstring& s) {
    // UE FString: { wchar_t* Data; int32 Num; int32 Max; }
    struct FStringRaw { wchar_t* Data; int32_t Num; int32_t Max; };
    size_t len = s.size();
    wchar_t* buf = (wchar_t*)HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, (len + 1) * sizeof(wchar_t));
    if (!buf) return;
    memcpy(buf, s.c_str(), len * sizeof(wchar_t));
    buf[len] = 0;
    FStringRaw* fs = (FStringRaw*)dst;
    fs->Data = buf;
    fs->Num = (int32_t)(len + 1);
    fs->Max = (int32_t)(len + 1);
}

static bool WriteArg(uint8_t* parms, const PropertyInfo& pi, const ArgValue& v) {
    uint8_t* dst = parms + pi.offset;
    switch (v.kind) {
    case ArgValue::STR:
        if (pi.size >= 16) { WriteFString(dst, v.sw); return true; }
        return false;
    case ArgValue::INT:
        if (pi.size == 1) { *(uint8_t*)dst = (uint8_t)v.i; return true; }
        if (pi.size == 2) { *(int16_t*)dst = (int16_t)v.i; return true; }
        if (pi.size == 4) { *(int32_t*)dst = (int32_t)v.i; return true; }
        if (pi.size == 8) { *(int64_t*)dst = v.i; return true; }
        return false;
    case ArgValue::FLOAT:
        if (pi.size == 8) { *(double*)dst = v.f; return true; }
        if (pi.size == 4) { *(float*)dst = (float)v.f; return true; }
        return false;
    case ArgValue::BOOL:
        if (pi.size >= 1) { *(uint8_t*)dst = v.b ? 1 : 0; return true; }
        return false;
    case ArgValue::NAME: {
        // FName（构造需要 pool；此处仅支持 index 直填）
        if (pi.size >= 8) { *(int32_t*)dst = (int32_t)v.i; *(uint32_t*)(dst + 4) = 0; return true; }
        return false;
    }
    case ArgValue::PTR:
        if (pi.size == 8) { *(void**)dst = v.p; return true; }
        return false;
    default:
        return false;
    }
}

typedef void (*ProcessEventFn)(UObject*, UFunction*, void*);

static bool Invoke(UObject* obj, UFunction* fn, void* parms) {
    if (!obj || !fn) return false;
    void** vt = *(void***)obj;
    if (!vt) return false;
    ProcessEventFn pe = (ProcessEventFn)vt[g_rt.processEventIndex];
    if (!pe) return false;
    pe(obj, fn, parms);
    return true;
}

static std::string Lower(std::string s) {
    for (auto& c : s) c = (char)tolower((unsigned char)c);
    return s;
}

bool CallFunction(UObject* obj, UFunction* fn,
                  const std::map<std::string, ArgValue>& args,
                  std::string* errOut) {
    FunctionInfo info;
    if (!DescribeFunction(fn, info)) {
        if (errOut) *errOut = "function layout unresolved: " + GetObjectName((UObject*)fn);
        return false;
    }
    int32_t parmsSize = info.parmsSize;
    if (parmsSize <= 0) {
        int32_t maxEnd = 0;
        for (auto& p : info.params) maxEnd = std::max(maxEnd, p.offset + p.size);
        parmsSize = maxEnd;
    }
    if (parmsSize <= 0) parmsSize = 64;

    uint8_t* parms = (uint8_t*)HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, parmsSize + 32);
    if (!parms) { if (errOut) *errOut = "alloc failed"; return false; }

    int filled = 0;
    for (auto& p : info.params) {
        std::string key = Lower(p.name);
        const ArgValue* v = nullptr;
        for (auto& kv : args) {
            if (Lower(kv.first) == key) { v = &kv.second; break; }
        }
        if (!v) continue;
        if (WriteArg(parms, p, *v)) ++filled;
    }
    if (filled == 0 && !args.empty()) {
        if (errOut) *errOut = "no parameter matched (fn=" + info.name + ")";
        HeapFree(GetProcessHeap(), 0, parms);
        return false;
    }
    bool ok = Invoke(obj, fn, parms);
    if (!ok && errOut) *errOut = "ProcessEvent failed";
    HeapFree(GetProcessHeap(), 0, parms);
    return ok;
}

bool CallOnObject(UObject* obj, const std::string& functionName,
                  const std::map<std::string, ArgValue>& args,
                  std::string* errOut) {
    UFunction* fn = nullptr;
    // 先在同类的函数表里找
    if (obj) {
        std::string clsName = GetClassName(obj);
        UObject* clsObj = FindFirstObjectOfClass("Class");
        (void)clsObj;
        // 直接全局查找同名函数
        fn = FindFunction(functionName);
        if (!fn) fn = FindFunction(clsName + "." + functionName);
    }
    if (!fn) { if (errOut) *errOut = "function not found: " + functionName; return false; }
    return CallFunction(obj, fn, args, errOut);
}

// ---------------- 高层封装 ----------------
static UObject* FindChatManager() {
    const char* names[] = { "SSChatManager", "SCUMGameSession", "GameMode", "SCUMGameMode" };
    for (const char* n : names) {
        UObject* o = FindFirstObjectOfClass(n);
        if (o) return o;
    }
    return nullptr;
}

bool BroadcastChat(const std::wstring& sender, const std::wstring& text,
                   int64_t senderId, const std::wstring& senderSteamId,
                   const std::string& chatType, std::string* err) {
    const char* fns[] = { "Chat_Server_BroadcastChatMessage", "BroadcastChatMessage",
                          "Server_BroadcastChatMessage", "SendChatMessage" };
    UObject* mgr = FindChatManager();
    if (!mgr) { if (err) *err = "chat manager not found"; return false; }

    std::map<std::string, ArgValue> args;
    ArgValue a;
    a.kind = ArgValue::STR; a.sw = text;      args["Message"] = a;  args["Text"] = a; args["ChatMessage"] = a;
    a.sw = sender;                             args["SenderName"] = a; args["PlayerName"] = a; args["Name"] = a;
    a.sw = senderSteamId;                      args["SteamId"] = a; args["SteamID"] = a; args["SenderSteamId"] = a;
    ArgValue n; n.kind = ArgValue::INT; n.i = senderId;
    args["SenderId"] = n; args["PlayerId"] = n; args["Sender"] = n;

    std::string localErr;
    for (const char* f : fns) {
        UFunction* fn = FindFunction(f);
        if (!fn) continue;
        if (CallFunction(mgr, fn, args, &localErr)) return true;
    }
    if (err) *err = "no usable chat function (" + localErr + ")";
    return false;
}

bool SendAnnouncement(const std::wstring& title, const std::wstring& body, std::string* err) {
    const char* fns[] = { "Multicast_DisplayNotification", "Multicast_ShowEventNotification",
                          "NetMulticast_RequestNotification", "Client_ShowNotification" };
    UObject* mgr = FindChatManager();
    if (!mgr) { if (err) *err = "manager not found"; return false; }
    std::map<std::string, ArgValue> args;
    ArgValue a; a.kind = ArgValue::STR; a.sw = title; args["Title"] = a; args["NotificationText"] = a; args["Text"] = a;
    ArgValue b; b.kind = ArgValue::STR; b.sw = body;  args["Body"] = b; args["Message"] = b; args["Description"] = b;
    std::string localErr;
    for (const char* f : fns) {
        UFunction* fn = FindFunction(f);
        if (!fn) continue;
        if (CallFunction(mgr, fn, args, &localErr)) return true;
    }
    if (err) *err = "no usable notification function (" + localErr + ")";
    return false;
}

bool GiveItem(const std::wstring& playerNameOrSteamId, const std::wstring& itemClass,
              int32_t amount, std::string* err) {
    const char* fns[] = { "AddItem", "Server_AddItem", "SpawnItemInInventory", "GiveItem" };
    std::map<std::string, ArgValue> args;
    ArgValue p; p.kind = ArgValue::STR; p.sw = playerNameOrSteamId;
    args["PlayerName"] = p; args["SteamId"] = p; args["Target"] = p; args["Player"] = p;
    ArgValue it; it.kind = ArgValue::STR; it.sw = itemClass;
    args["ItemClass"] = it; args["Item"] = it; args["ClassName"] = it;
    ArgValue n; n.kind = ArgValue::INT; n.i = amount;
    args["Amount"] = n; args["Count"] = n; args["Quantity"] = n;

    UObject* mgr = FindChatManager();
    if (!mgr) mgr = FindFirstObjectOfClass("SCUMGameMode");
    if (!mgr) { if (err) *err = "target object not found"; return false; }
    std::string localErr;
    for (const char* f : fns) {
        UFunction* fn = FindFunction(f);
        if (!fn) continue;
        if (CallFunction(mgr, fn, args, &localErr)) return true;
    }
    if (err) *err = "no usable item function (" + localErr + ")";
    return false;
}

} // namespace ue
