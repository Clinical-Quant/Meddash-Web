import sqlite3
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Define database path relative to this script's location
DB_PATH = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\meddash_kols.db"

def calculate_svs_metrics(df):
    """
    Calculates the Scientific Velocity Score (SVS) metrics for a given DataFrame of publications.
    Requires columns: 'kol_id', 'published_date', 'is_primary_author', 'author_position'
    """
    if df.empty:
        return pd.DataFrame()

    # Convert published_date to datetime, handling potential errors
    df['published_date'] = pd.to_datetime(df['published_date'].astype(str), errors='coerce')
    # Drop rows with invalid dates as they can't be scored
    df = df.dropna(subset=['published_date'])
    
    if df.empty:
         return pd.DataFrame()

    # 1. & 2. RWPS (Recency Score) and ALB (Authorship Bonus)
    current_date = datetime.now()
    
    def calculate_paper_score(row):
        # Calculate age in years
        age_years = (current_date - row['published_date']).days / 365.25
        
        # RWPS base weight
        if age_years <= 1:
            base_weight = 1.0
        elif age_years <= 2:
            base_weight = 0.8
        elif age_years <= 3:
            base_weight = 0.6
        elif age_years <= 5:
            base_weight = 0.4
        elif age_years <= 10:
            base_weight = 0.2
        else:
            base_weight = 0.0 # Older than 10 years gets 0 weight for velocity
            
        # ALB multiplier
        alb_multiplier = 1.0
        if row['is_primary_author'] == 1 or row['author_position'] in ['First', 'Last']:
            alb_multiplier = 1.5
            
        # The paper's contribution to the score
        return base_weight, alb_multiplier, base_weight * alb_multiplier

    # Apply calculations
    scores = df.apply(calculate_paper_score, axis=1, result_type='expand')
    df['rwps_base'] = scores[0]
    df['alb_mult'] = scores[1]
    df['paper_weight'] = scores[2]

    # Aggregate by KOL
    kol_metrics = df.groupby('kol_id').agg(
        total_rwps=('rwps_base', 'sum'),
        total_alb=('alb_mult', lambda x: np.mean(x) if len(x) > 0 else 0) # Average ALB multiplier
    ).reset_index()

    # 3. VAC (Velocity Momentum)
    # Calculate annualized rates
    date_24m_ago = current_date - relativedelta(months=24)
    date_60m_ago = current_date - relativedelta(months=60) # Prior 36 months before the last 24

    def calculate_vac(kol_pubs):
        # Papers in last 24 months (2 years)
        pubs_last_24 = kol_pubs[kol_pubs['published_date'] >= date_24m_ago]
        annual_rate_last_24 = len(pubs_last_24) / 2.0

        # Papers in prior 36 months (years 3, 4, 5 ago)
        pubs_prior_36 = kol_pubs[(kol_pubs['published_date'] >= date_60m_ago) & (kol_pubs['published_date'] < date_24m_ago)]
        annual_rate_prior_36 = len(pubs_prior_36) / 3.0

        return annual_rate_last_24 - annual_rate_prior_36

    # Calculate VAC for each KOL
    vac_scores = df.groupby('kol_id').apply(calculate_vac, include_groups=False).reset_index(name='vac_score')
    
    # Merge metrics
    kol_metrics = pd.merge(kol_metrics, vac_scores, on='kol_id', how='left')
    
    # 4. Final SVS Formula: (0.5 * RWPS) + (0.3 * VAC) + (0.2 * ALB)
    # Using total_rwps for the RWPS component, and average ALB multiplier for ALB component
    kol_metrics['raw_svs'] = (0.5 * kol_metrics['total_rwps']) + (0.3 * kol_metrics['vac_score']) + (0.2 * kol_metrics['total_alb'])

    return kol_metrics


def export_kols():
    print("=" * 60)
    print(" Meddash KOL Exporter (SVS Enabled) ")
    print("=" * 60)
    
    # Get search term from command line arguments or prompt the user
    if len(sys.argv) > 1:
        term = " ".join(sys.argv[1:])
        print(f"Searching for Specific Disease MeSH Term or ID: '{term}'")
    else:
        term = input("Enter a Specific Disease MeSH term or MeSH ID to filter KOLs: ").strip()
        if not term:
            print("Search term cannot be empty. Exiting.")
            sys.exit(1)

    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}. Please run the ingestion pipeline first.")
        sys.exit(1)

    print(f"Connecting to database to calculate SVS metrics...")
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # --- 1. Calculate Broad Therapeutic Area score (tRWPS) across ALL publications ---
        # Fetch ALL publications for all KOLs to calculate the baseline/broad velocity
        print("Calculating Broad Therapeutic Area scores (tRWPS)...")
        broad_query = """
        SELECT 
            ka.kol_id,
            p.pmid,
            p.published_date,
            ka.is_primary_author,
            ka.author_position
        FROM kol_authorships ka
        JOIN publications p ON ka.publication_id = p.id
        """
        broad_df = pd.read_sql_query(broad_query, conn)
        t_metrics = calculate_svs_metrics(broad_df)
        
        if t_metrics.empty:
             print("Insufficient data in database to calculate scores.")
             sys.exit(1)

        # Normalize tRWPS (0-100)
        # Handle case where min == max to avoid division by zero
        t_min = t_metrics['raw_svs'].min()
        t_max = t_metrics['raw_svs'].max()
        if t_max > t_min:
            t_metrics['tRWPS'] = ((t_metrics['raw_svs'] - t_min) / (t_max - t_min)) * 100
        else:
             t_metrics['tRWPS'] = 50.0 # Default if everyone is the same
             
        # Keep only necessary broad columns
        t_scores = t_metrics[['kol_id', 'tRWPS']]


        # --- 2. Calculate Specific Disease MeSH score (dRWPS) for the search term ---
        print(f"Calculating Specific Disease MeSH scores (dRWPS) for '{term}'...")
        specific_query = """
        SELECT 
            ka.kol_id,
            k.first_name,
            k.last_name,
            p.pmid,
            p.published_date,
            ka.is_primary_author,
            ka.author_position,
            mo.mesh_term
        FROM kols k
        JOIN kol_authorships ka ON k.id = ka.kol_id
        JOIN publications p ON ka.publication_id = p.id
        JOIN publication_mesh_map pmm ON p.pmid = pmm.pmid
        JOIN mesh_ontology mo ON pmm.mesh_id = mo.mesh_id
        WHERE mo.mesh_term LIKE ? OR mo.mesh_id = ?
        """
        search_term_wildcard = f"%{term}%"
        specific_df = pd.read_sql_query(specific_query, conn, params=(search_term_wildcard, term))
        
        if specific_df.empty:
            print(f"\nNo publications found associated with the specific MeSH term: '{term}'")
            # We could still output the broad scores, but usually, we want to filter the cohort
            sys.exit(0)
            
        d_metrics = calculate_svs_metrics(specific_df)
        
        # Normalize dRWPS (0-100) for the cohort matching this term
        if not d_metrics.empty:
            d_min = d_metrics['raw_svs'].min()
            d_max = d_metrics['raw_svs'].max()
            if d_max > d_min:
                d_metrics['dRWPS'] = ((d_metrics['raw_svs'] - d_min) / (d_max - d_min)) * 100
            else:
                 d_metrics['dRWPS'] = 50.0
        else:
             # Should not happen given df.empty check above, but safe
             d_metrics['dRWPS'] = 0.0

        # Keep only necessary specific columns and raw counts for context
        d_scores = d_metrics[['kol_id', 'dRWPS']].copy()
        
        # Calculate context metrics for the specific disease
        disease_context = specific_df.groupby('kol_id').agg(
            total_disease_pubs=('pmid', 'nunique'),
            most_recent_disease_pub=('published_date', 'max'),
            disease_mesh_topics=('mesh_term', lambda x: ', '.join(set(x)))
        ).reset_index()
        
        # Format date nicely for the client CSV
        disease_context['most_recent_disease_pub'] = disease_context['most_recent_disease_pub'].dt.strftime('%Y-%m')
        
        d_scores = pd.merge(d_scores, disease_context, on='kol_id', how='left')


        # --- 3. Final Merge and Formatting ---
        print("Finalizing results...")
        # Get KOL names (using specific_df to ensure we only get KOLs who match the search)
        kols_info = specific_df[['kol_id', 'first_name', 'last_name']].drop_duplicates()
        
        # Merge everything
        final_df = pd.merge(kols_info, d_scores, on='kol_id', how='inner')
        final_df = pd.merge(final_df, t_scores, on='kol_id', how='left')
        
        # Clean up column names for the CSV
        final_df = final_df.rename(columns={
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'dRWPS': 'Specific Disease SVS (dRWPS)',
            'tRWPS': 'Broad Area SVS (tRWPS)',
            'total_disease_pubs': 'Total Relevant Publications',
            'most_recent_disease_pub': 'Most Recent Publication Date',
            'disease_mesh_topics': 'Matching MeSH Topics'
        })
        
        # Drop internal IDs and sort by the specific disease score
        final_df = final_df.drop(columns=['kol_id'])
        final_df = final_df.sort_values(by='Specific Disease SVS (dRWPS)', ascending=False)
        
        # Round the scores to 2 decimal places for neatness
        final_df['Specific Disease SVS (dRWPS)'] = final_df['Specific Disease SVS (dRWPS)'].round(2)
        final_df['Broad Area SVS (tRWPS)'] = final_df['Broad Area SVS (tRWPS)'].round(2)

        # Export
        filename_term = "".join([c if c.isalnum() else "_" for c in term])
        
        # Divert exports into the /export_scripts/ directory to keep the workspace clean
        export_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'export_scripts'))
        os.makedirs(export_dir, exist_ok=True)
        output_file = os.path.join(export_dir, f"KOL_Export_{filename_term}_SVS.csv")
        
        try:
            final_df.to_csv(output_file, index=False)
        except PermissionError:
            print(f"\n[!] PERMISSION ERROR: Could not write to '{output_file}'.")
            print("[!] Please ensure the CSV file is closed (e.g. exit out of Excel or another viewer) and try again.")
            sys.exit(1)
        
        print(f"\nSUCCESS! Found {len(final_df)} KOL(s).")
        print(f"Exported client-ready CSV with SVS scores to: {output_file}")
        print("\nPreview of top SVS results:")
        print(final_df[['First Name', 'Last Name', 'Specific Disease SVS (dRWPS)', 'Broad Area SVS (tRWPS)', 'Total Relevant Publications']].head().to_string(index=False))
            
    except Exception as e:
        print(f"An error occurred during SVS calculation/export: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    export_kols()
