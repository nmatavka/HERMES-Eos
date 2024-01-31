/* Copyright (c) 2017, Computer History Museum All rights reserved. Redistribution and use in source and binary forms, with or without modification, are permitted (subject to the limitations in the disclaimer below) provided that the following conditions are met:  * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.  * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following    disclaimer in the documentation and/or other materials provided with the distribution.  * Neither the name of Computer History Museum nor the names of its contributors may be used to endorse or promote products    derived from this software without specific prior written permission. NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. */#include "petepch.h"//#include "SpotlightAPI.h"GWorldPtr GetGlobalGWorld(PETEGlobalsHandle globals){	Rect boundsRect;	GWorldPtr newGWorld;		if((**globals).offscreenGWorld != nil) {		return (**globals).offscreenGWorld;	}	boundsRect.top = 0;	boundsRect.left = 0;	boundsRect.bottom = 1;	boundsRect.right = 1;	if(NewGWorld(&newGWorld, 0, &boundsRect, nil, nil, useTempMem) == noErr) {		return ((**globals).offscreenGWorld = newGWorld);	} else {		return nil;	}}OSErr InitializeGlobals(PETEGlobalsHandle *globals){//	short StdSizes[] = {7,9,10,12,14,18,24,36,48};	short StdSizes[9];	RgnHandle newScratchRgn;	WhiteInfoHandle whitespaceGlobals;	short **fontSizes;	struct StringList {		short numStrings;		unsigned char strings[];	} **strListHand;	Handle lineBreak;	Byte hState;	OSErr errCode, tempErr;	long gestaltResponse;	//	SLInit();	/* Stupid compiler */	StdSizes[0] = 7;	StdSizes[1] = 9;	StdSizes[2] = 10;	StdSizes[3] = 12;	StdSizes[4] = 14;	StdSizes[5] = 18;	StdSizes[6] = 24;	StdSizes[7] = 36;	StdSizes[8] = 48;		newScratchRgn = nil;	whitespaceGlobals = nil;	fontSizes = nil;	*globals = (PETEGlobalsHandle)MyNewHandle(sizeof(PETEGlobals), &tempErr, hndlClear);	if((errCode = tempErr) == noErr) {		lineBreak = GetResource('LBRK', 128);		if(lineBreak != nil) {			HNoPurge(lineBreak);			DetachResource(lineBreak);			if(ResError() != noErr) {				ReleaseResource(lineBreak);				lineBreak = nil;			}		}		newScratchRgn = NewRgn();		if(newScratchRgn != nil) {			whitespaceGlobals = (WhiteInfoHandle)MyNewHandle(sizeof(WhiteInfo), &tempErr, 0);			if((errCode = tempErr) == noErr) {				strListHand = (struct StringList **)GetResource('STR#', 16600);				if(strListHand != nil) {					hState = HGetState((Handle)strListHand);					HNoPurge((Handle)strListHand);				}				fontSizes = (short **)MyNewHandle((strListHand != nil) ? (**strListHand).numStrings * sizeof(short) : sizeof(StdSizes), &tempErr, 0);				if((errCode = tempErr) == noErr) {					if(strListHand == nil) {						BlockMoveData(StdSizes, *fontSizes, sizeof(StdSizes));					} else {						long offset = 0L;						short count;						short len;												for(count = 0; count < (**strListHand).numStrings; ++count) {							(*fontSizes)[count] = 0;							len = (**strListHand).strings[offset++];							while(--len >= 0) {								(*fontSizes)[count] *= 10;								(*fontSizes)[count] += (**strListHand).strings[offset++] - '0';							}						}					}				}				if(strListHand != nil) {					HSetState((Handle)strListHand, hState);				}			}		} else {			errCode = memFullErr;		}	} else {		*globals = nil;	}		if(errCode != noErr) {		if(newScratchRgn != nil) {			DisposeRgn(newScratchRgn);		}		DisposeHandle(lineBreak);		DisposeHandle((Handle)fontSizes);		DisposeHandle((Handle)whitespaceGlobals);		DisposeHandle((Handle)*globals);		*globals = nil;	} else {		/* Set the flags for available features on the system and other parameters*/		(***globals).flags.hasControlManager = ((Gestalt(gestaltControlMgrAttr, &gestaltResponse) == noErr) && (gestaltResponse & gestaltControlMgrPresent));		(***globals).flags.hasAppearanceManager = ((Gestalt(gestaltAppearanceAttr, &gestaltResponse) == noErr) && (gestaltResponse & (1 << gestaltAppearanceExists)));		(***globals).flags.hasDragManager = ((Gestalt(gestaltDragMgrAttr, &gestaltResponse) == noErr) && (gestaltResponse & (1 << gestaltDragMgrPresent)) && ((long)InstallTrackingHandler != kUnresolvedCFragSymbolAddress));		(***globals).flags.hasDoubleByte = !(!((short)GetScriptManagerVariable(smDoubleByte)));		(***globals).flags.hasMultiScript = ((Byte)GetScriptManagerVariable(smEnabled) > 1);				GetGlobalGWorld(*globals);		(***globals).scratchRgn = newScratchRgn;		(**whitespaceGlobals).curScript = (**whitespaceGlobals).parseScriptCode = smCurrentScript;		(**whitespaceGlobals).hasDoubleByte = (***globals).flags.hasDoubleByte;		(***globals).whitespaceGlobals = whitespaceGlobals;		(***globals).romanWordWrapTable = lineBreak;		SetPETEDefaultColor((***globals).defaultBGColor);		(***globals).fontSizes = fontSizes;		/* Initialize graphic list */		GraphicInList(*globals, nil);	}	return errCode;}OSErr DisposeGlobals(PETEGlobalsHandle globals){	long docIndex;		DisposeScrapGraphics((**globals).clip.styleScrap, 0L, -1L, true);	DisposeHandle((Handle)(**globals).clip.styleScrap);		docIndex = (InlineGetHandleSize((Handle)globals) - sizeof(PETEGlobals)) / sizeof(DocumentInfoHandle);	while(--docIndex >= 0L) {		DisposeDocument(globals, (**globals).docInfoArray[docIndex]);	}	if((**globals).offscreenGWorld != nil) {		DisposeGWorld((**globals).offscreenGWorld);	}		if((**globals).scratchRgn != nil) {		DisposeRgn((**globals).scratchRgn);	}		DisposeHandle((Handle)(**globals).whitespaceGlobals);	DisposeHandle((Handle)(**globals).defaultFonts);	DisposeHandle((Handle)(**globals).labelStyles);	DisposeHandle((Handle)(**globals).fontSizes);	DisposeHandle((Handle)globals);	return noErr;}OSErr SetDefaultStyle(PETEGlobalsHandle globals, DocumentInfoHandle docInfo, PETEDefaultFontPtr defaultFont){	PETEDefaultFontHandle defFontHandle;	PETEDefaultFontPtr defFontPtr;	PETEPortInfo savedPortInfo;	short width;	long count;	OSErr errCode;		defFontHandle = (docInfo == nil) ? (**globals).defaultFonts : (**docInfo).defaultFonts;	if(defaultFont == nil) {		if(defFontHandle == nil) {			return noErr;		}		DisposeHandle((Handle)defFontHandle);		if(docInfo == nil) {			(**globals).defaultFonts = nil;		} else {			(**docInfo).defaultFonts = nil;		}	} else if(defFontHandle == nil) {		errCode = MyPtrToHand(defaultFont, (Handle *)&defFontHandle, sizeof(PETEDefaultFontEntry), 0);		if(errCode == noErr) {			if(docInfo == nil) {				(**globals).defaultFonts = defFontHandle;			} else {				(**docInfo).defaultFonts = defFontHandle;			}		}	} else {		count = InlineGetHandleSize((Handle)defFontHandle);		if(count < 0L) {			return count;		}		for(defFontPtr = *defFontHandle, count /= sizeof(PETEDefaultFontEntry); --count >= 0L; ++defFontPtr) {			if((defFontPtr->pdScript == defaultFont->pdScript) && (!defFontPtr->pdPrint == !defaultFont->pdPrint) && (!defFontPtr->pdFixed == !defaultFont->pdFixed)) {				*defFontPtr = *defaultFont;				break;			}		}		if(count < 0L) {			errCode = PtrAndHand(defaultFont, (Handle)defFontHandle, sizeof(PETEDefaultFontEntry));		} else {			errCode = noErr;		}	}		if(docInfo != nil) {		count = 0L;		goto ResetIt;	} else {			if((defaultFont != nil) && (defaultFont->pdScript == smRoman)) {			(**globals).romanFixedFontWidth = 0L;			if(!defaultFont->pdPrint) {				SavePortInfo(nil, &savedPortInfo);				TextFont(defaultFont->pdFont);				TextSize(defaultFont->pdSize);				TextFace(0);				width = CharWidth('W');				if(width == CharWidth('.')) {					(**globals).romanFixedFontWidth = width;					(**globals).romanFixedFont = defaultFont->pdFont;					(**globals).romanFixedSize = defaultFont->pdSize;				}				ResetPortInfo(&savedPortInfo);			}		}			count = InlineGetHandleSize((Handle)globals) - sizeof(PETEGlobals);		count /= sizeof(DocumentInfoHandle);		while(--count >= 0L) {			docInfo = (**globals).docInfoArray[count];		ResetIt :			RecalcStyleHeights(nil, docInfo, ((**docInfo).printData != nil));			ResetAndInvalidateDocument(docInfo);		}	}		return errCode;}OSErr SetLabelStyle(PETEGlobalsHandle globals, DocumentInfoHandle docInfo, PETELabelStylePtr labelStyle){	PETELabelStyleHandle labelHandle;	PETELabelStylePtr labelPtr;	long count;	OSErr errCode;		labelHandle = (docInfo == nil) ? (**globals).labelStyles : (**docInfo).labelStyles;	if(labelHandle == nil) {		errCode = MyPtrToHand(labelStyle, (Handle *)&labelHandle, sizeof(PETELabelStyleEntry), 0);		if(errCode == noErr) {			if(docInfo == nil) {				(**globals).labelStyles = labelHandle;			} else {				(**docInfo).labelStyles = labelHandle;			}		}	} else {		count = InlineGetHandleSize((Handle)labelHandle);		if(count < 0L) {			return count;		}		for(labelPtr = *labelHandle, count /= sizeof(PETELabelStyleEntry); --count >= 0L; ++labelPtr) {			if(labelStyle->plLabel == labelPtr->plLabel) {				*labelPtr = *labelStyle;				break;			}		}		if(count < 0L) {			errCode = PtrAndHand(labelStyle, (Handle)labelHandle, sizeof(PETELabelStyleEntry));		} else {			errCode = noErr;		}	}		if(docInfo != nil) {		count = 0L;		goto ResetIt;	} else {		count = InlineGetHandleSize((Handle)globals) - sizeof(PETEGlobals);		count /= sizeof(DocumentInfoHandle);		while(--count >= 0L) {			docInfo = (**globals).docInfoArray[count];		ResetIt :			RecalcStyleHeights(nil, docInfo, ((**docInfo).printData != nil));			ResetAndInvalidateDocument(docInfo);		}	}		return errCode;}OSErr SetDefaultColor(PETEGlobalsHandle globals, DocumentInfoHandle docInfo, RGBColor *defaultColor){	if(docInfo != nil) {		(**docInfo).defaultColor = *defaultColor;	} else {		(**globals).defaultColor = *defaultColor;	}	return noErr;}OSErr SetDefaultBGColor(PETEGlobalsHandle globals, DocumentInfoHandle docInfo, RGBColor *defaultColor){	if(docInfo != nil) {		(**docInfo).defaultBGColor = *defaultColor;	} else {		(**globals).defaultBGColor = *defaultColor;	}	return noErr;}void GetWhitespaceGlobals(WhiteInfoHandle whitespaceGlobals, ScriptCode script){	Handle itlHandle;	long offset, length;	Byte hState;	Boolean doubleByte;		if(script == smCurrentScript) {		script = FontScript();	}	if(script != (**whitespaceGlobals).curScript) {		doubleByte = ((**whitespaceGlobals).hasDoubleByte && (((short)GetScriptVariable(script, smScriptFlags) & (1 << smsfSingByte)) == 0));		if((doubleByte) && (script != (**whitespaceGlobals).parseScriptCode)) {			/* Set the parse table script code */			(**whitespaceGlobals).parseScriptCode = script;						hState = HGetState((Handle)whitespaceGlobals);			HLock((Handle)whitespaceGlobals);			/* Get the character length table */			FillParseTable((**whitespaceGlobals).table, script);			HSetState((Handle)whitespaceGlobals, hState);		}		(**whitespaceGlobals).doubleByte = doubleByte;				(**whitespaceGlobals).itlHandle = nil;		(**whitespaceGlobals).curScript = script;	} else {		doubleByte = (**whitespaceGlobals).doubleByte;	}		if(((**whitespaceGlobals).itlHandle == nil) || (*(**whitespaceGlobals).itlHandle == nil)) {		GetIntlResourceTable(script, smWhiteSpaceList, &itlHandle, &offset, &length);		(**whitespaceGlobals).itlHandle = itlHandle;		(**whitespaceGlobals).offset = offset;	}}void LiveScroll(PETEGlobalsHandle globals, Boolean live){	if((**globals).flags.useLiveScrolling != live) {		(**globals).flags.useLiveScrolling = live;		if((**globals).flags.hasAppearanceManager) {			DocumentInfoHandle docInfo;			long docIndex;			ControlRef oldScroll, newScroll;			Rect controlRect;						G_MEMCANTFAIL(globals);			docIndex = (InlineGetHandleSize((Handle)globals) - sizeof(PETEGlobals)) / sizeof(DocumentInfoHandle);			while(--docIndex >= 0L) {				docInfo = (**globals).docInfoArray[docIndex];				if((**docInfo).flags.hasVScroll) {					oldScroll = (**docInfo).vScroll;					GetControlRect(oldScroll, &controlRect);					newScroll = NewControl(GetControlOwner(oldScroll), &controlRect, nil, IsControlVisible(oldScroll), GetControlValue(oldScroll), GetControlMinimum(oldScroll), GetControlMaximum(oldScroll), (**globals).flags.useLiveScrolling ? kControlScrollBarLiveProc : kControlScrollBarProc, GetControlReference(oldScroll));#if TARGET_CPU_PPC					if((**(**docInfo).globals).flags.hasControlManager) {						SetControl32BitMinimum(newScroll, GetControl32BitMinimum(oldScroll));						SetControl32BitMaximum(newScroll, GetControl32BitMaximum(oldScroll));						SetControl32BitValue(newScroll, GetControl32BitValue(oldScroll));						SetControlViewSize(newScroll, GetControlViewSize(oldScroll));					}#endif					if((**globals).flags.hasAppearanceManager && (**docInfo).containerControl)						EmbedControl(newScroll, (**docInfo).containerControl);					DisposeControl(oldScroll);					(**docInfo).vScroll = newScroll;				}				if((**docInfo).flags.hasHScroll) {					oldScroll = (**docInfo).hScroll;					GetControlRect(oldScroll, &controlRect);					newScroll = NewControl(GetControlOwner(oldScroll), &controlRect, nil, IsControlVisible(oldScroll), GetControlValue(oldScroll), GetControlMinimum(oldScroll), GetControlMaximum(oldScroll), (**globals).flags.useLiveScrolling ? kControlScrollBarLiveProc : kControlScrollBarProc, GetControlReference(oldScroll));#if TARGET_CPU_PPC					if((**(**docInfo).globals).flags.hasControlManager) {						SetControl32BitMinimum(newScroll, GetControl32BitMinimum(oldScroll));						SetControl32BitMaximum(newScroll, GetControl32BitMaximum(oldScroll));						SetControl32BitValue(newScroll, GetControl32BitValue(oldScroll));						SetControlViewSize(newScroll, GetControlViewSize(oldScroll));					}#endif					if((**globals).flags.hasAppearanceManager && (**docInfo).containerControl)						EmbedControl(newScroll, (**docInfo).containerControl);					DisposeControl(oldScroll);					(**docInfo).hScroll = newScroll;				}			}			G_MEMCANFAIL(globals);		}	}}