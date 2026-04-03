#ifndef AUDITDEFS_H
#define AUDITDEFS_H

#define kAuditShutdown 1 //
OSErr AuditShutdown(long faceTime, long rearTime, long connectTime, long totalTime+Timestamp);

extern short AuditCategories[];
#define MaxAuditType 1

#endif //AUDITDEFS_H
