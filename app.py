from dash import Dash, html, dcc, Input, Output, callback
from signal_generator import generate_historical_signals
from datetime import datetime, timedelta
import json
from urllib.parse import parse_qs

# Color palette for signals (matches React frontend)
COLOR_PALETTE = [
    "#2563eb",  # Blue
    "#dc2626",  # Red
    "#16a34a",  # Green
    "#d97706",  # Orange
    "#8b5cf6",  # Purple
    "#ec4899",  # Pink
    "#06b6d4",  # Cyan
    "#f59e0b",  # Amber
]

# Chart layout constants
CHART_MARGINS = {'l': 60, 'b': 60, 't': 80, 'r': 200}
GRID_COLOR = '#eee'
BG_COLOR = 'white'
TEXT_COLOR = '#999'
LEGEND_POSITION = {'x': 1.05, 'y': 1}
FONT_SIZE_ANNOTATION = 14
DEFAULT_HOURS = 24
ALPHA_TRANSPARENCY = 0.1


def get_color_with_alpha(color_hex, alpha=0.1):
    """Convert hex color to rgba with specified alpha"""
    try:
        hex_color = color_hex.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f'rgba({r}, {g}, {b}, {alpha})'
    except (ValueError, IndexError, TypeError):
        # Fallback for invalid colors (e.g. if HSL is passed)
        return f'rgba(100, 100, 100, {alpha})'


app = Dash(__name__)
server = app.server  # Required for production deployment

# Custom CSS to reset browser defaults and prevent scrollbars
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                margin: 0;
                padding: 0;
                overflow: hidden;
                width: 100vw;
                height: 100vh;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Graph(id='main-graph', style={'height': '100vh', 'width': '100vw'}),
    dcc.Interval(id='interval-component', interval=2000)
], style={'margin': 0, 'padding': 0, 'overflow': 'hidden', 'height': '100vh', 'width': '100vw'})

# Theme definitions matching React frontend
# Theme definitions matching React frontend
# Structure: {'theme_name': {'dark': {...}, 'light': {...}}}
THEME_DEFINITIONS = {
    'aurora': {
        'dark': {
            'bg_color': '#000000',
            'paper_color': '#000000',
            'text_color': '#ffffff',
            'grid_color': '#333333',
            'font_color': '#e5e7eb'
        },
        'light': {
            'bg_color': '#ffffff',
            'paper_color': '#ffffff',
            'text_color': '#0f172a',
            'grid_color': '#e2e8f0',
            'font_color': '#64748b'
        }
    },
    'ocean': {
        'dark': {
            'bg_color': '#0f172a',
            'paper_color': '#0f172a',
            'text_color': '#f8fafc',
            'grid_color': '#1e293b',
            'font_color': '#94a3b8'
        },
        'light': {
            'bg_color': '#f0f9ff',  # Very light blue
            'paper_color': '#f0f9ff',
            'text_color': '#0c4a6e',
            'grid_color': '#bae6fd',
            'font_color': '#0369a1'
        }
    },
    'sunset': {
        'dark': {
            'bg_color': '#2a1a1a',  # Dark warm
            'paper_color': '#2a1a1a',
            'text_color': '#fef2f2',
            'grid_color': '#451a1a',
            'font_color': '#fca5a5'
        },
        'light': {
            'bg_color': '#fff7ed',  # Very light orange
            'paper_color': '#fff7ed',
            'text_color': '#7c2d12',
            'grid_color': '#ffedd5',
            'font_color': '#9a3412'
        }
    },
    'forest': {
        'dark': {
            'bg_color': '#1a2e1a', # Dark green
            'paper_color': '#1a2e1a',
            'text_color': '#f0fdf4',
            'grid_color': '#2e4c2e', 
            'font_color': '#86efac'
        },
        'light': {
            'bg_color': '#f0fdf4',  # Very light green
            'paper_color': '#f0fdf4',
            'text_color': '#14532d',
            'grid_color': '#bbf7d0',
            'font_color': '#166534'
        }
    }
}

def parse_query_params(search):
    """Parse query parameters from URL search string
    
    Returns: (signal_ids, signal_metadata, is_live, start, end, theme_name, mode)
    """
    if not search:
        now = datetime.now()
        return [], {}, False, now - timedelta(hours=DEFAULT_HOURS), now, 'aurora', 'dark', None
    
    params = parse_qs(search.lstrip('?'))
    
    signal_ids = []
    signal_metadata = {}
    is_live = False
    theme_name = 'aurora'
    now = datetime.now()
    start = now - timedelta(hours=DEFAULT_HOURS)
    end = now
    
    # Parse signal_id parameter
    if 'signal_id' in params:
        signal_ids = params['signal_id'][0].split(',')
    
    # Parse signals metadata (JSON array)
    if 'signals' in params:
        try:
            signals_data = json.loads(params['signals'][0])
            for idx, sig in enumerate(signals_data):
                signal_metadata[sig['id']] = {
                    'name': sig.get('name', sig['id']),
                    'color': sig.get('color', COLOR_PALETTE[idx % len(COLOR_PALETTE)])
                }
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # Log parsing error but continue with defaults
            print(f"Error parsing signals metadata: {e}")
            
    # Parse theme
    if 'theme' in params:
        theme_name = params['theme'][0]

    # Parse mode (light/dark)
    mode = 'dark' # default
    if 'mode' in params:
        mode = params['mode'][0]
    
    # Parse live mode
    if 'live' in params:
        is_live = params['live'][0].lower() == 'true'
    
    # Parse date range
    if 'start' in params:
        try:
            start = datetime.fromisoformat(params['start'][0].replace('Z', '+00:00'))
        except (ValueError, TypeError) as e:
            print(f"Error parsing start date: {e}")
    
    if 'end' in params:
        try:
            end = datetime.fromisoformat(params['end'][0].replace('Z', '+00:00'))
        except (ValueError, TypeError) as e:
            print(f"Error parsing end date: {e}")

    # Parse timezone offset (minutes)
    # JS getTimezoneOffset() returns positive if local is behind UTC (e.g. UTC-5 is 300)
    # So Local = UTC - offset
    if 'tz' in params:
        try:
            tz_offset = int(params['tz'][0])
            start = start - timedelta(minutes=tz_offset)
            end = end - timedelta(minutes=tz_offset)
            
            # Remove tzinfo to make it naive (Local Time) for clear display in Plotly
            start = start.replace(tzinfo=None)
            end = end.replace(tzinfo=None)
        except (ValueError, TypeError) as e:
            print(f"Error parsing timezone: {e}")
    
    # Parse highlight
    highlight_id = None
    if 'highlight' in params:
        val = params['highlight'][0]
        if val and val != 'null' and val != 'undefined':
            highlight_id = val
            
    return signal_ids, signal_metadata, is_live, start, end, theme_name, mode, highlight_id


def build_signal_traces(signal_ids, signal_metadata, start, end, theme, highlight_id=None):
    """Build chart traces for signals
    
    Returns: (chart_data, aggregation_level)
    """
    chart_data = []
    aggregation_level = None
    
    for idx, signal_id in enumerate(signal_ids):
        data = generate_historical_signals(signal_id, start, end)
        
        if data and aggregation_level is None:
            aggregation_level = data[0].get('aggregation_level', 'unknown')
        
        # Get color and name
        if signal_id in signal_metadata:
            color = signal_metadata[signal_id]['color']
            name = signal_metadata[signal_id]['name']
        else:
            color = COLOR_PALETTE[idx % len(COLOR_PALETTE)]
            name = signal_id
        
        # Determine opacity based on highlight
        line_color = color
        fill_color = get_color_with_alpha(color, ALPHA_TRANSPARENCY)
        
        if highlight_id and highlight_id != signal_id:
            # Dim non-highlighted signals
            line_color = get_color_with_alpha(color, 0.2) # Very dim line
            fill_color = get_color_with_alpha(color, 0.05) # Very dim fill
        
        # Build hover template
        hover_template = (
            f"<b>{name}</b><br>"
            "Time: %{x}<br>"
            "Value: %{y:.2f}<br>"
            "Min: %{customdata[0]:.2f}<br>"
            "Max: %{customdata[1]:.2f}<extra></extra>"
        )
        
        trace = {
            'x': [d['timestamp'] for d in data],
            'y': [d['value'] for d in data],
            'customdata': [
                [d.get('min_value', d['value']), d.get('max_value', d['value'])]
                for d in data
            ],
            'type': 'scatter',
            'mode': 'lines+markers',
            'name': name,
            'line': {'color': line_color, 'width': 2},
            'fill': 'tozeroy',
            'fillcolor': fill_color,
            'hovertemplate': hover_template
        }
        chart_data.append(trace)
    
    return chart_data, aggregation_level


def get_empty_chart(theme_config):
    """Return empty state chart with theme"""
    return {
        'data': [],
        'layout': {
            'title': {
                'text': 'No signals selected',
                'font': {'color': theme_config['text_color']}
            },
            'xaxis': {'showgrid': False, 'visible': False},
            'yaxis': {'showgrid': False, 'visible': False},
            'plot_bgcolor': theme_config['bg_color'],
            'paper_bgcolor': theme_config['paper_color'],
            'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0},
            'annotations': [{
                'text': 'Select signals from the sidebar',
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'showarrow': False,
                'font': {'size': FONT_SIZE_ANNOTATION, 'color': theme_config['font_color']}
            }]
        }
    }, True


def get_chart_figure(chart_data, signal_ids, aggregation_level, start, end, is_live, theme_config):
    """Build chart figure layout with theme"""
    # Calculate duration to determine date format
    duration = end - start
    if duration > timedelta(hours=12):
        time_fmt = "%b %d %H:%M"
    else:
        time_fmt = "%H:%M"

    title_text = (
        f'{len(signal_ids)} Signal(s)<br>'
        f'<span style="font-size: 10px; color: {theme_config["font_color"]}">'
        f'{start.strftime(time_fmt)} - {end.strftime(time_fmt)}'
        f'</span>'
    )
    
    return {
        'data': chart_data,
        'layout': {
            'title': {
                 'text': title_text,
                 'font': {'color': theme_config['text_color'], 'size': 14},
                 'x': 0.05,
                 'y': 0.95
            },
            'showlegend': True,
            'legend': {
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'right',
                'x': 1,
                'font': {'color': theme_config['text_color']}
            },
            'hovermode': 'x unified',
            # Maximized margins (l/r/b reduced to 0 or close to 0)
            'margin': {'l': 30, 'r': 10, 't': 40, 'b': 20},
            'autosize': True,
            'xaxis': {
                'showgrid': False, 
                'zeroline': False,
                'color': theme_config['font_color'],
                'tickfont': {'color': theme_config['font_color']},
                # Smart tick formatting based on zoom level
                'tickformatstops': [
                    {'dtickrange': [None, 60000], 'value': '%H:%M:%S'},   # < 1 min
                    {'dtickrange': [60000, 3600000], 'value': '%H:%M'},   # < 1 hour
                    {'dtickrange': [3600000, None], 'value': '%b %d %H:%M'} # >= 1 hour (shows Date + Time)
                ]
            },
            'yaxis': {
                'showgrid': True, 
                'gridcolor': theme_config['grid_color'],
                'zeroline': False,
                'color': theme_config['font_color'],
                'tickfont': {'color': theme_config['font_color']}
            },
            'plot_bgcolor': theme_config['bg_color'],
            'paper_bgcolor': theme_config['paper_color']
        }
    }, not is_live

@callback(
    [Output('main-graph', 'figure'), Output('interval-component', 'disabled')],
    [Input('url', 'search'), Input('interval-component', 'n_intervals')]
)
def update_chart(search, _):
    """Update chart based on query parameters from React"""
    signal_ids, signal_metadata, is_live, start, end, theme_name, mode, highlight_id = parse_query_params(search)
    
    # Determine theme config
    theme_def = THEME_DEFINITIONS.get(theme_name, THEME_DEFINITIONS['aurora'])
    
    # Get specific mode config (default to dark if mode invalid)
    theme_config = theme_def.get(mode, theme_def['dark'])
    
    if not signal_ids:
        return get_empty_chart(theme_config)
    
    chart_data, aggregation_level = build_signal_traces(
        signal_ids,
        signal_metadata,
        start,
        end,
        theme_config,
        highlight_id
    )
    return get_chart_figure(
        chart_data,
        signal_ids,
        aggregation_level,
        start,
        end,
        is_live,
        theme_config
    )

if __name__ == "__main__":
    app.run(debug=True)