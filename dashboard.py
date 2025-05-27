import requests
import pandas as pd
from datetime import datetime
import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.graph_objects as go
import plotly.express as px

# API Keys
WAQI_API_KEY = "2e052070bf816edc1f1b1051c1cba4ecb1d4b132"
OPENWEATHER_API_KEY = "51d3ec48eb720a74b9db4ec8afe765c2"

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=["https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css"])
server = app.server

# CSS styles
LIGHT_THEME = {
    'bg': '#f0f4f0',  # Light green-gray for nature vibe
    'text': '#333333',
    'card': '#ffffff',
    'border': '#d1d8d1',
    'primary': '#2c5f2d',  # Dark green
    'hover': '#5cb85c'     # Success green
}

DARK_THEME = {
    'bg': '#1a1a1a',  # Dark forest green
    'text': '#e0e6e0',
    'card': '#2d3e2d',
    'border': '#4a5c4a',
    'primary': '#5cb85c',  # Lighter green for contrast
    'hover': '#8cd98c'
}

# ===== Data Fetching Functions (Unchanged) =====
def fetch_air_quality_data(city="Los Angeles", api_key=WAQI_API_KEY):
    try:
        print(f"Fetching air quality data for {city}...")
        url = f"https://api.waqi.info/feed/{city}/?token={api_key}"
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        print("WAQI API Response:", data)

        if data["status"] != "ok":
            print("WAQI API error:", data.get("data", "Unknown error"))
            return pd.DataFrame()

        aqi = data["data"]["aqi"]
        iaqi = data["data"]["iaqi"]
        time_str = data["data"]["time"]["s"]

        try:
            timestamp = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            timestamp = datetime.now()

        pollutants = {
            "pm25": iaqi.get("pm25", {}).get("v", None),
            "pm10": iaqi.get("pm10", {}).get("v", None),
            "o3": iaqi.get("o3", {}).get("v", None),
            "no2": iaqi.get("no2", {}).get("v", None),
            "so2": iaqi.get("so2", {}).get("v", None),
            "co": iaqi.get("co", {}).get("v", None),
        }

        df = pd.DataFrame({
            "city": city,
            "timestamp": timestamp,
            "aqi": aqi,
            **pollutants
        }, index=[0])

        return df

    except requests.exceptions.RequestException as e:
        print(f"WAQI API request failed: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return pd.DataFrame()

def fetch_weather_data(city="Los Angeles", api_key=OPENWEATHER_API_KEY):
    try:
        print(f"\nFetching weather data for {city}...")
        geo_url = "http://api.openweathermap.org/geo/1.0/direct"
        geo_params = {"q": city, "limit": 1, "appid": api_key}
        geo_response = requests.get(geo_url, params=geo_params)
        geo_response.raise_for_status()

        geo_data = geo_response.json()
        if not geo_data:
            print("City not found in OpenWeatherMap.")
            return None, None

        lat = geo_data[0]["lat"]
        lon = geo_data[0]["lon"]
        print(f"Coordinates found: lat={lat}, lon={lon}")

        pollution_url = "http://api.openweathermap.org/data/2.5/air_pollution"
        pollution_params = {"lat": lat, "lon": lon, "appid": api_key}
        pollution_response = requests.get(pollution_url, params=pollution_params)
        pollution_response.raise_for_status()

        pollution_data = pollution_response.json()
        print("OpenWeatherMap Response:", pollution_data)

        if not pollution_data.get("list"):
            print("No pollution data available.")
            return None, None

        air_quality = pollution_data["list"][0]["main"]
        pollutants = pollution_data["list"][0]["components"]

        return air_quality, pollutants

    except requests.exceptions.RequestException as e:
        print(f"OpenWeatherMap API error: {str(e)}")
        return None, None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None, None

# ===== Dashboard Layout =====
app.layout = html.Div([
    # Store for theme preference
    dcc.Store(id='theme-store', storage_type='local', data={'dark': False}),

    # Main container
    html.Div([
        # Header
        html.Div([
            html.H1("Air Quality Dashboard", style={'flex': '1', 'fontSize': '28px', 'fontWeight': '600'}),
            html.Button(
                html.I(className="fas fa-sun", id='theme-icon'),
                id='theme-toggle',
                style={'background': 'none', 'border': 'none', 'cursor': 'pointer', 'fontSize': '20px', 'padding': '5px'}
            )
        ], style={
            'display': 'flex',
            'justifyContent': 'space-between',
            'alignItems': 'center',
            'padding': '15px 20px',
            'borderBottom': '1px solid',
            'marginBottom': '20px'
        }),

        # City input and refresh button
        html.Div([
            dcc.Input(
                id='city-input',
                type='text',
                value='Los Angeles',
                placeholder='Enter a city name',
                style={
                    'flex': '1',
                    'padding': '10px',
                    'borderRadius': '8px',
                    'border': '1px solid',
                    'marginRight': '10px',
                    'fontSize': '16px'
                }
            ),
            html.Button(
                'Refresh',
                id='refresh-button',
                n_clicks=0,
                style={
                    'padding': '10px 20px',
                    'borderRadius': '8px',
                    'border': 'none',
                    'cursor': 'pointer',
                    'fontSize': '16px',
                    'fontWeight': '500'
                }
            )
        ], style={
            'display': 'flex',
            'marginBottom': '20px',
            'padding': '0 20px'
        }),

        # Last updated info
        html.Div(id='last-updated', style={
            'textAlign': 'center',
            'marginBottom': '20px',
            'fontSize': '14px',
            'fontStyle': 'italic',
            'padding': '0 20px'
        }),

        # Tabs
        dcc.Tabs([
            dcc.Tab(label='AQI Overview', children=[
                html.Div([
                    html.Div([
                        html.Div([
                            html.H3("WAQI Air Quality Index", style={'textAlign': 'center', 'fontSize': '20px'}),
                            dcc.Graph(id='waqi-aqi-gauge', config={'displayModeBar': False})
                        ], style={
                            'padding': '20px',
                            'borderRadius': '10px',
                            'margin': '10px',
                            'flex': '1',
                            'boxShadow': '0 4px 12px rgba(0,0,0,0.1)'
                        }),
                        html.Div([
                            html.H3("OpenWeatherMap AQI", style={'textAlign': 'center', 'fontSize': '20px'}),
                            dcc.Graph(id='owm-aqi-gauge', config={'displayModeBar': False})
                        ], style={
                            'padding': '20px',
                            'borderRadius': '10px',
                            'margin': '10px',
                            'flex': '1',
                            'boxShadow': '0 4px 12px rgba(0,0,0,0.1)'
                        })
                    ], style={'display': 'flex', 'flexWrap': 'wrap', 'marginBottom': '20px'}),
                    html.Div([
                        html.H3("Pollutants Comparison", style={'textAlign': 'center', 'fontSize': '20px'}),
                        dcc.Graph(id='pollutants-comparison')
                    ], style={
                        'padding': '20px',
                        'borderRadius': '10px',
                        'margin': '10px',
                        'boxShadow': '0 4px 12px rgba(0,0,0,0.1)'
                    })
                ], style={'padding': '0 20px'})
            ]),
            dcc.Tab(label='Pollutant Details', children=[
                html.Div([
                    html.Div([
                        html.H3("WAQI Pollutant Levels", style={'textAlign': 'center', 'fontSize': '20px'}),
                        dcc.Graph(id='waqi-pollutants')
                    ], style={
                        'padding': '20px',
                        'borderRadius': '10px',
                        'margin': '10px',
                        'flex': '1',
                        'boxShadow': '0 4px 12px rgba(0,0,0,0.1)'
                    }),
                    html.Div([
                        html.H3("OpenWeatherMap Pollutants", style={'textAlign': 'center', 'fontSize': '20px'}),
                        dcc.Graph(id='owm-pollutants')
                    ], style={
                        'padding': '20px',
                        'borderRadius': '10px',
                        'margin': '10px',
                        'flex': '1',
                        'boxShadow': '0 4px 12px rgba(0,0,0,0.1)'
                    })
                ], style={'display': 'flex', 'flexWrap': 'wrap', 'padding': '0 20px'})
            ])
        ]),

        # Auto-refresh interval
        dcc.Interval(id='interval-component', interval=60 * 60 * 1000, n_intervals=0)
    ], style={'maxWidth': '1200px', 'margin': '0 auto'})
], id='main-container')

# ===== Theme Management Callbacks =====
@callback(
    Output('theme-store', 'data'),
    Input('theme-toggle', 'n_clicks'),
    State('theme-store', 'data'),
    prevent_initial_call=True
)
def update_theme_store(n_clicks, current_theme):
    dark_mode = current_theme.get('dark', False) if current_theme else False
    return {'dark': not dark_mode}

@callback(
    [Output('main-container', 'style'),
     Output('theme-icon', 'className'),
     Output('theme-toggle', 'style'),
     Output('city-input', 'style'),
     Output('refresh-button', 'style'),
     Output('last-updated', 'style'),
     Output('waqi-aqi-gauge', 'style'),
     Output('owm-aqi-gauge', 'style'),
     Output('pollutants-comparison', 'style'),
     Output('waqi-pollutants', 'style'),
     Output('owm-pollutants', 'style')],
    Input('theme-store', 'data')
)
def update_theme(theme_data):
    dark_mode = theme_data.get('dark', False) if theme_data else False
    theme = DARK_THEME if dark_mode else LIGHT_THEME

    container_style = {
        'backgroundColor': theme['bg'],
        'color': theme['text'],
        'minHeight': '100vh'
    }
    icon_class = "fas fa-moon" if dark_mode else "fas fa-sun"
    toggle_style = {
        'background': 'none',
        'border': 'none',
        'cursor': 'pointer',
        'fontSize': '20px',
        'padding': '5px',
        'color': theme['text']
    }
    input_style = {
        'flex': '1',
        'padding': '10px',
        'borderRadius': '8px',
        'border': f'1px solid {theme["border"]}',
        'marginRight': '10px',
        'fontSize': '16px',
        'backgroundColor': theme['card'],
        'color': theme['text']
    }
    button_style = {
        'padding': '10px 20px',
        'borderRadius': '8px',
        'border': 'none',
        'cursor': 'pointer',
        'fontSize': '16px',
        'fontWeight': '500',
        'backgroundColor': theme['primary'],
        'color': '#ffffff',
        'transition': 'background-color 0.3s'
    }
    button_style_hover = {'backgroundColor': theme['hover']}  # Applied via CSS in real-world, simulated here
    last_updated_style = {
        'textAlign': 'center',
        'marginBottom': '20px',
        'fontSize': '14px',
        'fontStyle': 'italic',
        'padding': '0 20px',
        'color': theme['text']
    }
    graph_style = {'backgroundColor': theme['card'], 'borderRadius': '10px'}

    return (container_style, icon_class, toggle_style, input_style, button_style,
            last_updated_style, graph_style, graph_style, graph_style, graph_style, graph_style)

# ===== Dashboard Update Callback =====
@callback(
    [Output('waqi-aqi-gauge', 'figure'),
     Output('owm-aqi-gauge', 'figure'),
     Output('pollutants-comparison', 'figure'),
     Output('waqi-pollutants', 'figure'),
     Output('owm-pollutants', 'figure'),
     Output('last-updated', 'children')],
    [Input('refresh-button', 'n_clicks'),
     Input('interval-component', 'n_intervals'),
     Input('theme-store', 'data')],
    [State('city-input', 'value')]
)
def update_dashboard(n_clicks, n_intervals, theme_data, city):
    dark_mode = theme_data.get('dark', False) if theme_data else False
    theme = DARK_THEME if dark_mode else LIGHT_THEME

    waqi_data = fetch_air_quality_data(city)
    owm_aqi, owm_pollutants = fetch_weather_data(city)

    last_updated = f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | City: {city}"

    # WAQI AQI Gauge
    waqi_aqi_fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=waqi_data['aqi'].iloc[0] if not waqi_data.empty else 0,
        title={'text': f"WAQI AQI - {city}", 'font': {'color': theme['text']}},
        gauge={
            'axis': {'range': [0, 500], 'tickcolor': theme['text']},
            'bar': {'color': theme['primary']},
            'steps': [
                {'range': [0, 50], 'color': "#5cb85c"},
                {'range': [50, 100], 'color': "#f0ad4e"},
                {'range': [100, 150], 'color': "#ff7f0e"},
                {'range': [150, 200], 'color': "#d9534f"},
                {'range': [200, 300], 'color': "#9467bd"},
                {'range': [300, 500], 'color': "#8c564b"}
            ],
            'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': waqi_data['aqi'].iloc[0] if not waqi_data.empty else 0}
        }
    ))
    waqi_aqi_fig.update_layout(paper_bgcolor=theme['card'], plot_bgcolor=theme['card'], font={'color': theme['text']}, margin={'t': 50, 'b': 30})

    # OpenWeatherMap AQI Gauge
    owm_aqi_fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=owm_aqi['aqi'] * 20 if owm_aqi else 0,
        title={'text': f"OpenWeatherMap AQI - {city}", 'font': {'color': theme['text']}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': theme['text']},
            'bar': {'color': theme['primary']},
            'steps': [
                {'range': [0, 20], 'color': "#5cb85c"},
                {'range': [20, 40], 'color': "#f0ad4e"},
                {'range': [40, 60], 'color': "#ff7f0e"},
                {'range': [60, 80], 'color': "#d9534f"},
                {'range': [80, 100], 'color': "#9467bd"}
            ],
            'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': owm_aqi['aqi'] * 20 if owm_aqi else 0}
        }
    ))
    owm_aqi_fig.update_layout(paper_bgcolor=theme['card'], plot_bgcolor=theme['card'], font={'color': theme['text']}, margin={'t': 50, 'b': 30})

    # Pollutants Comparison Chart
    if not waqi_data.empty and owm_pollutants:
        pollutants = ['pm25', 'pm10', 'o3', 'no2', 'so2', 'co']
        waqi_values = [waqi_data[p].iloc[0] if p in waqi_data.columns else 0 for p in pollutants]
        owm_values = [owm_pollutants.get(p, 0) for p in ['pm2_5', 'pm10', 'o3', 'no2', 'so2', 'co']]

        comparison_fig = go.Figure()
        comparison_fig.add_trace(go.Bar(x=pollutants, y=waqi_values, name='WAQI', marker_color='#2c5f2d'))
        comparison_fig.add_trace(go.Bar(x=pollutants, y=owm_values, name='OpenWeatherMap', marker_color='#5cb85c'))
        comparison_fig.update_layout(
            title={'text': f"Pollutants Comparison - {city}", 'font': {'color': theme['text']}},
            barmode='group',
            yaxis_title="Concentration (µg/m³)",
            paper_bgcolor=theme['card'],
            plot_bgcolor=theme['card'],
            font={'color': theme['text']},
            legend={'font': {'color': theme['text']}},
            xaxis={'tickfont': {'color': theme['text']}},
            yaxis={'tickfont': {'color': theme['text']}},
            margin={'t': 50, 'b': 30}
        )
    else:
        comparison_fig = go.Figure()
        comparison_fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font={'color': theme['text']})
        comparison_fig.update_layout(paper_bgcolor=theme['card'], plot_bgcolor=theme['card'])

    # WAQI Pollutants Chart
    if not waqi_data.empty:
        pollutants = ['pm25', 'pm10', 'o3', 'no2', 'so2', 'co']
        values = [waqi_data[p].iloc[0] if p in waqi_data.columns else 0 for p in pollutants]
        waqi_poll_fig = px.bar(x=pollutants, y=values, labels={'x': 'Pollutant', 'y': 'Concentration (µg/m³)'}, title=f"WAQI Pollutant Levels - {city}", color=pollutants, color_discrete_sequence=px.colors.qualitative.Pastel)
        waqi_poll_fig.update_layout(paper_bgcolor=theme['card'], plot_bgcolor=theme['card'], font={'color': theme['text']}, legend={'font': {'color': theme['text']}}, xaxis={'tickfont': {'color': theme['text']}}, yaxis={'tickfont': {'color': theme['text']}}, margin={'t': 50, 'b': 30})
    else:
        waqi_poll_fig = go.Figure()
        waqi_poll_fig.add_annotation(text="No WAQI data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font={'color': theme['text']})
        waqi_poll_fig.update_layout(paper_bgcolor=theme['card'], plot_bgcolor=theme['card'])

    # OpenWeatherMap Pollutants Chart
    if owm_pollutants:
        pollutants = ['pm2_5', 'pm10', 'o3', 'no2', 'so2', 'co']
        values = [owm_pollutants.get(p, 0) for p in pollutants]
        owm_poll_fig = px.bar(x=pollutants, y=values, labels={'x': 'Pollutant', 'y': 'Concentration (µg/m³)'}, title=f"OpenWeatherMap Pollutant Levels - {city}", color=pollutants, color_discrete_sequence=px.colors.qualitative.Pastel)
        owm_poll_fig.update_layout(paper_bgcolor=theme['card'], plot_bgcolor=theme['card'], font={'color': theme['text']}, legend={'font': {'color': theme['text']}}, xaxis={'tickfont': {'color': theme['text']}}, yaxis={'tickfont': {'color': theme['text']}}, margin={'t': 50, 'b': 30})
    else:
        owm_poll_fig = go.Figure()
        owm_poll_fig.add_annotation(text="No OpenWeatherMap data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font={'color': theme['text']})
        owm_poll_fig.update_layout(paper_bgcolor=theme['card'], plot_bgcolor=theme['card'])

    return waqi_aqi_fig, owm_aqi_fig, comparison_fig, waqi_poll_fig, owm_poll_fig, last_updated

if __name__ == '__main__':
    app.run(port=5001)