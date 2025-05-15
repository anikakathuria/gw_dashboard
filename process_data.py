import pandas as pd
def process_data(data, channel_mapping):
    """
    Process the raw data for the dashboard.

    Arguments:
        data (pd.dataframe): contains all posts and their metadata
        channel_mapping (pd.dataframe): contains the mapping of channels to companies

    Returns:
        data (pd.dataframe:) same dataframe after the following processing steps:
            - Merging with the channel mapping dataframe to attach a company name to each post
            - Processing the "y_pred" column, which is the classification result from the LLM, into invidual boolean fields 
            and adding a "misc" field and "other_green"/"other_fossil" field if the post is classified as green but none of the other green/fossil fuel categories are true.
            We end up with the following fields for classification fo the post (all boolean):
                - fossil_fuel
                - primary_product
                - petrochemical_product
                - ff_infrastructure_production
                - green
                - renewable_energy
                - emissions_reduction
                - false_solutions
                - recycling
                - other_green
                - misc
            - Dropping duplicates based on the "complete_post_text" column
            - Adding an "engagement" field which is the sum of likes and comments
            - Adding a "green_brown" field which is the final label of the post based off the LLM classification. 
                - "green" for green posts
                - "brown" for fossil fuel posts
                - "green_brown" for posts that are both green and fossil fuel
                - "misc" for posts that are neither green nor fossil fuel
            - Adding a "year" field which is the year of the post
            - Replacing "InstagramDirect" with "Instagram" in the "platform_name" field
            - Sorting the data by the "published_at" field in descending order

    """



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


    def get_final_green_ff_label(post):
        """
        Arguments: 
        post: Receives a row of the dataframe containing all posts as a representation of a single post

        Returns:
        final label of the post based off the LLM classification. Looks at column 'green' and 'fossil_fuel' which both contain boolean values
        "green" for green posts
        "brown" for fossil fuel posts
        "green_brown" for posts that are both green and fossil fuel
        "misc" for posts that are neither green nor fossil fuel

        """
        if post['green'] and post['fossil_fuel']:
            return "green_brown"
        elif post['green']:
            return "green"
        elif post['fossil_fuel']:
            return "brown"
        else:
            return "misc"
    
    #df['label'] = df.apply(lambda row: label_post_green_brown(row['green'], row['fossil_fuel']), axis=1)
    data["green_brown"] = data.apply(get_final_green_ff_label, axis=1)
    data["year"] = data['published_at'].dt.year

    data["search_data_fields.platform_name"] = data["search_data_fields.platform_name"].replace("InstagramDirect", "Instagram")

    # Sort data by published_at
    data = data.sort_values(by='published_at', ascending=False)
    #data = data[data['search_data_fields.is_reply'] == False]
    return data