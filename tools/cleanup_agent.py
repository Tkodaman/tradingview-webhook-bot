import os
import sys
import time
import shutil
import hashlib
import json
import re
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

# ANSI Renk Kodları
C_RED = '\033[91m'
C_GREEN = '\033[92m'
C_YELLOW = '\033[93m'
C_CYAN = '\033[96m'
C_END = '\033[0m'

BASE_DIR = Path(__file__).resolve().parent.parent
QUARANTINE_DIR = BASE_DIR / "_quarantine"
REPORT_JSON = BASE_DIR / "cleanup_report.json"
REPORT_MD = BASE_DIR / "cleanup_report.md"

# --- KORUMA LİSTESİ (Safelist) ---
SAFE_EXTS = {".env", ".env.example", ".db", ".sqlite", ".sqlite3"}
SAFE_PATHS = [
    "agents", "core", "tests", "main.py", "requirements.txt",
    ".git", ".gitignore", "tools/cleanup_agent.py", "venv", ".venv"
]

def check_bot_running():
    """Check if main.py is currently running."""
    try:
        # Windows command to check if python main.py is running
        output = subprocess.check_output('tasklist /v', shell=True).decode('utf-8', errors='ignore')
        # tasklist output might not show full command line args reliably depending on privileges,
        # but if we check for python.exe we can at least warn.
        # A better cross-platform approach without psutil is hard, so we'll just check if python is running
        # and prompt a generic warning.
        if "python" in output.lower():
            print(f"{C_RED}UYARI: main.py şu anda çalışıyor gibi görünüyor!{C_END}")
            print(f"{C_YELLOW}Çalışan bir botun log/db veya cache dosyalarına müdahale etmek risklidir.{C_END}")
            ans = input("Yine de devam etmek istiyor musunuz? (evet/HAYIR): ").strip().lower()
            if ans != "evet":
                print("İşlem iptal edildi.")
                sys.exit(0)
    except Exception:
        pass # Ignore errors if wmic is not available or fails

def extract_config_paths() -> set:
    """Regex ile core/config.py dosyasını tarayıp referans verilen pathleri bul."""
    config_file = BASE_DIR / "core" / "config.py"
    safe_config_paths = set()
    if config_file.exists():
        content = config_file.read_text(encoding='utf-8', errors='ignore')
        # Basit string/path çıkarma (örn: "logs/system.log" veya "data/...")
        matches = re.findall(r'[\'"]([a-zA-Z0-9_/\-\.]+\.[a-zA-Z0-9]+)[\'"]', content)
        for match in matches:
            safe_config_paths.add(match)
    return safe_config_paths

def get_file_hash(filepath: Path) -> str:
    """SHA256 file hash."""
    h = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""

def is_safe(filepath: Path, safe_config_paths: set, now: float) -> bool:
    """Dosyanın koruma listesinde olup olmadığını kontrol et."""
    try:
        rel_path = filepath.relative_to(BASE_DIR).as_posix()
    except ValueError:
        return True # Not in BASE_DIR

    # Extension check
    for ext in SAFE_EXTS:
        if filepath.name.endswith(ext) or filepath.name == ext:
            return True

    # Path prefix check
    for safe_path in SAFE_PATHS:
        if rel_path == safe_path or rel_path.startswith(safe_path + "/"):
            return True

    # Config reference check
    for cfg_path in safe_config_paths:
        if cfg_path in rel_path:
            return True

    # 24 hours check
    try:
        mtime = filepath.stat().st_mtime
        if (now - mtime) < 86400: # 24 saat = 86400 saniye
            return True
    except Exception:
        return True # Can't read stat, assume safe

    return False

def categorize_file(filepath: Path, rel_path: str, now: float) -> str:
    """Dosyayı kategorize et."""
    if rel_path.startswith("venv/") or rel_path.startswith(".venv/"):
        return "venv"
    if "/__pycache__/" in rel_path or rel_path.endswith(".pyc") or "/.pytest_cache/" in rel_path:
        return "cache"
    if rel_path.endswith(".log"):
        mtime = filepath.stat().st_mtime
        if (now - mtime) > (7 * 86400):
            return "logs_old"
        return "logs_recent"
    if rel_path.endswith(".DS_Store") or rel_path.endswith(".tmp") or "node_modules/" in rel_path:
        return "garbage"
    if "backtest" in rel_path.lower() and (rel_path.endswith(".html") or rel_path.endswith(".csv")):
        mtime = filepath.stat().st_mtime
        if (now - mtime) > (30 * 86400):
            return "backtest_old"
        return "backtest_recent"
    return "other"

def run_scanner():
    print(f"{C_CYAN}Tarama başlatılıyor...{C_END}")
    safe_config_paths = extract_config_paths()
    now = time.time()

    file_hashes = {}
    categories = {
        "venv": {"size": 0, "count": 0},
        "cache": {"size": 0, "count": 0},
        "logs_old": {"size": 0, "count": 0},
        "logs_recent": {"size": 0, "count": 0},
        "garbage": {"size": 0, "count": 0},
        "backtest_old": {"size": 0, "count": 0},
        "backtest_recent": {"size": 0, "count": 0},
        "other": {"size": 0, "count": 0}
    }
    
    candidates_to_remove = []
    duplicate_groups = {} # hash -> [list of files]
    
    total_scanned_size = 0
    total_scanned_count = 0

    for root, dirs, files in os.walk(BASE_DIR):
        root_path = Path(root)
        # Hızlı eleme (örneğin _quarantine ve .git içini tarama)
        if "_quarantine" in root_path.parts or ".git" in root_path.parts:
            continue

        for file in files:
            filepath = root_path / file
            try:
                rel_path = filepath.relative_to(BASE_DIR).as_posix()
                size = filepath.stat().st_size
                total_scanned_size += size
                total_scanned_count += 1
                
                cat = categorize_file(filepath, rel_path, now)
                categories[cat]["size"] += size
                categories[cat]["count"] += 1
                
                if is_safe(filepath, safe_config_paths, now):
                    continue
                    
                # Garbage ve eski log/backtest işaretleme
                if cat in ["cache", "logs_old", "garbage", "backtest_old"]:
                    candidates_to_remove.append(filepath)
                    continue

                # Hash and Duplicate Check
                fhash = get_file_hash(filepath)
                if fhash:
                    if fhash not in file_hashes:
                        file_hashes[fhash] = [filepath]
                    else:
                        file_hashes[fhash].append(filepath)

            except Exception:
                pass
                
    # Duplicate processing
    total_dup_remove_size = 0
    total_dup_remove_count = 0
    dup_report_info = []

    for fhash, paths in file_hashes.items():
        if len(paths) > 1:
            # Sort by mtime (oldest first)
            paths.sort(key=lambda p: p.stat().st_mtime)
            original = paths[0]
            duplicates = paths[1:]
            
            dup_size = sum(p.stat().st_size for p in duplicates)
            total_dup_remove_size += dup_size
            total_dup_remove_count += len(duplicates)
            
            candidates_to_remove.extend(duplicates)
            duplicate_groups[fhash] = {
                "original": original.relative_to(BASE_DIR).as_posix(),
                "duplicates": [p.relative_to(BASE_DIR).as_posix() for p in duplicates]
            }
            dup_report_info.append(duplicate_groups[fhash])

    # Rapor Hazırlama
    total_remove_size = sum(p.stat().st_size for p in candidates_to_remove)
    
    report_data = {
        "summary": {
            "total_scanned_files": total_scanned_count,
            "total_scanned_size_mb": round(total_scanned_size / (1024*1024), 2),
            "total_remove_candidates": len(candidates_to_remove),
            "total_remove_size_mb": round(total_remove_size / (1024*1024), 2)
        },
        "categories_mb": {k: round(v["size"] / (1024*1024), 2) for k, v in categories.items()},
        "duplicate_groups": dup_report_info,
        "removal_candidates": [p.relative_to(BASE_DIR).as_posix() for p in candidates_to_remove]
    }
    
    with open(REPORT_JSON, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=4, ensure_ascii=False)
        
    md_lines = [
        "# Temizlik Ajanı Raporu (Cleanup Report)",
        f"**Tarih:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 1. Genel Özet",
        f"- **Taranan Toplam Dosya:** {report_data['summary']['total_scanned_files']}",
        f"- **Taranan Toplam Boyut:** {report_data['summary']['total_scanned_size_mb']} MB",
        f"- **Silinmesi Önerilen (Karantinaya Alınacak) Dosya Sayısı:** {report_data['summary']['total_remove_candidates']}",
        f"- **Kazanılacak Alan:** {report_data['summary']['total_remove_size_mb']} MB",
        "",
        "## 2. Kategori Boyut Dağılımı (MB)",
    ]
    for k, v in report_data["categories_mb"].items():
        md_lines.append(f"- **{k}**: {v} MB")
        
    md_lines.extend([
        "",
        "## 3. Duplicate (Tekrarlı) Dosyalar"
    ])
    if not dup_report_info:
        md_lines.append("- Kopya dosya bulunamadı.")
    else:
        for grp in dup_report_info:
            md_lines.append(f"- **Orijinal:** `{grp['original']}`")
            for dup in grp['duplicates']:
                md_lines.append(f"  - **Silinecek Kopya:** `{dup}`")
                
    md_lines.extend([
        "",
        "> [!IMPORTANT]",
        "> HİÇBİR DOSYA SİLİNMEDİ. Karantinaya taşımak için scripti `--apply` bayrağı ile çalıştırın."
    ])

    with open(REPORT_MD, 'w', encoding='utf-8') as f:
        f.write("\n".join(md_lines))

    print(f"{C_GREEN}Tarama tamamlandı!{C_END}")
    print(f"Raporlar oluşturuldu: {REPORT_MD} & {REPORT_JSON}")
    print(f"Silinecek (Karantinaya alınacak) Dosya Sayısı: {len(candidates_to_remove)}")
    print(f"Kazanılacak Alan: {report_data['summary']['total_remove_size_mb']} MB\n")
    return candidates_to_remove

def apply_quarantine(candidates: list):
    """Dosyaları silmek yerine karantinaya taşı."""
    if not candidates:
        print("Karantinaya alınacak dosya yok.")
        return

    today = datetime.now().strftime('%Y-%m-%d')
    q_dir = QUARANTINE_DIR / today
    q_dir.mkdir(parents=True, exist_ok=True)

    moved = 0
    for file_path in candidates:
        try:
            rel_path = file_path.relative_to(BASE_DIR)
            dest_path = q_dir / rel_path
            
            # Create subdirectories in quarantine if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(file_path), str(dest_path))
            moved += 1
        except Exception as e:
            print(f"{C_RED}Dosya taşınamadı: {file_path} - Hata: {e}{C_END}")

    print(f"{C_GREEN}Başarılı! {moved} adet dosya karantinaya taşındı: {q_dir}{C_END}")
    print("Bu dosyaları kalıcı silmek için daha sonra '--purge-quarantine' kullanabilirsiniz.")

def purge_quarantine():
    """7 günden eski karantina klasörlerini kalıcı sil."""
    if not QUARANTINE_DIR.exists():
        print("Karantina klasörü bulunamadı.")
        return

    now = datetime.now()
    removed_count = 0
    
    for item in QUARANTINE_DIR.iterdir():
        if item.is_dir():
            # item ismi YYYY-MM-DD formatında olmalı
            try:
                folder_date = datetime.strptime(item.name, '%Y-%m-%d')
                days_old = (now - folder_date).days
                
                if days_old > 7:
                    print(f"{C_YELLOW}Kalıcı silinecek karantina klasörü: {item.name} ({days_old} günlük){C_END}")
                    ans = input("Bu klasörü TAMAMEN SİLMEK İSTİYOR MUSUNUZ? Devam etmek için 'EVET' yazın: ").strip()
                    if ans == "EVET":
                        shutil.rmtree(item)
                        print(f"{C_GREEN}{item.name} kalıcı olarak silindi.{C_END}")
                        removed_count += 1
                    else:
                        print(f"{item.name} silinmedi.")
            except ValueError:
                pass # Not a valid date folder
                
    if removed_count == 0:
        print("Silinecek (7 günden eski) karantina verisi bulunamadı.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Proje Temizlik ve Optimize Ajanı")
    parser.add_argument("--apply", action="store_true", help="Tespit edilen dosyaları ./_quarantine/ klasörüne taşır (SİLMEZ).")
    parser.add_argument("--purge-quarantine", action="store_true", help="7 günden eski karantina dosyalarını kalıcı olarak siler (Onay ister).")
    args = parser.parse_args()

    check_bot_running()

    if args.purge_quarantine:
        purge_quarantine()
    else:
        candidates = run_scanner()
        if args.apply:
            apply_quarantine(candidates)
        else:
            print(f"{C_YELLOW}DİKKAT: Bu bir DRY-RUN (Sadece Rapor) çalışmasıydı.{C_END}")
            print(f"Karantinaya taşıma işlemini uygulamak için: python tools/cleanup_agent.py --apply")
