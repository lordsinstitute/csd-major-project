# Problem Statement

**Project Title:** Analysis of Big Data Research Hotspots Based on Keyword Co-occurrence

## 1. Background
Big Data is one of the fastest-growing research areas, with thousands of papers published every year across databases such as Web of Science, Scopus, IEEE Xplore and Google Scholar. The sheer volume makes it difficult for researchers, students and institutions to see which topics are active, emerging, or declining.

Author keywords describe the core themes of a paper. When two keywords appear together in the same paper, they are said to **co-occur**. Aggregating these co-occurrences across a large corpus yields a network in which frequently linked keywords form clusters that represent research hotspots.

## 2. Problem Statement
Manual literature reviews are slow, subjective and cannot scale to the volume of Big Data publications. There is a need for an automated, reproducible system that:
- extracts keywords from bibliographic records,
- cleans and standardises them,
- builds a keyword co-occurrence network,
- detects thematic clusters, and
- visualises hotspots and their evolution over time.

## 3. Objectives
1. Collect bibliographic data on Big Data research from a chosen source.
2. Preprocess keywords (cleaning, lemmatisation, synonym merging).
3. Build a keyword co-occurrence matrix and network.
4. Compute network metrics (degree, betweenness, closeness, centrality, density).
5. Detect clusters/communities (e.g., Louvain) that represent research hotspots.
6. Analyse hotspot trends across time periods.
7. Present results through interactive visualizations and a summary report.

## 4. Scope
**In scope**
- Bibliographic metadata (title, authors, year, keywords, abstract, source)
- Keyword frequency and co-occurrence analysis
- Network and cluster analysis, temporal trend analysis
- Visualization dashboard

**Out of scope**
- Full-text mining of papers
- Citation network or author collaboration analysis
- Real-time database crawling

## 5. Proposed Solution (Summary)
A Python-based pipeline (pandas, NLTK/spaCy, NetworkX, python-louvain) with a visualization layer (Matplotlib/Plotly/PyVis, optionally Streamlit) that turns raw bibliographic records into hotspot insights.

## 6. Expected Outcomes
- Cleaned keyword dataset
- Keyword co-occurrence matrix and network graph
- Ranked list of top keywords and clusters
- Identified hotspot themes (e.g., machine learning, cloud computing, IoT, data mining, privacy)
- Timeline view of emerging and declining topics

## 7. Stakeholders
Researchers, students, academic institutions, funding bodies, and project guide/evaluators.

## 8. Tools and Technologies
| Area | Tools |
|------|-------|
| Language | Python 3.10+ |
| Data handling | pandas, NumPy |
| NLP | NLTK / spaCy |
| Network analysis | NetworkX, python-louvain |
| Visualization | Matplotlib, Plotly, PyVis, VOSviewer (optional) |
| UI | Streamlit (optional) |
| Version control | Git, GitHub |
