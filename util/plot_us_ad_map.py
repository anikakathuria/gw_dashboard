# util/plot_us_map.py
import pandas as pd
import plotly.express as px

_US_STATE_ABBR = {
    "Alabama": "AL","Alaska": "AK","Arizona": "AZ","Arkansas": "AR","California": "CA","Colorado": "CO",
    "Connecticut": "CT","Delaware": "DE","District of Columbia": "DC","Florida": "FL","Georgia": "GA",
    "Hawaii": "HI","Idaho": "ID","Illinois": "IL","Indiana": "IN","Iowa": "IA","Kansas": "KS","Kentucky": "KY",
    "Louisiana": "LA","Maine": "ME","Maryland": "MD","Massachusetts": "MA","Michigan": "MI","Minnesota": "MN",
    "Mississippi": "MS","Missouri": "MO","Montana": "MT","Nebraska": "NE","Nevada": "NV","New Hampshire": "NH",
    "New Jersey": "NJ","New Mexico": "NM","New York": "NY","North Carolina": "NC","North Dakota": "ND",
    "Ohio": "OH","Oklahoma": "OK","Oregon": "OR","Pennsylvania": "PA","Rhode Island": "RI","South Carolina": "SC",
    "South Dakota": "SD","Tennessee": "TN","Texas": "TX","Utah": "UT","Vermont": "VT","Virginia": "VA",
    "Washington": "WA","West Virginia": "WV","Wisconsin": "WI","Wyoming": "WY",
}

_ALL_USPS = list(_US_STATE_ABBR.values())  # includes DC

def _to_usps(series: pd.Series) -> pd.Series:
    """Accept either full names or USPS codes; normalize to USPS codes."""
    s = series.astype(str).str.strip()
    # If looks like 2-letter codes already, upper-case them
    two = s.str.match(r'^[A-Za-z]{2}$', na=False)
    s.loc[two] = s.loc[two].str.upper()
    # Map full names to codes
    need_map = ~two
    if need_map.any():
        s.loc[need_map] = s.loc[need_map].map(_US_STATE_ABBR).fillna(s.loc[need_map])
    return s

def plot_us_ad_map(
    df: pd.DataFrame,
    metric: str = "impressions",
    state_col: str = "region",
    include_all_states: bool = True
):
    """
    df expects columns:
      - state_col: per-row region (full name or 2-letter USPS code)
      - impressions_median, spend_median, impressions_per_dollar
    metric: "impressions", "spend", or "impressions_per_dollar"
    Returns a Plotly Figure (USA choropleth by state).
    """
    if metric not in ("impressions", "spend", "impressions_per_dollar"):
        raise ValueError("metric must be 'impressions', 'spend', or 'impressions_per_dollar'")

    if metric == "impressions":
        value_col = "impressions_median"
        color_label = "Impressions (median sum)"
        title = "Impressions by State"
    elif metric == "spend":
        value_col = "spend_median"
        color_label = "Spend (median sum, USD)"
        title = "Spend by State"
    else:  # impressions_per_dollar
        value_col = "impressions_per_dollar"
        color_label = "Impressions per Dollar"
        title = "Efficiency (Impressions per $) by State"

    if state_col not in df.columns:
        raise KeyError(f"'{state_col}' column not found in df")
    if value_col not in df.columns:
        raise KeyError(f"'{value_col}' column not found in df")

    tmp = df[[state_col, value_col]].copy()
    tmp[state_col] = _to_usps(tmp[state_col])

    tmp = tmp[tmp[state_col].str.match(r'^[A-Z]{2}$', na=False)]

    agg = tmp.groupby(state_col, as_index=False)[value_col].sum()

    if include_all_states:
        full = pd.DataFrame({state_col: _ALL_USPS})
        agg = full.merge(agg, on=state_col, how="left").fillna({value_col: 0})

    fig = px.choropleth(
        agg,
        locations=state_col,
        locationmode="USA-states",
        color=value_col,
        scope="usa",
        labels={value_col: color_label},
        color_continuous_scale="Oranges",
        hover_name=state_col,
    )

    if metric == "spend":
        hover_tmpl = "<b>%{location}</b><br>Spend: $%{z:,.0f}<extra></extra>"
    elif metric == "impressions":
        hover_tmpl = "<b>%{location}</b><br>Impressions: %{z:,.0f}<extra></extra>"
    else:  # impressions_per_dollar
        hover_tmpl = "<b>%{location}</b><br>Impressions per $: %{z:,.2f}<extra></extra>"

    fig.update_traces(hovertemplate=hover_tmpl)
    fig.update_layout(
        title=title,
        margin=dict(l=20, r=20, t=60, b=20),
        coloraxis_colorbar=dict(title=color_label)
    )
    return fig
