// auto-generated: forwarder storage + resolver
#include <windows.h>
#include <string.h>

extern "C" {
extern void* p_DllCanUnloadNow;
extern void* p_DllGetClassObject;
extern void* p_DwmAttachMilContent;
extern void* p_DwmDefWindowProc;
extern void* p_DwmDetachMilContent;
extern void* p_DwmEnableBlurBehindWindow;
extern void* p_DwmEnableComposition;
extern void* p_DwmEnableMMCSS;
extern void* p_DwmExtendFrameIntoClientArea;
extern void* p_DwmFlush;
extern void* p_DwmGetColorizationColor;
extern void* p_DwmGetCompositionTimingInfo;
extern void* p_DwmGetGraphicsStreamClient;
extern void* p_DwmGetGraphicsStreamTransformHint;
extern void* p_DwmGetTransportAttributes;
extern void* p_DwmGetUnmetTabRequirements;
extern void* p_DwmGetWindowAttribute;
extern void* p_DwmInvalidateIconicBitmaps;
extern void* p_DwmIsCompositionEnabled;
extern void* p_DwmModifyPreviousDxFrameDuration;
extern void* p_DwmQueryThumbnailSourceSize;
extern void* p_DwmRegisterThumbnail;
extern void* p_DwmRenderGesture;
extern void* p_DwmSetDxFrameDuration;
extern void* p_DwmSetIconicLivePreviewBitmap;
extern void* p_DwmSetIconicThumbnail;
extern void* p_DwmSetPresentParameters;
extern void* p_DwmSetWindowAttribute;
extern void* p_DwmShowContact;
extern void* p_DwmTetherContact;
extern void* p_DwmTetherTextContact;
extern void* p_DwmTransitionOwnedWindow;
extern void* p_DwmUnregisterThumbnail;
extern void* p_DwmUpdateThumbnailProperties;
extern void* p_DwmpAllocateSecurityDescriptor;
extern void* p_DwmpDxGetWindowSharedSurface;
extern void* p_DwmpDxUpdateWindowSharedSurface;
extern void* p_DwmpDxgiIsThreadDesktopComposited;
extern void* p_DwmpEnableDDASupport;
extern void* p_DwmpFreeSecurityDescriptor;
extern void* p_DwmpGetColorizationParameters;
extern void* p_DwmpRenderFlick;
extern void* p_DwmpSetColorizationParameters;
extern void* p_DwmpUpdateProxyWindowForCapture;
}

static const char* kExportNames[] = {
    "DllCanUnloadNow",
    "DllGetClassObject",
    "DwmAttachMilContent",
    "DwmDefWindowProc",
    "DwmDetachMilContent",
    "DwmEnableBlurBehindWindow",
    "DwmEnableComposition",
    "DwmEnableMMCSS",
    "DwmExtendFrameIntoClientArea",
    "DwmFlush",
    "DwmGetColorizationColor",
    "DwmGetCompositionTimingInfo",
    "DwmGetGraphicsStreamClient",
    "DwmGetGraphicsStreamTransformHint",
    "DwmGetTransportAttributes",
    "DwmGetUnmetTabRequirements",
    "DwmGetWindowAttribute",
    "DwmInvalidateIconicBitmaps",
    "DwmIsCompositionEnabled",
    "DwmModifyPreviousDxFrameDuration",
    "DwmQueryThumbnailSourceSize",
    "DwmRegisterThumbnail",
    "DwmRenderGesture",
    "DwmSetDxFrameDuration",
    "DwmSetIconicLivePreviewBitmap",
    "DwmSetIconicThumbnail",
    "DwmSetPresentParameters",
    "DwmSetWindowAttribute",
    "DwmShowContact",
    "DwmTetherContact",
    "DwmTetherTextContact",
    "DwmTransitionOwnedWindow",
    "DwmUnregisterThumbnail",
    "DwmUpdateThumbnailProperties",
    "DwmpAllocateSecurityDescriptor",
    "DwmpDxGetWindowSharedSurface",
    "DwmpDxUpdateWindowSharedSurface",
    "DwmpDxgiIsThreadDesktopComposited",
    "DwmpEnableDDASupport",
    "DwmpFreeSecurityDescriptor",
    "DwmpGetColorizationParameters",
    "DwmpRenderFlick",
    "DwmpSetColorizationParameters",
    "DwmpUpdateProxyWindowForCapture",
};
static void** kSlots[] = {
    (void**)&p_DllCanUnloadNow,
    (void**)&p_DllGetClassObject,
    (void**)&p_DwmAttachMilContent,
    (void**)&p_DwmDefWindowProc,
    (void**)&p_DwmDetachMilContent,
    (void**)&p_DwmEnableBlurBehindWindow,
    (void**)&p_DwmEnableComposition,
    (void**)&p_DwmEnableMMCSS,
    (void**)&p_DwmExtendFrameIntoClientArea,
    (void**)&p_DwmFlush,
    (void**)&p_DwmGetColorizationColor,
    (void**)&p_DwmGetCompositionTimingInfo,
    (void**)&p_DwmGetGraphicsStreamClient,
    (void**)&p_DwmGetGraphicsStreamTransformHint,
    (void**)&p_DwmGetTransportAttributes,
    (void**)&p_DwmGetUnmetTabRequirements,
    (void**)&p_DwmGetWindowAttribute,
    (void**)&p_DwmInvalidateIconicBitmaps,
    (void**)&p_DwmIsCompositionEnabled,
    (void**)&p_DwmModifyPreviousDxFrameDuration,
    (void**)&p_DwmQueryThumbnailSourceSize,
    (void**)&p_DwmRegisterThumbnail,
    (void**)&p_DwmRenderGesture,
    (void**)&p_DwmSetDxFrameDuration,
    (void**)&p_DwmSetIconicLivePreviewBitmap,
    (void**)&p_DwmSetIconicThumbnail,
    (void**)&p_DwmSetPresentParameters,
    (void**)&p_DwmSetWindowAttribute,
    (void**)&p_DwmShowContact,
    (void**)&p_DwmTetherContact,
    (void**)&p_DwmTetherTextContact,
    (void**)&p_DwmTransitionOwnedWindow,
    (void**)&p_DwmUnregisterThumbnail,
    (void**)&p_DwmUpdateThumbnailProperties,
    (void**)&p_DwmpAllocateSecurityDescriptor,
    (void**)&p_DwmpDxGetWindowSharedSurface,
    (void**)&p_DwmpDxUpdateWindowSharedSurface,
    (void**)&p_DwmpDxgiIsThreadDesktopComposited,
    (void**)&p_DwmpEnableDDASupport,
    (void**)&p_DwmpFreeSecurityDescriptor,
    (void**)&p_DwmpGetColorizationParameters,
    (void**)&p_DwmpRenderFlick,
    (void**)&p_DwmpSetColorizationParameters,
    (void**)&p_DwmpUpdateProxyWindowForCapture,
};

void InitDwmapiForwarders(HMODULE self) {
    // Prefer a renamed copy in the app directory: loading "dwmapi.dll" by path
    // would resolve to this proxy itself because the base name is already loaded.
    HMODULE real = LoadLibraryA("dwmapi_orig.dll");
    if (!real) {
        char sys[MAX_PATH] = {0};
        GetSystemDirectoryA(sys, MAX_PATH);
        strcat_s(sys, MAX_PATH, "\\dwmapi.dll");
        real = LoadLibraryA(sys);
    }
    if (!real) return;
    for (size_t i = 0; i < sizeof(kExportNames)/sizeof(kExportNames[0]); ++i) {
        *kSlots[i] = (void*)GetProcAddress(real, kExportNames[i]);
    }
}
