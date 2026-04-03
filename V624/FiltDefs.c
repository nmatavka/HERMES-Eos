#include "filtdefs.h"
extern void *FAflkNone(void);

#pragma segment FILTRUN
void *FATable(FilterKeywordEnum fk)
{
	switch (fk)
	{
		case flkNone: return(FAflkNone);
		default:
			return(nil);
	}
}

short FAPass(FilterKeywordEnum fk)
{
	switch (fk)
	{
		case flkNone: return(0);
		default: return(0);
	}
}

#pragma segment FilterWin
short FAMultiple(FilterKeywordEnum fk)
{
	switch (fk)
	{
		case flkNone: return(1);
		default: return(0);
	}
}

Boolean FAProOnly(FilterKeywordEnum fk)
{
	switch (fk)
	{
			return(1); break;
		default:
			return(0); break;
	}
}
