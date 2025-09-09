import dash
from dash import Input, Output, State, clientside_callback

def register_navigation_callbacks(app):
    """
    Register callbacks for navigation and pagination in the dashboard.
    Arguments:
        app (dash.Dash): The Dash app instance.
    Returns:
        None
    """
    @app.callback(
        Output('current_page', 'data'),
        [Input('prev_page', 'n_clicks'),
         Input('next_page', 'n_clicks'),
         # Add all filter inputs that should reset the page
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
         # Tab change
         Input('tabs', 'value')],
        [State('current_page', 'data')]
    )
    def update_page(prev_clicks, next_clicks, 
                   # Filter states
                   sm_years, sm_companies, sm_entities, sm_platforms, sm_classifs,
                   view_toggle, left_view, right_view, sm_uniqueness, keyword_search,
                   sm_fossil_subcategories, sm_green_subcategories,
                   # Analytics filters
                   an_years, an_companies, an_entities, an_platforms, an_uniqueness,
                   an_fossil_subcategories, an_green_subcategories,
                   # Tab
                   active_tab,
                   # Current page state
                   current_page):
        """
        Update the current page.

        Arguments:
            prev_clicks (int): Number of clicks on the previous page button.
            next_clicks (int): Number of clicks on the next page button.
            sm_start (str): Start date for social media filter.
            sm_end (str): End date for social media filter.
            sm_companies (list): Selected companies for social media filter.
            sm_entities (list): Selected entities for social media filter.
            sm_platforms (list): Selected platforms for social media filter.
            sm_classifs (list): Selected classifications for social media filter.
            view_toggle (str): View toggle state.
            left_view (str): Left view state.
            right_view (str): Right view state.
            sm_uniqueness (str): Uniqueness toggle state for social media.
            keyword_search (str): Keyword search value.
            sm_fossil_subcategories (list): Selected fossil subcategories for social media filter.
            sm_green_subcategories (list): Selected green subcategories for social media filter.
            an_start (str): Start date for analytics filter.
            an_end (str): End date for analytics filter.
            an_companies (list): Selected companies for analytics filter.
            an_entities (list): Selected entities for analytics filter.
            an_platforms (list): Selected platforms for analytics filter.
            an_uniqueness (str): Uniqueness toggle state for analytics.
            an_fossil_subcategories (list): Selected fossil subcategories for analytics filter.
            an_green_subcategories (list): Selected green subcategories for analytics filter.
            active_tab (str): The currently active tab in the dashboard.
            current_page (int): The current page number.
        
        Returns:
            int: The updated page number.
        """
        ctx = dash.callback_context
        page = current_page or 0

        if not ctx.triggered:
            return 0  # Default to first page
        
        # Get the ID of the component that triggered the callback
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # If tab changed or any filter changed, reset to page 0
        if triggered_id != 'prev_page' and triggered_id != 'next_page':
            return 0
        
        # Only handle pagination if we're on the social media tab
        if active_tab == "social_media":
            # Handle pagination buttons
            if triggered_id == 'prev_page':
                return max(0, page - 1)
            if triggered_id == 'next_page':
                return page + 1
        
        return page
    
    # Add a clientside callback to scroll to top when page changes
    clientside_callback(
        """
        function(page_number) {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
            return null;
        }
        """,
        Output('_', 'children'),  # This is a dummy output
        [Input('current_page', 'data')]
    )
