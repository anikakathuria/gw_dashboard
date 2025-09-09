from dash import Input, Output, State
import dash

def register_filter_callbacks(app, data):
    """
    Register callbacks for filtering and resetting filters in the dashboard.

    Arguments:
        app (dash.Dash): The Dash app instance.
        data (pd.DataFrame): The dataframe containing the data to be filtered.
    
    Returns:
        None
    """
    @app.callback(
        [Output("entity_filter", "options"),
         Output("entity_filter", "value")],
        [Input("company_filter", "value")]
    )
    def update_channels(selected_companies):
        """
        Update the options for the channel filter based on the selected companies.
        Arguments:
            selected_companies (list): List of selected companies.  
        Returns:
            options (list): List of dictionaries containing label and value for each channel.
            channels (list): List of unique channels for the selected companies.
        """
        if not selected_companies:
            return [], []
        channels = []
        for company in selected_companies:
            company_channels = data.loc[
                data['company'] == company, 'attributes.search_data_fields.channel_data.channel_name'
            ].dropna().unique()
            channels.extend(company_channels)
        channels = sorted(set(channels))
        options = [{"label": ch, "value": ch} for ch in channels]
        return options, channels

    # --- Dependent options: Channels list follows Companies selection (ANALYTICS) ---
    @app.callback(
        [Output("analytics_entity_filter", "options"),
         Output("analytics_entity_filter", "value")],
        [Input("analytics_company_filter", "value")]
    )
    def update_analytics_channels(selected_companies):
        """
        Update the options for the analytics channel filter based on the selected companies.
        Arguments:
            selected_companies (list): List of selected companies.

        Returns:
            options (list): List of dictionaries containing label and value for each channel.
            channels (list): List of unique channels for the selected companies.
        """
        if not selected_companies:
            return [], []
        channels = []
        for company in selected_companies:
            company_channels = data.loc[
                data['company'] == company, 'attributes.search_data_fields.channel_data.channel_name'
            ].dropna().unique()
            channels.extend(company_channels)
        channels = sorted(set(channels))
        options = [{"label": ch, "value": ch} for ch in channels]
        return options, channels

    # --- View-specific UI visibility (Social) ---
    @app.callback(
        Output("comparison_subtoggle", "style"),
        [Input("view_toggle", "value")]
    )
    def toggle_comparison_controls(view_toggle):
        """
        Toggle the visibility of the comparison controls based on the selected view mode.
        The comparison view should only be an option in the Post Feed tab.

        Arguments:
            view_toggle (str): The selected view mode.
        Returns:
            style (dict): CSS style for the comparison controls.
        """
        return {"display": "block"} if view_toggle == "compare_posts" else {"display": "none"}

    @app.callback(
        Output("classification_filter", "style"),
        [Input("view_toggle", "value")]
    )
    def toggle_classification_filter(view_toggle):
        """
        Toggle the visibility of the classification filter based on the selected view mode.
        The classification filter should only be an option if the comparison toggle is "All Posts", not "Comparison View". 
        Arguments:
            view_toggle (str): The selected view mode.
        Returns:
            style (dict): CSS style for the classification filter.
        """
        # Hide classification multi-select in comparison mode
        return {"display": "none"} if view_toggle == "compare_posts" else {"display": "block"}

    # --- Sidebar visibility per tab ---
    @app.callback(
        [Output("social_sidebar", "style"),
         Output("analytics_sidebar", "style"),
         Output("about_sidebar", "style")],
        Input("tabs", "value")
    )
    def toggle_sidebars(tab):
        """
        Toggle the visibility of the sidebars based on the selected tab.
        Arguments:
            tab (str): The selected tab.
        Returns:
            social_style (dict): CSS style for the social media sidebar.
            analytics_style (dict): CSS style for the analytics sidebar.
            about_style (dict): CSS style for the about sidebar.
        """
        if tab == "social_media":
            return {"display": "block"}, {"display": "none"}, {"display": "none"}
        elif tab == "analytics":
            return {"display": "none"}, {"display": "block"}, {"display": "none"}
        return {"display": "none"}, {"display": "none"}, {"display": "block"}

    # === NEW: Show/Hide containers for COMPANIES & CHANNELS (both sidebars) ===

    # Social: Companies
    @app.callback(
        Output("company_filter_container", "style"),
        Input("toggle_company_filter", "value")
    )
    def toggle_social_companies(toggle_vals):
        return {"display": "block"} if toggle_vals and "show" in toggle_vals else {"display": "none"}

    # Social: Channels
    @app.callback(
        Output("entity_filter_container", "style"),
        Input("toggle_entity_filter", "value")
    )
    def toggle_social_channels(toggle_vals):
        return {"display": "block"} if toggle_vals and "show" in toggle_vals else {"display": "none"}

    # Analytics: Companies
    @app.callback(
        Output("analytics_company_filter_container", "style"),
        Input("toggle_analytics_company_filter", "value")
    )
    def toggle_analytics_companies(toggle_vals):
        return {"display": "block"} if toggle_vals and "show" in toggle_vals else {"display": "none"}

    # Analytics: Channels
    @app.callback(
        Output("analytics_entity_filter_container", "style"),
        Input("toggle_analytics_entity_filter", "value")
    )
    def toggle_analytics_channels(toggle_vals):
        return {"display": "block"} if toggle_vals and "show" in toggle_vals else {"display": "none"}

    # --- Reset (SOCIAL) ---
    @app.callback(
        [Output("keyword_search", "value"),
         Output("view_toggle", "value"),
         Output("left_view", "value"),
         Output("right_view", "value"),
         Output("date_range", "value"),                 # RangeSlider -> value=[min_year, max_year]
         Output("company_filter", "value"),
         Output("platform_filter", "value"),
         Output("classification_dropdown", "value"),
         Output("uniqueness_toggle", "value"),
         Output("social_fossil_subcategories", "value"),
         Output("social_green_subcategories", "value"),
         Output("toggle_company_filter", "value"),      # keep Companies shown after reset
         Output("toggle_entity_filter", "value")],      # keep Channels hidden after reset
        [Input("reset_social_filters", "n_clicks")],
        prevent_initial_call=True
    )
    def reset_social_filters(n_clicks):
        """
        Reset the filters in the social media tab to their default values.
        Arguments:
            n_clicks (int): Number of clicks on the reset button.
        Returns:
                keyword_search (str): Default value for the keyword search.
                view_toggle (str): Default value for the view toggle.
                left_view (str): Default value for the left view.
                right_view (str): Default value for the right view.
                date_range (str): Default value for the date range.
                company_filter (list): Default value for the company filter.
                platform_filter (list): Default value for the platform filter.
                classification_dropdown (list): Default value for the classification dropdown.
                uniqueness_toggle (str): Default value for the uniqueness toggle.
                social_fossil_subcategories (list): Default value for the social fossil subcategories.
                social_green_subcategories (list): Default value for the social green subcategories.
        """
        if not n_clicks:
            return dash.no_update

        companies = sorted(data['company'].dropna().unique())
        platforms = sorted(data['attributes.search_data_fields.platform_name'].dropna().unique())
        min_year = int(data['attributes.published_at'].min().year)
        max_year = int(data['attributes.published_at'].max().year)

        return (
            "",                       # keyword_search
            "compare_posts",          # view_toggle
            "green",                  # left_view
            "brown",                  # right_view
            [min_year, max_year],     # date_range (RangeSlider)
            companies,                # company_filter
            platforms,                # platform_filter
            ["green", "brown", "green_brown", "misc"],  # classification_dropdown
            "all",                    # uniqueness_toggle
            [],                       # social_fossil_subcategories
            [],                       # social_green_subcategories
            ["show"],                 # toggle_company_filter -> show container
            []                        # toggle_entity_filter  -> keep hidden by default
        )

    # --- Reset (ANALYTICS) ---
    @app.callback(
        [Output("analytics_date_range", "value"),       # RangeSlider -> [min_year, max_year]
         Output("analytics_company_filter", "value"),
         Output("analytics_platform_filter", "value"),
         Output("analytics_uniqueness_toggle", "value"),
         Output("analytics_fossil_subcategories", "value"),
         Output("analytics_green_subcategories", "value"),
         Output("toggle_analytics_company_filter", "value"),   # show Companies after reset
         Output("toggle_analytics_entity_filter", "value")],   # hide Channels after reset
        [Input("reset_analytics_filters", "n_clicks")],
        prevent_initial_call=True
    )
    def reset_analytics_filters(n_clicks):
        """
        Reset the filters in the analytics tab to their default values.
        Arguments:
            n_clicks (int): Number of clicks on the reset button.
        
        Returns:
            analytics_date_range (str): Default value for the analytics date range.
            analytics_company_filter (list): Default value for the analytics company filter.
            analytics_platform_filter (list): Default value for the analytics platform filter.
            analytics_uniqueness_toggle (str): Default value for the analytics uniqueness toggle.
            analytics_fossil_subcategories (list): Default value for the analytics fossil subcategories.
            analytics_green_subcategories (list): Default value for the analytics green subcategories.
        """
        if not n_clicks:
            return dash.no_update

        companies = sorted(data['company'].dropna().unique())
        platforms = sorted(data['attributes.search_data_fields.platform_name'].dropna().unique())
        min_year = int(data['attributes.published_at'].min().year)
        max_year = int(data['attributes.published_at'].max().year)

        return (
            [min_year, max_year],  # analytics_date_range
            companies,             # analytics_company_filter
            platforms,             # analytics_platform_filter
            "all",                 # analytics_uniqueness_toggle
            [],                    # analytics_fossil_subcategories
            [],                    # analytics_green_subcategories
            ["show"],              # toggle_analytics_company_filter -> show
            []                     # toggle_analytics_entity_filter  -> hide
        )
