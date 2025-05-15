from dash import Input, Output, html, dcc
import pandas as pd
from layouts.components import create_post_component
from util.functions import url_deduplicate
from util.plot_overview import plot_overview
from util.plot_greenwashing_score import plot_combined_greenwashing_scores
from util.plot_green_share import plot_green_share

def register_content_callbacks(app, data, codebook, green_brown_colors, classification_labels):
    """
    Register callbacks for the content section of the dashboard.
    This function handles the content rendering of different tabs (Social Media, Analytics, About)
    and applies the necessary filters based on user input.

    Arguments:
        app: The Dash app instance.
        data: The DataFrame containing the social media data.
        codebook: The codebook for the data.
        green_brown_colors: Dictionary mapping classification labels to colors.
        classification_labels: Dictionary mapping classification labels to their display names.

    Returns:
        None
    """
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
        """
        Render the content of the selected tab based on user inputs and filters.
        This function filters the data based on the selected criteria and generates the appropriate content.
        It handles the rendering of social media posts, analytics plots, and the about section.

        Arguments:
            tab_name (str): The name of the selected tab.
            current_page (int): The current page number for pagination.
            sm_start (str): Start date for social media filtering.
            sm_end (str): End date for social media filtering.
            sm_companies (list): List of selected companies for social media filtering.
            sm_entities (list): List of selected entities for social media filtering.
            sm_platforms (list): List of selected platforms for social media filtering.
            sm_classifs (list): List of selected classifications for social media filtering.
            view_toggle (str): The current view toggle state.
            left_view (str): The left view classification for comparison.
            right_view (str): The right view classification for comparison.
            sm_uniqueness (str): Uniqueness filter for social media posts.
            keyword_search (str): Keyword search string for filtering posts.
            sm_fossil_subcategories (list): Selected fossil subcategories for social media filtering.
            sm_green_subcategories (list): Selected green subcategories for social media filtering.

            an_start (str): Start date for analytics filtering.
            an_end (str): End date for analytics filtering.
            an_companies (list): List of selected companies for analytics filtering.
            an_entities (list): List of selected entities for analytics filtering.
            an_platforms (list): List of selected platforms for analytics filtering.
            an_uniqueness (str): Uniqueness filter for analytics posts.
            an_fossil_subcategories (list): Selected fossil subcategories for analytics filtering.
            an_green_subcategories (list): Selected green subcategories for analytics filtering.

        Returns:
            html.Div: The content to be displayed in the selected tab.
        """
        filtered_data = data.copy()

        
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

            posts_per_page = 10
            
            if view_toggle == "all_posts":
                posts_per_page = 10
                # All Posts View
                start = current_page * posts_per_page
                end = start + posts_per_page
                
                # Pass the view_toggle to create_post_component
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

                # Get every other item starting with the first item
                posts_first_half = posts[::2]

                # Get every other item starting with the second item
                posts_second_half = posts[1::2]
                
                return html.Div([
                    post_count,
                    html.Div([
                        html.Div([
                            html.Div(posts_first_half, className="posts-grid")
                        ], style={"width": "48%", "display": "inline-block"}),
                        html.Div([
                            html.Div(posts_second_half, className="posts-grid")
                        ], style={"width": "48%", "display": "inline-block", "margin-left": "4%"})
                    ]),
                    pagination_buttons
                ])
            
            elif view_toggle == "compare_posts":
                # Comparison View with pagination
                left_data = filtered_data[filtered_data['green_brown'] == left_view]
                right_data = filtered_data[filtered_data['green_brown'] == right_view]
                
                # Apply pagination to both sides
                start = current_page * posts_per_page
                end = start + posts_per_page
                
                # Pass the view_toggle to create_post_component
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
            raw_greenwashing_fig = plot_combined_greenwashing_scores(filtered_data)
            green_share_fig = plot_green_share(filtered_data)
            
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
                        "This section shows the distribution of social media posts across categories and sub-categories.",
                        className="analytics-description"
                    ),
                    html.P([
                            html.Strong("Total Proportions (left) "),
                            "Stacked bar chart showing the fraction of posts labelled by CLAIMS as Only Green, Only Fossil, Green+Fossil, or Miscellaneous."
                    ], className="analytics-description"),
                    html.P([
                            html.Strong("All Green Posts (middle): "),
                            "Bar chart showing the number of posts by Green subcategory, as labelled by CLAIMS: Emissions Reduction, False Solutions, Other Green, Recycling/Waste Management, and Low-Carbon Technologies. Posts assigned both Fossil Fuel and Green labels by CLAIMS indicate efforts to greenwash messaging about fossil fuels, and are therefore included in this bar chart."
                    ], className="analytics-description"),
                    html.P([
                            html.Strong("All Fossil Posts (right): "),
                            "Bar chart showing the number of posts by Fossil Fuel subcategory, as labelled by CLAIMS: Primary Product, Petrochemical Product, Other Fossil Fuel, and Infrastructure & Production."
                    ], className="analytics-description"),
                    
                    
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
                        "CDO has pioneered the first quantitative social media Greenwashing Score, which compares the prevalence of a company’s green messaging to its actual climate mitigation investments. The Greenwashing Score is defined as % Green posts divided by % Green CAPEX (capital expenditures), with values greater than 1 indicating greenwashing at the company-level, which we term macro-scale greenwashing. The line graphs show the Greenwashing Score over time for each company.",
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
                        "Line graph showing the fraction of climate-relevant social media posts that contain Green messaging. We here define Green messaging as any post labelled by CLAIMS as Only Green or Green+Fossil. We define climate-relevant posts as all posts except Miscellaneous ones.",
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
            
        elif tab_name == "about":
            # Calculate dynamic values for the About section
            total_posts = len(data)
            platforms = ", ".join(sorted(data['search_data_fields.platform_name'].unique()))
            
            # Add hidden pagination buttons for about tab to ensure they're always in the DOM
            hidden_pagination = html.Div([
                html.Button('← Previous', id='prev_page', n_clicks=0, className="pagination-button"),
                html.Button('Next →', id='next_page', n_clicks=0, className="pagination-button")
            ], style={"display": "none"})
            
            return html.Div([
                # About Section
                html.Div([
                    html.P([
                        html.Strong("What is CLAIMS?")
                    ], style={"font-size": "20px", "margin-bottom": "8px"}),
                    html.P([
                        "CLAIMS (Climate Language and Influence Monitoring System) is a tool of the Climate Discourse Observatory that automatically detects greenwashing in oil companies' social media posts. Search by keywords, topic, company, or platform to see data visualizations and summary statistics (Analytics), or explore the raw labelled posts yourself (Post Feed)."
                    ], style={"font-size": "14px", "margin-bottom": "16px"}),
                    html.P([
                        html.Strong("How does CLAIMS work?")
                    ], style={"font-size": "20px", "margin-bottom": "8px"}),
                    
                    html.P([
                        html.Strong("Model")
                    ], style={"font-size": "14px", "margin-bottom": "8px"}),
                    html.P([
                        "By fine-tuning the ChatGPT-4o Large Language Model from OpenAI, CLAIMS reliably classifies text in social media posts from fossil fuel producers according to the typology of \"green\" and \"fossil fuel\" messaging shown below. Human coders have validated the accuracy of CLAIMS, which achieves F1 predictive performance scores of 80%+."
                    ], style={"font-size": "14px", "margin-bottom": "8px"}),
                    html.P([
                        f"For this pilot study, ChatGPT coded {total_posts} organic posts and paid ads from BP, ExxonMobil, Shell, and the American Petroleum Institute on Facebook, Instagram, X (Twitter), and YouTube."
                    ], style={"font-size": "14px", "margin-bottom": "16px"}),
                    
                    html.P([
                        html.Strong("Typology")
                    ], style={"font-size": "14px", "margin-bottom": "8px"}),
                    
                    html.P([
                        "The typology contains five \"green\" categories and four \"fossil fuel\" categories. Multiple labels can apply to the same post."
                    ], style={"font-size": "14px", "margin-bottom": "8px"}),
                    # Placeholder for a diagram - you can add an image here
                    html.Div([
                        html.Img(
                            src="/assets/codebook_diagram.png",  # Replace with actual image path
                            style={
                                "max-width": "50%",
                                "height": "20%",
                                "margin": "20px auto",
                                "display": "block"
                            }
                        )
                    ], style={"text-align": "center", "margin": "30px 0"}),
                
                    html.P([
                        html.Strong("Glossary")
                    ], style={"font-size": "14px", "margin-bottom": "16px"}),

                    html.Ul([
                        html.Li([
                    
                    html.P([
                        html.Strong("Green posts", style={"font-size": "14px"}),
                        ": If CLAIMS assigns at least one Green label to a post, the post is coded as Green."
                    ], style={"font-size": "14px", "margin-bottom": "8px"}),
                    
                    html.Ul([
                        html.Li([
                            html.Strong("Decreasing Emissions"),
                            ": Positive or neutral references to greenhouse gas emissions reduction."
                        ]),
                        html.Li([
                            html.Strong("Renewables & Low-Carbon Technologies"),
                            ": Positive or neutral references to renewable energy and/or other low-carbon technology solutions, such as solar, wind, or hydropower."
                        ]),
                        html.Li([
                            html.Strong("False Solutions"),
                            ": Positive or neutral references to fossil-fuel-adjacent \'false solutions\' to climate change, such as carbon capture, hydrogen, or \"clean\" methane."
                        ]),
                        html.Li([
                            html.Strong("Recycling & Waste Management"),
                            ": Positive or neutral references to recycling and waste management efforts."
                        ]),
                        html.Li([
                            html.Strong("Other Green"),
                            ": Other green messaging, such as nature and generic environmental references."
                        ])
                    ], style={"font-size": "14px", "margin-bottom": "16px", "padding-left": "30px"})
                        ]),

                    html.Li([
                    
                    html.P([
                        html.Strong("Fossil Fuel posts"),
                        ": If CLAIMS assigns at least one Fossil Fuel label to a post and no green labels, the post is coded as Fossil Fuel."
                    ], style={"font-size": "14px", "margin-bottom": "8px"}),
                    
                    html.Ul([
                        html.Li([
                            html.Strong("Primary Product"),
                            ": References to one or more fossil fuel primary products, such as coal, oil, or methane."
                        ]),
                        html.Li([
                            html.Strong("Petrochemical Product"),
                            ": References to one or more petrochemical products, such as gasoline or lubricants."
                        ]),
                        html.Li([
                            html.Strong("Infrastructure & Production"),
                            ": References to fossil fuel production, operations, and/or infrastructure, such as pipelines, oil fields, or refineries."
                        ]),
                        html.Li([
                            html.Strong("Other Fossil Fuel"),
                            ": Other fossil fuel related messaging not captured by the labels above."
                        ])
                    ], style={"font-size": "14px", "margin-bottom": "16px", "padding-left": "30px"})

                    ]),

                    html.Li([
                    
                    html.P([
                        html.Strong("Miscellaneous posts"),
                        ": Posts not assigned any Green or Fossil Fuel labels by CLAIMS are not relevant to climate change and are coded as Miscellaneous."
                    ], style={"font-size": "14px", "margin-bottom": "16px"}) ]),

                    html.Li([
                    
                    html.P([
                        html.Strong("Micro-scale greenwashing"),
                        ": Micro-scale greenwashing is greenwashing at the level of an individual social media post. This reflects the fact that posts assigned both Fossil Fuel and Green labels by CLAIMS indicate efforts to greenwash messaging about fossil fuels."
                    ], style={"font-size": "14px", "margin-bottom": "16px"}) ]),
                    html.Li([
                    
                    html.P([
                        html.Strong("Macro-scale greenwashing/Greenwashing Score"),
                        ": Macro-scale greenwashing is greenwashing at the company-level. To measure macro-scale greenwashing, CDO has pioneered the first quantitative social media Greenwashing Score, which compares the prevalence of a company's green messaging to its actual climate mitigation investments. To calculate the Greenwashing Score, we first calculate the prevalence of green posts (% Green posts) among all climate-relevant posts (those labeled as Green or Fossil Fuel by CLAIMS). Next, we determine the company's spending on low-carbon technologies as a fraction of its total capital expenditures (% Green CAPEX). The Greenwashing Score is defined as % Green posts divided by % Green CAPEX, with values greater than 1 indicating macro-scale greenwashing."
                    ], style={"font-size": "14px", "margin-bottom": "32px"}) ])
                    ]),
                    
                    html.P([
                        html.Strong("What is the Climate Discourse Observatory?")
                    ], style={"font-size": "14px", "font-size": "20px", "margin-bottom": "16px"}),
                    
                    html.P([
                        "CDO is a research initiative based at the Climate Accountability Lab at the University of Miami, directed by Dr. Geoffrey Supran in collaboration with the Algorithmic Transparency Institute (ATI), a project of the National Conference on Citizenship."
                    ], style={"font-size": "14px", "margin-bottom": "16px"}),

                ], className="analytics-section"),
                
                # Add hidden pagination buttons
                hidden_pagination
                
            ], className="analytics-container")
