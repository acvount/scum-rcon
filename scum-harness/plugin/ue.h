// ue.h — Unreal Engine 5 reflection layer for SCUM dedicated server (Win64 Shipping)
// 目的：在 SCUMServer.exe 进程内定位 GObjects / GNamePool，按 UFunction 反射信息调用服务端函数。
#pragma once
#define NOMINMAX
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <string>
#include <vector>
#include <map>
#include <mutex>

namespace ue {

// ---------- 基础类型 ----------
struct FName {
    int32_t  ComparisonIndex;   // 0x00  FNameEntryId -> FNamePool
    uint32_t Number;            // 0x04  实例号
};

struct UObject;
struct UClass;
struct UFunction;
struct FProperty;

// FUObjectItem（UE5，x64）
struct FUObjectItem {
    UObject* Object;            // 0x00
    int32_t  Flags;             // 0x08
    int32_t  ClusterRootIndex;  // 0x0C
    int32_t  SerialNumber;      // 0x10
    int32_t  Pad;               // 0x14
};

// FChunkedFixedUObjectArray
struct FChunkedFixedUObjectArray {
    FUObjectItem** Objects;         // 0x00  chunk 指针数组
    FUObjectItem*  PreAllocatedObjects;
    int32_t        MaxElements;     // 0x10
    int32_t        NumElements;     // 0x14
    int32_t        MaxChunks;       // 0x18
    int32_t        NumChunks;       // 0x1C
    static const int32_t PerChunk = 64 * 1024;
};

// FUObjectArray
struct FUObjectArray {
    int32_t ObjFirstGCIndex;            // 0x00
    int32_t ObjLastNonGCIndex;          // 0x04
    int32_t MaxObjectsNotConsideredByGC;// 0x08
    int32_t OpenForDisregardForGC;      // 0x0C
    FChunkedFixedUObjectArray ObjObjects; // 0x10
};

// UObject（UE5 x64）
struct UObject {
    void**    VTable;           // 0x00
    int32_t   ObjectFlags;      // 0x08
    int32_t   InternalIndex;    // 0x0C
    UClass*   ClassPrivate;     // 0x10
    FName     NamePrivate;      // 0x18
    UObject*  OuterPrivate;     // 0x20
};

// UClass / UFunction 与 UObject 同布局起始
struct UClass : UObject {};
struct UFunction : UObject {};

// FNamePool（UE5）
struct FNamePool {
    uint32_t  Lock;             // 0x00  FRWLock
    uint32_t  CurrentBlock;     // 0x04
    uint32_t  CurrentByteCursor;// 0x08
    uint32_t  Pad;              // 0x0C
    uint8_t*  Blocks[8192];     // 0x10
};
static const uint32_t FNameMaxBlocks = 8192;

// ---------- 全局状态 ----------
struct Runtime {
    uintptr_t moduleBase = 0;
    size_t    moduleSize = 0;
    FUObjectArray* objects = nullptr;   // GUObjectArray 地址
    FNamePool*     names = nullptr;     // GNamePool 地址
    int32_t        processEventIndex = 68; // UObject vtable 中 ProcessEvent 的槽位
    bool ready = false;
};

extern Runtime g_rt;

// ---------- 基础工具 ----------
bool   Init(HMODULE self);
uintptr_t DiscoverNamePool();
uint8_t* GetNoneBlock();
int ScanBlockRefs(uintptr_t* outAddrs, uint64_t* outWords, int maxHits);
std::vector<std::pair<uint32_t, std::string>> FindNames(const std::string& needle, int maxHits);                                        // 定位全局结构
void   Log(const char* fmt, ...);
std::string FNameToString(const FName& n);
UObject* GetObjectByIndex(int32_t idx);
int32_t  NumObjects();

// ---------- 反射 ----------
struct PropertyInfo {
    FProperty* prop = nullptr;
    std::string name;
    std::string type;        // BoolProperty / StrProperty / IntProperty / ObjectProperty / StructProperty / ArrayProperty ...
    std::string structName;  // StructProperty / ObjectProperty 的类名
    int32_t offset = 0;      // 结构体内偏移（相对 Parms）
    int32_t size = 0;
    int32_t arrayDim = 1;
};

struct FunctionInfo {
    UFunction* fn = nullptr;
    std::string name;
    std::string fullName;
    int32_t parmsSize = 0;
    std::vector<PropertyInfo> params;
};

// UFunction 元数据（实测布局）
struct FunctionLayout {
    int32_t offFunctionFlags = 0xB0;   // uint32
    int32_t offNumParms      = 0xB4;   // uint8
    int32_t offParmsSize     = 0xB6;   // uint16
    int32_t offReturnOffset  = 0xB8;   // uint16
    int32_t offFunc          = 0xD8;   // FNativeFuncPtr
    int32_t offChildProps    = 0x50;   // FField* ChildProperties
};
extern FunctionLayout g_flayout;

bool DescribeFunction(UFunction* fn, FunctionInfo& out);
UFunction* FindFunction(const std::string& fullOrShortName);
UObject*   FindFirstObjectOfClass(const std::string& className);
std::vector<UObject*> FindAllObjectsOfClass(const std::string& className);
std::string GetObjectName(UObject* o);
std::string GetObjectNameFast(UObject* o);
std::string GetClassNameFast(UObject* o);
bool TryClassName(UObject* o, char* buf, size_t cap);
bool TryObjectName(UObject* o, char* buf, size_t cap);
bool DecodeNameById(uint32_t id, char* buf, size_t cap);
bool PtrReadable(const void* p, size_t len);
void RefreshRanges();
std::string GetClassName(UObject* o);
std::string GetFullPath(UObject* o);

// ---------- 调用 ----------
struct ArgValue {
    enum Kind { NONE, STR, INT, FLOAT, BOOL, NAME, PTR } kind = NONE;
    std::wstring sw;      // STR (UE FString 为 UTF-16)
    std::string  s;       // NAME
    int64_t  i = 0;
    double   f = 0;
    bool     b = false;
    void*    p = nullptr;
};

// 通过 UFunction 反射组装参数并 ProcessEvent
bool CallFunction(UObject* obj, UFunction* fn,
                  const std::map<std::string, ArgValue>& args,
                  std::string* errOut);

// 对类实例调用（按函数短名）
bool CallOnObject(UObject* obj, const std::string& functionName,
                  const std::map<std::string, ArgValue>& args,
                  std::string* errOut);

// 高层封装
bool BroadcastChat(const std::wstring& sender, const std::wstring& text,
                   int64_t senderId, const std::wstring& senderSteamId,
                   const std::string& chatType, std::string* err);
bool SendAnnouncement(const std::wstring& title, const std::wstring& body, std::string* err);
bool GiveItem(const std::wstring& playerNameOrSteamId, const std::wstring& itemClass,
              int32_t amount, std::string* err);

} // namespace ue
