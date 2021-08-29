import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from datetime import datetime as dt
from dash_html_components.Img import Img
from dash.exceptions import PreventUpdate

import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
from dash_html_components.Div import Div

from model import prediction 
from sklearn.svm import SVR 

app = dash.Dash(__name__)
server = app.server

def get_stock_price_fig(df):
    #generate stock price graph
    fig = px.line(df,
        x = "Date",
        y = ["Close", "Open"],
        title="Closing and Opening Price vs Date")
    return fig


def get_more(df):
    df["EWA_21"] = df['Close'].ewm(span=21, adjust=False).mean()
    fig = px.scatter(df,
        x = "Date",
        y = "EWA_21",
        title = "Exponential Moving Average vs Date"
    )
    fig.update_traces(mode='lines+markers')
    return fig


#this portion set how the web app looks like 
app.layout = html.Div([
    html.Div(
        [
            html.P("Welcome to the Stock Dash App!", className="start"),

            html.Div([
                html.Div(id='prompt-stock-code', children="Input stock code:"),
                html.Div(dcc.Input(id='stock-code-input', type='text')), #stock code input
                html.Button('Search', id='stock-search-button'),
            ]),
         
            html.Div([
                dcc.DatePickerRange( #Date range picker input
                    id='date-picker-range',
                    max_date_allowed=dt.now(),
                    end_date=dt.today().date(),
#                                         min_date_allowed=dt(1995, 8, 5),
#                                         max_date_allowed=dt.now(),
#                                         initial_visible_month=dt.now(),
#                                         end_date=dt.now().date()),
                )
            ]),
            
            html.Div([
                html.Button('Stock Price', id='Stock-Price-button'), #Stock price button
                html.Button('Indicators', id='Indicators-button'),  #indicators button
                dcc.Input(placeholder='number of days', id='forecast-input', type='number'), #Number of days of forecast input
                html.Button('Forecast', id='Forcast-button'), #Forecast button
            ]),
        ], className="nav"), 
    
    html.Div(
        [
            html.Div([#company name and logo
                html.Img(id="logo"),
                html.P(id="Company-Name")
            ], 
            className="header"),

            html.Div(id="description", className="description_ticker"),

            html.Div([], id="graphs-content"), #stock price 

            html.Div([], id="main-content"), #indicators

            html.Div([], id="forecast-content") # Forecast plot
        ], 
        className="content")
],
className="container")



#get info for stock ticker search
@app.callback([
    Output("logo", "src"), 
    Output("Company-Name", "children"), 
    Output("description", "children"),
    Output("Stock-Price-button", "n_clicks"),
    Output("Indicators-button", "n_clicks"),
    Output("Forcast-button", "n_clicks")],
    [Input('stock-search-button', 'n_clicks')],
    [State('stock-code-input', 'value')]
)
def update_date(self, v):
    if self == None:
        return None, None, "Please enter a correct stock code in the search box to get details.", None, None, None
    else:
        if v == None:
            raise PreventUpdate
        else:
            ticker = yf.Ticker(v)
            inf = ticker.info
            df = pd.DataFrame().from_dict(inf, orient="index").T
            return df["logo_url"].values[0], df["shortName"].values[0], df["longBusinessSummary"].values[0], None, None, None



#generate stock price graph
@app.callback(
    [Output("graphs-content", "children")],
    [Input('Stock-Price-button', 'n_clicks'),
     Input("date-picker-range", "start_date"), 
     Input("date-picker-range", "end_date")],
    [State('stock-code-input', 'value')]
)
def stock_price(self, start_date, end_date, v):
    if self == None:
        return [""]
    if v == None:
        raise PreventUpdate
    else:
        if start_date != None:
            df = yf.download(v, str(start_date), str(end_date))
        else:
            df = yf.download(v)

    df.reset_index(inplace=True)
    fig = get_stock_price_fig(df)  
    return [dcc.Graph(figure=fig)]


#generate indicator graph
@app.callback(
    [Output("main-content", "children")],
    [Input("Indicators-button", "n_clicks"),
     Input("date-picker-range", "start_date"), 
     Input("date-picker-range", "end_date")],
    [State("stock-code-input", 'value')]
)
def indicators(self, start_date, end_date, v):
    if self == None:
        return [""]
    if v == None:
        return [""]

    if start_date == None:
        df_indicator = yf.download(v)
    else: 
        df_indicator= yf.download(v, str(start_date), str(end_date))

    df_indicator.reset_index(inplace=True)
    fig = get_more(df_indicator)
    return [dcc.Graph(figure=fig)]


#generate forcast price graph 
@app.callback(
    [Output("forecast-content", "children")],
    [Input("Forcast-button","n_clicks")],
    [State("forecast-input", "value"),
     State("stock-code-input", "value")]
)
def forecast(self, n_days, v):
    if self == None:
        return[""]
    if v == None:
        raise PreventUpdate
    fig = prediction(v, int(n_days)+1)
    return [dcc.Graph(figure=fig)]


if __name__ == '__main__':
    app.run_server(debug=True)