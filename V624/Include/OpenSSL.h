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
    Thin project wrapper for the vendored OpenSSL 3 headers plus the
    Eudora-specific adapter surface used by ssl.c.
*/

#ifndef EUDORA_OPENSSL
#define EUDORA_OPENSSL

#ifdef __cplusplus
extern "C" {
#endif

#include <openssl/bio.h>
#include <openssl/crypto.h>
#include <openssl/err.h>
#include <openssl/ssl.h>
#include <openssl/x509.h>
#include <openssl/x509_vfy.h>

BIO *BIO_new_ot(TransStream ts, int close_flag);

OSStatus InitOpenSSL(void);
OSStatus OpenSSLReadCerts(SSL_CTX *ctx, StringPtr hostName);

typedef int (*CertVerifyProc)(int, X509_STORE_CTX *);

OSStatus SetupSSLConnection(TransStream ep, long method, CertVerifyProc callback);
OSStatus CleanupSSLConnection(TransStream ep);

void DumpCertStore(X509_STORE *store);
Boolean IsCertInKeychain(X509 *theCert);
OSStatus ShowOpenSSLCertToUser(X509 *theCert);
OSStatus AddOpenSSLCertToKeychain(X509 *theCert);
Handle GetOpenSSLCertText(X509 *theCert);

#ifdef __cplusplus
}
#endif

#endif
