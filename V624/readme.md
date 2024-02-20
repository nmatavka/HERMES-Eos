## Resources

I am almost certain that, in transferring the code to me, the resource forks got "blitzed" due to the use of inappropriate archivers (i.e. I got a tarball instead of a DMG, which isn't exactly Apple-friendly where resource forks are concerned). This means that all the .rsrc files (compiled form) are likely unusable - which is why they have a file size of zero.

That having been said, I have *ALL* the resources in one big Rez source file, called all-resources.r (naturally enough). Untangling it may or may not be a hassle; in case it is, whatever poor sod works on this project after me has my deepest sympathies. (I feel like it *shouldn't* be a problem to make reference to all-resources.r or, once you compile it, all-resources.rsrc---but I've been wrong before.)

## Xcode import

This is a PEF app, Carbon-on-PPC. Obviously it can't remain that way: the next target is Mach-O, Carbon-on-Intel (Cocoa in the distance). Anyway, it was developed on CodeWarrior IDE, which is long dead. I performed a brute-force conversion into Xcode, because I don't anticipate anyone working on this to be using a PPC workstation (real or emulated) at any time. I know that the whole process of going from PEF to Mach-O can produce link errors out the wazoo if there is a long skein of dependencies, and I'm sure the CodeWarrior to Xcode conversion wasn't perfect either (I certainly didn't arse about with it too much).

By the way, I suggest the use of Xcode 11.3.1	and macos 10.14 "Mojave".

## Missing files

There is some code not included here, more or less because I've been questioning whether it really counts as a dependency or not. Much of it appears to be holdovers from UNIX (which makes sense because macOS is a UNIX) - thing is, it seems to be associated to the letters MPW (which stand for Macintosh Programmer's Workshop, a sort of Cygwin for Classic, i.e. pre-UNIX, Macintosh). So whether to use the UNIX version of, say, Hesiod or Kerberos, or the long-dead MPW port, is a question mark in my eyes.

That's not /everything/, for example, Wintertree is a spellcheck module that really isn't ideal for this project or any project; it's developed by one man who charges an arm and a leg for it---no way, Jose! It *is*, however, a big fraction.

## "Profiling"

This is Qualcomm's euphemism for serial code validation, nagware, copy protection, customer tracking/spying, and related functions. We anticipate releasing the Carbon-on-Intel version as free and open source software, and the Cocoa version as fully commercial, paid software. Therefore, profiling is strictly an *undesirable* functionality in my eyes, and the first or second milestone will literally include the words "no profiling" in the description.

## Legalities

Though the Eudora code belongs to us, the Eudora name absolutely does **not**. Furthermore, considering that Eudora for Windows and for Mac are entirely separate apps with separate code bases and even languages (C++ and C), I consider it highly important to disambiguate. As such, every occurrence of the word "Eudora" will have to be replaced with the word "Eos" (Titaness of the new dawn, from Hellenic mythology) and every occurrence of the word "Qualcomm" will have to be replaced with "HERMES" (all caps).