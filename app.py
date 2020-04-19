# -*- coding: utf-8 -*-
import dash
import pathlib
import numpy as np
import pandas as pd
from datetime import timedelta
from helpers import human_format
import plotly.graph_objects as go
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

external_stylesheets = [dbc.themes.BOOTSTRAP,
'https://use.fontawesome.com/releases/v5.11.2/css/all.css',
{'href': 'https://fonts.googleapis.com/icon?family=Material+Icons',
'rel': 'stylesheet'}]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.title = 'COVID-19'
server = app.server
app.config.suppress_callback_exceptions = True
PATH = pathlib.Path(__file__).parent

df = pd.read_csv(PATH.joinpath("data/covid.csv").resolve())
df["date"] = pd.to_datetime(df["date"], dayfirst=True)
begin_date = df['date'].min() + timedelta(days=1)
end_date = df['date'].max()
no_days = (end_date - begin_date).days
df['Timeline'] = df['date'].dt.strftime('%b %d')

seq = [0, 9, 23, 38, 52, 69, 83, 99]
slider_marks = {i: (begin_date + timedelta(days=i)).strftime('%b')
if ((begin_date + timedelta(days=i)).day == 1 or i == 0) else (begin_date + timedelta(days=i)).strftime('%d')
                for i in seq}
config = {'modeBarButtonsToRemove': ['pan2d', 'select2d', 'lasso2d', 'zoomOut2d', 'zoomIn2d', 'hoverClosestCartesian',
                                     'zoom2d', 'autoScale2d', 'hoverCompareCartesian', 'zoomInGeo', 'zoomOutGeo',
                                     'hoverClosestGeo', 'hoverClosestGl2d', 'toggleHover',
                                     'zoomInMapbox', 'zoomOutMapbox', 'toggleSpikelines'],
          'displaylogo': False}

map_data_options = [{'label': 'Confirmed Cases', 'value': 'confirmed_cases'},
                    {'label': 'Deaths', 'value': 'deaths'},
                    {'label': 'Recovered', 'value': 'recovered'},
                    {'label': 'Active Cases', 'value': 'active'}, ]

map_section = dbc.Container([
    dbc.Row([
        html.Div(
        className="app-header",
        children=[
            html.Div('Coronavirus outbreak in the world', className="app-header--title")
        ]),
        dbc.Col(dcc.Graph(id='map_plot', config=config, style={'height': '78vh'}), width=12),
    ]),

    dbc.Row(
        dbc.Col(
            dbc.Select(id='map_data', options=map_data_options, className='position-relative',
                       style={'left': '3vw', 'top': '-75vh', 'width': '240px', 'font_size': '36px', 'color': '#9400D3'}, value='confirmed_cases')
            , className='col-12')
        , id='timeline', style={'height': '0px'}),

    dbc.Row([
        dbc.Col([
            dbc.Checklist(options=[{"label": "Per (million) Capita", "value": True, 'disabled': False}], value=[],
                          id="per_capita", switch=True, className='position-relative',
                          style={'padding-top': '20px', 'left': '3vw', 'top': '-70vh', 'color': '#9400D3', 'width': '240px', 'font_size': '36px'}),
        ], className='col-12'),
        dbc.Col([
            dbc.Checklist(options=[{"label": "Exclude Population < 300K", "value": True, 'disabled': False}], value=[],
                          id="small_pop", switch=True, className='position-relative',
                          style={'left': '3vw', 'top': '-68vh', 'color': '#9400D3', 'width': '240px', 'font_size': '36px'}),
        ], className='col-12'),
    ], style={'height': '0px'}),

    html.Div(
        dcc.Slider(min=0, max=no_days, step=1, value=no_days, id='date_slider', updatemode='mouseup',
                   marks=slider_marks,
                   className='pl-0')
        , className='position-relative', style={'left': '3vw', 'bottom': '-2vh', 'width': '94vw', 'height': '0px'}),

    dbc.Card([
        dbc.CardHeader(
            html.H2("", id='stat_card_header', className='m-0',
                    style={'color': 'purple'})
            , style={'backgroundColor': 'rgba(255,255,255,0.5)'}),
        dbc.CardBody([
            html.H4("", id='lbl_cases', style={'color': '#666666'}),
            html.Pre('', id='lbl_cases_per_capita', style={'color': '#666666'}),
            html.H4('', id='lbl_deaths', style={'color': '#666666'}),
            html.Pre('', id='lbl_deaths_rate', className='m-0', style={'color': '#666666'}),
        ], style={'backgroundColor': 'rgba(255,255,255,0.5)', 'padding': '10px 5px 10px 20px'})
    ], style={'backgroundColor': 'rgba(255,255,255,0.5)', 'left': '3vw', 'top': '-30vh', 'width': '242px'}),

], fluid=True, id='map_section', style={'height': '90vh'})


@app.callback(Output('per_capita', 'options'),
              [Input('map_data', 'value')])
def upd_switch_label(value):
    if value == 'confirmed_cases':
        return [{"label": "Per (million) Capita", "value": True, 'disabled': False}]
    else:
        return [{"label": "As Rate on Cases", "value": True, 'disabled': False}]


@app.callback([Output('map_plot', 'figure'), Output('stat_card_header', 'children'),
               Output('lbl_cases', 'children'), Output('lbl_cases_per_capita', 'children'),
               Output('lbl_deaths', 'children'), Output('lbl_deaths_rate', 'children')],
              [Input('map_data', 'value'), Input('per_capita', 'value'), Input('date_slider', 'value'),
               Input('small_pop', 'value')])
def update_map(map_data, per_capita, sel_day, small_pop):
    target_col = map_data + '_rate' if per_capita else map_data

    sel_date = begin_date + timedelta(days=sel_day)
    if small_pop:
        dff = df[(df['date'] == sel_date) & df['pop_flag'] == 1]
    else:
        dff = df[(df['date'] == sel_date)]

    max_col = df[df['pop_flag'] == 1][target_col].max()
    sizeref = 2 * max_col / (60 ** 2)
    points_opacity = 0.9 - 0.7 * (np.sqrt(np.maximum(0, np.minimum(dff[target_col], max_col))) / np.sqrt(max_col))

    data_per_capita = map_data + '_rate'
    if map_data == 'confirmed_cases':
        ht = '<b>%{customdata[0]}</b><br>' \
             + 'Cases : %{customdata[2]:,f}<br>' \
             + 'Population : %{customdata[1]:,.1f} mio<br>' \
             + 'Per capita : %{customdata[3]:,.0f}<extra></extra>'
    else:
        ht = '<b>%{customdata[0]}</b><br>' \
             + map_data.capitalize() + ' : %{customdata[2]:,f}<br>' \
             + 'Cases : %{customdata[4]:,f}<br>' \
             + '% of cases : %{customdata[3]:,.1%}<extra></extra>'

    customdata = dff.loc[:, ['country_area', 'population', map_data, data_per_capita, 'confirmed_cases']].to_numpy()

    if map_data == 'confirmed_cases':
        m_color = 'purple'
    elif map_data == 'deaths':
        m_color = 'red'
    elif map_data == 'recovered':
        m_color = 'green'
    else:
        m_color = 'orange'

    fig = go.Figure()
    fig.add_trace(go.Scattermapbox(mode='markers', lat=dff['lat'], lon=dff['long'], hovertemplate=ht,
                                   marker_size=np.maximum(0, np.minimum(dff[target_col], max_col)),
                                   marker_sizeref=sizeref, marker_sizemode='area',
                                   customdata=customdata,
                                   marker_color=m_color, marker_opacity=points_opacity.to_numpy()))

    fig.update_layout(
        hovermode='closest',
        mapbox=dict(
            accesstoken='pk.eyJ1IjoiYWdhcndhbHYiLCJhIjoiY2s5Nm80M2VkMDRqNTNmbWdzZHNlcmV4byJ9.NvNqJjQiQoJ-uOg0V-LMZg',
            center={'lat': 30, 'lon': -3.4},
            zoom=1.7,
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        autosize=True,
    )

    # compute aggregate stats on Dff
    agg_dff = df.loc[(df['date'] >= sel_date - timedelta(days=1)) & (df['date'] <= sel_date),
                     ['date', 'confirmed_cases', 'deaths', 'recovered', 'active', 'population']].groupby(['date']).sum()
    total_cases_sel_date = agg_dff.loc[sel_date, 'confirmed_cases']
    total_population_sel_date = agg_dff.loc[sel_date, 'population']
    total_cases_prev_date = agg_dff.loc[sel_date - timedelta(days=1), 'confirmed_cases']

    total_deaths_sel_date = agg_dff.loc[sel_date, 'deaths']
    total_death_prev_date = agg_dff.loc[sel_date - timedelta(days=1), 'deaths']

    selected_date = str(sel_date.month_name()) + " " + str(sel_date.day)
    if total_cases_prev_date > 0:
        cases_variance = total_cases_sel_date / total_cases_prev_date - 1
    else:
        cases_variance = ''
    if total_population_sel_date > 0:
        cases_per_exposure = total_cases_sel_date / total_population_sel_date
    else:
        cases_per_exposure = ''
    if total_death_prev_date > 0:
        death_variance = total_deaths_sel_date / total_death_prev_date - 1
    else:
        death_variance = ''
    if total_cases_sel_date > 0:
        death_rate = total_deaths_sel_date / total_cases_sel_date
    else:
        death_rate = ''

    cases_label = ["Cases : " + human_format(total_cases_sel_date),
                   dbc.Badge(str('{:+.0%}'.format(cases_variance)), className="mr-3 position-relative float-right", id='badge_case',
                             style={'backgroundColor': '#9400D3', 'width':'50px'}),
                   dbc.Tooltip("Variance over previous day", target="badge_case")
                   ]

    lbl_cases_per_capita = "per (million) capita: " + human_format(cases_per_exposure)

    lbl_deaths = ["Deaths : " + human_format(total_deaths_sel_date),
                  dbc.Badge(str('{:+.0%}'.format(death_variance)), className="mr-3 position-relative float-right", id='badge_death',
                            style={'backgroundColor': '#9400D3', 'width':'50px'}),
                  dbc.Tooltip("Variance over previous day", target="badge_death")
                  ]

    lbl_deaths_rate = 'as % cases: ' + str('{:.1%}'.format(death_rate))

    return fig, selected_date, cases_label, lbl_cases_per_capita, lbl_deaths, lbl_deaths_rate

app.layout = html.Div(children=[
    map_section
    ]
)
if __name__ == '__main__':
    app.run_server(debug=True, threaded=True)