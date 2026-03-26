import os
import glob

base_dir = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend"

# Map exactly the old relative string formats to new relative formats (the user has full path prefix usually)
reps = {
    r"Meddash_organized_backend\06_Shared_Datastores\meddash_kols.db": r"Meddash_organized_backend\06_Shared_Datastores\meddash_kols.db",
    r"Meddash_organized_backend/06_Shared_Datastores/meddash_kols.db": r"Meddash_organized_backend/06_Shared_Datastores/meddash_kols.db",
    r"Meddash_organized_backend\\06_Shared_Datastores\\meddash_kols.db": r"Meddash_organized_backend\\06_Shared_Datastores\\meddash_kols.db",
    
    r"Meddash_organized_backend\06_Shared_Datastores\ct_trials.db": r"Meddash_organized_backend\06_Shared_Datastores\ct_trials.db",
    r"Meddash_organized_backend/06_Shared_Datastores/ct_trials.db": r"Meddash_organized_backend/06_Shared_Datastores/ct_trials.db",
    r"Meddash_organized_backend\\06_Shared_Datastores\\ct_trials.db": r"Meddash_organized_backend\\06_Shared_Datastores\\ct_trials.db",
    
    r"Meddash_organized_backend\06_Shared_Datastores\biocrawler_leads.db": r"Meddash_organized_backend\06_Shared_Datastores\biocrawler_leads.db",
    r"Meddash_organized_backend/06_Shared_Datastores/biocrawler_leads.db": r"Meddash_organized_backend/06_Shared_Datastores/biocrawler_leads.db",
    r"Meddash_organized_backend\\06_Shared_Datastores\\biocrawler_leads.db": r"Meddash_organized_backend\\06_Shared_Datastores\\biocrawler_leads.db",
    
    # Folders
    r"Meddash_organized_backend\06_Shared_Datastores\csv_exports": r"Meddash_organized_backend\06_Shared_Datastores\csv_exports",
    r"Meddash_organized_backend/06_Shared_Datastores/csv_exports": r"Meddash_organized_backend/06_Shared_Datastores/csv_exports",
    r"Meddash_organized_backend\\06_Shared_Datastores\\csv_exports": r"Meddash_organized_backend\\06_Shared_Datastores\\csv_exports",
    
    r"Meddash_organized_backend\07_DevOps_Observability\logs": r"Meddash_organized_backend\07_DevOps_Observability\logs",
    r"Meddash_organized_backend/07_DevOps_Observability/logs": r"Meddash_organized_backend/07_DevOps_Observability/logs",
    r"Meddash_organized_backend\\07_DevOps_Observability\\logs": r"Meddash_organized_backend\\07_DevOps_Observability\\logs",

    r"Meddash_organized_backend\07_DevOps_Observability\telegram_notifier.py": r"Meddash_organized_backend\07_DevOps_Observability\telegram_notifier.py",
    r"Meddash_organized_backend/07_DevOps_Observability/telegram_notifier.py": r"Meddash_organized_backend/07_DevOps_Observability/telegram_notifier.py",
    r"Meddash_organized_backend\\07_DevOps_Observability\\telegram_notifier.py": r"Meddash_organized_backend\\07_DevOps_Observability\\telegram_notifier.py",
    
    # 01 Scripts
    r"Meddash_organized_backend\01_KOL_Data_Engine\nightly_scheduler.py": r"Meddash_organized_backend\01_KOL_Data_Engine\nightly_scheduler.py",
    r"Meddash_organized_backend\01_KOL_Data_Engine\run_pipeline.py": r"Meddash_organized_backend\01_KOL_Data_Engine\run_pipeline.py",
    r"Meddash_organized_backend\01_KOL_Data_Engine\extract_publications.py": r"Meddash_organized_backend\01_KOL_Data_Engine\extract_publications.py",
    r"Meddash_organized_backend\01_KOL_Data_Engine\db_ingestion.py": r"Meddash_organized_backend\01_KOL_Data_Engine\db_ingestion.py",
    r"Meddash_organized_backend\01_KOL_Data_Engine\kol_disambiguator.py": r"Meddash_organized_backend\01_KOL_Data_Engine\kol_disambiguator.py",
    r"Meddash_organized_backend\01_KOL_Data_Engine\kol_weight.py": r"Meddash_organized_backend\01_KOL_Data_Engine\kol_weight.py",
    r"Meddash_organized_backend\01_KOL_Data_Engine\review_disambiguations.py": r"Meddash_organized_backend\01_KOL_Data_Engine\review_disambiguations.py",
    r"Meddash_organized_backend\01_KOL_Data_Engine\load_sjr.py": r"Meddash_organized_backend\01_KOL_Data_Engine\load_sjr.py",
    
    # 02 Scripts
    r"Meddash_organized_backend\02_CT_Data_Engine\ct_initializer.py": r"Meddash_organized_backend\02_CT_Data_Engine\ct_initializer.py",
    r"Meddash_organized_backend\02_CT_Data_Engine\ct_crawler.py": r"Meddash_organized_backend\02_CT_Data_Engine\ct_crawler.py",
    r"Meddash_organized_backend\02_CT_Data_Engine\ct_ingestion.py": r"Meddash_organized_backend\02_CT_Data_Engine\ct_ingestion.py",
    r"Meddash_organized_backend\02_CT_Data_Engine\ct_mesh_mapper.py": r"Meddash_organized_backend\02_CT_Data_Engine\ct_mesh_mapper.py",
    r"Meddash_organized_backend\02_CT_Data_Engine\ct_kol_bridge.py": r"Meddash_organized_backend\02_CT_Data_Engine\ct_kol_bridge.py",
    r"Meddash_organized_backend\02_CT_Data_Engine\ct_results_parser.py": r"Meddash_organized_backend\02_CT_Data_Engine\ct_results_parser.py",
    r"Meddash_organized_backend\02_CT_Data_Engine\ct_pub_bridge.py": r"Meddash_organized_backend\02_CT_Data_Engine\ct_pub_bridge.py",
    r"Meddash_organized_backend\02_CT_Data_Engine\ct_eligibility_parser.py": r"Meddash_organized_backend\02_CT_Data_Engine\ct_eligibility_parser.py",
    r"Meddash_organized_backend\02_CT_Data_Engine\ct_raw_json": r"Meddash_organized_backend\02_CT_Data_Engine\ct_raw_json",

    # 03
    r"Meddash_organized_backend\03_BioCrawler_GTM": r"Meddash_organized_backend\03_BioCrawler_GTM",
    r"Meddash_organized_backend/03_BioCrawler_GTM": r"Meddash_organized_backend/03_BioCrawler_GTM",
    r"Meddash_organized_backend\\03_BioCrawler_GTM": r"Meddash_organized_backend\\03_BioCrawler_GTM",

    r"Meddash_organized_backend\03_BioCrawler_GTM": r"Meddash_organized_backend\03_BioCrawler_GTM",
    r"Meddash_organized_backend/03_BioCrawler_GTM": r"Meddash_organized_backend/03_BioCrawler_GTM",
    r"Meddash_organized_backend\\03_BioCrawler_GTM": r"Meddash_organized_backend\\03_BioCrawler_GTM",

    # 04
    r"Meddash_organized_backend\04_Product_KOL_Briefs\generate_kol_brief.py": r"Meddash_organized_backend\04_Product_KOL_Briefs\generate_kol_brief.py",
    r"Meddash_organized_backend\04_Product_KOL_Briefs\export_kols.py": r"Meddash_organized_backend\04_Product_KOL_Briefs\export_kols.py",
    r"Meddash_organized_backend\04_Product_KOL_Briefs\kol_briefs": r"Meddash_organized_backend\04_Product_KOL_Briefs\kol_briefs",
    r"Meddash_organized_backend\04_Product_KOL_Briefs\KOL_BRIEF_PRODUCT_1": r"Meddash_organized_backend\04_Product_KOL_Briefs\KOL_BRIEF_PRODUCT_1",

    # 05
    r"Meddash_organized_backend\05_Product_TA_Landscape\fetch_ta_landscape_data.py": r"Meddash_organized_backend\05_Product_TA_Landscape\fetch_ta_landscape_data.py",
    r"Meddash_organized_backend\05_Product_TA_Landscape\generate_ta_landscape_stepwise.py": r"Meddash_organized_backend\05_Product_TA_Landscape\generate_ta_landscape_stepwise.py",
    r"Meddash_organized_backend\05_Product_TA_Landscape\ta_landscape_cache": r"Meddash_organized_backend\05_Product_TA_Landscape\ta_landscape_cache",
    r"Meddash_organized_backend\05_Product_TA_Landscape\generate_ta_landscape.py": r"Meddash_organized_backend\05_Product_TA_Landscape\generate_ta_landscape.py",

    # Generic remaining
    r"Meddash_organized_backend\07_DevOps_Observability\meddash_filepaths.md": r"Meddash_organized_backend\07_DevOps_Observability\meddash_filepaths.md",
    r"Meddash_organized_backend\07_DevOps_Observability\backup_antigravity.ps1": r"Meddash_organized_backend\07_DevOps_Observability\backup_antigravity.ps1",
}

# Expand the list with / and \\ for specific scripts that missed it
expanded_reps = {}
for k, v in reps.items():
    expanded_reps[k] = v
    if '\\' in k and '/' not in k:
        expanded_reps[k.replace('\\', '/')] = v.replace('\\', '/')
        expanded_reps[k.replace('\\', '\\\\')] = v.replace('\\', '\\\\')

changed_files = 0
for root, _, files in os.walk(base_dir):
    for filename in files:
        if filename.endswith(('.py', '.md', '.bat', '.ps1', '.txt', '.sql', '.yaml', '.json')):
            fpath = os.path.join(root, filename)
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            new_content = content
            for old, new in expanded_reps.items():
                new_content = new_content.replace(old, new)
            
            # Additional fallback catch-all for any remaining `scratch\meddash` without specific file matching
            # Be very careful! Only run this dynamically if needed, but for now we skip.
            if new_content != content:
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                changed_files += 1

print(f"Patched {changed_files} files.")
