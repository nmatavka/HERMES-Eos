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

#include "EudoraXcodeCompatibility.h"
#include "allheaders.h"
#include "mydefs.h"

/*
 * The legacy POP sources still carry the old KPOP/Kerberos-IV split. In the
 * Xcode build we reinterpret that path as Kerberos 5 over normal POP AUTH
 * GSSAPI, so the old alternate-port and alternate-pref selectors collapse onto
 * the regular POP/GSSAPI path.
 */
#ifdef PREF_K5_POP
#undef PREF_K5_POP
#define PREF_K5_POP PREF_KERBEROS
#endif

#ifdef KERB_POP_PORT
#undef KERB_POP_PORT
#define KERB_POP_PORT POP_PORT
#endif

#ifdef KERBEROS_POP_SERVICE
#undef KERBEROS_POP_SERVICE
#define KERBEROS_POP_SERVICE K5_POP_SERVICE
#endif

#endif
