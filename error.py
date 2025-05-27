import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Initialize the Dash app with Bootstrap theme
app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}])
server = app.server

# Available cities
available_cities = [
    "Ahmedabad", "Aizawl", "Amaravati", "Amritsar", "Bengaluru", "Bhopal",
    "Brajrajnagar", "Chandigarh", "Chennai", "Coimbatore", "Delhi", "Ernakulam",
    "Gurugram", "Guwahati", "Hyderabad", "Jaipur", "Jorapokhar", "Kochi",
    "Kolkata", "Lucknow", "Mumbai", "Patna", "Shillong", "Talcher", "Thiruvananthapuram",
    "Visakhapatnam"
]

# Color palettes
LIGHT_THEME = {
    'primary': '#2e7d32',  # Dark green
    'secondary': '#388e3c',  # Medium green
    'background': '#e8f5e9',  # Light green
    'text': '#212529',
    'card': 'white',
    'plot_bg': 'white',
    'paper_bg': 'white',
    'grid': '#e6e6e6'
}

DARK_THEME = {
    'primary': '#81c784',  # Light green
    'secondary': '#66bb6a',  # Medium light green
    'background': '#1e1e1e',
    'text': '#f8f9fa',
    'card': '#2d2d2d',
    'plot_bg': '#2d2d2d',
    'paper_bg': '#2d2d2d',
    'grid': '#444'
}


# Generate sample data
def generate_sample_data(city):
    dates = pd.date_range(end=datetime.today(), periods=30).strftime('%Y-%m-%d').tolist()
    pollutants = ['PM2.5', 'PM10', 'NO2', 'CO', 'SO2', 'O3']

    return {
        'aqi': np.random.randint(50, 300, size=30),
        'pollutants': {p: np.random.randint(10, 200) for p in pollutants},
        'dates': dates,
        'pollutant_levels': [np.random.randint(10, 200) for _ in pollutants]
    }


# App layout with new order (Pollutants > Historical > Model Accuracy)
app.layout = dbc.Container(
    [
        dcc.Store(id='theme-store', data='light'),

        # Header with theme toggle
        dbc.Row(
            dbc.Col(
                html.Div(
                    [
                        html.Div(
                            dbc.Button(
                                id='theme-toggle',
                                className='btn btn-outline-secondary',
                                style={'position': 'absolute', 'right': '20px', 'top': '20px'}
                            ),
                            style={'position': 'relative'}
                        ),
                        html.H1("Air Quality Dashboard", className="text-center my-4"),
                        html.P("Real-time air quality monitoring", className="text-center text-muted mb-4")
                    ],
                    style={'position': 'relative'}
                ),
                width=12
            )
        ),

        # Main content
        dbc.Row([
            # Left sidebar (controls and prediction)
            dbc.Col([
                dbc.Card(
                    [
                        dbc.CardHeader("City Selection", className="h5"),
                        dbc.CardBody([
                            dcc.Dropdown(
                                id='city-dropdown',
                                options=[{'label': city, 'value': city} for city in available_cities],
                                value='Delhi',
                                clearable=False,
                                className="mb-3"
                            ),
                            dbc.Button(
                                'Predict AQI',
                                id='predict-button',
                                color="primary",
                                className="w-100",
                                n_clicks=0
                            )
                        ])
                    ],
                    id='city-card',
                    className="mb-4"
                ),

                dbc.Card(
                    [
                        dbc.CardHeader("Prediction Result", className="h5"),
                        dbc.CardBody(id='prediction-result')
                    ],
                    id='prediction-card',
                    className="mb-4"
                ),

                dbc.Card(
                    [
                        dbc.CardHeader("Health Recommendations", className="h5"),
                        dbc.CardBody(id='health-recommendations')
                    ],
                    id='health-card'
                )
            ], md=4),

            # Right main content (reordered sections)
            dbc.Col([
                # 1. Pollutant Levels (now first section)
                dbc.Card(
                    [
                        dbc.CardHeader("Pollutant Levels", className="h5"),
                        dbc.CardBody([
                            dcc.Graph(id='pollutant-chart'),
                            html.Div([
                                dbc.Button("Refresh", id='refresh-button', color="light", className="me-2"),
                                html.Span(id='last-updated', className="text-muted small")
                            ], className="mt-2")
                        ])
                    ],
                    id='pollutant-card',
                    className="mb-4"
                ),

                # 2. Historical Trends (now second section)
                dbc.Card(
                    [
                        dbc.CardHeader("Historical Trends", className="h5"),
                        dbc.CardBody([
                            dcc.Graph(id='aqi-trend-chart'),
                            dcc.RangeSlider(
                                id='date-range-slider',
                                min=0,
                                max=29,
                                value=[0, 29],
                                marks={i: {'label': f'Day {i + 1}'} for i in range(0, 30, 5)}
                            )
                        ])
                    ],
                    id='trend-card',
                    className="mb-4"
                ),

                # 3. Model Performance (now last section)
                dbc.Card(
                    [
                        dbc.CardHeader("Model Performance", className="h5"),
                        dbc.CardBody([
                            dcc.Tabs([
                                dcc.Tab(
                                    label='Accuracy',
                                    children=[
                                        dcc.Graph(id='accuracy-graph'),
                                        html.P("Model accuracy comparison", className="text-muted small mt-2")
                                    ]
                                ),
                                dcc.Tab(
                                    label='Confusion Matrix',
                                    children=[
                                        dcc.Graph(id='confusion-matrix'),
                                        html.P("True vs predicted classes", className="text-muted small mt-2")
                                    ]
                                ),
                                dcc.Tab(
                                    label='Features',
                                    children=[
                                        dcc.Graph(id='feature-importance'),
                                        html.P("Feature importance values", className="text-muted small mt-2")
                                    ]
                                )
                            ])
                        ])
                    ],
                    id='metrics-card'
                )
            ], md=8)
        ])
    ],
    fluid=True,
    id='main-container',
    className=''
)


# Theme toggle callback
@app.callback(
    [Output('theme-store', 'data'),
     Output('theme-toggle', 'children')],
    [Input('theme-toggle', 'n_clicks')],
    [State('theme-store', 'data')]
)
def toggle_theme(n_clicks, current_theme):
    if n_clicks is None:
        return current_theme, "🌙"  # Moon icon for light theme

    new_theme = 'dark' if current_theme == 'light' else 'light'
    icon = "☀️" if new_theme == 'dark' else "🌙"
    return new_theme, icon


# Update theme styles
@app.callback(
    [Output('main-container', 'style'),
     Output('city-card', 'style'),
     Output('prediction-card', 'style'),
     Output('health-card', 'style'),
     Output('pollutant-card', 'style'),
     Output('trend-card', 'style'),
     Output('metrics-card', 'style')],
    [Input('theme-store', 'data')]
)
def update_theme_styles(theme):
    theme_colors = DARK_THEME if theme == 'dark' else LIGHT_THEME

    container_style = {
        'backgroundColor': theme_colors['background'],
        'color': theme_colors['text'],
        'minHeight': '100vh'
    }

    card_style = {
        'backgroundColor': theme_colors['card'],
        'color': theme_colors['text'],
        'border': 'none'
    }

    return [container_style] + [card_style] * 6


# Update chart themes
@app.callback(
    [Output('pollutant-chart', 'figure'),
     Output('aqi-trend-chart', 'figure'),
     Output('accuracy-graph', 'figure'),
     Output('confusion-matrix', 'figure'),
     Output('feature-importance', 'figure')],
    [Input('theme-store', 'data')]
)
def update_chart_themes(theme):
    theme_colors = DARK_THEME if theme == 'dark' else LIGHT_THEME

    # Common layout for all charts
    common_layout = {
        'plot_bgcolor': theme_colors['plot_bg'],
        'paper_bgcolor': theme_colors['paper_bg'],
        'font': {'color': theme_colors['text']},
        'xaxis': {'gridcolor': theme_colors['grid']},
        'yaxis': {'gridcolor': theme_colors['grid']}
    }

    # Pollutant chart (now first)
    pollutants = ['PM2.5', 'PM10', 'NO2', 'CO', 'SO2', 'O3']
    levels = np.random.randint(10, 200, size=len(pollutants))
    pollutant_fig = px.bar(
        x=pollutants, y=levels,
        labels={'x': 'Pollutant', 'y': 'Level (µg/m³)'},
        color=pollutants,
        color_discrete_sequence=px.colors.sequential.Greens
    )
    pollutant_fig.update_layout(common_layout)
    pollutant_fig.update_layout(showlegend=False)

    # AQI trend chart (now second)
    dates = pd.date_range(end=datetime.today(), periods=30).strftime('%Y-%m-%d').tolist()
    aqi_values = np.random.randint(50, 300, size=30)
    trend_fig = px.line(
        x=dates, y=aqi_values,
        labels={'x': 'Date', 'y': 'AQI'},
        color_discrete_sequence=[LIGHT_THEME['primary']]
    )
    trend_fig.add_hline(
        y=100,
        line_dash="dash",
        line_color="red",
        annotation_text="Unhealthy Threshold"
    )
    trend_fig.update_layout(common_layout)

    # Accuracy graph (now last)
    models = ['Random Forest', 'XGBoost', 'Gradient Boosting', 'SVM', 'Logistic Regression', 'Stacking']
    accuracy = [0.92, 0.91, 0.90, 0.88, 0.87, 0.93]
    accuracy_fig = px.bar(
        x=models, y=accuracy,
        labels={'x': 'Model', 'y': 'Accuracy'},
        color=models,
        color_discrete_sequence=px.colors.sequential.Greens
    )
    accuracy_fig.update_layout(common_layout)
    accuracy_fig.update_layout(showlegend=False)

    # Confusion matrix
    cm = [[120, 15], [10, 125]]
    cm_fig = px.imshow(
        cm,
        labels=dict(x="Predicted", y="Actual", color="Count"),
        x=['Healthy', 'Unhealthy'],
        y=['Healthy', 'Unhealthy'],
        color_continuous_scale='Greens'
    )
    cm_fig.update_layout(common_layout)

    # Feature importance
    features = ['PM2.5', 'PM10', 'NO2', 'CO', 'SO2', 'O3', 'NH3']
    importance = [0.25, 0.20, 0.15, 0.12, 0.10, 0.10, 0.08]
    feature_fig = px.bar(
        x=features, y=importance,
        labels={'x': 'Feature', 'y': 'Importance'},
        color=features,
        color_discrete_sequence=px.colors.sequential.Greens
    )
    feature_fig.update_layout(common_layout)
    feature_fig.update_layout(showlegend=False)

    return pollutant_fig, trend_fig, accuracy_fig, cm_fig, feature_fig


# Main dashboard callback
@app.callback(
    [Output('prediction-result', 'children'),
     Output('health-recommendations', 'children'),
     Output('last-updated', 'children')],
    [Input('predict-button', 'n_clicks'),
     Input('refresh-button', 'n_clicks')],
    [State('city-dropdown', 'value')]
)
def update_dashboard(predict_clicks, refresh_clicks, selected_city):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    # Simulate prediction
    aqi_value = np.random.randint(50, 300)
    prediction = "Unhealthy" if aqi_value > 100 else "Healthy"
    last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Prediction result
    prediction_card = [
        html.H4(f"{selected_city}", className="card-title"),
        html.Div([
            html.Span("AQI: ", className="text-muted"),
            html.Span(f"{aqi_value}",
                      className="display-4 text-danger" if aqi_value > 100
                      else "display-4 text-success")
        ], className="mb-2"),
        dbc.Badge(
            prediction,
            color="danger" if prediction == "Unhealthy" else "success",
            className="fs-5 mb-3"
        ),
        html.P(f"Threshold: 100 (Healthy ≤ 100, Unhealthy > 100)", className="text-muted"),
        html.Hr(),
        html.Small(f"Last updated: {last_updated}", className="text-muted")
    ]

    # Health recommendations
    if prediction == "Unhealthy":
        recommendations = [
            html.Ul([
                html.Li("Reduce outdoor activities"),
                html.Li("Close windows to avoid outdoor air"),
                html.Li("Wear a mask if going outside"),
                html.Li("Use air purifiers if available")
            ])
        ]
    else:
        recommendations = [
            html.Ul([
                html.Li("Enjoy outdoor activities"),
                html.Li("Good day for ventilation"),
                html.Li("Consider walking or cycling"),
                html.Li("Ideal for outdoor exercise")
            ])
        ]

    return prediction_card, recommendations, f"Last updated: {last_updated}"


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5003)