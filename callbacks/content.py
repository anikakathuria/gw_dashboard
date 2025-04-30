from dash import Input, Output, html, dcc
import pandas as pd
from layouts.components import create_post_component
from util.functions import url_deduplicate
from util.plot_overview import plot_overview
from util.plot_greenwashing_score import plot_combined_greenwashing_scores
from util.plot_green_share import plot_green_share

def register_content_callbacks(app, data, codebook, green_brown_colors, classification_labels):
    @app.callback(
        Output("content", "children"),
        [
            Input("tabs", "value"),
            Input('current_page', 'data'),

            # Social-media filters
            Input('date_range', 'start_date'),
            Input('date_range', 'end_date'),
            Input('company_filter', 'value'),
            Input('entity_filter', 'value'),
            Input('platform_filter', 'value'),
            Input('classification_dropdown', 'value'),
            Input('view_toggle', 'value'),
            Input('left_view', 'value'),
            Input('right_view', 'value'),
            Input('uniqueness_toggle', 'value'),
            Input('keyword_search', 'value'),
            Input('social_fossil_subcategories', 'value'),
            Input('social_green_subcategories', 'value'),

            # Analytics filters
            Input('analytics_date_range', 'start_date'),
            Input('analytics_date_range', 'end_date'),
            Input('analytics_company_filter', 'value'),
            Input('analytics_entity_filter', 'value'),
            Input('analytics_platform_filter', 'value'),
            Input('analytics_uniqueness_toggle', 'value'),
            Input('analytics_fossil_subcategories', 'value'),
            Input('analytics_green_subcategories', 'value'),
        ]
    )
    def render_tab(
        tab_name,
        current_page,

        # social inputs
        sm_start, sm_end, sm_companies, sm_entities, sm_platforms, sm_classifs,
        view_toggle, left_view, right_view, sm_uniqueness, keyword_search,
        sm_fossil_subcategories, sm_green_subcategories,

        # analytics inputs
        an_start, an_end, an_companies, an_entities, an_platforms, an_uniqueness,
        an_fossil_subcategories, an_green_subcategories
    ):
        filtered_data = data.copy()

        # ... [existing filtering code remains unchanged] ...
        
        if tab_name == "social_media":
            start_date, end_date = sm_start, sm_end
            companies, entities, platforms, classifications = (
                sm_companies, sm_entities, sm_platforms, sm_classifs
            )
            uniqueness = sm_uniqueness
            
            # Social subcategory filters
            subcategory_filters = {
                "primary_product": "primary_product" in sm_fossil_subcategories,
                "petrochemical_product": "petrochemical_product" in sm_fossil_subcategories,
                "ff_infrastructure_production": "ff_infrastructure_production" in sm_fossil_subcategories,
                "other_fossil": "other_fossil" in sm_fossil_subcategories,
                "renewable_energy": "renewable_energy" in sm_green_subcategories,
                "emissions_reduction": "emissions_reduction" in sm_green_subcategories,
                "false_solutions": "false_solutions" in sm_green_subcategories,
                "recycling": "recycling" in sm_green_subcategories,
                "other_green": "other_green" in sm_green_subcategories
            }
        else:  # analytics
            start_date, end_date = an_start, an_end
            companies, entities, platforms = an_companies, an_entities, an_platforms
            uniqueness = an_uniqueness
            keyword_search = None
            
            # Analytics subcategory filters
            subcategory_filters = {
                "primary_product": "primary_product" in an_fossil_subcategories,
                "petrochemical_product": "petrochemical_product" in an_fossil_subcategories,
                "ff_infrastructure_production": "ff_infrastructure_production" in an_fossil_subcategories,
                "other_fossil": "other_fossil" in an_fossil_subcategories,
                "renewable_energy": "renewable_energy" in an_green_subcategories,
                "emissions_reduction": "emissions_reduction" in an_green_subcategories,
                "false_solutions": "false_solutions" in an_green_subcategories,
                "recycling": "recycling" in an_green_subcategories,
                "other_green": "other_green" in an_green_subcategories
            }
        
        # Apply uniqueness filter
        if uniqueness == "unique":
            filtered_data = url_deduplicate(filtered_data, 'complete_post_text')
        
        # Apply keyword search
        if keyword_search:
            keyword_lower = keyword_search.lower()
            filtered_data = filtered_data[
                filtered_data['search_data_fields.post_title'].str.lower().str.contains(keyword_lower, na=False) |
                filtered_data['complete_post_text'].str.lower().str.contains(keyword_lower, na=False)
            ]
        
        # Apply date filter
        if start_date and end_date:
            filtered_data = filtered_data[
                (filtered_data['published_at'] >= start_date) & 
                (filtered_data['published_at'] <= end_date)
            ]
        
        # Apply company filter
        if companies:
            filtered_data = filtered_data[filtered_data['company'].isin(companies)]
        
        # Apply entity filter
        if entities:
            filtered_data = filtered_data[filtered_data['search_data_fields.channel_data.channel_name'].isin(entities)]
        
        # Apply platform filter
        if platforms:
            filtered_data = filtered_data[filtered_data['search_data_fields.platform_name'].isin(platforms)]
        
        # Apply subcategory filters
        for subcategory, is_active in subcategory_filters.items():
            if is_active:
                filtered_data = filtered_data[filtered_data[subcategory] == 1]
        
        if tab_name == "social_media":
            if classifications:
                filtered_data = filtered_data[filtered_data['green_brown'].isin(classifications)]

            posts_per_page = 5
            
            if view_toggle == "all_posts":
                # All Posts View
                start = current_page * posts_per_page
                end = start + posts_per_page
                
                posts = [create_post_component(row) for _, row in filtered_data.iloc[start:end].iterrows()]
            
                # Update pagination buttons visibility instead of recreating them
                pagination_buttons = html.Div([
                    html.Button(
                        '← Previous',
                        id='prev_page',
                        n_clicks=0,
                        disabled=current_page == 0,
                        className="pagination-button"
                    ),
                    html.Button(
                        'Next →',
                        id='next_page',
                        n_clicks=0,
                        disabled=end >= len(filtered_data),
                        className="pagination-button"
                    )
                ], style={
                    "text-align": "center",
                    "margin-top": "32px",
                    "padding-bottom": "32px",
                    "display": "block"  # Make sure buttons are visible
                })
                
                post_count = html.Div([
                    "Showing ",
                    html.Strong(f"{len(filtered_data)}"),
                    " posts"
                ], className="post-count")
                
                return html.Div([
                    post_count,
                    html.Div(posts, className="posts-grid"),
                    pagination_buttons
                ])
            
            elif view_toggle == "compare_posts":
                # Comparison View with pagination
                left_data = filtered_data[filtered_data['green_brown'] == left_view]
                right_data = filtered_data[filtered_data['green_brown'] == right_view]
                
                # Apply pagination to both sides
                start = current_page * posts_per_page
                end = start + posts_per_page
                
                left_posts = [create_post_component(row) for _, row in left_data.iloc[start:end].iterrows()]
                right_posts = [create_post_component(row) for _, row in right_data.iloc[start:end].iterrows()]
                
                max_posts = max(len(left_data), len(right_data))
                
                # Update pagination buttons visibility instead of recreating them
                pagination_buttons = html.Div([
                    html.Button(
                        '← Previous',
                        id='prev_page',
                        n_clicks=0,
                        disabled=current_page == 0,
                        className="pagination-button"
                    ),
                    html.Button(
                        'Next →',
                        id='next_page',
                        n_clicks=0,
                        disabled=end >= max_posts,
                        className="pagination-button"
                    )
                ], style={
                    "text-align": "center",
                    "margin-top": "32px",
                    "padding-bottom": "32px",
                    "display": "block"  # Make sure buttons are visible
                })
                
                post_counts = html.Div([
                    "Showing ",
                    f" {len(left_data)+len(right_data)} posts"
                ], className="post-count")
                
                return html.Div([
                    post_counts,
                    html.Div([
                        html.Div([
                            html.H3(f"{classification_labels[left_view]} Posts", className="comparison-title"),
                            html.Div(left_posts, className="posts-grid")
                        ], style={"width": "48%", "display": "inline-block"}),
                        html.Div([
                            html.H3(f"{classification_labels[right_view]} Posts", className="comparison-title"),
                            html.Div(right_posts, className="posts-grid")
                        ], style={"width": "48%", "display": "inline-block", "margin-left": "4%"})
                    ]),
                    pagination_buttons
                ])
        
        elif tab_name == "analytics":
            # Generate overview plots using the Plotly-based functions
            overview_fig = plot_overview(filtered_data, codebook, green_brown_colors)
            raw_greenwashing_fig = plot_combined_greenwashing_scores(filtered_data, green_brown_colors)
            green_share_fig = plot_green_share(filtered_data, green_brown_colors)
            
            post_count = html.Div([
                "Analysis based on ",
                html.Strong(f"{len(filtered_data)}"),
                " posts"
            ], className="post-count")
            
            # Add hidden pagination buttons for analytics tab to ensure they're always in the DOM
            hidden_pagination = html.Div([
                html.Button('← Previous', id='prev_page', n_clicks=0, className="pagination-button"),
                html.Button('Next →', id='next_page', n_clicks=0, className="pagination-button")
            ], style={"display": "none"})
            
            return html.Div([
                post_count,
                # Overview Section
                html.Div([
                    html.H2("Post Classification Overview", className="analytics-header"),
                    html.P(
                        "The proportions in the stacked bar chart (below, left) show how many posts were identified as green or brown. Multiple labels can apply to the same post. The two bar charts indicate the frequency of all green and fossil fuel labels. Posts with both green and fossil fuel labels indicate micro-scale greenwashing, therefore, we code them as green.",
                        className="analytics-description"
                    ),
                    html.Div(
                        dcc.Graph(
                            figure=overview_fig,
                            config={'displayModeBar': False},
                            style={"height": "600px"}
                        )
                    )
                ], className="analytics-section"),
                
                # Greenwashing Score Section
                html.Div([
                    html.H2("Greenwashing score: % Green posts / % Green CAPEX", className="analytics-header"),
                    html.P(
                        "The green CAPEX (Capital Expenditures) measures the fraction of low-carbon capital investments among all capital investments. The ratio of green communication to green CAPEX reveals the degree of greenwashing across the industry. The line graph below shows the Greenwashing score over time by company.",
                        className="analytics-description"
                    ),
                    html.Div(
                        dcc.Graph(
                            figure=raw_greenwashing_fig,
                            config={'displayModeBar': False},
                            style={"height": "600px"}
                        )
                    )
                ], className="analytics-section"),

                # Green Share Section
                html.Div([
                    html.H2("Green Share of Climate Relevant posts", className="analytics-header"),
                    html.P(
                        "The line graph below shows the ratio of green (including green & fossil fuel) posts to fossil fuel posts across time.",
                        className="analytics-description"
                    ),
                    html.Div(
                        dcc.Graph(
                            figure=green_share_fig,
                            config={'displayModeBar': False},
                            style={"height": "600px"}
                        )
                    )
                ], className="analytics-section"),
                
                # Add hidden pagination buttons
                hidden_pagination

            ], className="analytics-container")
