#ifndef PREFDEFS_H
#define PREFDEFS_H

Boolean PrefBounds(short prefN,long *lower,long *upper);
Boolean PrefAudit(short prefN);
typedef enum {
	PREF_0,
/*1*/	,
	PREF_STRN_LIMIT
} PrefStrnEnum;

#endif
