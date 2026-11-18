from datetime import datetime,timezone
def utcnow():return datetime.now(timezone.utc).replace(tzinfo=None)
def normalize(dt):
    if dt.tzinfo is not None:return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt
def iso(dt):return dt.strftime('%Y-%m-%dT%H:%M:%SZ') if dt else None
