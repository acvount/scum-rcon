// ue.cpp — UE5 runtime reflection bootstrap for SCUMServer.exe (Win64 Shipping)
#include "ue.h"
#include <psapi.h>
#include <cstdarg>
#include <algorithm>
#include <cctype>
#include <ctype.h>
#include <cstring>

#pragma comment(lib, "psapi.lib")

namespace ue {

Runtime g_rt;
FunctionLayout g_flayout;
static std::recursive_mutex g_initMutex;
static int g_headerSize = 2;   // 2 for classic FNameEntry, 4 when a probe hash prefix is present
// WITH_CASE_PRESERVING_NAME off (shipping): bIsWide:1 | ProbeHash:5 | Len:10  -> shift 6
// WITH_CASE_PRESERVING_NAME on:              bIsWide:1 | Len:15             -> shift 1
static int g_lenShift = 6;

static inline uint32_t NameLen(uint16_t header) {
    return (header >> g_lenShift) & (g_lenShift == 1 ? 0x7FFF : 0x3FF);
}

static FILE* g_logFile = nullptr;
static std::mutex g_logMutex;

void Log(const char* fmt, ...) {
    std::lock_guard<std::mutex> lk(g_logMutex);
    char buf[4096];
    va_list ap; va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);
    OutputDebugStringA(buf); OutputDebugStringA("\n");
    if (!g_logFile) {
        char path[MAX_PATH];
        GetModuleFileNameA(nullptr, path, MAX_PATH);
        std::string p(path);
        p = p.substr(0, p.find_last_of("\\/")) + "\\scum_harness.log";
        g_logFile = fopen(p.c_str(), "a");
    }
    if (g_logFile) { fprintf(g_logFile, "%s\n", buf); fflush(g_logFile); }
}

// ---------------- memory helpers ----------------
struct Range { uintptr_t lo, hi; };
static std::vector<Range> g_ranges;

static void BuildRanges() {
    g_ranges.clear();
    uintptr_t p = 0x10000;
    MEMORY_BASIC_INFORMATION mbi;
    while (VirtualQuery((void*)p, &mbi, sizeof(mbi))) {
        if (mbi.State == MEM_COMMIT && !(mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD)) && !(mbi.Protect & PAGE_NOACCESS))
            g_ranges.push_back({ (uintptr_t)mbi.BaseAddress, (uintptr_t)mbi.BaseAddress + mbi.RegionSize });
        uintptr_t next = (uintptr_t)mbi.BaseAddress + mbi.RegionSize;
        if (next <= p) break;
        p = next;
    }
}

static bool InRanges(const void* ptr, size_t len) {
    uintptr_t v = (uintptr_t)ptr;
    size_t lo = 0, hi = g_ranges.size();
    while (lo < hi) {
        size_t mid = (lo + hi) / 2;
        if (g_ranges[mid].hi <= v) lo = mid + 1;
        else hi = mid;
    }
    if (lo >= g_ranges.size()) return false;
    return v >= g_ranges[lo].lo && v + len <= g_ranges[lo].hi;
}

static bool ValidPtr(const void* p) { return InRanges(p, 1); }

void RefreshRanges() { BuildRanges(); }

static bool PlausiblePtr(const void* p) {
    uintptr_t v = (uintptr_t)p;
    return v >= 0x10000 && v < 0x7FFFFFFFFFFFull;
}

// ---------------- PE section lookup ----------------
static bool GetSectionRange(const char* name, uintptr_t& start, uintptr_t& end) {
    uint8_t* base = (uint8_t*)g_rt.moduleBase;
    IMAGE_DOS_HEADER* dos = (IMAGE_DOS_HEADER*)base;
    if (dos->e_magic != IMAGE_DOS_SIGNATURE) return false;
    IMAGE_NT_HEADERS* nt = (IMAGE_NT_HEADERS*)(base + dos->e_lfanew);
    if (nt->Signature != IMAGE_NT_SIGNATURE) return false;
    IMAGE_SECTION_HEADER* sec = IMAGE_FIRST_SECTION(nt);
    for (int i = 0; i < nt->FileHeader.NumberOfSections; ++i, ++sec) {
        char nm[9] = {0};
        memcpy(nm, sec->Name, 8);
        if (strcmp(nm, name) == 0) {
            start = (uintptr_t)base + sec->VirtualAddress;
            end = start + sec->Misc.VirtualSize;
            return true;
        }
    }
    return false;
}

// ---------------- pattern scan ----------------
struct Pattern { std::vector<int> bytes; };

static Pattern ParsePattern(const char* s) {
    Pattern p; const char* c = s;
    while (*c) {
        while (*c == ' ') ++c;
        if (!*c) break;
        if (c[0] == '?' && c[1] == '?') { p.bytes.push_back(-1); c += 2; }
        else { char h[3] = { c[0], c[1], 0 }; p.bytes.push_back((int)strtol(h, nullptr, 16)); c += 2; }
    }
    return p;
}

static uintptr_t ScanRipRelative(const Pattern& pat, int dispOffset, int instrLen, uintptr_t begin, uintptr_t end) {
    const size_t n = pat.bytes.size();
    for (uint8_t* p = (uint8_t*)begin; p + n < (uint8_t*)end; ++p) {
        bool ok = true;
        for (size_t i = 0; i < n; ++i) {
            if (pat.bytes[i] >= 0 && p[i] != (uint8_t)pat.bytes[i]) { ok = false; break; }
        }
        if (!ok) continue;
        int32_t disp = *(int32_t*)(p + dispOffset);
        uintptr_t target = (uintptr_t)(p + instrLen) + disp;
        if (PlausiblePtr((void*)target) && ValidPtr((void*)target)) return target;
    }
    return 0;
}

// ---------------- FName decoding ----------------
static bool DecodeEntry(FNamePool* pool, uint32_t id, char* out, size_t outLen) {
    if (!pool) return false;
    uint32_t block = id >> 16;
    uint32_t offset = (id & 0xFFFF) * 2;
    // FName blocks are 64 KiB; offset must stay inside one block and the pool
    // must expose at least that many block slots to be a candidate.
    if (block >= FNameMaxBlocks) return false;
    if (offset + 4 >= 65536) return false;
    uint8_t* blockPtr = pool->Blocks[block];
    if (!PlausiblePtr(blockPtr)) return false;
    // Validate the exact entry window: a block may end at a region boundary.
    if (!InRanges(blockPtr + offset, g_headerSize + 2)) return false;
    uint16_t header = *(uint16_t*)(blockPtr + offset);
    bool wide = (header & 1) != 0;
    uint32_t len = NameLen(header);
    if (len == 0 || len > 512) return false;
    if (offset + g_headerSize + len > 65536) return false;
    uint8_t* data = blockPtr + offset + g_headerSize;
    if (!InRanges(data, len)) return false;
    size_t n = len < outLen - 1 ? len : outLen - 1;
    if (!wide) {
        memcpy(out, data, n); out[n] = 0;
        for (size_t i = 0; i < n; ++i) {
            unsigned char c = (unsigned char)out[i];
            if (c < 0x20 || c > 0x7E) return false;
        }
    } else {
        uint16_t* w = (uint16_t*)data;
        for (size_t i = 0; i < n; ++i) out[i] = (char)(w[i] & 0x7F);
        out[n] = 0;
    }
    return true;
}

static bool IsIdentifier(const char* s) {
    size_t n = strlen(s);
    if (n == 0 || n > 128) return false;
    for (size_t i = 0; i < n; ++i) {
        unsigned char c = (unsigned char)s[i];
        if (!(isalnum(c) || c == '_' || c == '/' || c == '.' || c == '-')) return false;
    }
    return true;
}

std::string FNameToString(const FName& n) {
    char buf[1024];
    if (!DecodeEntry(g_rt.names, (uint32_t)n.ComparisonIndex, buf, sizeof(buf))) return "";
    if (n.Number > 0) {
        char full[1100];
        snprintf(full, sizeof(full), "%s_%u", buf, n.Number - 1);
        return std::string(full);
    }
    return std::string(buf);
}

// ---------------- GUObjectArray ----------------
static bool LooksLikeObjectArray(FUObjectArray* p) {
    FChunkedFixedUObjectArray& a = p->ObjObjects;
    int32_t num = a.NumElements, mx = a.MaxElements;
    if (num < 500 || num > 40000000) return false;
    if (mx < num || mx > 60000000) return false;
    if (!PlausiblePtr(a.Objects)) return false;
    if (!ValidPtr(a.Objects)) return false;
    FUObjectItem** chunks = a.Objects;
    if (!PlausiblePtr(chunks[0])) return false;
    if (!ValidPtr(chunks[0])) return false;
    UObject* first = chunks[0][0].Object;
    if (!PlausiblePtr(first)) return false;
    if (!ValidPtr(first)) return false;
    void** vt = *(void***)first;
    if (!PlausiblePtr(vt)) return false;
    uintptr_t v = (uintptr_t)vt;
    if (v < g_rt.moduleBase || v > g_rt.moduleBase + g_rt.moduleSize) return false;
    return true;
}

static bool FindObjectArrayBrute() {
    uintptr_t start = 0, end = 0;
    if (!GetSectionRange(".data", start, end)) return false;
    const int offsets[] = { 0x10, 0x18, 0x20, 0x08, 0x00 };
    uint32_t scanned = 0;
    for (uintptr_t p = start; p + 0x40 < end; p += 8) {
        ++scanned;
        for (int off : offsets) {
            int32_t num = *(int32_t*)(p + off + 0x14);
            if (num < 500 || num > 40000000) continue;
            FUObjectArray* cand = (FUObjectArray*)(p + off - 0x10);
            if (LooksLikeObjectArray(cand)) {
                g_rt.objects = cand;
                Log("[ue] GUObjectArray via brute scan at %p (off=0x%x, scanned=%u, num=%d)",
                    (void*)cand, off, scanned, cand->ObjObjects.NumElements);
                return true;
            }
        }
    }
    Log("[ue] brute scan exhausted (%u slots)", scanned);
    return false;
}

static bool FindObjectArraySig() {
    uintptr_t ts = 0, te = 0;
    if (!GetSectionRange(".text", ts, te)) return false;
    const char* pats[] = {
        "48 8B 05 ?? ?? ?? ?? 48 8B 0C C8",
        "48 8B 0D ?? ?? ?? ?? 48 8B 0C C8",
        "48 8B 05 ?? ?? ?? ?? 4C 8B 04 C8",
        "48 8B 0D ?? ?? ?? ?? 4C 8B 04 C9",
    };
    for (const char* s : pats) {
        uintptr_t addr = ScanRipRelative(ParsePattern(s), 3, 7, ts, te);
        if (!addr) continue;
        for (int delta = 0; delta <= 0x20; delta += 0x10) {
            FUObjectArray* cand = (FUObjectArray*)(addr - delta);
            if (LooksLikeObjectArray(cand)) {
                g_rt.objects = cand;
                Log("[ue] GUObjectArray via sig %s at %p", s, (void*)cand);
                return true;
            }
        }
    }
    return false;
}

// ---------------- GNamePool discovery (deterministic) ----------------
static FNamePool g_fakePool;
static uint8_t* g_noneBlock = nullptr;
uint8_t* GetNoneBlock() { return g_noneBlock; }

// Diagnostic: locate every word referencing the anchored block and dump the
// surrounding qwords so the real Blocks[] layout can be read off directly.
int ScanBlockRefs(uintptr_t* outAddrs, uint64_t* outWords, int maxHits) {
    int hits = 0;
    if (!g_noneBlock) return 0;
    uintptr_t ds = 0, de = 0;
    if (!GetSectionRange(".data", ds, de)) {
        ds = g_rt.moduleBase;
        de = g_rt.moduleBase + g_rt.moduleSize;
    }
    for (uintptr_t p = (ds + 7) & ~(uintptr_t)7; p + 8 <= de; p += 8) {
        if (*(uintptr_t*)p != (uintptr_t)g_noneBlock) continue;
        if (hits >= maxHits) break;
        outAddrs[hits] = p;
        for (int i = 0; i < 8; ++i) {
            if (InRanges((void*)(p + i * 8), 8)) outWords[hits * 8 + i] = *(uint64_t*)(p + i * 8);
            else outWords[hits * 8 + i] = 0;
        }
        ++hits;
    }
    return hits;
}

static int GetNumMountedBlocks() {
    int n = 0;
    for (int i = 0; i < 512; ++i) if (g_fakePool.Blocks[i]) ++n; else break;
    return n;
}
static bool DecodeEntryAt(uint8_t* block, uint32_t id, char* out, size_t outLen) {
    uint32_t offset = (id & 0xFFFF) * 2;
    if (offset + 8 >= 65536) return false;
    uint16_t header = *(uint16_t*)(block + offset);
    bool wide = (header & 1) != 0;
    uint32_t len = NameLen(header);
    if (len == 0 || len > 512) return false;
    const uint8_t* data = block + offset + g_headerSize;
    size_t n = len < outLen - 1 ? len : outLen - 1;
    if (!wide) {
        memcpy(out, data, n); out[n] = 0;
        for (size_t i = 0; i < n; ++i) {
            unsigned char c = (unsigned char)out[i];
            if (c < 0x20 || c > 0x7E) return false;
        }
    } else {
        const uint16_t* w = (const uint16_t*)data;
        for (size_t i = 0; i < n; ++i) out[i] = (char)(w[i] & 0x7F);
        out[n] = 0;
    }
    return true;
}

// UE creates names in a fixed order: None, ByteProperty, IntProperty, ...
// Verifying that prefix proves a candidate is the first FName block.
static bool ValidateNoneBlock(uint8_t* base, int headerSize, bool verbose) {
    static const char* expect[] = { "None", "ByteProperty", "IntProperty", "BoolProperty", "FloatProperty" };
    uint32_t off = 0;
    for (int i = 0; i < 5; ++i) {
        if (off + headerSize + 4 >= 65536) return false;
        uint16_t h = *(uint16_t*)(base + off);
        bool wide = (h & 1) != 0;
        uint32_t len = NameLen(h);
        if (len == 0 || len > 128) return false;
        char nm[256];
        if (!wide) {
            memcpy(nm, base + off + headerSize, len);
            nm[len] = 0;
        } else {
            const uint16_t* w = (const uint16_t*)(base + off + headerSize);
            for (uint32_t k = 0; k < len; ++k) nm[k] = (char)(w[k] & 0x7F);
            nm[len] = 0;
        }
        if (verbose && i < 3) Log("[ue]   entry%d = '%s'", i, nm);
        if (strcmp(nm, expect[i]) != 0) return false;
        off += headerSize + (wide ? len * 2 : len);
        off = (off + 1) & ~1u;
    }
    return true;
}

// A genuine FName block decodes a chain of identifiers from offset 0.
static bool ValidateBlockPrefixN(uint8_t* base, int count) {
    uint32_t off = 0;
    for (int i = 0; i < count; ++i) {
        if (off + 8 >= 65536) return false;
        uint16_t h = *(uint16_t*)(base + off);
        bool wide = (h & 1) != 0;
        uint32_t len = NameLen(h);
        if (len == 0 || len > 200) return false;
        char nm[256];
        if (!wide) {
            memcpy(nm, base + off + g_headerSize, len);
            nm[len] = 0;
        } else {
            const uint16_t* w = (const uint16_t*)(base + off + g_headerSize);
            for (uint32_t k = 0; k < len; ++k) nm[k] = (char)(w[k] & 0x7F);
            nm[len] = 0;
        }
        if (!IsIdentifier(nm)) return false;
        off += g_headerSize + (wide ? len * 2 : len);
        off = (off + 1) & ~1u;
    }
    return true;
}

static bool ValidateBlockPrefix(uint8_t* base) { return ValidateBlockPrefixN(base, 8); }

static uint8_t* FindNoneBlock() {
    g_lenShift = 6;
    g_headerSize = 2;
    for (auto& r : g_ranges) {
        if (r.hi - r.lo < 4096) continue;
        uint8_t* p = (uint8_t*)r.lo;
        uint8_t* end = (uint8_t*)r.hi;
        while (p + 4 < end) {
            uint8_t* hit = (uint8_t*)memchr(p, 'N', (size_t)(end - p));
            if (!hit || hit + 4 > end) break;
            for (int hs = 2; hs <= 4; hs += 2) {
                for (int sh = 6; sh >= 1; sh -= 5) {
                    if (hit - (uint8_t*)r.lo < hs) continue;
                    uint8_t* base = hit - hs;
                    g_lenShift = sh;
                    g_headerSize = hs;
                    if (NameLen(*(uint16_t*)base) != 4) continue;
                    if (ValidateNoneBlock(base, hs, false)) {
                        Log("[ue] discover: header size %d lenShift %d", hs, sh);
                        return base;
                    }
                }
            }
            g_lenShift = 6; g_headerSize = 2;
            p = hit + 1;
        }
    }
    return nullptr;
}

// Walk every FName entry and return (id, name) pairs containing the substring.
std::vector<std::pair<uint32_t, std::string>> FindNames(const std::string& needle, int maxHits) {
    std::vector<std::pair<uint32_t, std::string>> out;
    if (!g_rt.names) return out;
    for (int b = 0; b < 8192; ++b) {
        uint8_t* base = g_rt.names->Blocks[b];
        if (!base) break;
        if (!InRanges(base, 16)) break;
        uint32_t off = 0;
        while (off + 8 < 65536) {
            if (!InRanges(base + off, g_headerSize + 2)) break;
            uint16_t h = *(uint16_t*)(base + off);
            bool wide = (h & 1) != 0;
            uint32_t len = NameLen(h);
            if (len == 0 || len > 512) { off += 2; continue; }   // resync on bad header
            char nm[520];
            if (wide) {
                if (!InRanges(base + off + g_headerSize, len * 2)) break;
                const uint16_t* w = (const uint16_t*)(base + off + g_headerSize);
                for (uint32_t k = 0; k < len; ++k) nm[k] = (char)(w[k] & 0x7F);
                nm[len] = 0;
            } else {
                if (!InRanges(base + off + g_headerSize, len)) break;
                memcpy(nm, base + off + g_headerSize, len);
                nm[len] = 0;
            }
            if ((needle.empty() || strstr(nm, needle.c_str())) && IsIdentifier(nm)) {
                out.push_back({ (uint32_t)((b << 16) | (off / 2)), std::string(nm) });
                if ((int)out.size() >= maxHits) return out;
            }
            off += g_headerSize + (wide ? len * 2 : len);
            off = (off + 1) & ~1u;
        }
    }
    return out;
}

// Deterministic: find the qword in .data whose pointee is the first FName block.
// The pointee is accepted only when its prefix matches the fixed UE name order.
static uintptr_t FindBlocksArraySlot() {
    uintptr_t ds = 0, de = 0;
    if (!GetSectionRange(".data", ds, de)) return 0;
    for (uintptr_t p = (ds + 7) & ~(uintptr_t)7; p + 8 <= de; p += 8) {
        uint8_t* b = *(uint8_t**)p;
        if (!b || !PlausiblePtr(b)) continue;
        if (!InRanges(b, 32)) continue;
        for (int sh = 6; sh >= 1; sh -= 5) {
            for (int hs = 2; hs <= 4; hs += 2) {
                g_lenShift = sh;
                g_headerSize = hs;
                if (ValidateNoneBlock(b, hs, false)) return p;
            }
        }
    }
    g_lenShift = 6;
    g_headerSize = 2;
    return 0;
}

// Mount the real block array by finding the word that references the "None" block.
static bool MountBlocksArray(uint8_t* noneBlk, std::map<uint32_t, std::vector<uint32_t>>& byBlock) {
    int total = 0;
    for (auto& kv : byBlock) total += (int)kv.second.size();
    uintptr_t ds = 0, de = 0;
    if (!GetSectionRange(".data", ds, de)) return false;
    // GNamePool is a static global: its Blocks[] array lives in .data and is the
    // only place referencing the anchored first block.
    for (uintptr_t p = (ds + 7) & ~(uintptr_t)7; p + 8 <= de; p += 8) {
        if (*(uintptr_t*)p != (uintptr_t)noneBlk) continue;
        static FNamePool s_tmp;
        memset(&s_tmp, 0, sizeof(s_tmp));
        int have = 0;
        for (int i = 0; i < 8192; ++i) {
            if (!InRanges((void*)(p + i * 8), 8)) break;
            uint8_t* b = *(uint8_t**)(p + i * 8);
            if (!b || !PlausiblePtr(b) || !InRanges(b, 16)) break;
            s_tmp.Blocks[i] = b;
            ++have;
        }
        if (have < 4) continue;
        int ok = 0;
        for (auto& kv : byBlock) {
            for (uint32_t id : kv.second) {
                char buf[512];
                if (DecodeEntry(&s_tmp, id, buf, sizeof(buf)) && IsIdentifier(buf)) ++ok;
            }
        }
        Log("[ue] discover: MSM blocks @%p have=%d ok=%d/%d", (void*)p, have, ok, total);
        if (total > 0 && ok * 10 < total * 9) continue;   // require >=90% samples
        g_fakePool = s_tmp;
        g_rt.names = &g_fakePool;
        return true;
    }
    return false;
}

// Map every sampled FName block index to its 64 KiB block by scanning memory,
// then mount the mapping into a local pool. No assumption about FNamePool layout.
uintptr_t DiscoverNamePool() {
    std::lock_guard<std::recursive_mutex> initLock(g_initMutex);
    {
        uintptr_t slot = FindBlocksArraySlot();
        if (slot) {
            static FNamePool s_pool;
            memset(&s_pool, 0, sizeof(s_pool));
            int have = 0;
            for (int i = 0; i < 8192; ++i) {
                if (!InRanges((void*)(slot + i * 8), 8)) break;
                uint8_t* b = *(uint8_t**)(slot + i * 8);
                if (!b || !PlausiblePtr(b) || !InRanges(b, 16)) break;
                s_pool.Blocks[i] = b;
                ++have;
            }
            if (have >= 4) {
                g_fakePool = s_pool;
                g_rt.names = &g_fakePool;
                g_noneBlock = (uint8_t*)*(uintptr_t*)slot;
                Log("[ue] GNamePool.Blocks @%p blocks=%d (lenShift=%d header=%d) block0=%p",
                    (void*)slot, have, g_lenShift, g_headerSize, (void*)g_noneBlock);
                return (uintptr_t)&g_fakePool;
            }
            Log("[ue] blocks slot @%p rejected (have=%d)", (void*)slot, have);
        } else {
            Log("[ue] blocks array slot not found in .data");
        }
    }
    // collect samples grouped by FName block index so the pool must satisfy every block
    std::map<uint32_t, std::vector<uint32_t>> byBlock;
    for (int i = 0; i < 400000 && byBlock.size() < 96; ++i) {
        UObject* o = GetObjectByIndex(i);
        if (!PlausiblePtr(o)) continue;
        uint32_t id = (uint32_t)o->NamePrivate.ComparisonIndex;
        if (id <= 0) continue;
        uint32_t blk = id >> 16;
        if (blk >= 96) continue;
        auto& v = byBlock[blk];
        if (v.size() < 3) v.push_back(id);
    }
    std::vector<uint32_t> ids;
    for (auto& kv : byBlock) for (uint32_t v : kv.second) ids.push_back(v);
    Log("[ue] discover: %zu sample ids across %zu blocks", ids.size(), byBlock.size());
    if (byBlock.empty()) return 0;

    // Anchor block 0 on the literal "None" entry: it is the first FName ever created
    // and therefore sits at offset 0 of block 0. This is a hard UE invariant.
    const int kMaxBlocks = 128;
    static uint8_t* s_map[kMaxBlocks];
    for (int i = 0; i < kMaxBlocks; ++i) s_map[i] = nullptr;
    int mapped = 0;
    uint8_t* noneBlk = FindNoneBlock();
    g_noneBlock = noneBlk;
    if (noneBlk) {
        s_map[0] = noneBlk;
        ++mapped;
        Log("[ue] discover: None block0=%p (validated prefix)", (void*)noneBlk);
    }
    if (!s_map[0]) { Log("[ue] discover: None anchor not found"); return 0; }
    if (MountBlocksArray(noneBlk, byBlock)) {
        Log("[ue] discover: mounted real block array (%u entries via anchor)", GetNumMountedBlocks());
        return (uintptr_t)&g_fakePool;
    }
    for (auto& r : g_ranges) {
        if (r.hi - r.lo < 0x10000) continue;
        for (uintptr_t a = (r.lo + 0xFFFF) & ~(uintptr_t)0xFFFF; a + 0x10000 <= r.hi; a += 0x10000) {
            uint8_t* cand = (uint8_t*)a;
            if (!InRanges(cand, 0x10000)) continue;
            if (!ValidateBlockPrefix(cand)) continue;   // cheap reject before sample matching
            for (auto& kv : byBlock) {
                uint32_t b = kv.first;
                if (b >= (uint32_t)kMaxBlocks || s_map[b]) continue;
                bool all = true;
                for (uint32_t id : kv.second) {
                    char buf[512];
                    if (!DecodeEntryAt(cand, id, buf, sizeof(buf))) { all = false; break; }
                    if (!IsIdentifier(buf)) { all = false; break; }
                }
                if (!all) continue;
                if (!ValidateBlockPrefix(cand)) continue;
                bool taken = false;
                for (int i = 0; i < kMaxBlocks; ++i) if (s_map[i] == cand) { taken = true; break; }
                if (taken) continue;
                s_map[b] = cand;
                ++mapped;
                Log("[ue] discover: block %u -> %p", b, (void*)cand);
            }
        }
    }
    Log("[ue] discover: mapped %d blocks, block0=%p", mapped, (void*)s_map[0]);

    memset(&g_fakePool, 0, sizeof(g_fakePool));
    for (int i = 0; i < kMaxBlocks; ++i) g_fakePool.Blocks[i] = s_map[i];
    if (noneBlk) g_fakePool.Blocks[0] = noneBlk;   // anchored, never overwritten
    g_rt.names = &g_fakePool;
    if (!ValidateNoneBlock(g_fakePool.Blocks[0], g_headerSize, true)) {
        Log("[ue] discover: anchored block failed prefix recheck");
        g_rt.names = nullptr;
        return 0;
    }
    {
        char nb[512];
        if (!DecodeEntry(&g_fakePool, byBlock[0][0], nb, sizeof(nb))) {
            Log("[ue] discover: sanity decode failed");
            return 0;
        }
        Log("[ue] discover: sample name '%s'", nb);
    }
    return (uintptr_t)&g_fakePool;

    return 0;
}

// ---------------- GNamePool discovery ----------------
// The first entry of a UE5 FName block is "None"; locating a pointer to such a
// block identifies GNamePool without needing any sample object ids.
static bool FindNamePoolByNoneEntry() {
    uint8_t* base = (uint8_t*)g_rt.moduleBase;
    IMAGE_DOS_HEADER* dos = (IMAGE_DOS_HEADER*)base;
    if (dos->e_magic != IMAGE_DOS_SIGNATURE) return false;
    IMAGE_NT_HEADERS* nt = (IMAGE_NT_HEADERS*)(base + dos->e_lfanew);
    IMAGE_SECTION_HEADER* sec = IMAGE_FIRST_SECTION(nt);
    const int slotOffs[] = { 0x10, 0x18, 0x08, 0x20, 0x28 };
    for (int s = 0; s < nt->FileHeader.NumberOfSections; ++s, ++sec) {
        char nm[9] = {0};
        memcpy(nm, sec->Name, 8);
        uintptr_t start = (uintptr_t)base + sec->VirtualAddress;
        uintptr_t end = start + sec->Misc.VirtualSize;
        Log("[ue] section %s start=0x%llx size=0x%llx", nm,
            (unsigned long long)start, (unsigned long long)(end - start));
        if (end <= start || end - start > 0x10000000) continue;
        for (uintptr_t p = start; p + 0x240 < end; p += 8) {
            for (int so : slotOffs) {
                uint8_t* b0 = *(uint8_t**)(p + so);
                if (!PlausiblePtr(b0) || (uintptr_t)b0 < 0x100000) continue;
                if (!ValidPtr(b0)) continue;
                uint16_t h = *(uint16_t*)b0;
                if ((h & 1) != 0) continue;
                if ((h >> 1) != 4) continue;
                if (memcmp(b0 + 2, "None", 4) != 0) continue;
                FNamePool* cand = (FNamePool*)(p + so - 0x10);
                g_rt.names = cand;
                Log("[ue] GNamePool via None-entry at %p (module+0x%llx, slot=0x%x)", (void*)cand,
                    (unsigned long long)((uintptr_t)cand - g_rt.moduleBase), so);
                return true;
            }
        }
    }
    return false;
}

// ---------------- GNamePool calibration ----------------
static bool CalibrateNamePool() {
    if (!g_rt.objects) return false;
    std::vector<uint32_t> ids;
    for (int i = 0; i < 4096 && ids.size() < 12; ++i) {
        UObject* o = GetObjectByIndex(i);
        if (!PlausiblePtr(o) || !ValidPtr(o)) continue;
        UClass* cls = o->ClassPrivate;
        if (!PlausiblePtr(cls) || !ValidPtr(cls)) continue;
        uint32_t id = (uint32_t)cls->NamePrivate.ComparisonIndex;
        if (id) ids.push_back(id);
    }
    if (ids.empty()) { Log("[ue] name calibration: no samples"); return false; }

    uintptr_t start = 0, end = 0;
    if (!GetSectionRange(".data", start, end)) return false;
    uint32_t scanned = 0;
    for (uintptr_t p = start; p + 0x260 < end; p += 8) {
        ++scanned;
        uint8_t* b0 = *(uint8_t**)(p + 0x10);
        if (!PlausiblePtr(b0) || (uintptr_t)b0 < 0x100000) continue;
        FNamePool* cand = (FNamePool*)p;
        if (cand->CurrentBlock > 256) continue;
        if (!ValidPtr(b0)) continue;
        char buf[256];
        int ok = 0;
        for (uint32_t id : ids) {
            if (!DecodeEntry(cand, id, buf, sizeof(buf))) break;
            if (!IsIdentifier(buf)) break;
            ++ok;
        }
        if (ok < (int)ids.size()) continue;
        // 强校验：类名必须命中已知集合
        bool strong = false;
        const char* known[] = { "Class","Function","Package","ScriptStruct","BlueprintGeneratedClass",
                                "Object","World","Level","Struct","Enum","Property","IntProperty" };
        for (uint32_t id : ids) {
            char nb[256];
            if (!DecodeEntry(cand, id, nb, sizeof(nb))) continue;
            for (const char* k : known) if (strcmp(nb, k) == 0) { strong = true; break; }
            if (strong) break;
        }
        if (!strong) continue;
        g_rt.names = cand;
        Log("[ue] GNamePool at %p (module+0x%llx, scanned=%u)", (void*)cand,
            (unsigned long long)((uintptr_t)cand - g_rt.moduleBase), scanned);
        return true;
    }
    Log("[ue] name calibration failed (%u slots)", scanned);
    return false;
}

// ---------------- public ----------------
UObject* GetObjectByIndex(int32_t idx) {
    if (!g_rt.objects || idx < 0) return nullptr;
    FChunkedFixedUObjectArray& a = g_rt.objects->ObjObjects;
    if (idx >= a.NumElements) return nullptr;
    if (!a.Objects) return nullptr;
    if (!InRanges(a.Objects, sizeof(void*))) return nullptr;
    uintptr_t chunkSlot = (uintptr_t)(a.Objects + idx / FChunkedFixedUObjectArray::PerChunk);
    if (!InRanges((void*)chunkSlot, sizeof(void*))) return nullptr;
    FUObjectItem* chunk = *(FUObjectItem**)chunkSlot;
    if (!chunk) return nullptr;
    uintptr_t itemAddr = (uintptr_t)(chunk + (idx % FChunkedFixedUObjectArray::PerChunk));
    if (!InRanges((void*)itemAddr, sizeof(FUObjectItem))) return nullptr;
    UObject* obj = ((FUObjectItem*)itemAddr)->Object;
    if (!obj || !InRanges(obj, sizeof(UObject))) return nullptr;
    return obj;
}

int32_t NumObjects() {
    if (!g_rt.objects) return 0;
    return g_rt.objects->ObjObjects.NumElements;
}

std::string GetObjectName(UObject* o) {
    if (!PlausiblePtr(o)) return "";
    return FNameToString(o->NamePrivate);
}
std::string GetClassName(UObject* o) {
    if (!PlausiblePtr(o)) return "";
    UClass* c = o->ClassPrivate;
    if (!PlausiblePtr(c)) return "";
    return FNameToString(c->NamePrivate);
}

std::string GetObjectNameFast(UObject* o) {
    if (!PlausiblePtr(o)) return "";
    return FNameToString(o->NamePrivate);
}
std::string GetClassNameFast(UObject* o) {
    if (!PlausiblePtr(o)) return "";
    UClass* c = o->ClassPrivate;
    if (!PlausiblePtr(c)) return "";
    return FNameToString(c->NamePrivate);
}
std::string GetFullPath(UObject* o) {
    std::vector<std::string> parts;
    UObject* cur = o; int guard = 0;
    while (PlausiblePtr(cur) && guard++ < 32) {
        std::string n = GetObjectName(cur);
        if (n.empty()) break;
        parts.push_back(n);
        cur = cur->OuterPrivate;
    }
    std::string out;
    for (auto it = parts.rbegin(); it != parts.rend(); ++it) { if (!out.empty()) out += "."; out += *it; }
    return out;
}

bool Init(HMODULE self) {
    std::lock_guard<std::recursive_mutex> initLock(g_initMutex);
    g_rt.moduleBase = (uintptr_t)GetModuleHandleA(nullptr);
    MODULEINFO mi{};
    GetModuleInformation(GetCurrentProcess(), (HMODULE)g_rt.moduleBase, &mi, sizeof(mi));
    g_rt.moduleSize = mi.SizeOfImage;
    BuildRanges();
    Log("[ue] module base=%p size=0x%llx ranges=%zu", (void*)g_rt.moduleBase,
        (unsigned long long)g_rt.moduleSize, g_ranges.size());

    if (!FindObjectArraySig() && !FindObjectArrayBrute()) {
        Log("[ue] GUObjectArray missing");
        return false;
    }
    if (!DiscoverNamePool() && !FindNamePoolByNoneEntry()) return false;
    g_rt.ready = true;
    Log("[ue] init ok. objects=%d", NumObjects());
    return true;
}

// Exception-safe name readers: no C++ objects inside __try, so no unwind conflict.
bool TryClassName(UObject* o, char* buf, size_t cap) {
    buf[0] = 0;
    __try {
        if (!PlausiblePtr(o)) return false;
        UClass* c = o->ClassPrivate;
        if (!PlausiblePtr(c)) return false;
        return DecodeEntry(g_rt.names, (uint32_t)c->NamePrivate.ComparisonIndex, buf, cap);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
}

bool TryObjectName(UObject* o, char* buf, size_t cap) {
    buf[0] = 0;
    __try {
        if (!PlausiblePtr(o)) return false;
        return DecodeEntry(g_rt.names, (uint32_t)o->NamePrivate.ComparisonIndex, buf, cap);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
}

bool PtrReadable(const void* p, size_t len) { return InRanges(p, len); }

bool DecodeNameById(uint32_t id, char* buf, size_t cap) {
    buf[0] = 0;
    return DecodeEntry(g_rt.names, id, buf, cap);
}

UObject* FindFirstObjectOfClass(const std::string& className) {
    int32_t n = NumObjects();
    for (int32_t i = 0; i < n; ++i) {
        UObject* o = GetObjectByIndex(i);
        if (!PlausiblePtr(o)) continue;
        if (GetClassNameFast(o) == className) return o;
    }
    return nullptr;
}

std::vector<UObject*> FindAllObjectsOfClass(const std::string& className) {
    std::vector<UObject*> out;
    int32_t n = NumObjects();
    for (int32_t i = 0; i < n; ++i) {
        UObject* o = GetObjectByIndex(i);
        if (!PlausiblePtr(o)) continue;
        if (GetClassNameFast(o) == className) out.push_back(o);
    }
    return out;
}

UFunction* FindFunction(const std::string& name) {
    int32_t n = NumObjects();
    char cls[256], nm[512];
    for (int32_t i = 0; i < n; ++i) {
        UObject* o = GetObjectByIndex(i);
        if (!o) continue;
        if (!TryClassName(o, cls, sizeof(cls))) continue;
        if (strcmp(cls, "Function") != 0) continue;
        if (!TryObjectName(o, nm, sizeof(nm))) continue;
        if (name == nm) return (UFunction*)o;
    }
    return nullptr;
}

} // namespace ue
