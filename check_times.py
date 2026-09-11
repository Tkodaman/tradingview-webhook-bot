import os
import time

for f in ['templates/cand_5b4e9.html', 'templates/dashboard_working_backup.html']:
    if os.path.exists(f):
        mtime = os.path.getmtime(f)
        size = os.path.getsize(f)
        print(f, "Size:", size, "Modified:", time.ctime(mtime))
