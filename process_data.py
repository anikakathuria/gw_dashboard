import pandas as pd
def process_data(data, channel_mapping):
    # Remove duplicates in channel_mapping to avoid Cartesian product during merge
    channel_mapping = channel_mapping.drop_duplicates(subset=['search_data_fields.channel_data.channel_name'])
    # Merge with channel mapping to get company information
    data = data.merge(
        channel_mapping[['search_data_fields.channel_data.channel_name', 'entity']],
        on='search_data_fields.channel_data.channel_name', how='left'
    ).rename(columns={'entity': 'company'})

    # Split the "y_pred" column into individual binary fields
    fields = [
        "fossil_fuel", "primary_product", "petrochemical_product", "ff_infrastructure_production",
        "green", "renewable_energy", "emissions_reduction", "false_solutions", "recycling"
    ]
    y_pred_split = data["y_pred"].str.split(",", expand=True)
    for i, field in enumerate(fields):
        data[field] = y_pred_split[i].astype(int)
    # Add "misc" field
    data["misc"] = (data[fields].sum(axis=1) == 0).astype(int)
    # Add "other_green" field
    data["other_green"] = (
        (data["green"] == 1) &
        (data[["renewable_energy", "emissions_reduction", "false_solutions", "recycling"]].sum(axis=1) == 0)
    ).astype(int)
    # Add "other_fossil" field
    data["other_fossil"] = (
        (data["fossil_fuel"] == 1) &
        (data[["primary_product", "petrochemical_product", "ff_infrastructure_production"]].sum(axis=1) == 0)
    ).astype(int)
    data['published_at'] = pd.to_datetime(data['published_at'])
    # Drop duplicates
    data = data.drop_duplicates(subset=["complete_post_text"]).copy()
    # Compute engagement
    data["engagement"] = (
        pd.to_numeric(data["engagement_fields.likes_count"], errors="coerce").fillna(0).astype(int) +
        pd.to_numeric(data["engagement_fields.comments_count"], errors="coerce").fillna(0).astype(int)
    )
    # Classify greenwashing
    def classify_greenwashing(row):
        if row['green'] and row['fossil_fuel']:
            return "green_brown"
        elif row['green']:
            return "green"
        elif row['fossil_fuel']:
            return "brown"
        else:
            return "misc"

    data["green_brown"] = data.apply(classify_greenwashing, axis=1)
    data["year"] = data['published_at'].dt.year

    data["search_data_fields.platform_name"] = data["search_data_fields.platform_name"].replace("InstagramDirect", "Instagram")

    # Sort data by published_at
    data = data.sort_values(by='published_at', ascending=False)
    #data = data[data['search_data_fields.is_reply'] == False]
    return data