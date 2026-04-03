#ifndef TAE_H
#define TAE_H

struct TAESessionState {
	long opaque[8];
};

struct TAEDictState {
	long opaque[8];
};

extern void *TAEStartSession;
extern void *TAEEndSession;
extern void *TAEScanText;
extern void *TAEScoreSession;

#endif
