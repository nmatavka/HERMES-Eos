#include <string.h>

#include "EudoraKerberosCompat.h"

/*
 * The Xcode port uses a repo-owned MIT Kerberos build for GSSAPI/Kerberos V5
 * while keeping a thin KClient-shaped compatibility surface for the legacy
 * sources that still expect it.
 */
static OSErr EudoraKerberosTranslate(krb5_error_code error)
{
	if (error == 0)
		return noErr;
#ifdef KRB5_FCC_NOFILE
	if (error == KRB5_FCC_NOFILE)
		return cKrbNotLoggedIn;
#endif
#ifdef KRB5_CC_NOTFOUND
	if (error == KRB5_CC_NOTFOUND)
		return cKrbNotLoggedIn;
#endif
#ifdef KRB5_FCC_PERM
	if (error == KRB5_FCC_PERM)
		return cKrbNotLoggedIn;
#endif
	return fnfErr;
}

static void EudoraKerberosResetSession(KClientSessionInfo *session)
{
	if (!session)
		return;
	if (session->context != NULL && session->client != NULL)
		krb5_free_principal(session->context, session->client);
	if (session->context != NULL && session->ccache != NULL)
		krb5_cc_close(session->context, session->ccache);
	if (session->context != NULL)
		krb5_free_context(session->context);
	memset(session, 0, sizeof(*session));
}

static OSErr EudoraKerberosInitSession(KClientSessionInfo *session)
{
	krb5_error_code error;

	if (!session)
		return paramErr;
	if (session->initialized)
		return noErr;
	memset(session, 0, sizeof(*session));
	error = krb5_init_context(&session->context);
	if (error != 0)
		return EudoraKerberosTranslate(error);
	error = krb5_cc_default(session->context, &session->ccache);
	if (error != 0)
	{
		EudoraKerberosResetSession(session);
		return EudoraKerberosTranslate(error);
	}
	session->initialized = true;
	return noErr;
}

static OSErr EudoraKerberosRefreshPrincipal(KClientSessionInfo *session)
{
	krb5_error_code error;

	if (!session)
		return paramErr;
	if (!session->initialized)
	{
		OSErr err = EudoraKerberosInitSession(session);
		if (err != noErr)
			return err;
	}
	if (session->client != NULL)
	{
		krb5_free_principal(session->context, session->client);
		session->client = NULL;
	}
	error = krb5_cc_get_principal(session->context, session->ccache, &session->client);
	return EudoraKerberosTranslate(error);
}

static OSErr EudoraKerberosCopyDefaultUserName(UPtr name)
{
	KClientSessionInfo session;
	char *principal_name = NULL;
	OSErr err;

	memset(&session, 0, sizeof(session));
	if (name)
		*name = 0;
	err = EudoraKerberosInitSession(&session);
	if (err != noErr)
		return err;
	err = EudoraKerberosRefreshPrincipal(&session);
	if (err != noErr)
	{
		EudoraKerberosResetSession(&session);
		return err;
	}
	if (krb5_unparse_name(session.context, session.client, &principal_name) != 0 || principal_name == NULL)
	{
		EudoraKerberosResetSession(&session);
		return fnfErr;
	}
	if (name)
	{
		size_t copy_len = strlen(principal_name);
		if (copy_len > 255)
			copy_len = 255;
		memcpy(name, principal_name, copy_len);
		name[copy_len] = 0;
	}
	krb5_free_unparsed_name(session.context, principal_name);
	EudoraKerberosResetSession(&session);
	return noErr;
}

Boolean EudoraHaveSystemGSSAPI(void)
{
#if EUDORA_FEATURE_GSSAPI
	return true;
#else
	return false;
#endif
}

Boolean EudoraHaveKerberosIV(void)
{
	return false;
}

OSErr KClientDisposeSessionCompat(KClientSessionInfo *session)
{
	EudoraKerberosResetSession(session);
	return noErr;
}

OSErr KClientGetUserNameDeprecated(UPtr name)
{
	return EudoraKerberosCopyDefaultUserName(name);
}

OSErr KClientLoginCompat(KClientSessionInfo *session, KClientKey *key)
{
	(void)key;
	if (!session)
		return paramErr;
	return EudoraKerberosRefreshPrincipal(session);
}

OSErr KClientLogoutCompat(void)
{
	/*
	 * The Xcode port does not destroy the user's credential cache. We only
	 * release local session state.
	 */
	return noErr;
}

OSErr KClientMakeSendAuthCompat(KClientSessionInfo *session, UPtr fullName, UPtr ticket, unsigned long *bufferLength, long checksum, UPtr version)
{
	(void)session;
	(void)fullName;
	(void)ticket;
	(void)bufferLength;
	(void)checksum;
	(void)version;
	return unimpErr;
}

OSErr KClientNewSessionCompat(KClientSessionInfo *session, short localAddress, long localPort, short remoteAddress, long remotePort)
{
	(void)localAddress;
	(void)localPort;
	(void)remoteAddress;
	(void)remotePort;
	return EudoraKerberosInitSession(session);
}
