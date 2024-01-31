/* Copyright (c) 2017, Computer History Museum All rights reserved. Redistribution and use in source and binary forms, with or without modification, are permitted (subject to the limitations in the disclaimer below) provided that the following conditions are met:  * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.  * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following    disclaimer in the documentation and/or other materials provided with the distribution.  * Neither the name of Computer History Museum nor the names of its contributors may be used to endorse or promote products    derived from this software without specific prior written permission. NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. */#ifndef WAZOO_H#define WAZOO_H/* Copyright (c) 1997 by QUALCOMM Incorporated *//********************************************************************** * handles combined windows **********************************************************************/#define kWazooListResType 'Wzo1'#define kFreeWazooListResType 'Wzo2'#define kWazooDragType 'Wzoo'enum { kWazooRes1 = 1001, kWazooRes2 = 1002 };Boolean ClickWazoo(MyWindowPtr win,EventRecord *event,Point pt,Boolean *dontActivate);Boolean CloseWazoo(MyWindowPtr win);void DemoteWazoo(MyWindowPtr win);void DidResizeWazoo(MyWindowPtr win,Rect *oldCont);Boolean DraggingWazoo(MyWindowPtr win,DragTrackingMessage message,DragReference drag,OSErr *err);MyWindowPtr GetNewWazoo(short windowKind,Boolean *fIsWazoo);void InitWazoos(void);void KillWazoos(void);Boolean IsKindWazoo(short windowKind);Boolean IsWazoo(WindowPtr winWP);Boolean IsLonelyWazoo(WindowPtr winWP);Boolean IsWazooable(WindowPtr winWP);void PositionWazoo(MyWindowPtr win);void PromoteToWazoo(MyWindowPtr win);void UpdateWazoo(MyWindowPtr win);void SetupDefaultWazoos(void);void SafeWazooControl(MyWindowPtr win,ControlHandle ctl,short windowKind);void SetWinMinSize(MyWindowPtr win,short h,short v);Boolean WazooHelp(MyWindowPtr win,Point mouse);Boolean SelectOpenWazoo(short windowKind);Boolean IsWazooEmbedderCntl(ControlHandle cntl);Boolean IsWazooTabCntl(ControlHandle cntl);void DirtyWazoo(MyWindowPtr win, short windowKind);void SetTabBackColor(MyWindowPtr win);void WazooPreUpdate(MyWindowPtr win);MyWindowPtr FindOpenWazoo(short windowKind);void EmbedInWazoo(ControlRef cntl,WindowPtr win);#endif