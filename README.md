# Greenwashing Dashboard

## Overview

This prototype dashboard visualizes and categorizes social media posts according to our greenwashing typology. 
It enables users to filter, explore, and analyze messaging trends by companies and platforms. 
Built with Dash (Plotly), this tool shows how we want to integrate embedded content, rich filters, and interactive visualizations for the end-user.

---

## Features

### Post Feed

- **Post Setup**: 
  - Posts are embedded directly from Junkipedia using HTML/CSS/JavaScript. This logic is in `layouts/content.py`, where URLs like `junkipedia.org/posts/{post_id}` are used in embedded iframe components.
- **Label Assignment**: 
  - Each post is tagged with a high-level label: Green, Fossil, Green+Fossil, or Misc. Labels and color coding are handled in `callbacks/content.py`.
- **Subcategory Labels**:
  - If applicable, posts include subcategory classifications. These are derived from the data in `process_data.py`.

### Filters

Defined in `callbacks/filters.py` and configured in `layouts/sidebars.py`:

- **Keyword Search**: A text input allows filtering posts by keywords.
- **Date Range**: DatePickerRange component sets temporal boundaries.
- **View Mode**: Toggle between viewing all posts or comparing labels side-by-side.
- **Companies & Platforms**: Multi-dropdowns populated from the dataset.
- **Subcategories**: Conditional filters appear when relevant.
- **Channels**: Filter by data source or distribution outlet.
- **Message Type**: Select between "All" messages or "Unique" ones (de-duplicated logic handled in `process_data.py`).

### Analytics

Charts are rendered in `util/` modules and displayed via `layouts/content.py`.

- **Post Classification Overview** (`util/plot_overview.py`)
  - Bar graphs show counts by high-level label.
  - Subcategory breakdowns for Green and Fossil.
  - Uniform y-axis scaling is enforced for visual consistency.

- **Greenwashing Score** (`util/plot_greenwashing_score.py`)
  - Score = (% Green Posts) / (% Green CAPEX).
  - Toggle options: raw (linear), raw (log), normalized (linear).
  - CAPEX data comes from `low_carbon_ratios.csv`.

- **Green Share of Climate-Relevant Posts** (`util/plot_green_share.py`)
  - Line graph tracks the fraction of climate-oriented posts that exhibit Green messaging over time.

Analytics filters mirror the post feed’s, implemented via callbacks in `callbacks/filters.py`.

### About

- **About Section & Glossary**:
  - Static HTML/text components rendered from `layouts/content.py`.

---

## Data Sources

Stored in `/data/`:
- `final_greenwashing_dataset_for_dashboard_english_only.csv`: Main dataset.
- `low_carbon_ratios.csv`: Used for Greenwashing Score.
- `1_codebook.json`: Label definitions.
- `channel_mapping.csv`: Used in filtering and channel grouping.

---

## Development

### Running Locally

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Launch the app:
   ```bash
   python app.py
   ```

> `app_2.py` appears to be an alternate or test version — prefer `app.py` for main deployment.

---

## Future Ideas (Planned)

- Add a **Green+Fossil** comparison column.
- Break out **micro vs. macro** greenwashing over time.
- Overlay **real-world events** on trend graphs.
- Generate **word clouds** of frequent terms.
- Add **OCR** support to process image-based posts.
- Integrate **ad content** into analysis.

---

## Notes to ATI (Procedural)

- Typology, prompts, and dashboard updates will be iterative — this is version 1.0.
- Follow ATI precedent for submitting GitHub update requests.
