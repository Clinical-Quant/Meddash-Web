# 10_KOL_Centrality_Engine

Single-shot Meddash KOL authorship centrality engine.

Modes:

```bash
python 10_KOL_Centrality_Engine/run_centrality.py --dry-run --write-local
python 10_KOL_Centrality_Engine/schema_validate.py --create --json
python 10_KOL_Centrality_Engine/run_centrality.py --write-supabase --triggered-by manual
```

Safety:
- never prints Supabase credentials;
- writes summary JSON on success, partial, and failure;
- preserves previous latest scores until a new run is ready;
- labels scores as mapped authorship centrality, not absolute real-world influence.
