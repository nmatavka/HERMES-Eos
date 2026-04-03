/* Copyright (c) 2017, Computer History Museum
All rights reserved.
Redistribution and use in source and binary forms, with or without modification, are permitted (subject to
the limitations in the disclaimer below) provided that the following conditions are met:
 * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
   disclaimer in the documentation and/or other materials provided with the distribution.
 * Neither the name of Computer History Museum nor the names of its contributors may be used to endorse or promote products
   derived from this software without specific prior written permission.
NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE
COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
DAMAGE. */

/*
    OpenSSL.cp

    Eudora's OpenSSL adapter, updated for direct static linking against the
    vendored OpenSSL 3 build produced by Scripts/build_openssl.py.
*/

#include "OpenSSL.h"

#include <KeychainCore.h>
#include <KeychainHI.h>
#include <string.h>

/* NO MORE "relaxed pointer rules"!!! */
#pragma mpwc_relax off

extern TransVector ESSLSubTrans;

#ifndef kCDSACertClass
#define kCDSACertClass (0x80000000 + 0x1000)
#endif

static BIO_METHOD *gOTBioMethod = NULL;
static Boolean gOpenSSLInitialized = false;

static int BIO_ot_should_retry(OTResult err);
static int BIO_ot_non_fatal_error(OTResult err);
static int ot_write(BIO *bio, const char *buf, int num);
static int ot_read(BIO *bio, char *buf, int size);
static int ot_puts(BIO *bio, const char *str);
static long ot_ctrl(BIO *bio, int cmd, long num, void *ptr);
static int ot_new(BIO *bio);
static int ot_free(BIO *bio);
static OSErr OpenSSLAddCertToStore(SSL_CTX *ctx, CSSM_DATA_PTR cert, const char *hostName);
static OSStatus ApplyLegacyProtocolPolicy(SSL_CTX *ctx, long method);
static Handle GetDialogItemHandle(DialogPtr theDialog, short itemNo);
static pascal Boolean XShowFilterProc(DialogRef theDialog, EventRecord *theEvent, DialogItemIndex *itemHit);
static int CountKCCerts(SecKeychainRef theKC);


static BIO_METHOD *BIO_s_otsocket(void)
{
	if (gOTBioMethod != NULL)
		return gOTBioMethod;

	int type = BIO_TYPE_SOURCE_SINK | BIO_get_new_index();
	gOTBioMethod = BIO_meth_new(type, "ot_socket_in_Eudora");
	if (gOTBioMethod == NULL)
		return NULL;

	(void) BIO_meth_set_write(gOTBioMethod, ot_write);
	(void) BIO_meth_set_read(gOTBioMethod, ot_read);
	(void) BIO_meth_set_puts(gOTBioMethod, ot_puts);
	(void) BIO_meth_set_ctrl(gOTBioMethod, ot_ctrl);
	(void) BIO_meth_set_create(gOTBioMethod, ot_new);
	(void) BIO_meth_set_destroy(gOTBioMethod, ot_free);
	return gOTBioMethod;
}


BIO *BIO_new_ot(TransStream ts, int close_flag)
{
	BIO *ret = BIO_new(BIO_s_otsocket());
	if (ret == NULL)
		return NULL;
	BIO_set_data(ret, ts);
	BIO_set_shutdown(ret, close_flag);
	BIO_set_init(ret, 1);
	return ret;
}


static int ot_new(BIO *bio)
{
	BIO_set_data(bio, NULL);
	BIO_set_init(bio, 0);
	BIO_set_shutdown(bio, 0);
	return 1;
}


static int ot_free(BIO *bio)
{
	if (bio == NULL)
		return 0;
	BIO_set_data(bio, NULL);
	BIO_set_init(bio, 0);
	return 1;
}


static int ot_read(BIO *bio, char *out, int outl)
{
	long err = 0;

	ASSERT(outl > 0);
	if (out == NULL || outl <= 0)
		return 0;

	TransStream stream = (TransStream) BIO_get_data(bio);
	if (stream == NULL)
		return 0;

	SInt32 processed = outl;
	err = (*ESSLSubTrans.vRecvTrans)(stream, (unsigned char *) out, &processed);
	if (noErr == err)
		err = processed;

	BIO_clear_retry_flags(bio);
	if (err <= noErr) {
		if (BIO_ot_should_retry(err)) {
			BIO_set_retry_read(bio);
			err = -1;
		}
		else
			err = 0;
	}

	return err;
}


static int ot_write(BIO *bio, const char *in, int inl)
{
	long err = 0;

	ASSERT(NULL != in);
	ASSERT(inl > 0);

	if (NULL == in || inl <= 0)
		return 0;

	TransStream stream = (TransStream) BIO_get_data(bio);
	if (stream == NULL)
		return 0;

	err = (*ESSLSubTrans.vSendTrans)(stream, (unsigned char *) in, inl, nil);
	if (noErr == err)
		err = inl;

	BIO_clear_retry_flags(bio);
	if (err < 0) {
		if (BIO_ot_should_retry(err)) {
			BIO_set_retry_write(bio);
			err = -1;
		}
		else
			err = 0;
	}

	return err;
}


static int ot_puts(BIO *bio, const char *str)
{
	ASSERT(NULL != str);
	return ot_write(bio, str, strlen(str));
}


static long ot_ctrl(BIO *bio, int cmd, long num, void *ptr)
{
	long ret = 1;

	switch (cmd) {
		case BIO_CTRL_RESET:
			BIO_set_init(bio, 0);
			BIO_set_data(bio, NULL);
			ret = 0;
			break;

		case BIO_C_FILE_SEEK:
		case BIO_C_FILE_TELL:
		case BIO_CTRL_INFO:
			ret = 0;
			break;

		case BIO_C_SET_FD:
			BIO_set_data(bio, ptr);
			BIO_set_shutdown(bio, (int) num);
			BIO_set_init(bio, 1);
			break;

		case BIO_C_GET_FD:
			if (BIO_get_init(bio)) {
				ret = (long) BIO_get_data(bio);
				if (ptr != NULL)
					*((int *) ptr) = (int) ret;
			}
			else
				ret = -1;
			break;

		case BIO_CTRL_GET_CLOSE:
			ret = BIO_get_shutdown(bio);
			break;

		case BIO_CTRL_SET_CLOSE:
			BIO_set_shutdown(bio, (int) num);
			break;

		case BIO_CTRL_PENDING:
		case BIO_CTRL_WPENDING:
			ret = 0;
			break;

		case BIO_CTRL_DUP:
		case BIO_CTRL_FLUSH:
			ret = 1;
			break;

		default:
			ret = 0;
			break;
	}

	return ret;
}


int BIO_ot_should_retry(OTResult err)
{
	ASSERT(err <= 0);
	return BIO_ot_non_fatal_error(err);
}


int BIO_ot_non_fatal_error(OTResult err)
{
	ASSERT(err <= 0);
	switch (err) {
		case noErr:
		case kOTNoDataErr:
		case kOTFlowErr:
		case kOTStateChangeErr:
			return 1;

		default:
			return 0;
	}
}


static OSStatus ApplyLegacyProtocolPolicy(SSL_CTX *ctx, long method)
{
	int minVersion = 0;
	int maxVersion = 0;

	switch (method) {
		case 0x0301:
		case 102:
			minVersion = TLS1_VERSION;
			maxVersion = TLS1_VERSION;
			break;

		case 0x0302:
			minVersion = TLS1_1_VERSION;
			maxVersion = TLS1_1_VERSION;
			break;

		case 0x0303:
			minVersion = TLS1_2_VERSION;
			maxVersion = TLS1_2_VERSION;
			break;

#ifdef TLS1_3_VERSION
		case 0x0304:
			minVersion = TLS1_3_VERSION;
			maxVersion = TLS1_3_VERSION;
			break;
#endif

		case 0x0300:
		case 101:
		case 100:
		case 2:
		default:
			break;
	}

	if (minVersion != 0 && !SSL_CTX_set_min_proto_version(ctx, minVersion))
		return paramErr;
	if (maxVersion != 0 && !SSL_CTX_set_max_proto_version(ctx, maxVersion))
		return paramErr;
	return noErr;
}


OSStatus SetupSSLConnection(TransStream ep, long method, CertVerifyProc callback)
{
	ASSERT(ep->ctx == NULL);
	ASSERT(ep->ssl == NULL);
	ASSERT(ep->bio == NULL);

	OSStatus err = InitOpenSSL();
	if (noErr != err)
		return err;

	const SSL_METHOD *meth = TLS_client_method();
	ASSERT(meth != NULL);
	if (meth == NULL)
		return coreFoundationUnknownErr;

	ep->ctx = SSL_CTX_new(meth);
	ASSERT(ep->ctx != NULL);
	if (ep->ctx == NULL)
		return coreFoundationUnknownErr;

	err = ApplyLegacyProtocolPolicy(ep->ctx, method);
	if (err != noErr) {
		(void) CleanupSSLConnection(ep);
		return err;
	}

	if (NULL == callback)
		SSL_CTX_set_verify(ep->ctx, SSL_VERIFY_NONE, NULL);
	else
		SSL_CTX_set_verify(ep->ctx, SSL_VERIFY_PEER, callback);

	(void) OpenSSLReadCerts(ep->ctx, ep->serverName);
	SSL_CTX_set_verify_depth(ep->ctx, 4);

	ep->ssl = SSL_new(ep->ctx);
	ASSERT(ep->ssl != NULL);
	if (ep->ssl == NULL) {
		(void) CleanupSSLConnection(ep);
		return coreFoundationUnknownErr;
	}

	ep->bio = BIO_new_ot(ep, BIO_NOCLOSE);
	ASSERT(ep->bio != NULL);
	if (ep->bio == NULL) {
		(void) CleanupSSLConnection(ep);
		return coreFoundationUnknownErr;
	}

	SSL_set_bio(ep->ssl, ep->bio, ep->bio);
	SSL_set_connect_state(ep->ssl);
	return noErr;
}


OSStatus CleanupSSLConnection(TransStream ep)
{
	if (NULL != ep->ssl) {
		SSL_free(ep->ssl);
		ep->ssl = NULL;
	}
	if (NULL != ep->ctx) {
		SSL_CTX_free(ep->ctx);
		ep->ctx = NULL;
	}
	ep->bio = NULL;
	return noErr;
}


OSStatus InitOpenSSL(void)
{
	if (gOpenSSLInitialized)
		return noErr;

	uint64 initFlags = OPENSSL_INIT_LOAD_SSL_STRINGS | OPENSSL_INIT_LOAD_CRYPTO_STRINGS | OPENSSL_INIT_NO_LOAD_CONFIG;
	if (OPENSSL_init_ssl(initFlags, NULL) != 1)
		return coreFoundationUnknownErr;

	gOpenSSLInitialized = true;
	return noErr;
}


static OSErr OpenSSLAddCertToStore(SSL_CTX *ctx, CSSM_DATA_PTR cert, const char *hostName)
{
	(void) hostName;
	const unsigned char *cursor = cert->Data;
	X509 *X509Ptr = d2i_X509(NULL, &cursor, cert->Length);
	if (NULL != X509Ptr) {
		X509_STORE *store = SSL_CTX_get_cert_store(ctx);
		if (store != NULL)
			(void) X509_STORE_add_cert(store, X509Ptr);
		X509_free(X509Ptr);
	}

	return noErr;
}


void DumpCertStore(X509_STORE *store)
{
	(void) store;
}


OSStatus OpenSSLReadCerts(SSL_CTX *ctx, StringPtr hostName)
{
	(void) hostName;

	OSStatus err = noErr;
	SecKeychainItemRef item = NULL;
	SecKeychainSearchRef search = NULL;
	SecKeychainRef anchors = NULL;

	err = SecKeychainOpen("/System/Library/Keychains/X509Anchors", &anchors);
	if (err != noErr)
		return err;

	err = SecKeychainSearchCreateFromAttributes(anchors, kCDSACertClass, NULL, &search);
	while (err == noErr) {
		item = NULL;
		err = SecKeychainSearchCopyNext(search, &item);
		if (err != noErr)
			break;

		CSSM_DATA derCert;
		OSStatus certErr = SecCertificateGetData(item, &derCert);
		if (certErr == noErr)
			(void) OpenSSLAddCertToStore(ctx, &derCert, (const char *) hostName);

		CFRelease(item);
		item = NULL;
	}

	if (item != NULL)
		CFRelease(item);
	if (search != NULL)
		CFRelease(search);
	if (anchors != NULL)
		CFRelease(anchors);

	if (err == errKCItemNotFound)
		return noErr;
	return err;
}


Boolean IsCertInKeychain(X509 *theCert)
{
	Boolean retVal = false;
	OSStatus err = noErr;
	SecKeychainItemRef item = NULL;
	SecKeychainSearchRef search = NULL;

	err = SecKeychainSearchCreateFromAttributes(NULL, kCDSACertClass, NULL, &search);
	while (err == noErr && !retVal) {
		item = NULL;
		err = SecKeychainSearchCopyNext(search, &item);
		if (err != noErr)
			break;

		CSSM_DATA derCert;
		OSStatus certErr = SecCertificateGetData(item, &derCert);
		if (certErr == noErr) {
			const unsigned char *cursor = derCert.Data;
			X509 *X509Ptr = d2i_X509(NULL, &cursor, derCert.Length);
			if (NULL != X509Ptr) {
				retVal = (0 == X509_cmp(theCert, X509Ptr));
				X509_free(X509Ptr);
			}
		}

		CFRelease(item);
		item = NULL;
	}

	if (item != NULL)
		CFRelease(item);
	if (search != NULL)
		CFRelease(search);

	return retVal;
}


static Handle GetDialogItemHandle(DialogPtr theDialog, short itemNo)
{
	DialogItemType itemType;
	Handle item;
	Rect box;

	GetDialogItem(theDialog, itemNo, &itemType, &item, &box);
	return item;
}


static pascal Boolean XShowFilterProc(DialogRef theDialog, EventRecord *theEvent, DialogItemIndex *itemHit)
{
	if (theEvent->what != keyDown && theEvent->what != autoKey)
		return StdFilterProc(theDialog, theEvent, itemHit);

	if (theEvent->modifiers & cmdKey)
		return StdFilterProc(theDialog, theEvent, itemHit);

	char key = (char) (theEvent->message & charCodeMask);
	switch (key) {
		case kHomeCharCode:
		case kEndCharCode:
		case kPageUpCharCode:
		case kPageDownCharCode:
		case kLeftArrowCharCode:
		case kRightArrowCharCode:
		case kUpArrowCharCode:
		case kDownArrowCharCode:
			return StdFilterProc(theDialog, theEvent, itemHit);

		case kReturnCharCode:
		case kEnterCharCode:
			*itemHit = kStdOkItemIndex;
			return true;

		case kEscapeCharCode:
			*itemHit = kStdCancelItemIndex;
			return true;

		default:
			*itemHit = -1;
			SysBeep(1);
			return true;
	}

	return false;
}


OSStatus ShowOpenSSLCertToUser(X509 *theCert)
{
	MyWindowPtr theWin = GetNewMyDialog(SSL_CERT_DLOG_X, NULL, NULL, (WindowPtr) InFront);
	if (theWin == NULL)
		return memFullErr;

	DialogPtr theDialog = GetMyWindowDialogPtr(theWin);

	Str255 aString;
	GetRString(aString, SSL_CERT_PROMPT);
	SetDialogItemText(GetDialogItemHandle(theDialog, 4), aString);

	Handle certText = GetOpenSSLCertText(theCert);
	TESetText(*certText, GetHandleSize(certText), GetDialogTextEditHandle(theDialog));
	DisposeHandle(certText);

	SetDialogDefaultItem(theDialog, kStdOkItemIndex);
	SetDialogCancelItem(theDialog, kStdCancelItemIndex);

	ModalFilterUPP filterProc = NewModalFilterUPP(XShowFilterProc);
	short dItem = kStdCancelItemIndex;
	Boolean done = false;

	StartMovableModal(theDialog);
	ShowWindow(GetDialogWindow(theDialog));
	HiliteButtonOne(theDialog);
	while (!done) {
		MovableModalDialog(theDialog, filterProc, &dItem);
		switch (dItem) {
			case kStdOkItemIndex:
			case kStdCancelItemIndex:
				done = true;
				break;
		}
	}

	EndMovableModal(theDialog);
	MyDisposeDialog(theDialog);
	DisposeModalFilterUPP(filterProc);

	return dItem == kStdOkItemIndex ? noErr : userCanceledErr;
}


static int CountKCCerts(SecKeychainRef theKC)
{
	int retVal = 0;
	OSErr err = noErr;
	SecKeychainSearchRef searchRef = NULL;

	err = SecKeychainSearchCreateFromAttributes(theKC, kCDSACertClass, NULL, &searchRef);
	if (noErr == err) {
		SecKeychainItemRef itemRef = NULL;
		while (noErr == (err = SecKeychainSearchCopyNext(searchRef, &itemRef))) {
			retVal++;
			CFRelease(itemRef);
			itemRef = NULL;
		}

		CFRelease(searchRef);
	}

	return retVal;
}


OSStatus AddOpenSSLCertToKeychain(X509 *theCert)
{
	OSStatus err = noErr;
	SecCertificateRef certRef = NULL;
	CSSM_DATA cert;

	cert.Data = NULL;
	cert.Length = i2d_X509(theCert, NULL);
	if ((SInt32) cert.Length <= 0)
		return paramErr;

	cert.Data = (UInt8 *) OPENSSL_malloc(cert.Length);
	if (cert.Data == NULL)
		return memFullErr;

	unsigned char *cursor = cert.Data;
	if (i2d_X509(theCert, &cursor) != (int) cert.Length) {
		OPENSSL_free(cert.Data);
		return paramErr;
	}

	err = SecCertificateCreateFromData(&cert, CSSM_CERT_X_509v3, CSSM_CERT_ENCODING_DER, &certRef);
	if (err == noErr) {
		SecKeychainRef defKC = NULL;
		err = SecKeychainCopyDefault(&defKC);
		if (noErr == err) {
			int oldCount = CountKCCerts(defKC);
			int newCount;

			err = SecCertificateAddToKeychain(certRef, NULL);
			newCount = CountKCCerts(defKC);
			ASSERT(noErr == err && newCount == oldCount + 1);
			CFRelease(defKC);
		}

		CFRelease(certRef);
	}

	OPENSSL_free(cert.Data);
	return err;
}


static OSStatus AppendHandleNL(Handle h, char *text)
{
	OSStatus err = noErr;
	long oldSize = GetHandleSize(h);
	long len = strlen(text);
	if (len > 0)
		text[len - 1] = '\r';
	SetHandleSize(h, oldSize + len);
	if (noErr == (err = MemError()))
		BlockMoveData(text, *h + oldSize, len);
	return err;
}


Handle GetOpenSSLCertText(X509 *theCert)
{
	BIO *bMem = BIO_new(BIO_s_mem());
	X509_print(bMem, theCert);

	Handle retVal = NewHandle(0);
	char line[256];
	while (BIO_gets(bMem, line, sizeof(line))) {
		(void) AppendHandleNL(retVal, line);
	}
	BIO_free(bMem);
	return retVal;
}
