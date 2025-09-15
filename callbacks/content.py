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
    """
    @app.callback(
        [
            Output("content", "children"),
            Output("post_count_badge", "children"),
            Output("analytics_post_count_badge", "children"),
        ], 
        [
            Input("tabs", "value"),
            Input('current_page', 'data'),

            # Social-media filters
            Input('date_range', 'value'),
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
            Input('analytics_date_range', 'value'),
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
        sm_years, sm_companies, sm_entities, sm_platforms, sm_classifs,
        view_toggle, left_view, right_view, sm_uniqueness, keyword_search,
        sm_fossil_subcategories, sm_green_subcategories,

        # analytics inputs
        an_years, an_companies, an_entities, an_platforms, an_uniqueness,
        an_fossil_subcategories, an_green_subcategories
    ):
        filtered_data = data.copy()
        print(len(filtered_data))

        # --- small helper: get first existing column name from candidates ---
        def first_existing(df, candidates):
            for c in candidates:
                if c in df.columns:
                    return c
            return None
        
        if tab_name == "social_media":
            if sm_years and len(sm_years) == 2:
                y0, y1 = int(sm_years[0]), int(sm_years[1])
                start_date, end_date = f"{y0}-01-01", f"{y1}-12-31",
            else:
                start_date = end_date = None
            companies, entities, platforms, classifications = (
                sm_companies, sm_entities, sm_platforms, sm_classifs
            )
            uniqueness = sm_uniqueness
            
            # Social subcategory filters
            subcategory_filters = {
                "primary_product": "primary_product" in sm_fossil_subcategories,
                "petrochemical_product": "petrochemical_product" in sm_fossil_subcategories,
                "infrastructure_production": "infrastructure_production" in sm_fossil_subcategories,
                "other_fossil": "fossil_fuel_other" in sm_fossil_subcategories,
                "decreasing_emissions": "decreasing_emissions" in sm_green_subcategories,
                "viable_solutions": "viable_solutions" in sm_green_subcategories,
                "false_solutions": "false_solutions" in sm_green_subcategories,
                "recycling_waste_management": "recycling_waste_management" in sm_green_subcategories,
                "nature_animal_references": "nature_animal_references" in sm_green_subcategories,
                "generic_environmental_references": "generic_environmental_references" in sm_green_subcategories,
                "other_green": "green_other" in sm_green_subcategories
            }
        else:  # analytics
            if an_years and len(an_years) == 2:
                y0, y1 = int(an_years[0]), int(an_years[1])
                start_date, end_date = f"{y0}-01-01", f"{y1}-12-31",
            else:
                start_date = end_date = None
            companies, entities, platforms = an_companies, an_entities, an_platforms
            uniqueness = an_uniqueness
            keyword_search = None
            
            # Analytics subcategory filters
            subcategory_filters = {
                "primary_product": "primary_product" in an_fossil_subcategories,
                "petrochemical_product": "petrochemical_product" in an_fossil_subcategories,
                "infrastructure_production": "infrastructure_production" in an_fossil_subcategories,
                "other_fossil": "fossil_fuel_other" in an_fossil_subcategories,
                "decreasing_emissions": "decreasing_emissions" in an_green_subcategories,
                "viable_solutions": "viable_solutions" in an_green_subcategories,
                "false_solutions": "false_solutions" in an_green_subcategories,
                "recycling_waste_management": "recycling_waste_management" in an_green_subcategories,
                "nature_animal_references": "nature_animal_references" in an_green_subcategories,
                "generic_environmental_references": "generic_environmental_references" in an_green_subcategories,
                "other_green": "green_other" in an_green_subcategories
            }

        # ---- pick title/body columns safely (works across schema variants) ----
        title_col = first_existing(filtered_data, [
            'attributes.search_data_fields.post_title',
            'attributes.post_title',
            'post_title',
            'title'
        ])
        body_col = first_existing(filtered_data, [
            'attributes.complete_post_text',
            'complete_post_text',
            'attributes.search_data_fields.post_text',
            'post_text',
            'text',
            'content'
        ])

        # Apply uniqueness filter (dedupe) safely on whichever text column exists
        if uniqueness == "unique":
            dedup_col = body_col or title_col
            if dedup_col:
                filtered_data = url_deduplicate(filtered_data, dedup_col)

        # Apply keyword search robustly (if columns exist)
        if keyword_search:
            kw = str(keyword_search).lower()
            # If no searchable columns exist, skip filtering
            if title_col or body_col:
                mask = pd.Series(False, index=filtered_data.index)
                if title_col:
                    mask = mask | filtered_data[title_col].astype(str).str.lower().str.contains(kw, na=False)
                if body_col and body_col != title_col:
                    mask = mask | filtered_data[body_col].astype(str).str.lower().str.contains(kw, na=False)
                filtered_data = filtered_data[mask]

        # Apply date filter (ensure dtype is comparable)
        if start_date and end_date:
            col_date = 'attributes.published_at'
            if col_date in filtered_data.columns:
                if not pd.api.types.is_datetime64_any_dtype(filtered_data[col_date]):
                    filtered_data[col_date] = pd.to_datetime(filtered_data[col_date], errors='coerce')
                filtered_data = filtered_data[
                    (filtered_data[col_date] >= pd.to_datetime(start_date)) &
                    (filtered_data[col_date] <= pd.to_datetime(end_date))
                ]

        # Apply company filter
        if companies:
            filtered_data = filtered_data[filtered_data['company'].isin(companies)]
        
        # Apply entity filter
        if entities:
            filtered_data = filtered_data[
                filtered_data['attributes.search_data_fields.channel_data.channel_name'].isin(entities)
            ]
        
        # Apply platform filter
        if platforms:
            filtered_data = filtered_data[
                filtered_data['attributes.search_data_fields.platform_name'].isin(platforms)
            ]
        
        # Apply subcategory filters
        for subcategory, is_active in subcategory_filters.items():
            if is_active and subcategory in filtered_data.columns:
                filtered_data = filtered_data[filtered_data[subcategory] == 1]
        
        if tab_name == "social_media":
            if classifications:
                filtered_data = filtered_data[filtered_data['green_brown'].isin(classifications)]

            posts_per_page = 20
            
            if view_toggle == "all_posts":
                # All Posts View
                posts_per_page = 20
                start = current_page * posts_per_page
                end = start + posts_per_page
                
                all_posts = [
                    create_post_component(row, highlight=keyword_search)
                    for _, row in filtered_data.iloc[start:end].iterrows()
                ]
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
                    "display": "block"
                })
                
                # Simple two-column layout
                mid_point = (len(all_posts) + 1) // 2
                left_posts = all_posts[:mid_point]
                right_posts = all_posts[mid_point:]
                
                content_div = html.Div([
                    html.Div([
                        html.Div([
                            html.Div(left_posts, className="posts-grid")
                        ], style={"width": "48%", "display": "inline-block", "vertical-align": "top"}),
                        html.Div([
                            html.Div(right_posts, className="posts-grid")
                        ], style={"width": "48%", "display": "inline-block", "margin-left": "4%", "vertical-align": "top"})
                    ], style={"display": "flex", "align-items": "flex-start"}),
                    pagination_buttons
                ])

                sidebar_badge = html.Div([
                    "Showing ",
                    html.Strong(f"{len(filtered_data)}"),
                    " posts"
                ], className="post-count")

                return content_div, sidebar_badge, ""
            
            elif view_toggle == "compare_posts":
                # Comparison View with pagination
                left_data = filtered_data[filtered_data['green_brown'] == left_view]
                right_data = filtered_data[filtered_data['green_brown'] == right_view]
                
                # Apply pagination to both sides
                start = current_page * posts_per_page
                end = start + posts_per_page
                
                left_posts = [create_post_component(row, highlight=keyword_search)
                            for _, row in left_data.iloc[start:end].iterrows()]
                right_posts = [create_post_component(row, highlight=keyword_search)
                            for _, row in right_data.iloc[start:end].iterrows()]
                
                max_posts = max(len(left_data), len(right_data))
                
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
                    "textAlign": "center",
                    "marginTop": "32px",
                    "paddingBottom": "32px",
                    "display": "block"
                })
                
                # === FLEX WRAPPER + CATEGORY CONTAINERS ===
                content_div = html.Div([
                    html.Div([
                        # Left category column
                        html.Div([
                            html.H3(f"{classification_labels[left_view]} Posts",
                                    className="comparison-title",
                                    style={"margin": "0 0 12px 0", "textAlign": "center"}),
                            html.Div(left_posts, className="posts-grid")
                        ], className="category", style={"width": "48%"}),

                        # Right category column
                        html.Div([
                            html.H3(f"{classification_labels[right_view]} Posts",
                                    className="comparison-title",
                                    style={"margin": "0 0 12px 0", "textAlign": "center"}),
                            html.Div(right_posts, className="posts-grid")
                        ], className="category", style={"width": "48%"})
                    ], style={
                        "display": "flex",
                        "gap": "4%",
                        "alignItems": "flex-start"
                    }),
                    pagination_buttons
                ])

                left_n = len(left_data)
                right_n = len(right_data)
                sidebar_badge = html.Div([
                    "Showing ",
                    html.Strong(f"{left_n + right_n}"),
                    f" posts ({classification_labels[left_view]}: {left_n} | {classification_labels[right_view]}: {right_n})"
                ], className="post-count")

                return content_div, sidebar_badge, ""
        
        elif tab_name == "analytics":
            # Generate overview plots using the Plotly-based functions
            overview_fig = plot_overview(filtered_data, codebook, green_brown_colors)
            raw_greenwashing_fig = plot_combined_greenwashing_scores(filtered_data)
            green_share_fig = plot_green_share(filtered_data)
            
            # Hidden pagination buttons for analytics tab (keep DOM)
            hidden_pagination = html.Div([
                html.Button('← Previous', id='prev_page', n_clicks=0, className="pagination-button"),
                html.Button('Next →', id='next_page', n_clicks=0, className="pagination-button")
            ], style={"display": "none"})
            
            content_div = html.Div([
                # Overview Section
                html.Div([
                    html.H2("Post Classification Overview", className="analytics-header"),
                    html.P(
                        "This section shows the distribution of social media posts across categories and sub-categories.",
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
                    html.Div(
                        dcc.Graph(
                            figure=raw_greenwashing_fig,
                            config={'displayModeBar': False},
                            style={"height": "600px"}
                        )
                    ),
                    html.P(
                        "CDO has pioneered the first quantitative social media Greenwashing Score, which compares the prevalence of a company’s green messaging to its actual climate mitigation investments. The Greenwashing Score is defined as % Green posts divided by % Green CAPEX (capital expenditures), with values greater than 1 indicating greenwashing at the company-level, which we term macro-scale greenwashing. The line graphs show the Greenwashing Score over time for each company.",
                        className="analytics-description"
                    ),
                ], className="analytics-section"),

                # Green Share Section
                html.Div([
                    html.H2("Green Share of Climate Relevant posts", className="analytics-header"),
                    html.Div(
                        dcc.Graph(
                            figure=green_share_fig,
                            config={'displayModeBar': False},
                            style={"height": "600px"}
                        )
                    ),
                    html.P(
                        "Line graph showing the fraction of climate-relevant social media posts that contain Green messaging. We here define Green messaging as any post labelled by CLAIMS as Only Green or Green+Fossil. We define climate-relevant posts as all posts except Miscellaneous ones.",
                        className="analytics-description"
                    ),
                ], className="analytics-section"),
                
                # Add hidden pagination buttons
                hidden_pagination

            ], className="analytics-container")

            analytics_badge = html.Div([
                "Analysis based on ",
                html.Strong(f"{len(filtered_data)}"),
                " posts"
            ], className="post-count")

            return content_div, "", analytics_badge
            
        elif tab_name == "about":
            # Hidden pagination to keep DOM
            hidden_pagination = html.Div([
                html.Button('← Previous', id='prev_page', n_clicks=0, className="pagination-button"),
                html.Button('Next →', id='next_page', n_clicks=0, className="pagination-button")
            ], style={"display": "none"})

            total_posts = len(data)
            
            content_div = html.Div([
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
                    html.Div([
                        html.Img(
                            src="/assets/codebook_diagram.png",
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
                                html.Li([html.Strong("Decreasing Emissions"), ": Positive or neutral references to greenhouse gas emissions reduction."]),
                                html.Li([html.Strong("Renewables & Low-Carbon Technologies"), ": Positive or neutral references to renewable energy and/or other low-carbon technology solutions, such as solar, wind, or hydropower."]),
                                html.Li([html.Strong("False Solutions"), ": Positive or neutral references to fossil-fuel-adjacent 'false solutions' to climate change, such as carbon capture, hydrogen, or \"clean\" methane."]),
                                html.Li([html.Strong("Recycling & Waste Management"), ": Positive or neutral references to recycling and waste management efforts."]),
                                html.Li([html.Strong("Other Green"), ": Other green messaging, such as nature and generic environmental references."])
                            ], style={"font-size": "14px", "margin-bottom": "16px", "padding-left": "30px"})
                        ]),

                        html.Li([
                            html.P([
                                html.Strong("Fossil Fuel posts"),
                                ": If CLAIMS assigns at least one Fossil Fuel label to a post and no green labels, the post is coded as Fossil Fuel."
                            ], style={"font-size": "14px", "margin-bottom": "8px"}),
                            html.Ul([
                                html.Li([html.Strong("Primary Product"), ": References to one or more fossil fuel primary products, such as coal, oil, or methane."]),
                                html.Li([html.Strong("Petrochemical Product"), ": References to one or more petrochemical products, such as gasoline or lubricants."]),
                                html.Li([html.Strong("Infrastructure & Production"), ": References to fossil fuel production, operations, and/or infrastructure, such as pipelines, oil fields, or refineries."]),
                                html.Li([html.Strong("Other Fossil Fuel"), ": Other fossil fuel related messaging not captured by the labels above."])
                            ], style={"font-size": "14px", "margin-bottom": "16px", "padding-left": "30px"})
                        ]),

                        html.Li([
                            html.P([
                                html.Strong("Miscellaneous posts"),
                                ": Posts not assigned any Green or Fossil Fuel labels by CLAIMS are not relevant to climate change and are coded as Miscellaneous."
                            ], style={"font-size": "14px", "margin-bottom": "16px"})
                        ]),

                        html.Li([
                            html.P([
                                html.Strong("Micro-scale greenwashing"),
                                ": Micro-scale greenwashing is greenwashing at the level of an individual social media post. This reflects the fact that posts assigned both Fossil Fuel and Green labels by CLAIMS indicate efforts to greenwash messaging about fossil fuels."
                            ], style={"font-size": "14px", "margin-bottom": "16px"})
                        ]),
                        html.Li([
                            html.P([
                                html.Strong("Macro-scale greenwashing/Greenwashing Score"),
                                ": Macro-scale greenwashing is greenwashing at the company-level. To measure macro-scale greenwashing, CDO has pioneered the first quantitative social media Greenwashing Score, which compares the prevalence of a company's green messaging to its actual climate mitigation investments. To calculate the Greenwashing Score, we first calculate the prevalence of green posts (% Green posts) among all climate-relevant posts (those labeled as Green or Fossil Fuel by CLAIMS). Next, we determine the company's spending on low-carbon technologies as a fraction of its total capital expenditures (% Green CAPEX). The Greenwashing Score is defined as % Green posts divided by % Green CAPEX, with values greater than 1 indicating macro-scale greenwashing."
                            ], style={"font-size": "14px", "margin-bottom": "32px"})
                        ])
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

            # For About, either show nothing or a dataset summary in the sidebar
            return content_div, "", ""
