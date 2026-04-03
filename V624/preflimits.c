#include <Types.h>
#include "PrefDefs.h"
#include "StringDefs.h"
Boolean PrefBounds(short prefN,long *lower,long *upper)
{
#ifdef LIGHT
	Boolean Light = true;
#else
	Boolean Light = false;
#endif

	long l,u;
	switch (prefN)
	{
		default: return(0);
	}
	*lower = l;
	*upper = u;
	return(-1);
}
