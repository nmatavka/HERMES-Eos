#ifdef TWO
#ifndef FILTDEFS_H
#define FILTDEFS_H

typedef enum {
	flkZero,
	flkNone,
	flkLimit
} FilterKeywordEnum;

#define FilterKeywordStrn 25200

void *FATable(FilterKeywordEnum fk);
short FAPass(FilterKeywordEnum fk);
short FAMultiple(FilterKeywordEnum fk);
Boolean FAProOnly(FilterKeywordEnum fk);
#endif
#endif
