import argparse
from pathlib import Path
import os
import pandas as pd
import requests

parser = argparse.ArgumentParser()

parser.add_argument('action_type')
parser.add_argument("input_path")

args = parser.parse_args()

action_type = args.action_type
input_path = Path(args.input_path)

if action_type not in ['labels', 'channels']:
    print(action_type)
    print("Usage: python add_data.py <action_type> <path> \n type can be 'labels' or 'channels'")
    raise SystemExit(1)

if not input_path.exists():
    print("The input path does not exist")
    raise SystemExit(1)

# --- Define API Call Function ---
def get_post(uid):
    url = f"{API_BASE}/posts"
    params = {"post_uid": uid}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    
    if "data" in data and len(data["data"]) > 0:
        attributes = data["data"][0].get("attributes", {})
        search_data = attributes.get("search_data_fields", {})
        channel = attributes.get("channel", {})
        
        # Extract format: if post_type is a list, grab the first element
        post_type = search_data.get("post_type")
        if isinstance(post_type, list):
            post_format = post_type[0] if post_type else None
        else:
            post_format = post_type
        
        return {
            "uid": uid,
            "url": search_data.get("url"),
            "junkipedia_url": search_data.get("post_link"),  # renamed field
            "format": post_format,
            "platform": search_data.get("platform_name"),
            "title": search_data.get("post_title"),
            "content": search_data.get("description"),
            "media": attributes.get("thumbnail_url") or attributes.get("ad_screenshot"),
            "published_at": search_data.get("published_at"),
            "created_at": attributes.get("created_at"),
            "engagement": search_data.get("engagement"),
            "channel_name": search_data.get("channel_name") or channel.get("channel_name"),
            "handle": attributes.get("handle") or channel.get("handle"),
            "channel_url": channel.get("link"),
            "profile_image": search_data.get("channel_data", {}).get("channel_profile_image"),
            "bio": channel.get("bio"),
            "transcript_text": search_data.get("transcript_text"),
            "channel_uid": channel.get("channel_uid")
        }
    else:
        return {"uid": uid}

# Input is a csv of labeled data that contains uid,post_body_text,primary_product,petrochemical_product,ff_infrastructure_OR_production,green_message,renewable_energy,emissions_reduction,false_solutions,recycling,green,brown,misc
if action_type == 'labels':
    # --- Setup ---
    # Define the API base URL and read the API key from an environment variable.
    API_BASE = "https://www.junkipedia.org/api/v1"
    API_KEY = ''  # Make sure to set this in your environment
    if not API_KEY:
        raise ValueError("Please set the JUNKIPEDIA_KEY environment variable.")

    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    print("Reading input data from", input_path)

    # --- Read Input Data ---
    # Read the CSV file containing the list of UIDs (labels)
    labels_df = pd.read_csv(input_path)

    # --- Fetch Data from API ---
    # Process the entire list of UIDs from the labels file
    ingested_records = []
    for uid in labels_df['uid']:
        try:
            record = get_post(uid)
            ingested_records.append(record)
        except Exception as e:
            print(f"Error fetching data for UID {uid}: {e}")
            # Append a record with just the UID if an error occurs
            ingested_records.append({"uid": uid})

    # Convert the list of records to a DataFrame
    ingested_df = pd.DataFrame(ingested_records)

    # --- Merge Data ---
    # Merge the labels (from 6_sample_uids.csv) with the ingested data based on the "uid" field
    combined_df = pd.merge(labels_df, ingested_df, on="uid", how="left")

    # --- Write Output ---
    # Write the combined DataFrame to a new CSV file
    output_path = os.path.join("data", "labels_and_data_test.csv")
    combined_df.to_csv(output_path, mode='a', header=False, index=False)
    print(f"Combined data added to {output_path}")