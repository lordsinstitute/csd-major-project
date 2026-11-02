# System Diagrams

All diagrams use [Mermaid](https://mermaid.js.org/) and render directly on GitHub.

## 1. System Architecture
```mermaid
flowchart LR
    A[Bibliographic Databases<br/>WoS / Scopus / IEEE] --> B[Data Import Module]
    B --> C[Preprocessing Module<br/>clean, lemmatise, merge synonyms]
    C --> D[Keyword Analysis Module<br/>frequency, co-occurrence matrix]
    D --> E[Network Analysis Module<br/>metrics, community detection]
    E --> F[Trend Analysis Module]
    E --> G[Visualization Module]
    F --> G
    G --> H[Dashboard / Reports]
    C -.-> I[(Thesaurus)]
    B --> J[(Dataset Storage)]
    D --> J
```

## 2. Use Case Diagram
```mermaid
flowchart LR
    U([User])
    AD([Administrator])
    subgraph System
        UC1(Upload dataset)
        UC2(Configure parameters)
        UC3(Run analysis)
        UC4(View network and clusters)
        UC5(View trends)
        UC6(Export results)
        UC7(Manage thesaurus)
    end
    U --> UC1
    U --> UC2
    U --> UC3
    U --> UC4
    U --> UC5
    U --> UC6
    AD --> UC7
    AD --> UC3
```

## 3. Data Flow Diagram
### Level 0 (Context)
```mermaid
flowchart LR
    U([User]) -- dataset and parameters --> P((Keyword Co-occurrence<br/>Analysis System))
    P -- hotspots, charts, reports --> U
    DB[(Bibliographic Source)] -- records --> P
```

### Level 1
```mermaid
flowchart TD
    U([User]) -->|upload file| P1((1.0 Import and Validate))
    P1 -->|valid records| P2((2.0 Preprocess Keywords))
    T[(Thesaurus)] --> P2
    P2 -->|clean keywords| D1[(Cleaned Dataset)]
    D1 --> P3((3.0 Build Co-occurrence Matrix))
    P3 -->|matrix| P4((4.0 Network and Cluster Analysis))
    P4 -->|clusters and metrics| D2[(Results Store)]
    D1 --> P5((5.0 Trend Analysis))
    P5 --> D2
    D2 --> P6((6.0 Visualize and Export))
    P6 -->|charts and reports| U
```

## 4. Activity Diagram
```mermaid
flowchart TD
    S([Start]) --> A[Upload dataset]
    A --> B{Valid format?}
    B -- No --> A
    B -- Yes --> C[Remove duplicates]
    C --> D[Clean and normalise keywords]
    D --> E[Merge synonyms]
    E --> F[Apply frequency threshold]
    F --> G[Build co-occurrence matrix]
    G --> H[Construct network graph]
    H --> I[Compute centrality metrics]
    I --> J[Detect communities]
    J --> K[Analyse yearly trends]
    K --> L[Generate visualizations]
    L --> M[Export report]
    M --> E1([End])
```

## 5. Sequence Diagram
```mermaid
sequenceDiagram
    actor User
    participant UI as Dashboard
    participant DP as DataProcessor
    participant NA as NetworkAnalyzer
    participant VZ as Visualizer
    User->>UI: Upload file and set parameters
    UI->>DP: load_and_clean(file)
    DP-->>UI: cleaned keywords
    UI->>NA: build_network(keywords, min_freq)
    NA->>NA: compute metrics and communities
    NA-->>UI: graph, clusters
    UI->>VZ: render(graph, clusters)
    VZ-->>UI: charts
    UI-->>User: Display hotspots
    User->>UI: Export results
    UI-->>User: CSV / PNG / HTML
```

## 6. Class Diagram
```mermaid
classDiagram
    class DataLoader {
        +load_file(path)
        +validate()
        +remove_duplicates()
    }
    class KeywordProcessor {
        +clean(keywords)
        +lemmatize()
        +merge_synonyms(thesaurus)
        +filter_by_frequency(min_freq)
    }
    class CooccurrenceMatrix {
        +matrix
        +build(records)
        +to_dataframe()
    }
    class NetworkAnalyzer {
        +graph
        +build_graph(matrix)
        +compute_centrality()
        +detect_communities()
        +density()
    }
    class TrendAnalyzer {
        +analyze_by_year(records)
        +emerging_keywords()
    }
    class Visualizer {
        +plot_network()
        +plot_heatmap()
        +plot_wordcloud()
        +plot_trend()
    }
    class ReportGenerator {
        +export_csv()
        +export_report()
    }
    DataLoader --> KeywordProcessor
    KeywordProcessor --> CooccurrenceMatrix
    CooccurrenceMatrix --> NetworkAnalyzer
    NetworkAnalyzer --> Visualizer
    TrendAnalyzer --> Visualizer
    Visualizer --> ReportGenerator
```

## 7. ER Diagram
```mermaid
erDiagram
    PAPER ||--o{ PAPER_KEYWORD : has
    KEYWORD ||--o{ PAPER_KEYWORD : appears_in
    KEYWORD ||--o{ COOCCURRENCE : keyword1
    KEYWORD ||--o{ COOCCURRENCE : keyword2
    CLUSTER ||--o{ KEYWORD : groups
    PAPER {
        int paper_id PK
        string title
        string authors
        int year
        string source
        string doi
    }
    KEYWORD {
        int keyword_id PK
        string term
        int frequency
        int cluster_id FK
        float centrality
    }
    PAPER_KEYWORD {
        int paper_id FK
        int keyword_id FK
    }
    COOCCURRENCE {
        int keyword1_id FK
        int keyword2_id FK
        int weight
    }
    CLUSTER {
        int cluster_id PK
        string label
        int size
    }
```
