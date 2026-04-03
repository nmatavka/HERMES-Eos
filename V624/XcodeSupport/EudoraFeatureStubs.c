#include "register.h"
#include "paywin.h"
#include "networksetuplibrary.h"
#include "anal.h"
#include "light.h"

Boolean gCanPayMode = false;
NagStateHandle nagState = nil;
void *TAEStartSession = nil;
void *TAEEndSession = nil;
void *TAEScanText = nil;
void *TAEScoreSession = nil;
Boolean Light = true;

InitNagResultType InitNagging(void)
{
	return noDialogPending;
}

void DoPendingNagDialog(InitNagResultType pendingNagResult)
{
	(void) pendingNagResult;
}

void CheckNagging(UserStateType state)
{
	(void) state;
}

void RegisterEudoraHi(void)
{
}

void RegisterSuccess(uLong what)
{
	(void) what;
}

void AutoRegister(void)
{
}

OSErr AddConfig(AccuPtr accu, Boolean doShort)
{
	(void) accu;
	(void) doShort;
	return noErr;
}

void OpenPayWin(void)
{
	SysBeep(1);
}

OSErr UpdateRegInfoText(UserStateType state)
{
	(void) state;
	return noErr;
}

void TellPayWindowTheUpdateCheckIsDone(OSErr err)
{
	(void) err;
}

OSErr CodeEntryForProduct(UserStateType state, CodeEntryVariantType variant)
{
	(void) state;
	(void) variant;
	return userCanceledErr;
}

OSErr CodeEntryDialog(StringHandle regInfo)
{
	(void) regInfo;
	return userCanceledErr;
}

OSErr ParseRegFile(FSSpecPtr spec, parseNoiseType parseNoise, Boolean *needsRegistration, int *pnPolicyCode)
{
	(void) spec;
	(void) parseNoise;
	if (needsRegistration) {
		*needsRegistration = false;
	}
	if (pnPolicyCode) {
		*pnPolicyCode = 0;
	}
	return fnfErr;
}

Boolean SendUserToProfile(void)
{
	return false;
}

void StartPaymentProcess(void)
{
}

void PayWinIdle(MyWindowPtr win)
{
	(void) win;
}

Boolean UseNetworkSetup(void)
{
	return false;
}

void InitNetworkSetup(void)
{
}

OSErr CloseNetworkSetup(void)
{
	return noErr;
}

OSErr GetConnectionModeFromDatabase(unsigned long *connectionSelection)
{
	if (connectionSelection) {
		*connectionSelection = 0;
	}
	return paramErr;
}

OSErr GetPPPDialingInformationFromDatabase(Boolean *redial, unsigned long *numRedials, unsigned long *delay)
{
	if (redial) {
		*redial = false;
	}
	if (numRedials) {
		*numRedials = 0;
	}
	if (delay) {
		*delay = 0;
	}
	return paramErr;
}

OSErr GetCurrentPortNameFromFile(unsigned char *longPortName, char *portName, Boolean *enabled)
{
	if (longPortName) {
		longPortName[0] = 0;
	}
	if (portName) {
		portName[0] = 0;
	}
	if (enabled) {
		*enabled = false;
	}
	return fnfErr;
}

Boolean TCPWillDial(Boolean forceRead)
{
	(void) forceRead;
	return false;
}

Boolean HaveSpeller(void)
{
	return false;
}

void AnalScan(void)
{
}

void AnalScanPete(PETEHandle pte, Boolean toCompletion, Boolean toSpeak)
{
	(void) pte;
	(void) toCompletion;
	(void) toSpeak;
}

short AnalScanHandle(UHandle text, long offset, long len, Boolean *inHeader)
{
	(void) text;
	(void) offset;
	(void) len;
	if (inHeader) {
		*inHeader = false;
	}
	return 0;
}

Boolean AnalWarning(MessHandle messH)
{
	(void) messH;
	return false;
}

OSErr AnalFindMine(void)
{
	return fnfErr;
}

void LightEnableIf(MenuHandle mh, short item, Boolean enabledIf, Boolean enabledIfLight)
{
	(void) enabledIf;
	EnableIf(mh, item, enabledIfLight);
}

void MarkAsProOnly(MenuHandle theMenu, short item)
{
	DisableItem(theMenu, item);
}
