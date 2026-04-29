# KOL Network Centrality Analysis
## How to Measure Centrality in KOL Networks

**Purpose**: Explain standard centrality models, how to apply them to KOL data, and implementation approach.

**Created**: April 2026

---

## PART 1: What is Centrality and Why It Matters for KOLs

### 1.1 Definition

**Centrality** measures how important a node (KOL) is within a network. In KOL networks:
- **High centrality** = KOL is well-connected, influential, or controls information flow
- **Low centrality** = KOL is peripheral, less connected, or isolated

### 1.2 Why Centrality Matters for KOL Intelligence

| Centrality Type | What It Tells You | Business Value |
|-----------------|-------------------|----------------|
| **Degree** | How many direct collaborations | Breadth of influence |
| **Betweenness** | Broker between KOL clusters | Gatekeeper role, strategic partnerships |
| **Eigenvector** | Connected to influential KOLs | Quality of network |
| **Closeness** | Reach all KOLs quickly | Information dissemination speed |
| **PageRank** | Weighted influence by connection quality | Overall influence score |

---

## PART 2: Standard Centrality Models (The Mathematics)

### 2.1 Degree Centrality

**Definition**: Number of direct connections a node has.

**Formula**:
```
Degree_Centrality(v) = deg(v) / (n - 1)

where:
  deg(v) = number of edges connected to node v
  n = total number of nodes in network
```

**For KOLs**:
- Count of unique co-authors
- Count of unique trial collaborators
- Count of unique biotech affiliations

**Implementation**:
```python
def degree_centrality(graph):
    """
    Calculate degree centrality for all nodes.
    
    Time Complexity: O(n + m) where n=nodes, m=edges
    Space Complexity: O(n)
    """
    import networkx as nx
    return nx.degree_centrality(graph)

# For KOL networks:
# Raw degree (absolute count)
kol_degree = dict(graph.degree())

# Normalized degree (0-1 scale)
kol_degree_normalized = nx.degree_centrality(graph)
```

**Interpretation for KOLs**:
| Degree Score | Interpretation | KOL Tier |
|---------------|----------------|----------|
| > 50 connections | Super-connector, collaborates widely | Tier 1 |
| 20-50 connections | Well-connected, active collaborator | Tier 2 |
| 10-20 connections | Moderate connections | Tier 3 |
| < 10 connections | Limited collaborations | Tier 4 |

**Pros**: Simple, intuitive, fast to compute
**Cons**: Doesn't account for quality of connections

---

### 2.2 Betweenness Centrality

**Definition**: How often a node lies on the shortest path between other nodes.

**Formula**:
```
Betweenness_Centrality(v) = Σ [σ(s,t|v) / σ(s,t)]

where:
  σ(s,t) = number of shortest paths from s to t
  σ(s,t|v) = number of shortest paths from s to t passing through v
```

**For KOLs**:
- Bridges different KOL communities
- Controls information flow between clusters
- Strategic gatekeeper for medical affairs

**Implementation**:
```python
def betweenness_centrality(graph, normalized=True, k=None):
    """
    Calculate betweenness centrality.
    
    For large networks, use k-sample for approximation.
    
    Time Complexity: O(n * m) exact, O(k * n * m) sampled
    Space Complexity: O(n + m)
    """
    import networkx as nx
    
    if k and len(graph.nodes()) > 1000:
        # Use sampling for large networks
        return nx.betweenness_centrality(graph, k=k, normalized=normalized)
    else:
        return nx.betweenness_centrality(graph, normalized=normalized)

# For KOL networks with 10,000+ nodes:
kol_betweenness = betweenness_centrality(kol_graph, k=500)
```

**Interpretation for KOLs**:
| Betweenness Score | Interpretation | Strategic Value |
|-------------------|----------------|-----------------|
| > 0.1 | Critical broker, connects disparate clusters | Must engage for network access |
| 0.01-0.1 | Moderate broker role | Valuable for specific cluster access |
| < 0.01 | Not a broker | Limited network bridging value |

**Pros**: Identifies brokers and gatekeepers
**Cons**: Computationally expensive for large networks

---

### 2.3 Eigenvector Centrality

**Definition**: Importance based on importance of neighbors.

**Formula**:
```
Eigenvector_Centrality: Ax = λx

where:
  A = adjacency matrix
  x = eigenvector (centrality scores)
  λ = largest eigenvalue
```

**For KOLs**:
- Connected to other influential KOLs
- Quality over quantity of connections
- "Who you know matters"

**Implementation**:
```python
def eigenvector_centrality(graph, max_iter=100, tol=1e-06):
    """
    Calculate eigenvector centrality.
    
    Time Complexity: O(n * m) per iteration
    Space Complexity: O(n)
    """
    import networkx as nx
    return nx.eigenvector_centrality(graph, max_iter=max_iter, tol=tol)

# For large networks, use PageRank (variant of eigenvector):
def pagerank_centrality(graph, alpha=0.85):
    """
    PageRank is a variant of eigenvector centrality.
    Alpha = damping factor (probability of random jump)
    
    More stable for large networks.
    """
    return nx.pagerank(graph, alpha=alpha)
```

**Interpretation for KOLs**:
| Eigenvector Score | Interpretation | Network Quality |
|-------------------|----------------|------------------|
| > 0.1 | Connected to highly influential KOLs | Elite network |
| 0.01-0.1 | Moderately influential connections | Good network |
| < 0.01 | Connected to peripheral KOLs | Limited network quality |

**Pros**: Accounts for quality of connections
**Cons**: Doesn't work well with disconnected graphs

---

### 2.4 Closeness Centrality

**Definition**: Average shortest path distance to all other nodes.

**Formula**:
```
Closeness_Centrality(v) = (n - 1) / Σ d(v, u)

where:
  d(v,u) = shortest path distance from v to u
  n = total number of nodes
```

**For KOLs**:
- How quickly can reach all other KOLs
- Information dissemination speed
- Research collaboration efficiency

**Implementation**:
```python
def closeness_centrality(graph):
    """
    Calculate closeness centrality.
    
    Time Complexity: O(n * m) 
    Space Complexity: O(n)
    """
    import networkx as nx
    return nx.closeness_centrality(graph)
```

**Interpretation for KOLs**:
| Closeness Score | Interpretation | Information Reach |
|-----------------|----------------|-------------------|
| > 0.5 | Very close to all KOLs | Rapid information spread |
| 0.2-0.5 | Moderate reach | Standard dissemination |
| < 0.2 | Distant from most KOLs | Slow information spread |

**Pros**: Measures information dissemination potential
**Cons**: Sensitive to network size and connectivity

---

### 2.5 PageRank Centrality (Google's Variant)

**Definition**: Eigenvector centrality with random jumps.

**Formula**:
```
PageRank(v) = (1-d)/n + d * Σ [PageRank(u) / OutDegree(u)]

where:
  d = damping factor (usually 0.85)
  n = total nodes
  u = nodes linking to v
```

**For KOLs**:
- Similar to eigenvector but more stable
- Works better for directed networks (citations)
- Accounts for "random jump" (KOLs may connect randomly)

**Implementation**:
```python
def pagerank_centrality(graph, alpha=0.85, max_iter=100):
    """
    Calculate PageRank centrality.
    
    Alpha = damping factor (0.85 is standard)
    
    Time Complexity: O(n * m) per iteration
    Space Complexity: O(n)
    """
    import networkx as nx
    return nx.pagerank(graph, alpha=alpha, max_iter=max_iter)
```

**Interpretation for KOLs**:
| PageRank Score | Interpretation | Influence Level |
|----------------|----------------|------------------|
| > 0.01 | Highly influential in network | Top-tier influence |
| 0.001-0.01 | Moderately influential | Mid-tier influence |
| < 0.001 | Low influence | Peripheral influence |

---

### 2.6 Katz Centrality

**Definition**: Eigenvector centrality with attenuation for distant connections.

**Formula**:
```
Katz_Centrality(v) = α * Σ A(v,u) * Katz(u) + β

where:
  α = attenuation factor (must be < 1/λ_max)
  β = base centrality (usually 1)
  A = adjacency matrix
```

**For KOLs**:
- Captures both direct and indirect influence
- Attenuates influence from distant connections
- Good for hierarchical networks

**Implementation**:
```python
def katz_centrality(graph, alpha=0.1, beta=1.0):
    """
    Calculate Katz centrality.
    
    Alpha must be < 1/largest_eigenvalue
    Beta = base centrality for all nodes
    """
    import networkx as nx
    return nx.katz_centrality(graph, alpha=alpha, beta=beta)
```

---

## PART 3: KOL Network Types and Which Centrality to Use

### 3.1 Co-Authorship Network

**Nodes**: KOLs
**Edges**: Co-authored publications together
**Weight**: Number of co-authored papers

**Best Centrality Measures**:
| Purpose | Centrality | Why |
|---------|------------|-----|
| Identify prolific collaborators | Degree | Most co-authors |
| Find research bridges | Betweenness | Connects different research groups |
| Find most influential researchers | Eigenvector/PageRank | Connected to other influential KOLs |

**Data Source**: `kol_authorships` table

```python
def build_coauthorship_network(supabase_client, kol_ids=None):
    """
    Build co-authorship network from kol_authorships table.
    
    Nodes: KOLs
    Edges: Co-authored publications
    Weights: Number of co-authored papers
    """
    import networkx as nx
    
    # Get all authorships
    authorships = supabase_client.table('kol_authorships').select(
        'publication_id, kol_id'
    ).execute()
    
    # Group by publication
    publications = {}
    for a in authorships.data:
        if a['publication_id'] not in publications:
            publications[a['publication_id']] = []
        publications[a['publication_id']].append(a['kol_id'])
    
    # Build network
    G = nx.Graph()
    
    # Add nodes
    for a in authorships.data:
        G.add_node(a['kol_id'])
    
    # Add edges (co-authorships)
    for pub_id, kols in publications.items():
        for i, kol1 in enumerate(kols):
            for kol2 in kols[i+1:]:
                if G.has_edge(kol1, kol2):
                    G[kol1][kol2]['weight'] += 1
                else:
                    G.add_edge(kol1, kol2, weight=1)
    
    return G
```

### 3.2 Clinical Trial Collaboration Network

**Nodes**: KOLs
**Edges**: Participated in same clinical trial
**Weight**: Number of trials together

**Best Centrality Measures**:
| Purpose | Centrality | Why |
|---------|------------|-----|
| Find trial connectors | Degree | Most trial collaborators |
| Find trial bridges | Betweenness | Connects different trial networks |
| Find influential investigators | PageRank | Connected to other PIs |

**Data Source**: `trial_investigators` table

```python
def build_trial_network(supabase_client):
    """
    Build clinical trial collaboration network.
    
    Nodes: KOLs
    Edges: Same trial participation
    Weights: Number of trials together
    """
    import networkx as nx
    
    # Get all trial investigators
    investigators = supabase_client.table('trial_investigators').select(
        'trial_id, kol_id, role'
    ).execute()
    
    # Group by trial
    trials = {}
    for inv in investigators.data:
        if inv['trial_id'] not in trials:
            trials[inv['trial_id']] = []
        trials[inv['trial_id']].append(inv['kol_id'])
    
    # Build network
    G = nx.Graph()
    
    for inv in investigators.data:
        G.add_node(inv['kol_id'])
    
    for trial_id, kols in trials.items():
        for i, kol1 in enumerate(kols):
            for kol2 in kols[i+1:]:
                if G.has_edge(kol1, kol2):
                    G[kol1][kol2]['weight'] += 1
                else:
                    G.add_edge(kol1, kol2, weight=1)
    
    return G
```

### 3.3 Citation Network

**Nodes**: KOLs (publications)
**Edges**: Citation relationships
**Weight**: Number of citations

**Best Centrality Measures**:
| Purpose | Centrality | Why |
|---------|------------|-----|
| Find most cited | Degree (in-degree) | Most citations received |
| Find citation bridges | Betweenness | Connects citation flows |
| Find influential papers | PageRank | Citation propagation |

**Data Source**: `kol_authorships` with citation data

```python
def build_citation_network(supabase_client):
    """
    Build citation network (directed).
    
    Nodes: Publications
    Edges: Citations (directed)
    Weights: Citation count
    """
    import networkx as nx
    
    # Get citations
    citations = supabase_client.table('publication_citations').select(
        'publication_id, cited_publication_id'
    ).execute()
    
    G = nx.DiGraph()  # Directed graph for citations
    
    for cite in citations.data:
        G.add_edge(cite['publication_id'], cite['cited_publication_id'])
    
    return G
```

### 3.4 Biotech Affiliation Network

**Nodes**: KOLs
**Edges**: Same biotech affiliation
**Weight**: Relationship strength

**Best Centrality Measures**:
| Purpose | Centrality | Why |
|---------|------------|-----|
| Find industry connectors | Betweenness | Bridges biotech and academia |
| Find most affiliated | Degree | Most company affiliations |

**Data Source**: `biotech_associated_kols` table

```python
def build_biotech_network(supabase_client):
    """
    Build biotech affiliation network.
    
    Nodes: KOLs
    Edges: Same biotech company
    Weights: Relationship strength
    """
    import networkx as nx
    
    # Get biotech associations
    associations = supabase_client.table('biotech_associated_kols').select(
        'company_id, kol_id'
    ).execute()
    
    # Group by company
    companies = {}
    for assoc in associations.data:
        if assoc['company_id'] not in companies:
            companies[assoc['company_id']] = []
        companies[assoc['company_id']].append(assoc['kol_id'])
    
    # Build network
    G = nx.Graph()
    
    for assoc in associations.data:
        G.add_node(assoc['kol_id'])
    
    for company_id, kols in companies.items():
        for i, kol1 in enumerate(kols):
            for kol2 in kols[i+1:]:
                if G.has_edge(kol1, kol2):
                    G[kol1][kol2]['weight'] += 1
                else:
                    G.add_edge(kol1, kol2, weight=1)
    
    return G
```

---

## PART 4: Implementation for Your KOL Data

### 4.1 Complete Centrality Calculator

```python
import networkx as nx
import numpy as np
from typing import Dict, List, Tuple
import pandas as pd
from supabase import create_client

class KOLCentralityCalculator:
    """
    Calculate all centrality measures for KOL networks.
    
    Uses existing Supabase tables:
    - kol_authorships: Co-authorship network
    - trial_investigators: Clinical trial network
    - biotech_associated_kols: Biotech affiliation network
    """
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.client = create_client(supabase_url, supabase_key)
        self.networks = {}
        self.centrality_scores = {}
    
    def build_all_networks(self):
        """
        Build all KOL networks from Supabase data.
        """
        print("Building co-authorship network...")
        self.networks['coauthorship'] = self._build_coauthorship_network()
        
        print("Building trial collaboration network...")
        self.networks['trial'] = self._build_trial_network()
        
        print("Building biotech affiliation network...")
        self.networks['biotech'] = self._build_biotech_network()
        
        print("Building institution network...")
        self.networks['institution'] = self._build_institution_network()
        
        print(f"Networks built: {list(self.networks.keys())}")
    
    def _build_coauthorship_network(self) -> nx.Graph:
        """
        Build co-authorship network from kol_authorships.
        
        Edge weight = number of co-authored papers
        """
        # Get all authorships
        authorships = self.client.table('kol_authorships').select(
            'publication_id, kol_id'
        ).execute()
        
        # Group by publication
        publications = {}
        for a in authorships.data:
            if a['publication_id'] not in publications:
                publications[a['publication_id']] = []
            publications[a['publication_id']].append(a['kol_id'])
        
        # Build network
        G = nx.Graph()
        
        for a in authorships.data:
            G.add_node(a['kol_id'])
        
        for pub_id, kols in publications.items():
            for i, kol1 in enumerate(kols):
                for kol2 in kols[i+1:]:
                    if G.has_edge(kol1, kol2):
                        G[kol1][kol2]['weight'] += 1
                    else:
                        G.add_edge(kol1, kol2, weight=1)
        
        return G
    
    def _build_trial_network(self) -> nx.Graph:
        """
        Build clinical trial collaboration network from trial_investigators.
        
        Edge weight = number of trials together
        """
        investigators = self.client.table('trial_investigators').select(
            'trial_id, kol_id, role'
        ).execute()
        
        trials = {}
        for inv in investigators.data:
            if inv['trial_id'] not in trials:
                trials[inv['trial_id']] = []
            trials[inv['trial_id']].append(inv['kol_id'])
        
        G = nx.Graph()
        
        for inv in investigators.data:
            G.add_node(inv['kol_id'])
        
        for trial_id, kols in trials.items():
            for i, kol1 in enumerate(kols):
                for kol2 in kols[i+1:]:
                    if G.has_edge(kol1, kol2):
                        G[kol1][kol2]['weight'] += 1
                    else:
                        G.add_edge(kol1, kol2, weight=1)
        
        return G
    
    def _build_biotech_network(self) -> nx.Graph:
        """
        Build biotech affiliation network from biotech_associated_kols.
        
        Edge weight = same company
        """
        associations = self.client.table('biotech_associated_kols').select(
            'company_id, kol_id'
        ).execute()
        
        companies = {}
        for assoc in associations.data:
            if assoc['company_id'] not in companies:
                companies[assoc['company_id']] = []
            companies[assoc['company_id']].append(assoc['kol_id'])
        
        G = nx.Graph()
        
        for assoc in associations.data:
            G.add_node(assoc['kol_id'])
        
        for company_id, kols in companies.items():
            for i, kol1 in enumerate(kols):
                for kol2 in kols[i+1:]:
                    if G.has_edge(kol1, kol2):
                        G[kol1][kol2]['weight'] += 1
                    else:
                        G.add_edge(kol1, kol2, weight=1)
        
        return G
    
    def _build_institution_network(self) -> nx.Graph:
        """
        Build institution collaboration network.
        
        Nodes: KOLs
        Edges: Same institution
        """
        kols = self.client.table('kols').select(
            'id, institution_id'
        ).execute()
        
        institutions = {}
        for kol in kols.data:
            if kol['institution_id']:
                if kol['institution_id'] not in institutions:
                    institutions[kol['institution_id']] = []
                institutions[kol['institution_id']].append(kol['id'])
        
        G = nx.Graph()
        
        for kol in kols.data:
            G.add_node(kol['id'])
        
        for inst_id, kols_list in institutions.items():
            for i, kol1 in enumerate(kols_list):
                for kol2 in kols_list[i+1:]:
                    if G.has_edge(kol1, kol2):
                        G[kol1][kol2]['weight'] += 1
                    else:
                        G.add_edge(kol1, kol2, weight=1)
        
        return G
    
    def calculate_all_centrality(self, network_name: str = 'coauthorship') -> pd.DataFrame:
        """
        Calculate all centrality measures for a network.
        
        Returns DataFrame with kol_id and all centrality scores.
        """
        if network_name not in self.networks:
            raise ValueError(f"Network '{network_name}' not found. Build first.")
        
        G = self.networks[network_name]
        
        print(f"Calculating centrality for {network_name} network ({len(G.nodes())} nodes)...")
        
        # Calculate all centrality measures
        results = {}
        
        # 1. Degree Centrality
        print("  - Degree centrality...")
        results['degree'] = nx.degree_centrality(G)
        
        # 2. Raw degree (absolute count)
        results['degree_raw'] = dict(G.degree())
        
        # 3. Betweenness Centrality (sampled for large networks)
        print("  - Betweenness centrality...")
        if len(G.nodes()) > 1000:
            results['betweenness'] = nx.betweenness_centrality(G, k=min(500, len(G.nodes())))
        else:
            results['betweenness'] = nx.betweenness_centrality(G)
        
        # 4. Eigenvector Centrality
        print("  - Eigenvector centrality...")
        try:
            results['eigenvector'] = nx.eigenvector_centrality(G, max_iter=500)
        except nx.PowerIterationFailedConvergence:
            # Use PageRank instead for disconnected graphs
            results['eigenvector'] = nx.pagerank(G)
        
        # 5. Closeness Centrality
        print("  - Closeness centrality...")
        results['closeness'] = nx.closeness_centrality(G)
        
        # 6. PageRank
        print("  - PageRank centrality...")
        results['pagerank'] = nx.pagerank(G, alpha=0.85)
        
        # 7. Katz Centrality
        print("  - Katz centrality...")
        try:
            results['katz'] = nx.katz_centrality(G, alpha=0.005)
        except nx.NetworkXException:
            # Fallback if alpha too large
            results['katz'] = nx.katz_centrality(G, alpha=0.001)
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        df.index.name = 'kol_id'
        df = df.reset_index()
        
        # Calculate composite centrality score
        df['centrality_composite'] = (
            df['degree'] * 0.20 +
            df['betweenness'] * 0.20 +
            df['eigenvector'] * 0.25 +
            df['closeness'] * 0.15 +
            df['pagerank'] * 0.20
        )
        
        # Store results
        self.centrality_scores[network_name] = df
        
        return df
    
    def get_kol_centrality(self, kol_id: str, network_name: str = 'coauthorship') -> Dict:
        """
        Get all centrality scores for a specific KOL.
        """
        if network_name not in self.centrality_scores:
            self.calculate_all_centrality(network_name)
        
        df = self.centrality_scores[network_name]
        row = df[df['kol_id'] == kol_id]
        
        if row.empty:
            return {'error': f'KOL {kol_id} not found in network'}
        
        return row.to_dict('records')[0]
    
    def get_top_kols_by_centrality(
        self, 
        network_name: str = 'coauthorship',
        centrality_type: str = 'pagerank',
        top_n: int = 50
    ) -> pd.DataFrame:
        """
        Get top KOLs by a specific centrality measure.
        """
        if network_name not in self.centrality_scores:
            self.calculate_all_centrality(network_name)
        
        df = self.centrality_scores[network_name]
        return df.nlargest(top_n, centrality_type)
    
    def calculate_multi_network_centrality(self, kol_id: str) -> Dict:
        """
        Calculate centrality across all networks and aggregate.
        """
        results = {}
        
        for network_name in self.networks.keys():
            if network_name not in self.centrality_scores:
                self.calculate_all_centrality(network_name)
            
            df = self.centrality_scores[network_name]
            row = df[df['kol_id'] == kol_id]
            
            if not row.empty:
                results[network_name] = row.to_dict('records')[0]
        
        # Calculate aggregate scores
        if results:
            aggregate = {
                'kol_id': kol_id,
                'degree_avg': np.mean([r['degree'] for r in results.values() if 'degree' in r]),
                'betweenness_avg': np.mean([r['betweenness'] for r in results.values() if 'betweenness' in r]),
                'eigenvector_avg': np.mean([r['eigenvector'] for r in results.values() if 'eigenvector' in r]),
                'pagerank_avg': np.mean([r['pagerank'] for r in results.values() if 'pagerank' in r]),
                'centrality_composite_avg': np.mean([r['centrality_composite'] for r in results.values() if 'centrality_composite' in r])
            }
            results['aggregate'] = aggregate
        
        return results
```

### 4.2 Weighted Centrality (Your Custom Index)

**Your Data**: You have additional factors beyond raw network structure:
- H-index (academic influence)
- SVR Mango Index (journal weight)
- Institution prestige
- Country/region
- Recency score

**Weighted Centrality Formula**:
```
Weighted_Centrality = 
    Network_Centrality * (H-index_factor) * (Journal_factor) * (Institution_factor) * (Recency_factor)
```

**Implementation**:
```python
def calculate_weighted_centrality(
    kol_id: str,
    network_centrality: float,
    h_index: int,
    mango_index: float,
    institution_tier: int,
    recency_score: float
) -> float:
    """
    Calculate weighted centrality incorporating all KOL factors.
    
    Network Centrality: From graph analysis (PageRank, Eigenvector, etc.)
    H-index: Academic influence
    Mango Index: Journal weight (SVR Mango index)
    Institution Tier: 1=Top 10, 2=Top 50, 3=Top 100, 4=Other
    Recency Score: Publication momentum (0-1)
    """
    # H-index factor (logarithmic scaling)
    h_factor = np.log1p(h_index) / np.log1p(100)  # Normalized to 0-1
    
    # Journal factor
    journal_factor = mango_index / 10  # Assume mango index is 0-10 scale
    
    # Institution factor (tier-based)
    institution_factors = {1: 1.0, 2: 0.8, 3: 0.6, 4: 0.4}
    inst_factor = institution_factors.get(institution_tier, 0.5)
    
    # Recency factor
    recency_factor = recency_score  # Already 0-1
    
    # Weighted centrality
    weighted = network_centrality * h_factor * journal_factor * inst_factor * recency_factor
    
    return weighted
```

### 4.3 Composite Influence Score

```python
class KOLInfluenceScore:
    """
    Calculate comprehensive KOL influence score combining:
    1. Network centrality (from graph analysis)
    2. Academic metrics (H-index, citations)
    3. Trial experience (from clinical trials)
    4. Publication momentum (recency)
    5. Institution prestige
    """
    
    def __init__(self, supabase_client):
        self.client = supabase_client
    
    def calculate_full_score(self, kol_id: str) -> Dict:
        """
        Calculate full influence score for a KOL.
        
        Returns:
            Dict with all component scores and composite
        """
        # Get KOL data
        kol = self.client.table('kols').select('*').eq('id', kol_id).execute()
        metrics = self.client.table('kol_scholar_metrics').select('*').eq('kol_id', kol_id).execute()
        trials = self.client.table('trial_investigators').select('*').eq('kol_id', kol_id).execute()
        
        if not kol.data:
            return {'error': f'KOL {kol_id} not found'}
        
        kol_data = kol.data[0]
        metrics_data = metrics.data[0] if metrics.data else {}
        trial_data = trials.data
        
        # 1. Academic Score (H-index weighted)
        academic_score = self._calculate_academic_score(metrics_data)
        
        # 2. Trial Experience Score
        trial_score = self._calculate_trial_score(trial_data)
        
        # 3. Network Centrality Score (from graph analysis)
        network_score = self._get_network_score(kol_id)
        
        # 4. Publication Momentum Score
        momentum_score = self._calculate_momentum_score(kol_id)
        
        # 5. Institution Prestige Score
        institution_score = self._calculate_institution_score(kol_data.get('institution_id'))
        
        # Composite Score
        composite = (
            academic_score * 0.25 +
            trial_score * 0.20 +
            network_score * 0.25 +
            momentum_score * 0.15 +
            institution_score * 0.15
        )
        
        return {
            'kol_id': kol_id,
            'name': kol_data.get('name'),
            'academic_score': academic_score,
            'trial_score': trial_score,
            'network_score': network_score,
            'momentum_score': momentum_score,
            'institution_score': institution_score,
            'composite_score': composite,
            'tier': self._get_tier(composite)
        }
    
    def _calculate_academic_score(self, metrics: Dict) -> float:
        """
        Academic influence score based on H-index, citations, m-index.
        """
        h_index = metrics.get('h_index', 0)
        citations = metrics.get('citations', 0)
        m_index = metrics.get('m_index', 0)
        
        # Normalize H-index (log scale)
        h_normalized = np.log1p(h_index) / np.log1p(50)  # ~50 is top tier
        
        # Normalize citations (log scale)
        cite_normalized = np.log1p(citations) / np.log1p(10000)  # ~10k is top
        
        # M-index (productivity)
        m_normalized = min(m_index / 3.0, 1.0)  # ~3 is excellent
        
        # Weighted combination
        return h_normalized * 0.5 + cite_normalized * 0.3 + m_normalized * 0.2
    
    def _calculate_trial_score(self, trials: List[Dict]) -> float:
        """
        Trial experience score based on PI roles and phases.
        """
        if not trials:
            return 0.0
        
        # Count trials by role and phase
        pi_phase3 = sum(1 for t in trials if t.get('role') == 'PI' and t.get('phase') == 'Phase 3')
        pi_phase2 = sum(1 for t in trials if t.get('role') == 'PI' and t.get('phase') == 'Phase 2')
        coi_phase3 = sum(1 for t in trials if t.get('role') == 'Co-I' and t.get('phase') == 'Phase 3')
        
        # Score components
        pi_score = min((pi_phase3 * 10 + pi_phase2 * 5) / 50, 1.0)
        coi_score = min(coi_phase3 * 3 / 30, 1.0)
        
        return pi_score * 0.7 + coi_score * 0.3
    
    def _get_network_score(self, kol_id: str) -> float:
        """
        Get network centrality score from pre-calculated graph analysis.
        """
        # This would come from the centrality calculator
        # For now, placeholder
        return 0.5
    
    def _calculate_momentum_score(self, kol_id: str) -> float:
        """
        Publication momentum score based on recent publications.
        """
        # Get publications in last 2 years
        publications = self.client.table('kol_authorships').select(
            'publication_id, publications!inner(publication_date)'
        ).eq('kol_id', kol_id).execute()
        
        # Count recent publications
        # Placeholder - actual implementation would filter by date
        return 0.5
    
    def _calculate_institution_score(self, institution_id: str) -> float:
        """
        Institution prestige score.
        """
        if not institution_id:
            return 0.3
        
        # Get institution ranking
        institution = self.client.table('institutions').select('ranking_tier').eq(
            'id', institution_id
        ).execute()
        
        if not institution.data:
            return 0.3
        
        tier = institution.data[0].get('ranking_tier', 4)
        tier_scores = {1: 1.0, 2: 0.8, 3: 0.6, 4: 0.4}
        
        return tier_scores.get(tier, 0.4)
    
    def _get_tier(self, composite_score: float) -> str:
        """
        Classify KOL into tier based on composite score.
        """
        if composite_score >= 0.8:
            return 'Tier 1 - Global Thought Leader'
        elif composite_score >= 0.6:
            return 'Tier 2 - National Expert'
        elif composite_score >= 0.4:
            return 'Tier 3 - Regional Leader'
        elif composite_score >= 0.2:
            return 'Tier 4 - Local Expert'
        else:
            return 'Emerging KOL'
```

---

## PART 5: Centrality Score Interpretation

### 5.1 Score Ranges and Tiers

| Centrality Type | Tier 1 (Elite) | Tier 2 (High) | Tier 3 (Moderate) | Tier 4 (Low) |
|-----------------|----------------|---------------|-------------------|-------------|
| **Degree** | > 0.05 | 0.02-0.05 | 0.01-0.02 | < 0.01 |
| **Betweenness** | > 0.1 | 0.01-0.1 | 0.001-0.01 | < 0.001 |
| **Eigenvector** | > 0.1 | 0.01-0.1 | 0.001-0.01 | < 0.001 |
| **PageRank** | > 0.01 | 0.001-0.01 | 0.0001-0.001 | < 0.0001 |
| **Composite** | > 0.7 | 0.5-0.7 | 0.3-0.5 | < 0.3 |

### 5.2 What Each Centrality Means for KOL Engagement

| Centrality Type | High Score Means | Engagement Strategy |
|-----------------|------------------|---------------------|
| **Degree High** | Many direct collaborations | Leverage for introductions to collaborators |
| **Betweenness High** | Bridges different KOL clusters | Strategic partner for multi-center trials |
| **Eigenvector High** | Connected to influential KOLs | High-quality network access |
| **Closeness High** | Close to all KOLs in network | Rapid information dissemination |
| **PageRank High** | Overall influence | Priority engagement target |

---

## PART 6: Implementation Roadmap

### Phase 1: Network Construction (Week 1)
- [ ] Extract co-authorship data from `kol_authorships`
- [ ] Extract trial collaboration data from `trial_investigators`
- [ ] Extract biotech affiliation data from `biotech_associated_kols`
- [ ] Build NetworkX graphs for each network type

### Phase 2: Centrality Calculation (Week 2)
- [ ] Implement `KOLCentralityCalculator` class
- [ ] Calculate all centrality measures for each network
- [ ] Create composite centrality scores
- [ ] Store results in Supabase

### Phase 3: Weighted Integration (Week 3)
- [ ] Integrate H-index, Mango Index, institution tier
- [ ] Implement weighted centrality calculation
- [ ] Calculate multi-network aggregate scores
- [ ] Create influence score API endpoint

### Phase 4: Analysis & Visualization (Week 4)
- [ ] Build network visualization dashboard
- [ ] Create KOL influence score reports
- [ ] Implement centrality-based recommendations
- [ ] Integrate with KOL brief generator

---

## Conclusion

**Yes, you can measure centrality in your KOLs.** Here's how:

1. **Build Networks**: Use existing Supabase tables to construct co-authorship, trial collaboration, biotech affiliation, and institution networks

2. **Calculate Standard Centrality**: Degree, Betweenness, Eigenvector, Closeness, PageRank, Katz

3. **Weight with Your Data**: Combine network centrality with H-index, Mango Index, institution tier, recency score

4. **Create Composite Score**: Weighted average of all factors

**Key Tables**:
- `kol_authorships` → Co-authorship network
- `trial_investigators` → Clinical trial collaboration network
- `biotech_associated_kols` → Biotech affiliation network
- `kol_scholar_metrics` → H-index, citations, m-index

**Key Metrics**:
| Metric | Source | Weight |
|--------|--------|--------|
| Degree Centrality | Graph analysis | 20% |
| Betweenness Centrality | Graph analysis | 20% |
| Eigenvector Centrality | Graph analysis | 25% |
| Closeness Centrality | Graph analysis | 15% |
| PageRank | Graph analysis | 20% |
| H-index | Scholar metrics | Additional factor |
| Mango Index | Journal weight | Additional factor |
| Institution Tier | Institution data | Additional factor |
| Recency Score | Publication date | Additional factor |

---

**Document Status**: Complete
**Next Steps**: Implement Phase 1 network construction