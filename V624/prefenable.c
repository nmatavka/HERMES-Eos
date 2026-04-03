#include <Types.h>
#include "PrefDefs.h"
#include "StringDefs.h"
PersHandle SettingsPers(void);
#define ICCRAP	SettingsPers()!=PersList||!ReadIC||WriteIC
Boolean PrefEnabled(short prefN)
{
#ifdef LIGHT
	Boolean Light = true;
#else
	Boolean Light = false;
#endif

	switch (ABS(prefN))
	{
		default: return(True);
	}
}
