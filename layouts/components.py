import pandas as pd
from dash import html, dcc

# Define color schemes and classification labels
green_brown_colors = {
    "Green": "#a7caa0",
    "green": "#a7caa0",
    "Fossil": "#8b5b4b",
    "brown": "#8b5b4b",
    "green_brown": "#5a8c5a",
    "misc": "#808080",
}

classification_labels = {
    "green": "Green",
    "brown": "Fossil",
    "green_brown": "Green+Fossil",
    "misc": "Miscellaneous"
}

# Define the banner component of the dashboard
banner = html.Div([
    html.Div("CLAIMS", style={
        "font-size": "40px",
        "font-weight": "bold",
        "color": "white",
        "text-orientation": "upright",
        "height": "10%",
        "display": "flex",
        "align-items": "left",
        "justify-content": "left",
        "padding-right": "16px",
        "margin-bottom": "3px"
    }),
    html.Div([
        html.Div("Climate Language and", style={
            "font-size": "18px",
            "font-weight": "500",
            "color": "white",
            "margin-bottom": "4px"
        }),
        html.Div("Influence Monitoring System", style={
            "font-size": "18px",
            "font-weight": "500",
            "color": "white",
            "margin-bottom": "3px"
        })
    ], style={
        "display": "flex",
        "flex-direction": "column",
        "justify-content": "left",
        "margin-left": "16px"
    })
], className="banner", style={
    "display": "flex",
    "align-items": "left",
    "height": "auto"
})

def create_post_component(row):
    """
    Create a post component for the dashboard.
    Retrieves the Junkipedia HTML embedding and displays it in an iframe.
    Adds classification labels and other metadata as badges.

    Arguments:
        row (pd.Series): The row of data in the dataframe representing an invidual post.
        view_mode (str): The view mode for the post (e.g., "compare_posts").
    Returns:
        html.Div: The post component.
    """
    classification_class = f"classification-{row['green_brown']}"
    border_color = green_brown_colors.get(row['green_brown'], "#ddd")
    
    # Set width based on view mode
    post_width = "80%"
    
    # Get the post ID from the data
    # Assuming the post ID is in a column called 'post_id'
    # If it's not, you'll need to extract it from another field or URL
    post_id = row.get('id', None)
    height = row.get('computed_height', 800)
    width = row.get('computed_width', 600)
    
    # Create the iframe for the Junkipedia post with bottom 20px cut off
    junkipedia_iframe = html.Div([
        html.Iframe(
            src=f"/junkipedia_proxy/{post_id}",
            style={
                "width": f"{width}",
                "height": f"{height}", 
                "display": "block", 
            },
            # Add all necessary permissions to the sandbox
            sandbox="allow-scripts allow-same-origin allow-popups allow-forms allow-downloads"
        )
    ], style={
        "width": f"{width}",
        "position": "relative",
    })
    
    return html.Div([
        # Junkipedia content in an iframe - centered
        html.Div([
            junkipedia_iframe
        ], className="post-content", style={
            "display": "flex",
            "justify-content": "center",
            "align-items": "flex-start",  # Changed from center to flex-start
            "padding": "0",
            "margin": "0",
            "height": "auto"  # Allow container to grow
        }),
        
        # # Keep the original footers
        # html.Div([
        #     html.Span(
        #         classification_labels[row['green_brown']].title(),
        #         className=f"classification-badge {classification_class}",
        #         title=row['green_label_explanation'],
        #         style={"font-size": "14px"}
        #     ),
        # ], className="post-footer-1",  style={
        #     "background-color": f"{border_color}",
        #     "padding": "12px 16px",
        #     "text-align": "center",
        # }),
        
        html.Div([
            *[
                html.Span(
                    column.replace("_", " ").title(),  # Display column name as badge text
                    className=f"classification-badge classification-brown" if column in ["primary_product", "petrochemical_product", "infrastructure_production","other_fossil"]
                    else f"classification-badge classification-green",
                    title=row['ff_categories_explanation'] if column in ["primary_product", "petrochemical_product", "infrastructure_production"] else row['green_categories_explanation']
                )
                for column in [
                    "primary_product", "petrochemical_product", "infrastructure_production", "fossil_fuel_other",
                    "decreasing_emissions", "viable_solutions", "false_solutions", "recycling_waste_management", "nature_animal_references", "generic_environmental_references", "green_other"
                ]
                if row[column] == 1  # Only include badges for columns with a value of 1
            ]
        ], className="post-footer-2")
    ], className="social-post", style={
        "padding": "0",  # Remove padding to make container match iframe size
        "width": post_width,  # Set width based on view mode
        "margin": "0 auto",
        "height": "auto",  # Allow container to grow
        "display": "flex",
        "flex-direction": "column"
    })

""" 
Old Version of create_post_component without Junkipedia embedding



def format_date(date_str):
    ""
    Convert a date string to a more readable format.

    Arguments:
        date_str (str): The date string to format.
    Returns:
        date.strftime: The formatted date string.
    ""
    date = pd.to_datetime(date_str)
    return date.strftime("%B %d, %Y")


def create_original_post_component(row, view_mode="compare_posts"):
    classification_class = f"classification-{row['green_brown']}"
    border_color = green_brown_colors.get(row['green_brown'], "#ddd")
    
    # Set width based on view mode
    post_width = "75%" if view_mode == "compare_posts" else "100%"
    
    return html.Div([
        html.Div([
            html.H4(f"{row['company']} (@{row['search_data_fields.channel_data.channel_name']})", style={
                "margin": "0",
                "font-size": "16px",
                "font-weight": "600",
                "color": "#1a237e",
            }),
            html.Div(format_date(row['published_at']), className="post-date")
        ], className="post-header", style={"background-color": f"{border_color}"}), 
        html.Div([
            html.H5(row['search_data_fields.post_title'] if row['search_data_fields.post_title'] != "[]" else "", style={
                "margin": "0 0 12px 0",
                "font-size": "16px",
                "font-weight": "500",
            }),
            html.Div([
                html.P(
                    (row['complete_post_text'][:200]) if pd.notna(row['complete_post_text']) else "",
                    className="post-preview"
                ),
                html.Div(
                    row['complete_post_text'] if pd.notna(row['complete_post_text']) else "",
                    className="simple-tooltip"
                )
            ], className="tooltip-wrapper", style={"position": "relative", "cursor": "pointer"}),
            html.Img(
                src=row['thumbnail_url'],
                style={
                    "width": "100%",
                    "height": "200px",
                    "object-fit": "cover",
                    "border-radius": "8px",
                    "margin-bottom": "16px"
                }
            ) if row['thumbnail_url'] != "[]" else None,
        ], className="post-content"),
        html.Div([
            html.Span(f"👥 {row['engagement']:,}", className="engagement-badge"),
            html.Span(row['search_data_fields.platform_name'], className="platform-badge"),
            html.Span(
                classification_labels[row['green_brown']].title(),
                className=f"classification-badge {classification_class}",
                title=row['green_label_explanation']
            ),

        ], className="post-footer"),
        html.Div([
            *[
                html.Span(
                    column.replace("_", " ").title(),  # Display column name as badge text
                    className=f"classification-badge classification-brown" if column in ["primary_product", "petrochemical_product", "ff_infrastructure_production","other_fossil"]
                    else f"classification-badge classification-green",
                    title=row['ff_categories_explanation'] if column in ["primary_product", "petrochemical_product", "ff_infrastructure_production"] else row['green_categories_explanation']
                )
                for column in [
                    "primary_product", "petrochemical_product", "ff_infrastructure_production", "other_fossil",
                    "renewable_energy", "emissions_reduction", "false_solutions", "recycling", "other_green"
                ]
                if row[column] == 1  # Only include badges for columns with a value of 1
            ]
        ], className="post-footer")
    ], className="social-post", style={
        "border": f"2px solid {border_color}",
        "width": post_width,  # Set width based on view mode
        "margin": "0 auto"
    }) 
"""
