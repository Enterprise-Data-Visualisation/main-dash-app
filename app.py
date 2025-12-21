from dash import Dash, html, dcc, Input, Output, callback
from signal_generator import generate_historical_signals
from datetime import datetime, timedelta

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Signal Generator App"),
    dcc.Location(id='url', refresh=False),
    dcc.Graph(id='main-graph'),
    dcc.Interval(id='interval-component', interval=2000)
])

@callback(
    [Output('main-graph', 'figure'), Output('interval-component', 'disabled')],
    [Input('url', 'search'), Input('interval-component', 'n_intervals')]
)
def update_chart(search, n):
    # Parse URL: "?signal_id=temp_01" -> "temp_01"
    signal_id = "temp_01" 
    is_live = False
    if search and 'signal_id=' in search:
        signal_id = search.split('signal_id=')[1].split('&')[0]
        # Parse 'live'
        if 'live=true' in search:
            is_live = True
            
    # Fetch Data
    end = datetime.now()
    start = end - timedelta(hours=24)
    data = generate_historical_signals(signal_id, start, end)

    # Render
    return {
        'data': [{
            'x': [d['timestamp'] for d in data],
            'y': [d['value'] for d in data],
            'type': 'scatter',
            'mode': 'lines+markers',
            'line': {'color': '#2563eb', 'width': 2},
            'fill': 'tozeroy',
            'fillcolor': 'rgba(37, 99, 235, 0.1)'
        }],
        'layout': {
            'title': f'Streaming: {signal_id}',
            'margin': {'l': 40, 'b': 40, 't': 40, 'r': 20},
            'xaxis': {'showgrid': False, 'zeroline': False},
            'yaxis': {'showgrid': True, 'gridcolor': '#eee'},
            'plot_bgcolor': 'white',
            'paper_bgcolor': 'white'
        }
    }, not is_live

if __name__ == "__main__":
    app.run(debug=True)