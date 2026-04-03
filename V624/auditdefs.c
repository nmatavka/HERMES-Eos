extern OSErr Audit(short auditType,...);
extern OSErr AuditFlush(Boolean force);


OSErr AuditShutdown(long faceTime, long rearTime, long connectTime, long totalTime+Timestamp)
{
	OSErr err = Audit(kAuditShutdown,faceTime,rearTime,connectTime,totalTime+Timestamp);
	if (!err) err = AuditFlush(true);
	return err;
}
short AuditCategories[] = {4};
