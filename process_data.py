import pandas as pd
import ast
def process_data_csv(data, channel_mapping):
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
    channel_mapping = channel_mapping.drop_duplicates(subset=['attributes.search_data_fields.channel_data.channel_name'])
    # Merge with channel mapping to get company information
    data = data.merge(
        channel_mapping[['attributes.search_data_fields.channel_data.channel_name', 'entity']],
        on='attributes.search_data_fields.channel_data.channel_name', how='left'
    ).rename(columns={'entity': 'company'})

    # Split the "y_pred" column into individual binary fields
    fields = [
        "fossil_fuel", "primary_product", "petrochemical_product", "infrastructure_production",
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
        (data[["primary_product", "petrochemical_product", "infrastructure_production"]].sum(axis=1) == 0)
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

    data["attributes.search_data_fields.platform_name"] = data["attributes.search_data_fields.platform_name"].replace("InstagramDirect", "Instagram")

    # Sort data by published_at
    data = data.sort_values(by='published_at', ascending=False)
    #data = data[data['search_data_fields.is_reply'] == False]
    return data



def process_data_json(data_json: dict) -> pd.DataFrame:
    """
    Process the raw data for the dashboard from a column-oriented JSON input.

    Parameters
    ----------
    data_json : dict
        Column-oriented JSON where each key is a column name and each value is a
        dict mapping row-index strings (e.g., "0", "1", ...) to values. All fields
        share the same keys and correspond to the same posts.
    channel_mapping : pd.DataFrame
        A dataframe with at least:
            - 'attributes.search_data_fields.channel_data.channel_name'
            - 'entity'
        mapping channels to company names.

    Returns
    -------
    pd.DataFrame
        The processed dataframe with the same structure/fields as the CSV-based pipeline:
        - merged 'company'
        - expanded binary classification columns from y_pred (new schema)
            - 'fossil_fuel'
            - 'primary_product'
            - 'petrochemical_product'
            - 'infrastructure_production'
            - 'fossil_fuel_other'
            - 'green'
            - 'renewable_energy'
            - 'emissions_reduction'
            - 'false_solutions'
            - 'recycling'
            - 'nature_animal_references'
            - 'generic_environmental_references'
            - 'green_other'
        - 'misc'
        - 'engagement' (likes + comments)
        - 'green_brown' final label
        - 'year'
        - normalized 'attributes.search_data_fields.platform_name'
        - deduplicated by 'attributes.complete_post_text'
        - sorted by 'attributes.published_at' desc
    """

    #  Build a DataFrame from column-oriented JSON
    #    (each column is a dict of {"row_index_str": value})
    cols = {}
    for col, mapping in data_json.items():
        s = pd.Series(mapping)
        # Ensure integer index ordering (rows "0","1",... in order)
        try:
            s.index = s.index.astype(int)
            s = s.sort_index()
        except Exception:
            # If indices aren't numeric, keep original order
            pass
        cols[col] = s
    data = pd.DataFrame(cols)

    #get rid of most of the columns we don't need
    keep_columns = [
        'id',
        'y_pred',
        'attributes.published_at',
        'attributes.complete_post_text',
        'attributes.search_data_fields.channel_data.channel_name',
        'attributes.search_data_fields.platform_name',
        'attributes.engagement_fields.likes_count',
        #'attributes.engagement_fields.comments_count',
        #'attributes.search_data_fields.published_at',
        'computed_width',
        'computed_height',
        "green_label_explanation",
        "green_categories_explanation",
        "ff_label_explanation",
        "ff_categories_explanation",
        "parent_entity"
    ]
    data = data[keep_columns].copy()

    data = data.rename(columns={
        'parent_entity': 'company'
    })
    # 2) Expand y_pred (new schema) into binary columns
    fields = [
        "fossil_fuel",
        "primary_product",
        "petrochemical_product",
        "infrastructure_production",
        "fossil_fuel_other",
        "green",
        "decreasing_emissions",
        "viable_solutions",
        "false_solutions",
        "recycling_waste_management",
        "nature_animal_references",
        "generic_environmental_references",
        "green_other",
    ]

    # # Ensure y_pred exists (empty string for missing)
    # if "y_pred" not in data.columns:
    #     data["y_pred"] = ""

    # y_split = data["y_pred"].str.strip("[]").astype(str).str.split(",", expand=True)
    # print(y_split.head())

    # # Pad y_split to the correct number of columns
    # for i in range(len(fields)):
    #     if i not in y_split.columns:
    #         y_split[i] = pd.NA

    # # Assign and coerce to integers (0/1), treating invalid/missing as 0
    # for i, field in enumerate(fields):
    #     data[field] = pd.to_numeric(y_split[i],s errors="coerce").fillna(0).astype(int)

    data[fields] = data["y_pred"].apply(lambda x: pd.Series(ast.literal_eval(str(x))) if str(x).startswith("[") else pd.Series([0]*len(fields)))

    # 3) Derived flags
    # misc: 1 if none of the categories are set to 1
    data["misc"] = (data[fields].sum(axis=1) == 0).astype(int)

    # 4) Date handling
    # published_at to datetime and extract year
    if "attributes.published_at" in data.columns:
        data["attributes.published_at"] = pd.to_datetime(data["attributes.published_at"], unit="ms", errors="coerce", utc=False)
        data["year"] = data["attributes.published_at"].dt.year
    else:
        data["year"] = pd.NA

    # 5) Drop duplicates by text
    if "attributes.complete_post_text" in data.columns:
        data = data.drop_duplicates(subset=["attributes.complete_post_text"]).copy()

    # 6) Engagement = likes + comments (from engagement_fields.*)
    like_col = "attributes.engagement_fields.likes_count"
    comment_col = "attributes.engagement_fields.comments_count"
    # If these columns are missing, create them to avoid KeyErrors
    if like_col not in data.columns:
        data[like_col] = 0
    if comment_col not in data.columns:
        data[comment_col] = 0

    data["engagement"] = (
        pd.to_numeric(data[like_col], errors="coerce").fillna(0).astype(int)
        + pd.to_numeric(data[comment_col], errors="coerce").fillna(0).astype(int)
    )

    # 7) Final label from green / fossil
    def get_final_green_ff_label(post):
        g = bool(post.get("green", 0))
        f = bool(post.get("fossil_fuel", 0))
        if g and f:
            return "green_brown"
        elif g:
            return "green"
        elif f:
            return "brown"
        else:
            return "misc"

    data["green_brown"] = data.apply(get_final_green_ff_label, axis=1)

    # 8) Platform normalization
    platform_col = "attributes.search_data_fields.platform_name"
    if platform_col in data.columns:
        data[platform_col] = data[platform_col].replace("InstagramDirect", "Instagram")

    # 9) Sort by published_at desc when available
    data["attributes.published_at"] = pd.to_datetime(data["attributes.published_at"], errors="coerce")
    if "attributes.published_at" in data.columns:
        data = data.sort_values(by="attributes.published_at", ascending=False)


    return data
