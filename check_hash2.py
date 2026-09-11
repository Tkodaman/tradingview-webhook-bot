import hashlib

def get_hash(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return hashlib.md5(f.read().encode('utf-8')).hexdigest()

print("Rebuilt:", get_hash('dashboard_rebuilt_properly.html'))
print("Working backup:", get_hash('templates/dashboard_working_backup.html'))
