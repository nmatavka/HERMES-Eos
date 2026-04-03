#ifndef EUDORA_XCODE_PREFIX_H
#define EUDORA_XCODE_PREFIX_H

#define EUDORA_XCODE_BUILD 1
#define TARGET_API_MAC_CARBON 1

#include "Editor/Source/Precompiled headers/MacHeaders.c"

/*
 * Pull in the historical config first, then selectively remove the pieces that
 * no longer exist in the open tree or on the High Sierra build host.
 */
#include "conf.h"

#ifdef ADWARE
#undef ADWARE
#endif

#ifdef NAG
#undef NAG
#endif

#ifdef WINTERTREE
#undef WINTERTREE
#endif

#ifdef GSSAPI
#undef GSSAPI
#endif

#ifdef IMAP
#undef IMAP
#endif

#include "EudoraXcodeCompatibility.h"
#include "allheaders.h"
#include "mydefs.h"

#endif
