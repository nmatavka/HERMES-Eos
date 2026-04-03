#ifndef EUDORA_XCODE_COMPATIBILITY_H
#define EUDORA_XCODE_COMPATIBILITY_H

/*
 * Xcode-only compatibility shims for missing commercial/proprietary pieces.
 * These are intentionally small and are only meant to keep the legacy Carbon
 * tree buildable on the High Sierra/Xcode 9 host.
 */

#define EUDORA_FEATURE_REGISTRATION 0
#define EUDORA_FEATURE_NETWORK_SETUP 0
#define EUDORA_FEATURE_GSSAPI 0
#define EUDORA_FEATURE_WINTERTREE 0
#define EUDORA_FEATURE_TAE 0
#define EUDORA_FEATURE_SPOTLIGHT 0
#define EUDORA_FEATURE_CERTICOM 0
#define EUDORA_FEATURE_IMAP 0
#define EUDORA_FEATURE_SSL_OPENSSL 1

typedef enum {
	noDialogPending = 0,
	paymentRegPending = 1,
	codeEntryPending = 2,
	repayPending = 3,
	gracelessRepayPending = 4
} InitNagResultType;

typedef enum {
	ep4User = 1001,
	ep4RegUser,
	newUser,
	paidUser,
	freeUser,
	adwareUser,
	regFreeUser,
	regAdwareUser,
	deadbeatUser,
	boxUser = 1011,
	profileDeadbeatUser,
	unpaidUser,
	repayUser,
	userStateLimit
} UserStateType;

typedef struct {
	short version;
	UserStateType state;
	uLong regDate;
} NagStateRec, *NagStatePtr, **NagStateHandle;

extern Boolean gCanPayMode;
extern NagStateHandle nagState;

#define GetNagState() freeUser
#define ValidUser(state) ((void)(state), true)
#define EP4User(state) ((void)(state), false)
#define NewUser(state) ((void)(state), false)
#define FreeUser(state) ((void)(state), true)
#define PayUser(state) ((void)(state), false)
#define RepayUser(state) ((void)(state), false)
#define AdwareUser(state) ((void)(state), false)
#define RegisteredUser(state) ((void)(state), false)
#define DeadbeatUser(state) ((void)(state), false)
#define ProfileDeadbeatUser(state) ((void)(state), false)
#define UnpaidUser(state) ((void)(state), false)
#define BoxUser(state) ((void)(state), false)
#define PayMode(state) ((void)(state), false)
#define AdwareMode(state) ((void)(state), false)
#define FreeMode(state) ((void)(state), true)

#define IsValidUser() true
#define IsEP4User() false
#define IsNewUser() false
#define IsFreeUser() true
#define IsPayUser() false
#define IsRepayUser() false
#define IsAdwareUser() false
#define IsRegisteredUser() false
#define IsDeadbeatUser() false
#define IsProfileDeadbeatUser() false
#define IsUnpaidUser() false
#define IsBoxUser() false
#define IsPayMode() false
#define IsAdwareMode() false
#define IsFreeMode() true
#define CanPayMode() false
#define IsProfiledUser() false

typedef enum {
	sprNeverSpell = -2,
	sprSpellComplete = -1
} SpellResultEnum;

#define SpelledAuto(pte) ((void)(pte), false)
#define SpellDisabled(pte) ((void)(pte), true)
#define SpellChecked(pte) ((void)(pte), false)

Boolean HaveSpeller(void);

#endif
