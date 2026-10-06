from datetime import datetime
import pytz
trt = datetime.now(pytz.timezone('Europe/Istanbul'))
print(trt.strftime('%A %Y-%m-%d %H:%M:%S'))
