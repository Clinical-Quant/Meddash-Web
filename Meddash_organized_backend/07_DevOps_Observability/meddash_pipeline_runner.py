#!/usr/bin/env python3
"""Meddash Pipeline Runner — replaces all 5 n8n Code nodes.
Called by n8n Execute Command nodes instead of JavaScript Code nodes.

Usage: python3 meddash_pipeline_runner.py <command> [args]

Commands:
  engine01       — Run KOL pipeline
  engine02       — Run CT Delta crawler
  engine03       — Run BioCrawler
  health         — Generate health check summary
  log            — Save pipeline run log from stdin
"""
import sys
import os
import json
import subprocess
from datetime import datetime

MEDDASH_ROOT = '/mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend'
SUMMARY_DIR = os.path.join(MEDDASH_ROOT, '06_Shared_Datastores', 'pipeline_summaries')
STATE_DIR = os.path.join(MEDDASH_ROOT, '06_Shared_Datastores', 'pipeline_state')
ENV = {
    **os.environ,
    'MEDDASH_ROOT': MEDDASH_ROOT,
    'PYTHONPATH': os.path.join(MEDDASH_ROOT, '07_DevOps_Observability'),
    # n8n/Ops API sends centralized Telegram health messages.
    # Disable old per-engine notifier defaults that can produce Telegram 404 noise.
    'DISABLE_INTERNAL_TELEGRAM': '1',
}

def run_engine(name, script_dir, command):
    """Run a pipeline engine and return structured result."""
    try:
        start = datetime.now()
        result = subprocess.run(
            command,
            shell=True,
            cwd=script_dir,
            capture_output=True,
            text=True,
            env=ENV,
            timeout=600  # 10 min max
        )
        elapsed = (datetime.now() - start).total_seconds()
        return {
            'engine': name,
            'status': 'success' if result.returncode == 0 else 'error',
            'exit_code': result.returncode,
            'stdout': result.stdout[-2000:] if result.stdout else '',
            'stderr': result.stderr[-2000:] if result.stderr else '',
            'elapsed_seconds': round(elapsed, 1),
        }
    except subprocess.TimeoutExpired:
        return {'engine': name, 'status': 'timeout', 'elapsed_seconds': 600}
    except Exception as e:
        return {'engine': name, 'status': 'error', 'error': str(e)}

def engine01():
    # Scheduled/Ops API KOL mode must be bounded. The full KOL crawl can still
    # be run manually with nightly_scheduler.py defaults, but the daily pipeline
    # needs a predictable completion window for dashboard freshness and n8n.
    return run_engine('KOL', 
        os.path.join(MEDDASH_ROOT, '01_KOL_Data_Engine'),
        'python3 nightly_scheduler.py --max-targets 5 --max-results 5 --skip-disambiguation --skip-weights --skip-centrality --json-summary')

def engine02():
    return run_engine('CT_Delta',
        os.path.join(MEDDASH_ROOT, '02_CT_Data_Engine'),
        'python3 ct_crawler.py --mode delta --hours 24')

def engine03():
    # Workflow-safe BioCrawler mode: bounded API/deep sample.
    # `--mode all` can exceed n8n HTTP execution windows because it performs slow
    # Clearbit/SEC/ATS enrichment with sleeps across many companies.
    # Use `--mode test` for reliable scheduled runs; run full deep crawls manually when needed.
    return run_engine('BioCrawler',
        os.path.join(MEDDASH_ROOT, '03_BioCrawler_GTM'),
        'python3 biocrawler.py --mode test')

def health_check():
    """Check summary files and DB status."""
    health = {
        'overall_status': 'healthy',
        'engines': [],
        'timestamp': datetime.now().isoformat(),
    }
    
    summary_files = [
        ('KOL', 'kol_pipeline_summary.json'),
        ('CT_Delta', 'ct_crawler_summary.json'),
        ('BioCrawler', 'biocrawler_summary.json'),
    ]
    
    for name, fname in summary_files:
        fpath = os.path.join(SUMMARY_DIR, fname)
        try:
            with open(fpath) as f:
                data = json.load(f)
            health['engines'].append({
                'name': name,
                'status': data.get('status', 'unknown'),
                'last_run': data.get('timestamp', data.get('date', 'unknown')),
                'records': data.get('total_kols', data.get('total_trials', data.get('total_leads', 0))),
            })
        except Exception as e:
            health['engines'].append({'name': name, 'status': 'missing', 'error': str(e)})
            health['overall_status'] = 'degraded'
    
    # Check DBs
    import sqlite3
    dbs = [
        ('KOL', 'meddash_kols.db'),
        ('CT', 'ct_trials.db'),
        ('BioCrawler', 'biocrawler_leads.db'),
    ]
    for name, dbfile in dbs:
        dbpath = os.path.join(MEDDASH_ROOT, '06_Shared_Datastores', dbfile)
        try:
            conn = sqlite3.connect(dbpath)
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
            table = cur.fetchone()[0]
            cur.execute(f"SELECT COUNT(*) FROM [{table}]")
            count = cur.fetchone()[0]
            conn.close()
            health.setdefault('databases', []).append({'name': name, 'rows': count, 'status': 'ok'})
        except Exception as e:
            health.setdefault('databases', []).append({'name': name, 'status': 'error', 'error': str(e)})
            health['overall_status'] = 'degraded'
    
    # MeSH rotation
    now = datetime.now()
    start = datetime(now.year, 1, 1)
    week = ((now - start).days + start.weekday() + 1) // 7
    categories = ['Neoplasms (C04)', 'Nervous System (C10)', 'Cardiovascular (C14)', 
                   'Immune System (C20)', 'Respiratory (C08)', 'Digestive (C11)',
                   'Musculoskeletal (C05)', 'Mental Disorders (F03)', 'Infections (C01)',
                   'Endocrine (C19)', 'Eye Diseases (C11)', 'Urogenital (C12)']
    health['rotation'] = {
        'week': week,
        'category': categories[(week-1) % 12],
    }
    
    return health

def save_log():
    """Save pipeline run log from stdin."""
    try:
        input_data = sys.stdin.read()
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H%M%S')
        
        os.makedirs(STATE_DIR, exist_ok=True)
        log_file = os.path.join(STATE_DIR, f'pipeline_run_{date_str}_{time_str}.json')
        
        with open(log_file, 'w') as f:
            f.write(input_data)
        
        return {'status': 'saved', 'file': log_file}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: meddash_pipeline_runner.py <command>'}))
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'engine01':
        result = engine01()
    elif cmd == 'engine02':
        result = engine02()
    elif cmd == 'engine03':
        result = engine03()
    elif cmd == 'health':
        result = health_check()
    elif cmd == 'log':
        result = save_log()
    else:
        result = {'error': f'Unknown command: {cmd}'}
    
    print(json.dumps(result, indent=2))