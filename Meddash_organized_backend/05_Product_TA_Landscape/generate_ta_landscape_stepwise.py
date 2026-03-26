import os
import json
import sqlite3
import urllib.request
import urllib.parse
from datetime import datetime

# Database / Path Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, 'ta_landscape_cache')
REPORTS_DIR = os.path.join(BASE_DIR, 'ta_reports')

if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

GEMINI_MODEL = "gemini-2.5-pro"

class GeminiClient:
    @staticmethod
    def generate(prompt, model=GEMINI_MODEL):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            # Fallback to check raw Windows user environment if running in an old terminal session
            try:
                import subprocess
                out = subprocess.check_output('powershell -c "[Environment]::GetEnvironmentVariable(\'GEMINI_API_KEY\', \'User\')"', shell=True).decode().strip()
                if out: 
                    api_key = out
            except Exception:
                pass
                
        if not api_key:
            return "[ERROR] GEMINI_API_KEY environment variable not set. Please restart your terminal."
            
        print(f"\n[~] Prompting Gemini ({model})...")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2}
        }
        
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                for part in result.get('candidates', [{}])[0].get('content', {}).get('parts', []):
                    if 'text' in part:
                        return part['text']
                return "[WARNING] Valid response structure not found."
        except Exception as e:
            print(f"[!] Gemini API Error: {e}")
            return f"[ERROR CALLING GEMINI: {e}]"

# Definition of the 11 Sections
SECTIONS = [
    {
        "id": "1",
        "name": "Executive Summary",
        "rules": "Summarize the entire landscape in 500-700 words. Focus on trial phases, geographic hotspots, key sponsors, and primary MOAs. Tone must be authoritative and consulting-grade.",
        "data_keys": ["clinical_trials_data", "kol_network", "biocrawler_signals"]
    },
    {
        "id": "2",
        "name": "Disease Overview",
        "rules": "Provide disease definition, epidemiology, pathophysiology, current SoC, and unmet needs based on PubMed abstracts. 700-1000 words.",
        "data_keys": ["pubmed_literature"]
    },
    {
        "id": "3",
        "name": "Clinical Development Landscape",
        "rules": "Analyze trial volume, phase distribution, recruitment status, and study design. 800-1000 words.",
        "data_keys": ["clinical_trials_data"]
    },
    {
        "id": "4",
        "name": "Geographic Trial Footprint",
        "rules": "Identify global distribution, regional hubs, city-level concentration, and institutional clusters. 800-1000 words. Use the geography data.",
        "data_keys": ["clinical_trials_data"]
    },
    {
        "id": "5",
        "name": "Institutional Leadership",
        "rules": "Analyze top research centers and institutions leading clinical trials. Evaluate network centrality. 800-1000 words.",
        "data_keys": ["kol_network"]
    },
    {
        "id": "6",
        "name": "Key Opinion Leader Network",
        "rules": "Identify dominating investigators. 800-1000 words. Use KOL data.",
        "data_keys": ["kol_network"]
    },
    {
        "id": "7",
        "name": "Sponsor Landscape",
        "rules": "Analyze which organizations drive development. Industry vs Academic, leading sponsors. 800-1000 words.",
        "data_keys": ["clinical_trials_data", "biocrawler_signals"]
    },
    {
        "id": "8",
        "name": "Mechanism and Modality Trends",
        "rules": "Analyze therapeutic mechanisms, modalities, and combination therapies. 800-1000 words.",
        "data_keys": ["clinical_trials_data"]
    },
    {
        "id": "9",
        "name": "Strategic Signals & Development Catalysts",
        "rules": "Identify forward-looking catalysts, upcoming readouts (Phase 3), and competitive intelligence. 800-1200 words.",
        "data_keys": ["clinical_trials_data", "biocrawler_signals"]
    },
    {
        "id": "10",
        "name": "Methodology & Data Sources",
        "rules": "Provide a high-level, sophisticated methodology overview mentioning ClinicalTrials.gov, PubMed, etc. Do not mention internal algorithms or SQL logic. 400 words.",
        "data_keys": []
    },
    {
        "id": "11",
        "name": "References",
        "rules": "Generate Vancouver-style references using the provided PubMed PMIDs and NCT IDs. Do NOT cite internal databases.",
        "data_keys": ["pubmed_literature", "clinical_trials_data"]
    }
]

def build_prompt(section, landscape_data):
    prompt_context = ""
    for k in section["data_keys"]:
        if k in landscape_data:
            prompt_context += f"\\n--- {k.upper()} DATA ---\\n"
            prompt_context += json.dumps(landscape_data[k], indent=2)[:5000] # Limit size to prevent context overflow
            prompt_context += "\\n"
            
    base_prompt = f"""
    You are an elite biotech strategy consultant writing a specialized Therapeutic Area Landscape Report.
    Your tone must be highly analytical, neutral, objective, and sophisticated.
    Do not use marketing fluff word. Use precise clinical and financial terminology.
    
    You are writing SECTION {section['id']}: {section['name']}.
    
    SECTION RULES:
    {section['rules']}
    
    Format the output strictly in Markdown. Use headers (e.g., ## {section['name']}).
    
    Here is the exact intelligence data to use for this section. DO NOT invent fake clinical data. Stick strictly to the provided data.
    
    {prompt_context}
    
    WRITE SECTION {section['id']} NOW:
    """
    return base_prompt

def run_stepwise_generation(disease_term):
    safe_term = "".join(c if c.isalnum() else "_" for c in disease_term).strip("_").lower()
    cache_file = os.path.join(CACHE_DIR, f"{safe_term}_landscape_cache.json")
    
    if not os.path.exists(cache_file):
        print(f"[!] Cache not found for '{disease_term}'. Please run fetch_ta_landscape_data.py first.")
        return
        
    with open(cache_file, "r", encoding="utf-8") as f:
        landscape_data = json.load(f)
        
    report_file = os.path.join(REPORTS_DIR, f"TA_Landscape_{safe_term}.md")
    audit_file = os.path.join(REPORTS_DIR, f"TA_Landscape_{safe_term}_References_Audit.md")
    
    print(f"=== Starting Stepwise Generation for: {disease_term} ===")
    print(f"Output Report: {report_file}")
    print(f"Audit Trail: {audit_file}\n")
    
    # Initialize files
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"# Meddash TA Landscape: {disease_term}\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
    with open(audit_file, "w", encoding="utf-8") as f:
        f.write(f"# Primary Source Audit Trail: {disease_term}\n\n")

    for section in SECTIONS:
        print(f"\n{'='*50}\n[>] Processing Section {section['id']}: {section['name']}")
        
        while True:
            cmd = input(f"Generate Section {section['id']}? (y=yes / s=skip / q=quit): ").strip().lower()
            if cmd == 'q':
                print("[*] Aborting generation.")
                return
            elif cmd == 's':
                print("[*] Skipping section.")
                break
            elif cmd == 'y':
                prompt = build_prompt(section, landscape_data)
                
                # Write to audit
                with open(audit_file, "a", encoding="utf-8") as af:
                    af.write(f"## Section {section['id']} Audit Log\n")
                    af.write(f"**Data Keys Processed:** {', '.join(section['data_keys'])}\n\n")
                
                # Generate
                output = GeminiClient.generate(prompt)
                
                print(f"\n--- GENERATED PREVIEW (first 500 chars) ---")
                print(output[:500] + "\n...")
                print("-" * 50)
                
                acc = input("Approve and append to report? (y=yes / r=retry): ").strip().lower()
                if acc == 'y':
                    with open(report_file, "a", encoding="utf-8") as rf:
                        rf.write(output + "\n\n---\n\n")
                    print(f"[*] Section {section['id']} appended to {report_file}.")
                    break
                else:
                    print("[*] Retrying generation...")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Meddash Stepwise TA Landscape Generator")
    parser.add_argument("disease", type=str, help="The therapeutic area or condition (e.g., 'KRAS G12C')")
    args = parser.parse_args()
    
    run_stepwise_generation(args.disease)
