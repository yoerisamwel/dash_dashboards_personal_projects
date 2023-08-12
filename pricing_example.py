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

df = pd.read_csv(("check_zipcode_2_data.csv"), low_memory=False)
df_vendor_A = pd.read_csv(("vendor_A_data.csv"), low_memory=False)
df_vendor_B = pd.read_csv(("vendor_B_data.csv"), low_memory=False)

#----------------------------------------------------------------------------------------------------------------------
#joining
df_merge_A = pd.merge(df, df_vendor_A,  how='left', left_on=['sending_zip_code','delivery_zipcode'],
         right_on = ['sending_zip','receiving_zip'])
df_merge_AB = pd.merge(df_merge_A, df_vendor_B,  how='left', left_on=['sending_zip_code','delivery_zipcode'],
         right_on = ['sending_zip','receiving_zip'])
df_merge_AB = df_merge_AB.drop('Unnamed: 4', axis=1)
df_merge_AB = df_merge_AB.rename(columns={'vendor_x': 'vendor_A', 'sending_zip_x': 'sending_zip_vendor_A',
                                          'receiving_zip_x': 'receiving_zip_vendor_A',
                                          'vendor_A_pricing': 'vendor_A_pricing',
                                          'vendor_y': 'vendor_B', 'sending_zip_y': 'sending_zip_vendor_B',
                                          'receiving_zip_y': 'receiving_zip_vendor_B',
                                          'vendor_B_pricing': 'vendor_B_pricing'})
df_merge_AB['lowest_price_available'] = df_merge_AB[['vendor_A_pricing','vendor_B_pricing']].min(axis=1)

def should_have_shipped_from_vendor(df_should):

    conditions = [
        (df_should['vendor_A_pricing'] < df_should['shipping_price']) &
        (df_should['vendor_A_pricing'] < df_should['vendor_B_pricing']),
        (df_should['vendor_B_pricing'] < df_should['shipping_price']) &
        (df_should['vendor_B_pricing'] < df_should['vendor_A_pricing']),
        (df_should['shipping_price'] <= df_should['vendor_B_pricing']) &
        (df_should['shipping_price'] <= df_should['vendor_A_pricing'])
    ]
    values = ['Vendor A', 'Vendor B', 'Vendor C']
    df_should['optimal_vendor'] = np.select(conditions, values)

    return df_should
vendor_should_df = should_have_shipped_from_vendor(df_merge_AB)

def overspend(df_overspend):
    df_overspend['optimal_price'] = np.where((df_overspend['shipping_price'] <= df_overspend['lowest_price_available']),
                                   df_overspend['shipping_price'], df_overspend['lowest_price_available'])
    return df_overspend
pricing_df = overspend(vendor_should_df)

pricing_df['pricing_difference'] = pricing_df['shipping_price'] - pricing_df['optimal_price']

pricing_df_2 = pricing_df.copy()
pricing_df_2['purchase_time_index'] = pd.to_datetime(pricing_df_2['purchase_time_index'])
pricing_df_2['purchase_time_index_index'] = pricing_df_2.purchase_time_index.copy()
pricing_df_2.set_index('purchase_time_index_index', inplace=True)

#pricing_df_2.to_csv('out.csv')

#----------------------------------------------------------------------------------------------------------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}]
                )

app.layout = dbc.Container([
    dbc.Row(
            dbc.Col(html.H1("Outbound parcel pricing analysis dashboard",
                            className='text-center text-primary mb-4'),
                    width=12)),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    dcc.DatePickerRange(
                        id='date_picker',
                        calendar_orientation='horizontal',
                        day_size=39,
                        end_date_placeholder_text="Return",
                        with_portal=False,
                        first_day_of_week=0,
                        reopen_calendar_on_clear=True,
                        is_RTL=False,
                        clearable=True,
                        number_of_months_shown=1,
                        start_date=dt(2022, 9, 10).date(),
                        end_date=dt(2022, 11, 17).date(),
                        display_format='MMM Do, YY',
                        month_format='MMMM, YYYY',
                        minimum_nights=2,

                        persistence=True,
                        persisted_props=['start_date'],
                        persistence_type='session',

                        updatemode='singledate'
                    )
                ])
            ])
        )
    ]),
    dbc.Row(
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Total shipments per product"),
                dbc.CardBody(id='Bar1')]),
            width=12)),
    dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H4("Select receipient state", className="card-title"),
                    html.P("Select receipient state.",
                           className="card-text", ),
                    dcc.Dropdown(id='from_column_dropdown_state', options=[
                        {'label': i, 'value': i} for i in pricing_df_2.state.unique()
                    ], multi=False, value='Ohio')])),
            width=6),
        dbc.Col()
    ]),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Recipient shipment breakdown per state and county"),
                dbc.CardBody(id='Bar2')]),
            width=6),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Outbound spend per state"),
                dbc.CardBody(id='scatter3')]),
            width=6)]),
    dbc.Row([
        dbc.Col([
            dbc.Card(
                dbc.CardBody([
                        html.H4("Select sending FC", className="card-title"),
                        html.P("Select the sending zipcode.",
                               className="card-text", ),
                        dcc.Dropdown(id='from_column_dropdown_zip', options=[
                            {'label': i, 'value': i} for i in pricing_df_2.sending_zip_code.unique()
                        ], multi=False, value=22001)]
                )
            )
        ])
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Overspend per sending FC and state"),
                dbc.CardBody(id='Chloro_4')]),
            ],width=6)
    ]),
    dbc.Row(
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Sunburst"),
                dbc.CardBody(id='sun_5')]),
            width=12)),
])



#----------------------------------------------------------------------------------------------------------------------
#Callbacks
#Bar graph 1
@app.callback(
    Output(component_id='Bar1', component_property='children'),
    [Input(component_id='date_picker', component_property='start_date'),
     Input(component_id='date_picker', component_property='end_date')])


def build_graph_1(start_date, end_date):
    df_bar_1 = pricing_df_2.sort_index().loc[start_date:end_date]
    df_barchart1 = df_bar_1.groupby(['product','state']).size().sort_values(ascending=False).reset_index(
        name='shipment_sum')
    fig_1 = px.bar(df_barchart1, x="product", y="shipment_sum", color="state")
    return [dcc.Graph(id='Bar1_v1', figure=fig_1)]

#Bar graph 2
@app.callback(
    Output(component_id='Bar2', component_property='children'),
    [Input(component_id='date_picker', component_property='start_date'),
     Input(component_id='date_picker', component_property='end_date'),
     Input(component_id='from_column_dropdown_state', component_property='value')])


def build_graph_2(start_date, end_date, state):
    df_bar_2 = pricing_df_2.sort_index().loc[start_date:end_date]
    df_bar_3 = df_bar_2[df_bar_2['state'] == state]
    df_barchart2 = df_bar_3.groupby(['product', 'county']).size().sort_values(ascending=False).reset_index(
        name='shipment_sum')
    fig_1 = px.bar(df_barchart2, x="product", y="shipment_sum", color="county")
    return [dcc.Graph(id='Bar2_v1', figure=fig_1)]

#Pie graph 3
@app.callback(
    Output(component_id='scatter3', component_property='children'),
    [Input(component_id='date_picker', component_property='start_date'),
     Input(component_id='date_picker', component_property='end_date')])


def build_graph_3(start_date, end_date):
    df_bar_3 = pricing_df_2.sort_index().loc[start_date:end_date]
    df_bar_3 = df_bar_3.drop('purchase_time_index', axis=1)
    df_bar_3['shipment_count'] = 1
    df_barchart3 = df_bar_3.groupby(['product','state']).sum().reset_index()
    df_barchart3['average shipment cost'] = df_barchart3['shipping_price'] / df_barchart3['shipment_count']
    fig_1 = px.scatter(df_barchart3,x="state", y="average shipment cost", size="average shipment cost", color="product")
    return [dcc.Graph(id='scatter3_v1', figure=fig_1)]

#Chloro graph 4
@app.callback(
    Output(component_id='Chloro_4', component_property='children'),
    [Input(component_id='date_picker', component_property='start_date'),
     Input(component_id='date_picker', component_property='end_date'),
     Input(component_id='from_column_dropdown_zip', component_property='value')])


def build_graph_4(start_date, end_date, fc_zip):
    df_bar_2 = pricing_df_2.sort_index().loc[start_date:end_date]
    df_bar_3 = df_bar_2[df_bar_2['sending_zip_code'] == fc_zip]
    df_bar_3 = df_bar_3.drop('purchase_time_index', axis=1)
    df_barchart3 = df_bar_3.groupby(['state_abbr']).sum().reset_index()
    fig = go.Figure(data=go.Choropleth(
        locations=df_barchart3['state_abbr'],  # Spatial coordinates
        z=df_barchart3['pricing_difference'].astype(float),  # Data to be color-coded
        locationmode='USA-states',  # set of locations match entries in `locations`
        colorscale='Reds',
        colorbar_title="Overspend per state",
    ))

    fig.update_layout(
        title_text='Overspend per State',
        geo_scope='usa',  # limit map scope to USA
    )
    return [dcc.Graph(id='Chloro_4_v1', figure=fig)]

@app.callback(
    Output(component_id='sun_5', component_property='children'),
    [Input(component_id='date_picker', component_property='start_date'),
     Input(component_id='date_picker', component_property='end_date')])


def build_graph_8(start_date, end_date):
    df_sun_1 = pricing_df_2.sort_index().loc[start_date:end_date]
    df_sun_1 = df_sun_1.drop('purchase_time_index', axis=1)
    df_sun_1 = df_sun_1[df_sun_1['pricing_difference'] != 0]
    df_sun_2 = df_sun_1.groupby(['optimal_vendor','sending_zip_code', 'state', 'product']).sum().reset_index()
    fig = px.sunburst(df_sun_2, path=['optimal_vendor','sending_zip_code','state', 'product'], values='pricing_difference',
                      color='pricing_difference',width=1200,height=1200)

    return [dcc.Graph(id='sun_5_v1', figure=fig)]


#----------------------------------------------------------------------------------------------------------------------
#launching the app

if __name__ == '__main__':
    app.run_server(debug=True)