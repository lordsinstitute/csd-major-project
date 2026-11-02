# Software Requirements Specification (SRS)

**Project:** Analysis of Big Data Research Hotspots Based on Keyword Co-occurrence
**Version:** 1.0

## 1. Introduction
### 1.1 Purpose
This document specifies the requirements of a system that identifies research hotspots in Big Data literature using keyword co-occurrence analysis.

### 1.2 Scope
The system accepts bibliographic data files, processes keywords, builds co-occurrence networks, detects clusters, and displays hotspot analytics and visualizations.

### 1.3 Definitions
| Term | Meaning |
|------|---------|
| Co-occurrence | Two keywords appearing in the same paper |
| Hotspot | A dense cluster of frequently co-occurring keywords |
| Centrality | A measure of a node's importance in a network |
| Louvain | A community detection algorithm |
| SRS | Software Requirements Specification |

### 1.4 References
- IEEE Std 830-1998, Recommended Practice for SRS
- Web of Science / Scopus export documentation

## 2. Overall Description
### 2.1 Product Perspective
A standalone analytics application consisting of a data pipeline and a visualization interface.

### 2.2 Product Functions
- Import bibliographic data (CSV / Excel / BibTeX / TXT)
- Clean and normalise keywords
- Compute keyword frequencies
- Build co-occurrence matrix and network
- Calculate network metrics
- Detect communities (hotspots)
- Analyse trends by year
- Visualize and export results

### 2.3 User Classes
| User | Description |
|------|-------------|
| Researcher / Student | Uploads data, explores hotspots |
| Administrator | Manages thesaurus (synonym list) and settings |

### 2.4 Operating Environment
Windows / Linux / macOS, Python 3.10+, modern web browser, 4 GB RAM minimum.

### 2.5 Constraints
- Dependent on quality and completeness of source keywords
- Data export limits of bibliographic databases

### 2.6 Assumptions
- Input files contain keyword and publication-year fields
- Keywords are in English

## 3. Functional Requirements
| ID | Requirement |
|----|-------------|
| FR-01 | The system shall allow users to upload bibliographic files in CSV, XLSX, BibTeX or TXT format. |
| FR-02 | The system shall validate file format and required fields (title, year, keywords). |
| FR-03 | The system shall remove duplicate records. |
| FR-04 | The system shall clean keywords (lowercase, remove punctuation, lemmatise). |
| FR-05 | The system shall merge synonyms using a configurable thesaurus. |
| FR-06 | The system shall compute keyword frequency and rank keywords. |
| FR-07 | The system shall allow users to set a minimum frequency threshold. |
| FR-08 | The system shall generate a keyword co-occurrence matrix. |
| FR-09 | The system shall build a weighted undirected network graph. |
| FR-10 | The system shall compute degree, betweenness, closeness, eigenvector centrality and density. |
| FR-11 | The system shall detect communities and label them as hotspots. |
| FR-12 | The system shall display top keywords per cluster. |
| FR-13 | The system shall analyse keyword trends over selectable time periods. |
| FR-14 | The system shall render interactive network, heatmap, bar chart and word cloud visualizations. |
| FR-15 | The system shall export tables (CSV) and charts (PNG/SVG/HTML). |
| FR-16 | The system shall generate a summary report of hotspots. |

## 4. External Interface Requirements
### 4.1 User Interface
Web-based dashboard with upload panel, parameter panel, and result tabs (see `04_UI_Design.md`).
### 4.2 Hardware Interface
Standard PC/laptop; no special hardware.
### 4.3 Software Interface
Python libraries (pandas, NetworkX, spaCy/NLTK, Plotly, Streamlit); optional VOSviewer export.
### 4.4 Communication Interface
Local execution; HTTP over localhost when run through Streamlit.

## 5. Non-Functional Requirements
| ID | Category | Requirement |
|----|----------|-------------|
| NFR-01 | Performance | Process 10,000 records in under 2 minutes. |
| NFR-02 | Usability | A new user should complete an analysis within 5 steps. |
| NFR-03 | Reliability | Invalid inputs shall produce clear error messages without crashing. |
| NFR-04 | Scalability | Support up to 50,000 records. |
| NFR-05 | Portability | Run on Windows, Linux and macOS. |
| NFR-06 | Maintainability | Modular code with documentation and unit tests. |
| NFR-07 | Reproducibility | Same input and parameters shall give identical results. |
| NFR-08 | Security | Uploaded data is processed locally and not shared externally. |

## 6. Data Requirements
Input fields: `Title, Authors, Year, Author Keywords, Keywords Plus, Abstract, Source, DOI`.
Outputs: cleaned dataset, frequency table, co-occurrence matrix, graph file (GraphML/GEXF), cluster table, charts.

## 7. Use Cases (Summary)
| ID | Use Case | Actor |
|----|----------|-------|
| UC-01 | Upload dataset | User |
| UC-02 | Configure parameters | User |
| UC-03 | Run analysis | User |
| UC-04 | View network and clusters | User |
| UC-05 | View trends | User |
| UC-06 | Export results | User |
| UC-07 | Manage thesaurus | Administrator |

## 8. Acceptance Criteria
- All functional requirements FR-01 to FR-16 demonstrated on a sample dataset.
- Detected hotspots are interpretable and validated against known Big Data themes.
- Documentation and code available in the GitHub repository.
