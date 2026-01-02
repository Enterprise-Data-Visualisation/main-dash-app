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

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Graph(id='main-graph'),
    dcc.Interval(id='interval-component', interval=2000)
])

def parse_query_params(search):
    """Parse query parameters from URL search string
    
    Returns: (signal_ids, signal_metadata, is_live, start, end)
    """
    if not search:
        now = datetime.now()
        return [], {}, False, now - timedelta(hours=DEFAULT_HOURS), now
    
    params = parse_qs(search.lstrip('?'))
    
    signal_ids = []
    signal_metadata = {}
    is_live = False
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
    
    return signal_ids, signal_metadata, is_live, start, end


def build_signal_traces(signal_ids, signal_metadata, start, end):
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
            'line': {'color': color, 'width': 2},
            'fill': 'tozeroy',
            'fillcolor': get_color_with_alpha(color, ALPHA_TRANSPARENCY),
            'hovertemplate': hover_template
        }
        chart_data.append(trace)
    
    return chart_data, aggregation_level


def get_empty_chart():
    """Return empty state chart"""
    return {
        'data': [],
        'layout': {
            'title': 'No signals selected',
            'xaxis': {'showgrid': False},
            'yaxis': {'showgrid': True, 'gridcolor': GRID_COLOR},
            'plot_bgcolor': BG_COLOR,
            'paper_bgcolor': BG_COLOR,
            'annotations': [{
                'text': 'Select signals from the sidebar',
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'showarrow': False,
                'font': {'size': FONT_SIZE_ANNOTATION, 'color': TEXT_COLOR}
            }]
        }
    }, True


def get_chart_figure(chart_data, signal_ids, aggregation_level, start, end, is_live):
    """Build chart figure layout"""
    title = (
        f'{len(signal_ids)} Signal(s) - {start.strftime("%Y-%m-%d %H:%M")} '
        f'to {end.strftime("%Y-%m-%d %H:%M")}<br>'
        f'<sub>Aggregation: {aggregation_level if aggregation_level else "minute-level"}</sub>'
    )
    
    return {
        'data': chart_data,
        'layout': {
            'title': title,
            'showlegend': True,
            'legend': LEGEND_POSITION,
            'hovermode': 'x unified',
            'margin': CHART_MARGINS,
            'xaxis': {'showgrid': False, 'zeroline': False},
            'yaxis': {'showgrid': True, 'gridcolor': GRID_COLOR},
            'plot_bgcolor': BG_COLOR,
            'paper_bgcolor': BG_COLOR
        }
    }, not is_live


@callback(
    [Output('main-graph', 'figure'), Output('interval-component', 'disabled')],
    [Input('url', 'search'), Input('interval-component', 'n_intervals')]
)
def update_chart(search, _):
    """Update chart based on query parameters from React
    
    Args:
        search: URL search string with query parameters
        _: Interval counter (unused but required by callback)
    
    Expected URL parameters:
    - signal_id: comma-separated signal IDs (e.g., "signal_01,signal_02")
    - signals: JSON array with signal metadata [{id, name, color}, ...]
    - live: boolean for live mode
    - start: ISO date string for start time
    - end: ISO date string for end time
    
    Returns:
        Tuple of (figure, disabled_state) for graph and interval components
    """
    signal_ids, signal_metadata, is_live, start, end = parse_query_params(search)
    
    if not signal_ids:
        return get_empty_chart()
    
    chart_data, aggregation_level = build_signal_traces(
        signal_ids,
        signal_metadata,
        start,
        end
    )
    return get_chart_figure(
        chart_data,
        signal_ids,
        aggregation_level,
        start,
        end,
        is_live
    )

if __name__ == "__main__":
    app.run(debug=True)