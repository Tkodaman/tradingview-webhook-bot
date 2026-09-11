import hashlib

def get_hash(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return hashlib.md5(f.read().encode('utf-8')).hexdigest()

print("temp_sept3.html:", get_hash('temp_sept3.html'))
print("templates/dashboard.html:", get_hash('templates/dashboard.html'))
