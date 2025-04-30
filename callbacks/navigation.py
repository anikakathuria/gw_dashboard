import dash
from dash import Input, Output, State, clientside_callback

def register_navigation_callbacks(app):
    @app.callback(
        Output('current_page', 'data'),
        [Input('prev_page', 'n_clicks'),
         Input('next_page', 'n_clicks'),
         # Add all filter inputs that should reset the page
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
         # Tab change
         Input('tabs', 'value')],
        [State('current_page', 'data')]
    )
    def update_page(prev_clicks, next_clicks, 
                   # Filter states
                   sm_start, sm_end, sm_companies, sm_entities, sm_platforms, sm_classifs,
                   view_toggle, left_view, right_view, sm_uniqueness, keyword_search,
                   sm_fossil_subcategories, sm_green_subcategories,
                   # Analytics filters
                   an_start, an_end, an_companies, an_entities, an_platforms, an_uniqueness,
                   an_fossil_subcategories, an_green_subcategories,
                   # Tab
                   active_tab,
                   # Current page state
                   current_page):
        ctx = dash.callback_context
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
            if triggered_id == 'prev_page' and current_page > 0:
                return current_page - 1
            elif triggered_id == 'next_page':
                return current_page + 1
        
        return current_page
    
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
