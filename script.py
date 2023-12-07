import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from datetime import datetime, timedelta
import requests

# Define options for sensor-id dropdown based on compressor-id selection
sensor_options_dict = {
    '1': [{'label':'NDE', 'value':'0'}, {'label':'DE', 'value':'1'}, {'label':'E1', 'value':'2'}, {'label':'E2', 'value':'3'}, {'label':' ', 'value': '4'}],
    '2': [{'label':'NDE', 'value':'5'}, {'label':'DE', 'value':'6'}, {'label':'E1', 'value':'7'}, {'label':'E2', 'value':'8'}, {'label':' ', 'value': '9'}],
    '3': [{'label':'NDE', 'value':'10'}, {'label':'DE', 'value':'11'}, {'label':'E-DE', 'value':'12'}, {'label':'E-NDE', 'value': '13'}, {'label':' ', 'value': '14'}],
    '4': [{'label':'NDE', 'value':'15'}, {'label':'DE', 'value':'16'}, {'label':'E-DE', 'value':'17'}, {'label':'E-NDE', 'value':'18'}, {'label':' ', 'value': '19'}],
    '5': [{'label':'NDE', 'value':'20'}, {'label':'DE', 'value':'21'}, {'label':'E-DE', 'value':'22'}, {'label':'E-NDE', 'value':'23'}, {'label':' ', 'value': '24'}]
}

# Initialize the Dash app
app = dash.Dash(__name__)

# Function to fetch initial data
def fetch_data(compressor_id, sensor_id, start_date, end_date, selected_y_axis):
    # Format dates as strings in YYYY-MM-DD format
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    url = f"http://172.31.2.124:5000/cbmdata/rawdata?compressor_ids={compressor_id}&sensor_ids={sensor_id}&start_date={start_date_str}&end_date={end_date_str}"

    response = requests.get(url)
    data = response.json()

    # Extract relevant data from the "data" key
    relevant_data = {
        'timestamp': [],
        selected_y_axis: [],  # Use the selected y-axis dynamically
    }

    if compressor_id in data and 'sensors' in data[compressor_id]:
        sensor_data = data[compressor_id]['sensors'].get(sensor_id, {}).get('data', [])

        for entry in sensor_data:
            relevant_data['timestamp'].append(entry.get('timestamp'))
            relevant_data[selected_y_axis].append(entry.get(selected_y_axis))

    return relevant_data


# Define the layout of the app
app.layout = html.Div([
    # Dropdown menu for selecting x vs y
    html.Div([
        html.Label("Select chart type:", className='label'),
        dcc.Dropdown(
            id='y-axis',
            options=[
                {'label': 'Temperature vs Time', 'value': 'temp'},
                {'label': 'X-acc vs Time', 'value': 'x-acc'},
                {'label': 'X-vel vs Time', 'value': 'x-vel'},
                {'label': 'Z-acc vs Time', 'value': 'z-acc'},
                {'label': 'Z-vel vs Time', 'value': 'z-vel'}
            ],
            value='temp',  # Default selection
            className='dropdown'
        ),
        # Dropdown menu for compressor ID
        html.Label("Select compressor ID:", className='label'),
        dcc.Dropdown(
            id='compressor-id',
            options=[
                {'label': '200A', 'value': '1'},
                {'label': '200B', 'value': '2'},
                {'label': '200C', 'value': '3'},
                {'label': '200D', 'value': '4'},
                {'label': '90+', 'value': '5'}
            ],
            value='1',  # Default selection
            className='dropdown'
        ),
        # Dropdown menu for sensor ID
        html.Label("Select Sensor ID:", className='label'),
        dcc.Dropdown(
            id='sensor-id',
            options=[
                {'label': 'NDE', 'value': '0'},
                {'label': 'DE', 'value': '1'},
                {'label': 'E1', 'value': '2'},
                {'label': 'E2', 'value': '3'},
                {'label': ' ', 'value': '4'}
            ],
            value='1',  # Default selection
            className='dropdown'
        )
    ], className='label-dropdown-container'),

    # Line plot
    dcc.Graph(id='line-plot', figure={'data': [{'x': [], 'y': [], 'mode': 'lines'}]}),

    # Interval component to update data every 5 minutes
    dcc.Interval(
        id='interval-component',
        interval=5 * 60 * 1000,  # 5 minutes * 60 seconds/minute * 1000 milliseconds/second
        n_intervals=0
    ),
])

# Callback to update sensor-id dropdown options and set the value
@app.callback(
    [Output('sensor-id', 'options'),
     Output('sensor-id', 'value')],
    Input('compressor-id', 'value')
)
def update_sensor_options(selected_compressor_id):
    sensor_options = sensor_options_dict.get(selected_compressor_id, [])
    
    # Set the value to the first option if the options list is not empty
    selected_sensor_id = sensor_options[0]['value'] if sensor_options else None
    
    return sensor_options, selected_sensor_id

# Callback to update graph
@app.callback(
    [Output('line-plot', 'figure'),
     Output('line-plot', 'config')],
    [Input('y-axis', 'value'),
     Input('interval-component', 'n_intervals'),
     Input('compressor-id', 'value'),
     Input('sensor-id', 'value')]
)
def update_graph(y_axis, n_intervals, compressor_id, sensor_id):
    # Set start_date to 24 hours prior to now
    start_date = datetime.now() - timedelta(hours=24)
    # Set end_date to the current time
    end_date = datetime.now()

    data = fetch_data(compressor_id, sensor_id, start_date, end_date, y_axis)

    # Extract relevant data based on the selected y-axis
    x_data = data['timestamp']
    y_data = data[y_axis]

    # Create the line plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_data, y=y_data, mode='lines'))

    # Set axis titles
    fig.update_layout(
        xaxis_title='Timestamp',
        yaxis_title=y_axis.capitalize()  # Capitalize the y-axis label
    )

    # Set dynamic chart title
    chart_title = f"{y_axis.capitalize()} vs Time"
    fig.update_layout(title=chart_title, title_x=0.5, title_y=0.9)

    # Additional configuration for the chart, if needed
    chart_config = {'displayModeBar': True}

    return fig, chart_config

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
