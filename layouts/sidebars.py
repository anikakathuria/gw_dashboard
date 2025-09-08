from dash import html, dcc

def create_sidebars(data):
    """
    Creates the sidebars for the dashboard for each of the three tabs: Post Feed, Analytics, and About.
    Returns a tuple: (social_sidebar, analytics_sidebar, about_sidebar).
    """
    # Get unique companies and channels
    companies = sorted(data['company'].dropna().unique())
    company_channels = {
        company: sorted(
            data[data['company'] == company]['attributes.search_data_fields.channel_data.channel_name'].unique()
        )
        for company in companies
    }

    # ----- Year bounds for sliders -----
    min_year = int(data['attributes.published_at'].min().year)
    max_year = int(data['attributes.published_at'].max().year)

    # Tidy marks (about ~6 ticks incl. ends)
    def year_marks(a, b):
        rng = b - a
        step = max(1, rng // 6) if rng > 0 else 1
        marks = {y: str(y) for y in range(a, b + 1, step)}
        marks[a] = str(a)
        marks[b] = str(b)
        return marks

    # ---------------- Social Media Sidebar ----------------
    social_sidebar = html.Div([
        html.H3("Feed Filters", style={"margin-bottom": "14px", "color": "#1a237e", "font-weight": "600"}),

        # Reset button
        html.Button(
            "Reset All Filters",
            id="reset_social_filters",
            className="reset-button",
            style={
                "width": "100%",
                "margin-bottom": "20px",
                "padding": "8px",
                "background-color": "#f5f5f5",
                "border": "1px solid #ddd",
                "border-radius": "4px",
                "cursor": "pointer"
            }
        ),

        # Post count badge mount
        html.Div(id="post_count_badge", className="post-count-badge", style={"marginBottom": "12px"}),

        html.Label("Keyword Search", style={"font-weight": "500", "margin-bottom": "8px"}),
        dcc.Input(
            id="keyword_search",
            type="text",
            placeholder="Search in posts...",
            style={"width": "100%", "padding": "8px", "margin-bottom": "20px"}
        ),

        # Year slider (replaces DatePickerRange)
        html.Label("Year Range", style={"font-weight": "500", "margin-bottom": "8px"}),
        dcc.RangeSlider(
            id="date_range",                       # keep existing id used by callbacks
            min=min_year,
            max=max_year,
            value=[min_year, max_year],
            step=1,
            allowCross=False,
            marks=year_marks(min_year, max_year),
            tooltip={"placement": "bottom", "always_visible": False},
        ),

        html.Label("View", style={"font-weight": "500", "margin-bottom": "8px", "margin-top": "20px"}),
        dcc.RadioItems(
            id="view_toggle",
            options=[
                {"label": "Comparison View", "value": "compare_posts"},
                {"label": "All Posts", "value": "all_posts"},
            ],
            value="compare_posts",
            style={"margin-bottom": "20px"}
        ),
        html.Div(id="comparison_subtoggle", children=[
            html.Label("Classification 1", style={"font-weight": "300", "margin-bottom": "8px"}),
            dcc.Dropdown(
                id="left_view",
                options=[
                    {"label": "Green", "value": "green"},
                    {"label": "Fossil", "value": "brown"},
                    {"label": "Green + Fossil", "value": "green_brown"},
                    {"label": "Miscellaneous", "value": "misc"}
                ],
                value="green",
                style={"margin-bottom": "20px"}
            ),
            html.Label("Classification 2", style={"font-weight": "300", "margin-bottom": "8px"}),
            dcc.Dropdown(
                id="right_view",
                options=[
                    {"label": "Green", "value": "green"},
                    {"label": "Fossil", "value": "brown"},
                    {"label": "Green + Fossil", "value": "green_brown"},
                    {"label": "Miscellaneous", "value": "misc"}
                ],
                value="brown",
                style={"margin-bottom": "20px"}
            )
        ]),
        html.Label("Companies", style={"font-weight": "500", "margin-bottom": "8px"}),
        dcc.Dropdown(
            id="company_filter",
            options=[{"label": c, "value": c} for c in companies],
            multi=True,
            value=companies,
            style={"margin-bottom": "20px"}
        ),
        html.Label("Platforms", style={"font-weight": "500", "margin-bottom": "8px"}),
        dcc.Dropdown(
            id="platform_filter",
            options=[{"label": p, "value": p} for p in sorted(data['attributes.search_data_fields.platform_name'].unique())],
            multi=True,
            value=[p for p in sorted(data['attributes.search_data_fields.platform_name'].unique())],
            style={"margin-bottom": "20px"}
        ),
        html.Div(id="classification_filter", children=[
            html.Label("Classification", style={"font-weight": "500", "margin-bottom": "8px"}),
            dcc.Dropdown(
                id="classification_dropdown",
                options=[
                    {"label": "Green", "value": "green"},
                    {"label": "Fossil", "value": "brown"},
                    {"label": "Green + Fossil", "value": "green_brown"},
                    {"label": "Miscellaneous", "value": "misc"}
                ],
                multi=True,
                value=["green", "brown", "green_brown", "misc"],
                style={"margin-bottom": "20px"}
            )
        ]),
        # Subcategory filters
        html.Label("Subcategories", style={"font-weight": "500", "margin-bottom": "8px"}),
        html.Div([
            html.Div([
                html.Label("Fossil Fuel Categories", style={"font-weight": "500", "margin-bottom": "8px", "color": "#8b5b4b"}),
                dcc.Checklist(
                    id="social_fossil_subcategories",
                    options=[
                        {"label": "Primary Product", "value": "primary_product"},
                        {"label": "Petrochemical Product", "value": "petrochemical_product"},
                        {"label": "Fossil Fuel Infrastructure", "value": "infrastructure_production"},
                        {"label": "Other Fossil", "value": "other_fossil"}
                    ],
                    value=[],
                    style={"margin-bottom": "16px"}
                )
            ]),
            html.Div([
                html.Label("Green Categories", style={"font-weight": "500", "margin-bottom": "8px", "color": "#a7caa0"}),
                dcc.Checklist(
                    id="social_green_subcategories",
                    options=[
                        {"label": "Decreasing Emissions", "value": "decreasing_emissions"},
                        {"label": "Viable Solutions", "value": "viable_solutions"},
                        {"label": "False Solutions", "value": "false_solutions"},
                        {"label": "Recycling & Waste Management", "value": "recycling_waste_management"},
                        {"label": "Nature & Animal References", "value": "nature_animal_references"},
                        {"label": "Generic Environmental References", "value": "generic_environmental_references"},
                        {"label": "Other Green", "value": "other_green"}
                    ],
                    value=[],
                    style={"margin-bottom": "16px"}
                )
            ])
        ], style={"margin-bottom": "20px"}),
        html.Label("Channels", style={"font-weight": "500", "margin-bottom": "8px"}),
        dcc.Dropdown(
            id="entity_filter",
            options=[{"label": ch, "value": ch} for company in companies for ch in company_channels[company]],
            multi=True,
            value=[ch for ch_list in company_channels.values() for ch in ch_list],
            style={"margin-bottom": "20px"}
        ),
        html.Label("Message Type", style={"font-weight": "500", "margin-bottom": "8px"}),
        dcc.RadioItems(
            id="uniqueness_toggle",
            options=[
                {"label": "Unique Messages", "value": "unique"},
                {"label": "All Posts", "value": "all"},
            ],
            value="all",
            style={"margin-bottom": "20px"}
        )
    ], id="social_sidebar", className="sidebar")

    # Analytics Sidebar
    analytics_sidebar = html.Div([
        html.H3("Analytics Filters", style={"margin-bottom": "14px", "color": "#1a237e", "font-weight": "600"}),

        # Reset button
        html.Button(
            "Reset All Filters",
            id="reset_analytics_filters",
            className="reset-button",
            style={
                "width": "100%",
                "margin-bottom": "20px",
                "padding": "8px",
                "background-color": "#f5f5f5",
                "border": "1px solid #ddd",
                "border-radius": "4px",
                "cursor": "pointer"
            }
        ),

        # Post count badge mount for analytics
        html.Div(id="analytics_post_count_badge", className="post-count-badge", style={"marginBottom": "12px"}),

        # Year slider (replaces DatePickerRange)
        html.Label("Year Range", style={"font-weight": "500", "margin-bottom": "8px"}),
        dcc.RangeSlider(
            id="analytics_date_range",            # keep existing id used by callbacks
            min=min_year,
            max=max_year,
            value=[min_year, max_year],
            step=1,
            allowCross=False,
            marks=year_marks(min_year, max_year),
            tooltip={"placement": "bottom", "always_visible": False},
        ),

        html.Label("Companies", style={"font-weight": "500", "margin-top": "20px", "margin-bottom": "8px"}),
        dcc.Dropdown(
            id="analytics_company_filter",
            options=[{"label": c, "value": c} for c in companies],
            multi=True,
            value=companies,
            style={"margin-bottom": "20px"}
        ),
        html.Label("Platforms", style={"font-weight": "500", "margin-bottom": "8px"}),
        dcc.Dropdown(
            id="analytics_platform_filter",
            options=[{"label": p, "value": p} for p in sorted(data['attributes.search_data_fields.platform_name'].unique())],
            multi=True,
            value=[p for p in sorted(data['attributes.search_data_fields.platform_name'].unique())],
            style={"margin-bottom": "20px"}
        ),
        # Subcategory filters
        html.Label("Subcategories", style={"font-weight": "500", "margin-bottom": "8px"}),
        html.Div([
            html.Div([
                html.Label("Fossil Fuel Categories", style={"font-weight": "500", "margin-bottom": "8px", "color": "#8b5b4b"}),
                dcc.Checklist(
                    id="analytics_fossil_subcategories",
                    options=[
                        {"label": "Primary Product", "value": "primary_product"},
                        {"label": "Petrochemical Product", "value": "petrochemical_product"},
                        {"label": "Fossil Fuel Infrastructure", "value": "ff_infrastructure_production"},
                        {"label": "Other Fossil", "value": "other_fossil"}
                    ],
                    value=[],
                    style={"margin-bottom": "16px"}
                )
            ]),
            html.Div([
                html.Label("Green Categories", style={"font-weight": "500", "margin-bottom": "8px", "color": "#a7caa0"}),
                dcc.Checklist(
                    id="analytics_green_subcategories",
                    options=[
                        {"label": "Renewable Energy", "value": "renewable_energy"},
                        {"label": "Emissions Reduction", "value": "emissions_reduction"},
                        {"label": "False Solutions", "value": "false_solutions"},
                        {"label": "Recycling", "value": "recycling"},
                        {"label": "Other Green", "value": "other_green"}
                    ],
                    value=[],
                    style={"margin-bottom": "16px"}
                )
            ])
        ], style={"margin-bottom": "20px"}),
        html.Label("Channels", style={"font-weight": "500", "margin-bottom": "8px"}),
        dcc.Dropdown(
            id="analytics_entity_filter",
            options=[{"label": ch, "value": ch} for company in companies for ch in company_channels[company]],
            multi=True,
            value=[ch for ch_list in company_channels.values() for ch in ch_list],
            style={"margin-bottom": "20px"}
        ),
        html.Label("Message Type", style={"font-weight": "500", "margin-bottom": "8px"}),
        dcc.RadioItems(
            id="analytics_uniqueness_toggle",
            options=[
                {"label": "Unique Messages", "value": "unique"},
                {"label": "All Posts", "value": "all"},
            ],
            value="all",
            style={"margin-bottom": "20px"}
        )
    ], id="analytics_sidebar", className="sidebar", style={"display": "none"})

    # About Sidebar
    about_sidebar = html.Div([
        html.P("Select a tab to view and filter content.", style={"font-weight": "500", "margin-bottom": "8px"}),
    ], id="about_sidebar", className="sidebar", style={"display": "none"})

    return social_sidebar, analytics_sidebar, about_sidebar
