from dash import Input, Output, State, ALL, callback_context
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
            company_channels = data[data['company'] == company]['search_data_fields.channel_data.channel_name'].unique()
            channels.extend(company_channels)
        
        channels = sorted(channels)
        options = [{"label": channel, "value": channel} for channel in channels]
        return options, channels

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
            company_channels = data[data['company'] == company]['search_data_fields.channel_data.channel_name'].unique()
            channels.extend(company_channels)
        
        channels = sorted(channels)
        options = [{"label": channel, "value": channel} for channel in channels]
        return options, channels
    
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

        if view_toggle == "compare_posts":
            return {"display": "block"}
        return {"display": "none"}

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
        if view_toggle == "compare_posts":
            return {"display": "none"}
        return {"display": "block"}
    
    @app.callback(
        [Output("social_sidebar", "style"), Output("analytics_sidebar", "style"), Output("about_sidebar", "style")],
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
        else:  # about
            return {"display": "none"}, {"display": "none"}, {"display": "block"}
    
    # Reset social filters
    @app.callback(
        [Output("keyword_search", "value"),
         Output("view_toggle", "value"),
         Output("left_view", "value"),
         Output("right_view", "value"),
         Output("date_range", "start_date"),
         Output("date_range", "end_date"),
         Output("company_filter", "value"),
         Output("platform_filter", "value"),
         Output("classification_dropdown", "value"),
         Output("uniqueness_toggle", "value"),
         Output("social_fossil_subcategories", "value"),
         Output("social_green_subcategories", "value")],
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
        if n_clicks is None:
            return dash.no_update
        
        companies = sorted(data['company'].unique())
        platforms = sorted(data['search_data_fields.platform_name'].unique())
        
        return (
            "",  # keyword_search
            "compare_posts",  # view_toggle
            "green",  # left_view
            "brown",  # right_view
            data['published_at'].min().strftime('%Y-%m-%d'),  # date_range start
            data['published_at'].max().strftime('%Y-%m-%d'),  # date_range end
            companies,  # company_filter
            platforms,  # platform_filter
            ["green", "brown", "green_brown", "misc"],  # classification_dropdown
            "all",  # uniqueness_toggle
            [],  # social_fossil_subcategories
            []   # social_green_subcategories
        )
    
    # Reset analytics filters
    @app.callback(
        [Output("analytics_date_range", "start_date"),
         Output("analytics_date_range", "end_date"),
         Output("analytics_company_filter", "value"),
         Output("analytics_platform_filter", "value"),
         Output("analytics_uniqueness_toggle", "value"),
         Output("analytics_fossil_subcategories", "value"),
         Output("analytics_green_subcategories", "value")],
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
        
        if n_clicks is None:
            return dash.no_update
        
        companies = sorted(data['company'].unique())
        platforms = sorted(data['search_data_fields.platform_name'].unique())
        
        return (
            data['published_at'].min().strftime('%Y-%m-%d'),  # date_range start
            data['published_at'].max().strftime('%Y-%m-%d'),  # date_range end
            companies,  # company_filter
            platforms,  # platform_filter
            "all",  # uniqueness_toggle
            [],  # analytics_fossil_subcategories
            []   # analytics_green_subcategories
        )
