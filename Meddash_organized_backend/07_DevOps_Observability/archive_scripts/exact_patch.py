import os
import glob

base = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend"
kols_db = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\meddash_kols.db"
ct_db = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\ct_trials.db"
leads_db = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\biocrawler_leads.db"

exact_replacements = {
    'DB_FILE   = "meddash_kols.db"': f'DB_FILE   = r"{kols_db}"',
    'DB_FILE  = "meddash_kols.db"': f'DB_FILE  = r"{kols_db}"',
    'DB_FILE = "meddash_kols.db"': f'DB_FILE = r"{kols_db}"',
    "DB_FILE = 'meddash_kols.db'": f'DB_FILE = r"{kols_db}"',

    'DB_FILE  = "ct_trials.db"': f'DB_FILE  = r"{ct_db}"',
    'DB_FILE = "ct_trials.db"': f'DB_FILE = r"{ct_db}"',
    'DB_FILE   = "ct_trials.db"': f'DB_FILE   = r"{ct_db}"',
    
    'CT_DB  = "ct_trials.db"': f'CT_DB  = r"{ct_db}"',
    'CT_DB   = "ct_trials.db"': f'CT_DB   = r"{ct_db}"',
    'CT_DB = "ct_trials.db"': f'CT_DB = r"{ct_db}"',
    
    'KOL_DB = "meddash_kols.db"': f'KOL_DB = r"{kols_db}"',
    'KOL_DB  = "meddash_kols.db"': f'KOL_DB  = r"{kols_db}"',
    'KOL_DB   = "meddash_kols.db"': f'KOL_DB   = r"{kols_db}"',

    'ct_trials.db path': 'ct_trials.db path', # Do not replace help strings
    'meddash_kols.db path': 'meddash_kols.db path',

    'CT_DB_PATH = os.path.join(BASE_DIR, \'ct_trials.db\')': f'CT_DB_PATH = r"{ct_db}"',
    'KOL_DB_PATH = os.path.join(BASE_DIR, \'meddash_kols.db\')': f'KOL_DB_PATH = r"{kols_db}"',
    'BIOCRAWLER_DB_PATH = os.path.join(BASE_DIR, \'..\', \'biocrawler_marketing\', \'biocrawler_leads.db\')': f'BIOCRAWLER_DB_PATH = r"{leads_db}"',
    
    'db_path="biocrawler_db/biocrawler_leads.db"': f'db_path=r"{leads_db}"',
    'biocrawler_db_path="biocrawler_leads.db"': f'biocrawler_db_path=r"{leads_db}"',
    'meddash_db_path="../meddash_kols.db"': f'meddash_db_path=r"{kols_db}"',
    
    'DB_PATH = r"c:\\Users\\email\\.gemini\\antigravity\\Meddash_organized_backend\\03_BioCrawler_GTM\\biocrawler_db\\biocrawler_leads.db"': f'DB_PATH = r"{leads_db}"',
    
    "DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'meddash_kols.db'))": f'DB_PATH = r"{kols_db}"',
}

files_patched = 0
for root, _, files in os.walk(base):
    for filename in files:
        if filename.endswith(".py") and filename not in ["patch_paths.py", "patch_dbs.py", "exact_patch.py"]:
            filepath = os.path.join(root, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            new_content = content
            # Try all exact replace
            for old, new in exact_replacements.items():
                new_content = new_content.replace(old, new)
            
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Patched: {filepath.replace(base, '')}")
                files_patched += 1

print(f"Total files patched: {files_patched}")
