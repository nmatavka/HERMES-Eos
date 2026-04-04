#ifndef EUDORA_KERBEROS_COMPAT_H
#define EUDORA_KERBEROS_COMPAT_H

#if defined(EUDORA_XCODE_BUILD)

#include <gssapi.h>
#include <gssapi/gssapi_krb5.h>
#include <krb5.h>

typedef struct KClientSessionInfo {
	krb5_context context;
	krb5_ccache ccache;
	krb5_principal client;
	Boolean initialized;
} KClientSessionInfo;

typedef struct KClientKey {
	UInt32 reserved;
} KClientKey;

enum {
	cKrbNotLoggedIn = -23017
};

Boolean EudoraHaveSystemGSSAPI(void);
Boolean EudoraHaveKerberosIV(void);

OSErr KClientDisposeSessionCompat(KClientSessionInfo *session);
OSErr KClientGetUserNameDeprecated(UPtr name);
OSErr KClientLoginCompat(KClientSessionInfo *session, KClientKey *key);
OSErr KClientLogoutCompat(void);
OSErr KClientMakeSendAuthCompat(KClientSessionInfo *session, UPtr fullName, UPtr ticket, unsigned long *bufferLength, long checksum, UPtr version);
OSErr KClientNewSessionCompat(KClientSessionInfo *session, short localAddress, long localPort, short remoteAddress, long remotePort);

#else

#include "KClient.h"
#include "KClientCompat.h"
#include "KClientDeprecated.h"
#if TARGET_RT_MAC_CFM
#include "GSS.h"
#endif

#endif

#endif
