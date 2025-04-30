from dash import Input, Output, State, ALL, callback_context
import dash

def register_filter_callbacks(app, data):
    @app.callback(
        [Output("entity_filter", "options"),
         Output("entity_filter", "value")],
        [Input("company_filter", "value")]
    )
    def update_channels(selected_companies):
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
        if view_toggle == "compare_posts":
            return {"display": "block"}
        return {"display": "none"}

    @app.callback(
        Output("classification_filter", "style"),
        [Input("view_toggle", "value")]
    )
    def toggle_classification_filter(view_toggle):
        if view_toggle == "compare_posts":
            return {"display": "none"}
        return {"display": "block"}
    
    @app.callback(
        [Output("social_sidebar", "style"), Output("analytics_sidebar", "style"), Output("about_sidebar", "style")],
        Input("tabs", "value")
    )
    def toggle_sidebars(tab):
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
