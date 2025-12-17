# Oscars Data Scraping and Analysis Project

## Abstract

This project implements a comprehensive data pipeline for scraping, processing, and analyzing Oscar award nomination data. Utilizing advanced techniques in data engineering, natural language processing, and exploratory data analysis, the system extracts insights into gender representation and collaborative patterns in the film industry. The project demonstrates end-to-end data science workflows, from raw web scraping to actionable visualizations, and serves as a foundation for future machine learning applications.

## Introduction

The film industry, particularly awards ceremonies like the Oscars, provides rich data for analyzing trends in gender diversity, creative collaborations, and cultural impacts. This project addresses the need for automated data collection and analysis of Oscar nominations by developing a robust ETL pipeline that scrapes data from HTML sources, processes complex text formats, and generates statistical insights.

Key objectives:

- Automate extraction of Oscar nomination data.
- Normalize and standardize entity names and roles.
- Analyze gender dynamics in acting categories.
- Visualize collaborative networks among filmmakers.
- Provide a scalable framework for award data analysis.

The project integrates multiple disciplines: Data Engineering for pipeline development, Natural Language Processing for text parsing, Exploratory Data Analysis for insights, and Data Science for modeling patterns.

## Methodology

### Data Engineering (ETL Pipeline)

- **Extract**: Web scraping using BeautifulSoup to parse HTML from oscars/scraping/index.html, extracting nomination links and raw text.
- **Transform**:
  - Regex-based parsing of nomination strings (e.g., "Director - Film Title (Studio)").
  - Entity normalization using custom buffers and heuristics.
  - Gender inference via role hints and name-based detection.
  - Role mapping to standardized categories (acting, directing, writing, etc.).
  - Handling multifilm nominations and special awards.
- **Load**: Export to structured formats (CSV, SQLite) for analysis.

### Natural Language Processing (NLP)

- Advanced regex patterns for extracting entities, titles, roles, and affiliations from unstructured text.
- Custom tokenization and pattern matching for complex nomination formats.
- Normalization of names to handle variations and duplicates.

### Exploratory Data Analysis (EDA)

- Statistical analysis of nomination distributions by category, gender, and year.
- Identification of gender imbalances in acting awards.
- Analysis of collaborative pairs (actor-producer) using frequency counts.
- Decade-wise trends in winner demographics.

### Data Science

- Heuristic-based gender classification.
- Vectorization of film features for similarity analysis.
- Custom implementations of TF-IDF and cosine similarity for content-based recommendations.

## Implementation

### Project Structure

- src/: Core scripts including pipeline.py (main ETL),
  ecommendation_system.py (custom ML-like similarity).
- oscars/: Modular components for scraping (extract.py), parsing (GenderResolver.py, RoleMapper.py), and utilities.
- analysis/: EDA scripts (drafts.py for visualizations, \_helpers.py for data processing).
- data/: Input datasets ( he_oscar_award.csv, oscars-data.csv).
-     ransformed/: Output data and figures.
- equirements.txt: Python dependencies.

### Key Components

- **Pipeline Orchestrator**: Manages the ETL flow with profiling for performance optimization.
- **Parsing Engine**: Handles text extraction with configurable regex patterns.
- **Gender Resolver**: Combines role-based hints with name analysis for accurate classification.
- **Role Mapper**: Standardizes roles into functional categories.
- **Visualization Engine**: Generates heatmaps, bar charts, and network plots using Matplotlib and Seaborn.

### Technologies Used

- **Python**: Core language for scripting and data processing.
- **Pandas/Numpy**: Data manipulation and numerical operations.
- **BeautifulSoup**: HTML parsing.
- **Matplotlib/Seaborn**: Data visualization.
- **SQLite**: Data storage.

## Installation and Usage

1. Clone the repository:
   `git clone <repository-url>
cd scraping-project-2025`

2. Install dependencies:
   `pip install -r requirements.txt`

3. Run the main pipeline:
   `python src/pipeline.py`

This executes the full ETL process, generating outputs in transformed/.

## Results

### Data Processing Outcomes

- Successfully parsed 12,000+ nomination records from raw HTML.
- Achieved high accuracy in entity extraction and gender classification.
- Identified gender disparities: e.g., higher female representation in acting vs. directing categories.

### Visualizations

- **Heatmap of Nominations by Category and Gender**: Reveals imbalances across 20+ categories.
- **Top Collaborating Pairs**: Bar chart of frequent actor-producer collaborations.
- **Decade Trends**: Line plots showing evolution of gender ratios in acting winners.

### Performance

- Pipeline execution optimized with cProfile, identifying bottlenecks in text processing.
- Custom implementations provide transparency and educational value over black-box libraries.

## Future Work

Building on the current foundation, planned extensions include:

- **Machine Learning Integration**: Implement supervised models for improved gender prediction using labeled datasets.
- **Neural Networks**: Develop deep learning models (e.g., RNNs or Transformers) for advanced text parsing and entity recognition in nomination strings.
- **Recommendation Engine Enhancement**: Incorporate collaborative filtering and user-based preferences for personalized film suggestions.
- **Scalability**: Extend to other award ceremonies (e.g., Golden Globes, Emmys) and integrate real-time data sources.
- **Advanced Analytics**: Apply clustering algorithms to identify filmmaker networks and trend forecasting.

## Peer Review Insights

Based on project reviews, strengths include:

- Robust ETL pipeline with comprehensive error handling.
- Innovative use of regex for NLP tasks.
- Clear modular architecture facilitating maintenance.

Areas for improvement:

- Enhance documentation with more code examples.
- Add unit tests for critical components.
- Optimize performance for larger datasets.

## References

- Official Oscar data sources.
- Python libraries: Pandas, Scikit-learn, BeautifulSoup.
- Academic papers on gender in film industry.

## License

MIT License - See LICENSE file for details.

## Acknowledgments

This project was developed as part of a semester assignment, incorporating feedback from peer reviews to enhance quality and scope.
