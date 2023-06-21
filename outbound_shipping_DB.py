import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from datetime import datetime as dt

#----------------------------------------------------------------------------------------------------------------------
#data cleaning

df = pd.read_csv(("dummy_data.csv"), low_memory=False)

df['delivery_date'] = pd.to_datetime(df['delivery_date'])
df['purchase_time'] = pd.to_datetime(df['purchase_time'])
df["shipment_service"].fillna('Same_day', inplace = True)

#shipping distance and time between order placed and order shipped

df3 = df.copy()
df3.drop(df3[df3['shipment_service'] == '0'].index, inplace = True)

df3['time_delta'] = ((df3.delivery_date - df3.purchase_time)/np.timedelta64(1, 'D'))
df3['time_delta'] = df3['time_delta'].apply(np.ceil)
df3['time_delta'] = pd.Series(df3['time_delta'], dtype="int")

criteria = [df3['time_delta'].between(0,1), df3['time_delta'].between(1,2), df3['time_delta'].between(2,3)
            , df3['time_delta'].between(3,4), df3['time_delta'].between(4,5), df3['time_delta'].between(5,500)]
values = ['1', '2', '3', '4','5','6+']
df3['Date_difference_barchart_v1'] = np.select(criteria, values, 0)

criteria = [df3['haversine_distance_miles'].between(1, 25), df3['haversine_distance_miles'].between(26, 50), df3['haversine_distance_miles'].between(51, 75)
            , df3['haversine_distance_miles'].between(76, 100), df3['haversine_distance_miles'].between(101, 150), df3['haversine_distance_miles'].between(151, 200)
            , df3['haversine_distance_miles'].between(201, 250), df3['haversine_distance_miles'].between(251, 5000)]
values = [25, 50, 75,100,150,200,250 ,500]
df3['Shipping ranges'] = np.select(criteria, values, 0)
df3.haversine_distance_miles.round()
df3['Shipping_distance'] = df3['haversine_distance_miles'] 

#---------------------------------------------------------------------------------------

df3['Shipping_distance'] = pd.Series(df3['Shipping_distance'], dtype="int")
df5 = df3.copy()
df5.set_index('delivery_date', inplace=True)

# ---------------------------------------------------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}]
                )

card_3_dropdown = dbc.Card(
                        dbc.CardBody(
                                    [
                                        html.H4("Select product", className="card-title"),
                                        html.P("Select the product you would like to see in the map and the sunburst.",
                                        className="card-text",),
                                        dcc.Dropdown(id='from_column_dropdown_product', options=[
                                            {'label': i, 'value': i} for i in df5.product_name.unique()
                                        ], multi=False, value='Product B'),
                                        html.H4("Select the fulfillment center", className="card-title"),
                                        html.P("Select the fulfillment center you would like to see in the map.",
                                            className="card-text",),
                                        dcc.Dropdown(id='from_column_dropdown_FC', options=[
                                            {'label': i, 'value': i} for i in df5.fc.unique()
                                        ], multi=False, value='Location B'),
                                        html.H4("Select shipment service", className="card-title"),
                                        html.P("Select the shipping method you would like to see in the map.",
                                            className="card-text",),
                                        dcc.Dropdown(id='from_column_dropdown_shipping', options=[
                                            {'label': i, 'value': i} for i in df5.transportmode.unique()
                                        ], multi=False, value='express')
        
                                    ])
                                )

card_4_dropdown = dbc.Card(
                        dbc.CardBody([
                            dcc.DatePickerRange(
                                    id='my-date-picker-range',
                                    calendar_orientation='horizontal',
                                    day_size=39,
                                    end_date_placeholder_text="Return",
                                    with_portal=False,
                                    first_day_of_week=0,
                                    reopen_calendar_on_clear=True,
                                    is_RTL=False,
                                    clearable=True,
                                    number_of_months_shown=1,
                                    start_date=dt(2022, 10, 1).date(),
                                    end_date=dt(2022, 11, 1).date(),
                                    display_format='MMM Do, YY',
                                    month_format='MMMM, YYYY',
                                    minimum_nights=2,
                            
                                    persistence=True,
                                    persisted_props=['start_date'],
                                    persistence_type='session',
                            
                                    updatemode='singledate'
                                ),
                                dcc.Store(id='store_data_fedex_analysis', data=[], storage_type='memory'),
                                dcc.Dropdown(id='dropdown_plants_flowers',
                                                     options=[
                                                         {'label': 'Group A', 'value': 'Group A'},
                                                         {'label': 'Group B', 'value': 'Group B'},
                                                         {'label': 'Group C', 'value': 'Group C'},
                                                        {'label': 'Group D', 'value': 'Group D'}
                                                     ],
                                                     optionHeight=35,
                                                     value='Group B',
                                                     disabled=False,
                                                     multi=False,
                                                     searchable=True,
                                                     search_value='',
                                                     placeholder='Please select...',
                                                     clearable=True,
                                                     style={'width': "40%"},
                                                     )
                                                
                                                ])
                            )

app.layout = dbc.Container([

    dbc.Row(
            dbc.Col(html.H1("Outbound parcel analysis dashboard",
                            className='text-center text-primary mb-4'),
                    width=12)),

    dbc.Row(
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Total orders per shipping method"),
                dbc.CardBody(id='Bar5_v1')]),
            width=12)),
    dbc.Row(
        dbc.Col(card_4_dropdown, width=6)
    ),

    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Category shipping method breakdown"),
                dbc.CardBody(id='Bar3')]),
            width=6),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Days between order placed and order delivered"),
                dbc.CardBody(id='Bar1')]),
            width=6)]),

    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Distance between FC zipcode and recipient zipcode"),
                dbc.CardBody(id='Bar2')]),
            width=6),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Shipping method per fulfillment center"),
                dbc.CardBody(id='Bar4')]),
            width=6)]),

    dbc.Row(
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Scatterplot mapping of days between order placed and order shipped and shipping distance"),
                dbc.CardBody(id='Scat1')]),
            width=12)),

    dbc.Row([
        dbc.Col(card_3_dropdown, width=6),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Per state visualization of dropdowns to the left."),
                dbc.CardBody(id='cholro_1')]),
            width=6)]),

    dbc.Row(
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Sunburst per state/FC/shipping method"),
                dbc.CardBody(id='sun_1')]),
            width=12)),
    dbc.Row(
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Shipping method per SKU"),
                dbc.CardBody(id='Bar6')]),
            width=6))
],fluid = True)

#-------------------------------------------------------------------
#daterangepicker

#----------------------------------------------
#Bar graph 5
@app.callback(
    Output(component_id='Bar5_v1', component_property='children'),
    [Input(component_id='my-date-picker-range', component_property='start_date'),
     Input(component_id='my-date-picker-range', component_property='end_date')])


def build_graph_5(start_date, end_date):
    df5_2_1 = df5.loc[start_date:end_date]

    df_barchart5 = df5_2_1.groupby(['transportmode']).size().sort_values(ascending=False).reset_index(name='shipment_sum')
    fig_1 = px.bar(df_barchart5, x="transportmode", y="shipment_sum", color="transportmode")

    return [dcc.Graph(id='Bar5_v1', figure=fig_1)]

#----------------------------------------------
#Bar graph 1
@app.callback(
    Output(component_id='Bar1', component_property='children'),
    [Input(component_id='my-date-picker-range', component_property='start_date'),
     Input(component_id='my-date-picker-range', component_property='end_date'),
     Input(component_id='dropdown_plants_flowers', component_property='value')])


def build_graph_1(start_date, end_date, value):
    df5_2_2 = df5.loc[start_date:end_date]
    df_barchart1 = df5_2_2.groupby(['group', 'transportmode', 'Date_difference_barchart_v1']).size().sort_values(
        ascending=False).reset_index(name='shipment_sum')

    data_build_graph_1 = df_barchart1.copy()[df_barchart1['group'] == value]

    fig_bar_1 = px.bar(data_build_graph_1, x="Date_difference_barchart_v1", y="shipment_sum", color="transportmode")

    return [dcc.Graph(id='Bar1_v1', figure=fig_bar_1)]
#----------------------------------------------
#Bar graph 2

@app.callback(
    Output(component_id='Bar2', component_property='children'),
    [Input(component_id='my-date-picker-range', component_property='start_date'),
     Input(component_id='my-date-picker-range', component_property='end_date'),
     Input(component_id='dropdown_plants_flowers', component_property='value')])

def build_graph_1(start_date, end_date, value):
    df5_2_3 = df5.loc[start_date:end_date]
    df_barchart2 = df5_2_3.groupby(['group', 'transportmode', 'Shipping ranges']).size().sort_values(
        ascending=False).reset_index(name='shipment_sum')
    data_build_graph_1 = df_barchart2.copy()[df_barchart2['group'] == value]

    fig_bar_2 = px.bar(data_build_graph_1, x='Shipping ranges', y="shipment_sum", color="transportmode")

    return [dcc.Graph(id='Bar2_v1', figure=fig_bar_2)]

#----------------------------------------------
#Scat graph 1

@app.callback(
    Output(component_id='Scat1', component_property='children'),
    [Input(component_id='my-date-picker-range', component_property='start_date'),
     Input(component_id='my-date-picker-range', component_property='end_date'),
     Input(component_id='dropdown_plants_flowers', component_property='value')])


def build_graph_2(start_date, end_date, value):
    df5_2_4 = df5.loc[start_date:end_date]
    df_scat_chart_1 = df5_2_4.groupby(['group', 'transportmode', 'Shipping_distance', 'time_delta']).size().sort_values(
        ascending=False).reset_index(name='shipment_sum')

    data_build_graph_2 = df_scat_chart_1.copy()[df_scat_chart_1['group'] == value]

    fig_scat_1 = px.scatter(data_build_graph_2, x="Shipping_distance", y="time_delta",
                            size="shipment_sum", color="transportmode",
                            hover_name="transportmode", log_x=True, size_max=60)

    return [dcc.Graph(id='Scat1_v1', figure=fig_scat_1)]

#----------------------------------------------

#Bar graph 3
@app.callback(
    Output(component_id='Bar3', component_property='children'),
    [Input(component_id='my-date-picker-range', component_property='start_date'),
     Input(component_id='my-date-picker-range', component_property='end_date'),
     Input(component_id='dropdown_plants_flowers', component_property='value')])


def build_graph_3(start_date, end_date, value):
    df5_2_5 = df5.loc[start_date:end_date]
    df_barchart3 = df5_2_5.groupby(['group', 'transportmode']).size().sort_values(ascending=False).reset_index(
        name='shipment_sum')

    data_build_graph_3 = df_barchart3.copy()[df_barchart3['group'] == value]

    fig_bar_3 = px.bar(data_build_graph_3, x="transportmode", y="shipment_sum", color="transportmode")

    return [dcc.Graph(id='Bar3_v1', figure=fig_bar_3)]

#----------------------------------------------
#Bar graph 4
@app.callback(
    Output(component_id='Bar4', component_property='children'),
    [Input(component_id='my-date-picker-range', component_property='start_date'),
     Input(component_id='my-date-picker-range', component_property='end_date'),
     Input(component_id='dropdown_plants_flowers', component_property='value')])


def build_graph_4(start_date, end_date, value):
    df5_2_6 = df5.loc[start_date:end_date]
    df_barchart4 = df5_2_6.groupby(['group', 'fc', 'transportmode']).size().sort_values(ascending=False).reset_index(
        name='shipment_sum')

    data_build_graph_4 = df_barchart4.copy()[df_barchart4['group'] == value]

    fig_bar_4 = px.bar(data_build_graph_4, x="transportmode", y="shipment_sum", color="fc")

    return [dcc.Graph(id='Bar4_v1', figure=fig_bar_4)]

#----------------------------------------------
#Bar graph 6
@app.callback(
    Output(component_id='Bar6', component_property='children'),
    [Input(component_id='my-date-picker-range', component_property='start_date'),
     Input(component_id='my-date-picker-range', component_property='end_date'),
     Input(component_id='from_column_dropdown_product', component_property='value')])


def build_graph_6(start_date, end_date, value):
    df5_2_7 = df5.loc[start_date:end_date]
    df_barchart6 = df5_2_7.groupby(['product_name', 'transportmode']).size().sort_values(
        ascending=False).reset_index(name='shipment_sum')

    data_build_graph_6 = df_barchart6.copy()[df_barchart6['product_name'] == value]

    fig_bar_6 = px.bar(data_build_graph_6, x="transportmode", y="shipment_sum", color="product_name")

    return [dcc.Graph(id='Bar6_v1', figure=fig_bar_6)]

# ---------------------------------------------------------------

@app.callback(
    Output(component_id='cholro_1', component_property='children'),
    [Input(component_id='my-date-picker-range', component_property='start_date'),
     Input(component_id='my-date-picker-range', component_property='end_date'),
     Input(component_id='from_column_dropdown_product', component_property='value'),
    Input(component_id='from_column_dropdown_FC', component_property='value'),
    Input(component_id='from_column_dropdown_shipping', component_property='value')
     ])


def build_graph_7(start_date, end_date, filter_1, filter_2, filter_3):
    df4_2_1 = df5.loc[start_date:end_date]
    df4_3 = df4_2_1.groupby(['fc', 'transportmode', 'product_name', 'recipient_state']).size().sort_values(
        ascending=False).reset_index(name='shipment_sum')
    df_ch_1 = df4_3[df4_3['product_name'] == filter_1]
    df_ch_2 = df_ch_1[df_ch_1['fc'] == filter_2]
    df_ch_3 = df_ch_2[df_ch_2['transportmode'] == filter_3]
    fig = go.Figure(data=go.Choropleth(
        locations=df_ch_3['recipient_state'],  # Spatial coordinates
        z=df_ch_3['shipment_sum'].astype(float),  # Data to be color-coded
        locationmode='USA-states',  # set of locations match entries in `locations`
        colorscale='Reds',
        colorbar_title="shipment_sum",
    ))

    fig.update_layout(
        title_text='Total Fedex Shipments per State',
        geo_scope='usa',  # limit map scope to USA
    )

    return [dcc.Graph(id='Chloro_graph_1', figure=fig)]

# ---------------------------------------------------------------
# Connecting the Dropdown values to the graph
@app.callback(
    Output(component_id='sun_1', component_property='children'),
    [Input(component_id='my-date-picker-range', component_property='start_date'),
     Input(component_id='my-date-picker-range', component_property='end_date'),
     Input(component_id='from_column_dropdown_product', component_property='value')])


def build_graph_8(start_date, end_date, filter_1):
    df4_2_2 = df5.loc[start_date:end_date]
    df4_3 = df4_2_2.groupby(['fc', 'transportmode', 'product_name', 'recipient_state']).size().sort_values(
        ascending=False).reset_index(name='shipment_sum')
    df_ch_1 = df4_3[df4_3['product_name'] == filter_1]

    fig = px.sunburst(df_ch_1, path=['recipient_state','fc', 'transportmode'], values='shipment_sum', color='transportmode',width=1200,
                  height=1200)

    return [dcc.Graph(id='Sun_1', figure=fig)]


#------------------------------------------------
#launching the app

if __name__ == '__main__':
    app.run_server(debug=True)