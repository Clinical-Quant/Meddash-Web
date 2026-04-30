import os
import socket
import time
from typing import List, Dict, Any
from Bio import Entrez

# Always tell NCBI who you are when using E-utilities
# In production, replace this with your actual institutional or developer email
Entrez.email = "meddash_developer@example.com"

# Scheduled runs must not hang forever on NCBI E-utilities. Bio.Entrez uses
# urllib underneath, so a process-wide socket timeout is the simplest safe guard.
socket.setdefaulttimeout(int(os.getenv("MEDDASH_PUBMED_TIMEOUT", "20")))

# It's also highly recommended to use an API key for higher rate limits (10 requests/sec instead of 3).
# Entrez.api_key = "YOUR_NCBI_API_KEY" 

def fetch_recent_publications(therapeutic_area: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Queries PubMed for the most recent publications matching a therapeutic area
    and extracts metadata including parsed authorship.
    """
    print(f"[{time.strftime('%H:%M:%S')}] Searching PubMed for the most recent {max_results} publications for: '{therapeutic_area}'...")
    
    # 1. Search for the keyword to get a list of PMIDs (PubMed IDs)
    try:
        # retmax limits the number of returned IDs, sort="date" ensures we get the most recent
        # We append ' AND medline[sb]' to guarantee the articles have completed MeSH indexing.
        search_handle = Entrez.esearch(db="pubmed", term=f"{therapeutic_area} AND medline[sb]", retmax=max_results, sort="date")
        search_results = Entrez.read(search_handle)
        search_handle.close()
    except Exception as e:
        print(f"Error during search: {e}")
        return []

    id_list = search_results.get("IdList", [])
    if not id_list:
        print("No results found.")
        return []

    print(f"[{time.strftime('%H:%M:%S')}] Found {len(id_list)} publication IDs. Fetching details sequentially with strict rate limiting...\n")
    
    extracted_data = []

    # 2. Fetch details for the IDs
    # E-utilities strictly enforces rate limits. Without an API key, it is 3 requests per second.
    # To be extremely safe and avoid IP bans, we will enforce a 0.4s sleep (max ~2.5 req/sec).
    # We could fetch them in a batch, but fetching individually makes parsing sometimes easier to debug.
    # For 50 articles, batching is usually preferred, but demonstrating the explicit rate-limit as requested:
    
    # Alternatively, we can fetch all at once and parse, but the prompt emphasizes strict rate limiting via time.sleep().
    # Note: Fetching in batches of 10-50 is more efficient for NCBI, but we'll do individual fetches here
    # to explicitly show the sleep mechanism.
    
    for _, pmid in enumerate(id_list, 1):
        try:
            # STRICT RATE LIMITING: pause for 0.4 seconds before every fetch
            time.sleep(0.4) 
            
            fetch_handle = Entrez.efetch(db="pubmed", id=pmid, retmode="xml")
            article_records = Entrez.read(fetch_handle)
            fetch_handle.close()

            # Safely navigate the nested PubMed XML/JSON structure
            # Even if we fetch 1 ID, it comes back as a list
            if not article_records or "PubmedArticle" not in article_records:
                continue
                
            pubmed_article = article_records['PubmedArticle'][0]
            medline_citation = pubmed_article.get("MedlineCitation", {})
            article = medline_citation.get("Article", {})
            
            # --- Extract Publication Type ---
            pub_type = "Journal Article" # Default
            pub_types_list = article.get("PublicationTypeList", [])
            if pub_types_list:
                # The PublicationTypeList contains StringElements, each with a 'UI' attribute
                # The text itself is the type (e.g. 'Clinical Trial')
                pub_type = str(pub_types_list[0])  # Take the primary/first type listed

            # --- Extract General Info & Rich Journal Metadata ---
            title = article.get("ArticleTitle", "No Title Available")
            
            journal_dict = article.get("Journal", {})
            journal_title = journal_dict.get("Title", "Unknown Journal")
            issn = str(journal_dict.get("ISSN", ""))
            
            journal_issue = journal_dict.get("JournalIssue", {})
            volume = journal_issue.get("Volume", "")
            issue = journal_issue.get("Issue", "")
            
            pub_date_dict = journal_issue.get("PubDate", {})
            year = pub_date_dict.get("Year", "")
            month = pub_date_dict.get("Month", "")
            pub_date = f"{year} {month}".strip() or "Unknown Date"
            
            pages = article.get("Pagination", {}).get("MedlinePgn", "")
            
            # Construct rich citation: "Nature Medicine. 2024 Mar;volume 30(issue 3): pages 455-462."
            rich_journal = f"{journal_title}. {pub_date}"
            if volume: rich_journal += f";volume {volume}"
            if issue: rich_journal += f"(issue {issue})"
            if pages: rich_journal += f": pages {pages}"
            if rich_journal: rich_journal += "."
            
            # --- Extract Abstract ---
            abstract = "No Abstract Available"
            abstract_texts = article.get("Abstract", {}).get("AbstractText", [])
            if abstract_texts:
                parts = []
                for pt in abstract_texts:
                    label = getattr(pt, "attributes", {}).get("Label", "")
                    text_content = str(pt)
                    if label and label != "UNLABELLED":
                        parts.append(f"{label}: {text_content}")
                    else:
                        parts.append(text_content)
                abstract = " ".join(parts)
                
            # --- Construct URL ---
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            
            # --- Extract DOI ---
            doi = "No DOI Found"
            article_id_list = pubmed_article.get("PubmedData", {}).get("ArticleIdList", [])
            for article_id in article_id_list:
                if getattr(article_id, "attributes", {}).get("IdType") == "doi":
                    doi = str(article_id)
                    break
            
            # --- Parse Authors ---
            authors_list = article.get("AuthorList", [])
            parsed_authors = []
            
            if authors_list:
                num_authors = len(authors_list)
                for i, author in enumerate(authors_list):
                    if "CollectiveName" in author:
                        full_name = author["CollectiveName"]
                    else:
                        last_name = author.get("LastName", "")
                        fore_name = author.get("ForeName", "")
                        full_name = f"{fore_name} {last_name}".strip()
                    
                    if not full_name:
                        continue
                    
                    position = "Middle"
                    is_primary = False
                    
                    if i == 0:
                        position = "First"
                        is_primary = True
                    elif i == num_authors - 1 and num_authors > 1:
                        position = "Last"
                        is_primary = True 
                        
                    # Extract ORCID if present — lives inside author's Identifier list
                    orcid = None
                    for identifier in author.get("Identifier", []):
                        if getattr(identifier, "attributes", {}).get("Source", "") == "ORCID":
                            orcid_raw = str(identifier)
                            # Normalize to bare 16-digit format: 0000-0001-2345-6789
                            orcid = orcid_raw.replace("https://orcid.org/", "").strip()
                            break

                    # Extract institution affiliation — available from PubMed since ~2014
                    # AffiliationInfo is a list of dicts; the first entry is the primary affiliation
                    affiliation = None
                    affiliation_list = author.get("AffiliationInfo", [])
                    if affiliation_list:
                        raw_affil: str = str(affiliation_list[0].get("Affiliation", "")).strip()
                        if raw_affil:
                            # Affiliation strings can be very long (250+ chars); truncate cleanly at 255
                            affiliation = raw_affil[:255]

                    parsed_authors.append({
                        "name": full_name,
                        "position": position,
                        "is_primary": is_primary,
                        "orcid": orcid,              # None if not provided by PubMed
                        "affiliation": affiliation   # None for pre-2014 papers
                    })


            # --- Parse MeSH Terms ---
            # MeSH terms are usually found at medline_citation['MeshHeadingList']
            mesh_list = medline_citation.get("MeshHeadingList", [])
            parsed_mesh = []
            
            for mesh_heading in mesh_list:
                descriptor = mesh_heading.get('DescriptorName')
                if not descriptor:
                    continue
                    
                mesh_term = str(descriptor)
                mesh_id = descriptor.attributes.get('UI', 'Unknown')
                is_major = 1 if descriptor.attributes.get('MajorTopicYN', 'N') == 'Y' else 0
                
                parsed_mesh.append({
                    "mesh_id": mesh_id,
                    "mesh_term": mesh_term,
                    "is_major_topic": is_major
                })

            # Append to our structured dataset
            extracted_data.append({
                "pmid": str(pmid),
                "doi": doi,
                "title": title,
                "journal": rich_journal,      # Now uses the rich citation
                "published_date": pub_date,
                "publication_type": pub_type, 
                "abstract": abstract,         # Added Field
                "url": url,                   # Added Field
                "issn": issn,                 # Added Field
                "authors": parsed_authors,
                "mesh_terms": parsed_mesh     
            })
            
            print(f"[{time.strftime('%H:%M:%S')}] Successfully fetched & parsed PMID: {pmid}")
                
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Error fetching/parsing PMID {pmid}: {e}")
            continue

    return extracted_data

if __name__ == "__main__":
    # Test the function with a target keyword and 50 results
    TARGET_TA = "Oncology"
    
    results = fetch_recent_publications(TARGET_TA, max_results=50)
    
    print("\n" + "="*80)
    print(f"  EXTRACTION RESULTS FOR: '{TARGET_TA}' (Total: {len(results)})")
    print("="*80 + "\n")
    
    # Print the first 5 parsed records clearly to the console to verify logic
    display_limit = min(5, len(results))
    print(f"Displaying the first {display_limit} parsed publications...\n")
    
    for idx, pub in enumerate(results[:display_limit], 1):
        print(f"--- Publication {idx} ---")
        print(f"Title:          {pub['title']}")
        print(f"PMID:           {pub['pmid']}")
        print(f"DOI:            {pub['doi']}")
        print(f"URL:            {pub.get('url', 'N/A')}")
        print(f"Journal:        {pub['journal']}")
        print(f"Published Date: {pub['published_date']}")
        print(f"Abstract Preview: {pub.get('abstract', '')[:100]}...")
        print("Authors:")
        
        for author in pub['authors']:
            primary_tag = " <--- [PRIMARY AUTHOR]" if author['is_primary'] else ""
            print(f"  - {author['name']} ({author['position']}){primary_tag}")
        print("\n")
        
    if len(results) > display_limit:
        print(f"... and {len(results) - display_limit} more publications hidden from console output.\n")
