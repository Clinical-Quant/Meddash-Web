import os
import re

base = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend"

files_to_patch = []
for root, _, files in os.walk(base):
    for f in files:
        if f.endswith('.py'):
            files_to_patch.append(os.path.join(root, f))

# We want to replace standard definitions:
# DB_FILE = "ct_trials.db" -> DB_FILE = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\ct_trials.db"
# DB_PATH = "biocrawler_db/biocrawler_leads.db" -> ...

replacements = [
    (r'(?i)(DB_FILE\s*=\s*)["\']ct_trials\.db["\']', r'\1r"C:\\Users\\email\\.gemini\\antigravity\\Meddash_organized_backend\\06_Shared_Datastores\\ct_trials.db"'),
    (r'(?i)(CT_DB\s*=\s*)["\']ct_trials\.db["\']', r'\1r"C:\\Users\\email\\.gemini\\antigravity\\Meddash_organized_backend\\06_Shared_Datastores\\ct_trials.db"'),
    (r'(?i)(KOL_DB\s*=\s*)["\']meddash_kols\.db["\']', r'\1r"C:\\Users\\email\\.gemini\\antigravity\\Meddash_organized_backend\\06_Shared_Datastores\\meddash_kols.db"'),
    (r'(?i)(DB_FILE\s*=\s*)["\']meddash_kols\.db["\']', r'\1r"C:\\Users\\email\\.gemini\\antigravity\\Meddash_organized_backend\\06_Shared_Datastores\\meddash_kols.db"'),
    (r'(?i)(DATABASE\s*=\s*)["\']meddash_kols\.db["\']', r'\1r"C:\\Users\\email\\.gemini\\antigravity\\Meddash_organized_backend\\06_Shared_Datastores\\meddash_kols.db"'),
    (r'(?i)(DB_NAME\s*=\s*)["\']meddash_kols\.db["\']', r'\1r"C:\\Users\\email\\.gemini\\antigravity\\Meddash_organized_backend\\06_Shared_Datastores\\meddash_kols.db"'),
    
    (r'(?i)(DB_PATH\s*=\s*)r?["\'].*biocrawler_leads\.db["\']', r'\1r"C:\\Users\\email\\.gemini\\antigravity\\Meddash_organized_backend\\06_Shared_Datastores\\biocrawler_leads.db"'),
    (r'(?i)db_path=["\']biocrawler_db/biocrawler_leads\.db["\']', r'db_path=r"C:\\Users\\email\\.gemini\\antigravity\\Meddash_organized_backend\\06_Shared_Datastores\\biocrawler_leads.db"'),
    (r'(?i)biocrawler_db_path=["\']biocrawler_leads\.db["\']', r'biocrawler_db_path=r"C:\\Users\\email\\.gemini\\antigravity\\Meddash_organized_backend\\06_Shared_Datastores\\biocrawler_leads.db"'),
    (r'(?i)meddash_db_path=["\']\.\./meddash_kols\.db["\']', r'meddash_db_path=r"C:\\Users\\email\\.gemini\\antigravity\\Meddash_organized_backend\\06_Shared_Datastores\\meddash_kols.db"'),
    
    (r'(?i)(DB_PATH\s*=\s*os\.path\.abspath[^\)]*\))', r'DB_PATH = r"C:\\Users\\email\\.gemini\\antigravity\\Meddash_organized_backend\\06_Shared_Datastores\\meddash_kols.db"'),
    (r'(?i)(CT_DB_PATH\s*=\s*os\.path\.join.*)', r'CT_DB_PATH = r"C:\\Users\\email\\.gemini\\antigravity\\Meddash_organized_backend\\06_Shared_Datastores\\ct_trials.db"'),
    (r'(?i)(KOL_DB_PATH\s*=\s*os\.path\.join.*)', r'KOL_DB_PATH = r"C:\\Users\\email\\.gemini\\antigravity\\Meddash_organized_backend\\06_Shared_Datastores\\meddash_kols.db"'),
    (r'(?i)(BIOCRAWLER_DB_PATH\s*=\s*os\.path\.join.*)', r'BIOCRAWLER_DB_PATH = r"C:\\Users\\email\\.gemini\\antigravity\\Meddash_organized_backend\\06_Shared_Datastores\\biocrawler_leads.db"'),
]

patched_files = []
for file_path in files_to_patch:
    if "patch_dbs.py" in file_path or "patch_paths.py" in file_path:
        continue
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    for pattern, repl in replacements:
        new_content = re.sub(pattern, repl, new_content)
        
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        patched_files.append(file_path)

print(f"Patched {len(patched_files)} files:")
for p in patched_files:
    print(f" - {os.path.basename(p)}")
