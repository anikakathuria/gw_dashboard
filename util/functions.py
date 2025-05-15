def url_deduplicate(df, content_column):
    """
    Replace URLs in the content column with [URL] and remove duplicate entries based on the cleaned text.
    
    Arguments:
        df (pd.DataFrame): The input DataFrame.
        content_column (str): The name of the column containing the content.
    
    Returns:
        pd.DataFrame: A DataFrame with a new 'content_wo_url' column and duplicates removed based on it.
    """
    df = df.copy()
    df['content_wo_url'] = df[content_column].str.replace(r'http\S+|www\S+', '[URL]', regex=True)
    return df.drop_duplicates(subset='content_wo_url', keep='first')