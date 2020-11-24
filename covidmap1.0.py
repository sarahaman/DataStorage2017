################################################
#                _     _                       #
#               (_)   | |                      #
#  ___ _____   ___  __| |_ __ ___   __ _ _ __  #
# / __/ _ \ \ / / |/ _` | '_ ` _ \ / _` | '_ \ #
#| (_| (_) \ V /| | (_| | | | | | | (_| | |_) |#
# \___\___/ \_/ |_|\__,_|_| |_| |_|\__,_| .__/ #
#                                       | |    #
#                                       |_|    #
#                                              #
################################################

import json
import pandas as pd
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from urllib.request import urlopen
import psycopg2 as pspg

def retrieveData():
    '''
    Connects to the covidPolitics database. Queries covid data, then queries 
    political data. Merges the data on FIPS code and returns the merged df.
    '''
    conn = pspg.connect("dbname=covidPolitics user=alashley")
    cur = conn.cursor()
    
    cur.execute("select * from covid where date = 11")
    covid_pull = list(cur.fetchall())
    df_covid = pd.DataFrame(covid_pull, columns =['Date', 'County', 'State', 'FIPS', 'Cases', 'Deaths']) 
    
    cur.execute("select county, state, FIPS, gop_2016, gop_2020 from politics")
    politics_pull = list(cur.fetchall())
    df_politics = pd.DataFrame(politics_pull, columns =['County', 'State', 'FIPS', 'GOP_2016', 'GOP_2020']) 
    
    cur.execute("select county, state, FIPS, white, college_or_higher, ruralness, population, unemployment_rate from demographics")
    demo_pull = list(cur.fetchall())
    df_demo = pd.DataFrame(demo_pull, columns =['County', 'State', 'FIPS', 'white', 'college_or_higher', 'ruralness', 'population', 'unemployment_rate'])
    
    conn.close()
    
    df_temp = pd.merge(df_covid, df_politics, how = 'left', left_on=['FIPS'], right_on=['FIPS'])
    df = pd.merge(df_demo, df_temp, how = 'left', left_on=['FIPS'], right_on=['FIPS'])
    
    return df

temp = retrieveData()
df = temp.copy()

# Adds leading 0's to FIPS codes where needed

df['FIPS'] = df['FIPS'].astype('int64', copy=True)
df = df[df['FIPS'] < 80000].copy(deep=True)
df['FIPS'] = df['FIPS'].astype('str', copy=True)
df['FIPS'] = df['FIPS'].str.rjust(5, '0')

# Loads county outline vectors with which to render the map, matched by fips

with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    countyData = json.load(response)

mapbox_accesstoken = 'pk.eyJ1IjoicGxvdGx5bWFwYm94IiwiYSI6ImNrOWJqb2F4djBnMjEzbG50amg0dnJieG4ifQ.Zme1-Uzoi75IaFbieBDl3A'

###############################################################################

counties = df['County_x'].str.title().tolist()

pl_deep= [[0.0, 'rgb(253, 253, 204)'],
          [0.1, 'rgb(243, 79, 78)'],
          [0.2, 'rgb(243, 79, 78)'],
          [0.3, 'rgb(237, 63, 62)'],
          [0.4, 'rgb(237, 63, 62)'],
          [0.5, 'rgb(230, 31, 32)'],
          [0.6, 'rgb(230, 31, 32)'],
          [0.7, 'rgb(218, 15, 19)'],
          [0.8, 'rgb(218, 15, 19)'],
          [0.9, 'rgb(201, 0, 11)'],
          [1.0, 'rgb(201, 0, 11)']]

pl_pol= [[0.0, 'rgb(3, 1, 140)'],
         [0.1, 'rgb(33, 42, 165)'],
         [0.2, 'rgb(66, 89, 195)'],
         [0.3, 'rgb(123, 159, 242)'],
         [0.4, 'rgb(158, 194, 255)'],
         [0.5, 'rgb(253, 253, 204)'],
         [0.6, 'rgb(243, 79, 78)'],
         [0.7, 'rgb(237, 63, 62)'],
         [0.8, 'rgb(230, 31, 32)'],
         [0.9, 'rgb(218, 15, 19)'],
         [1.0, 'rgb(201, 0, 11)']]
                                
Types = ['Cases','Deaths', 'GOP_2020', 'GOP_2016']

trace1 = []    
    
for q in Types:
    if q != 'GOP_2020' and q != 'GOP_2016':   
        trace1.append(go.Choroplethmapbox(
            geojson = countyData,
            locations = df['FIPS'].tolist(),
            z = df[q].tolist(), 
            colorscale = pl_deep,
            text = counties,
            colorbar = dict(thickness=20, ticklen=3),
            marker_line_width=0, marker_opacity=0.7,
            visible=False,
            subplot='mapbox1',
            hovertemplate = "<b>%{text}</b><br><br>" +
                            "Number of "+str(q)+"=%{z}<br>" +
                            "<extra></extra>"))
    else:
        trace1.append(go.Choroplethmapbox(
            geojson = countyData,
            locations = df['FIPS'].tolist(),
            z = df[q].tolist(), 
            colorscale = pl_pol,
            text = counties,
            colorbar = dict(thickness=20, ticklen=3),
            marker_line_width=0, marker_opacity=0.7,
            visible=False,
            subplot='mapbox1',
            hovertemplate = "<b>%{text}</b><br><br>" +
                            "Proportion of GOP voters = %{z}<br>" +
                            "<extra></extra>"))
    
trace1[0]['visible'] = True

trace2 = []    
    
for q in Types:
    trace2.append(go.Bar(
        x=df.sort_values([q], ascending=False).head(10)[q],
        y=df.sort_values([q], ascending=False).head(10)['County_x'].str.title().tolist(),
        xaxis='x2',
        yaxis='y2',
        marker=dict(
            color='rgba(77, 153, 219, 0.5)',
            line=dict(
                color='rgba(77, 153, 219, 0.7)',
                width=0.5),
        ),
        visible=False,
        orientation='h',
    ))
    
trace2[0]['visible'] = True

###############################################################################

layout = go.Layout(
    title = {'text': 'National COVID-19 Cases: November, 2020',
    		 'font': {'size':28, 
    		 		  'family':'Arial'}},
    autosize = True,
    
    mapbox1 = dict(
        domain = {'x': [0.3, 1],'y': [0, 1]},
        center = {"lat": 37.0902, "lon": -95.7129},
        accesstoken = mapbox_accesstoken, 
        zoom = 2.5),

    xaxis2={
        'zeroline': False,
        "showline": False,
        "showticklabels":True,
        'showgrid':True,
        'domain': [0, 0.25],
        'side': 'left',
        'anchor': 'x2',
    },
    yaxis2={
        'domain': [0.4, 0.9],
        'anchor': 'y2',
        'autorange': 'reversed',
    },
    margin=dict(l=100, r=20, t=70, b=70),
    paper_bgcolor='rgb(227, 235, 240)',
    plot_bgcolor='rgb(227, 235, 240)',
)

layout.update(updatemenus=list([
    dict(x=0,
         y=1,
         xanchor='left',
         yanchor='middle',
         buttons=list([
             dict(
                 args=['visible', [True, False, False, False]],
                 label='Number of COVID-19 cases by county:',
                 method='restyle'
                 ),
             dict(
                 args=['visible', [False, True, False, False]],
                 label='Number of CoVID-19 deaths by county:',
                 method='restyle'
                 ),
             dict(
                 args=['visible', [False, False, True, False]],
                 label='Proportion of GOP voters by county in 2020:',
                 method='restyle'
                 ),
             dict(
                 args=['visible', [False, False, False, True]],
                 label='Proportion of GOP voters by county in 2016:',
                 method='restyle'
                 )  
            ]),
        )]))


fig=go.Figure(data=trace2 + trace1, layout=layout)

###############################################################################

figa = go.Figure()
figa.add_trace(go.Histogram(histfunc="sum", y=df['Deaths'], x=df['State'], name="sum deaths"))
figa.add_trace(go.Histogram(histfunc="sum", y=df['Cases'], x=df['State'], name="sum cases"))
figa.update_layout(barmode='stack')

figc = go.Figure(go.Scatter(x = df['population'], y = df['Cases'],mode='markers',
                  name='Population vs. Cases', marker=dict(color='#7595eb')))

figc.update_layout(title='Population vs. Cases',
                   plot_bgcolor='rgb(227, 235, 240)',
                   xaxis_title='Country Population',
                   yaxis_title='COVID-19 Cases',
                   font=dict(
                       family="Serif",
                       color="#000000"),
                   showlegend=True)

figd = go.Figure()
figd.add_trace(go.Histogram(histfunc="sum", y=df['Cases'], x=df['ruralness'], name="sum deaths"))
figd.update_layout(title='Ruralness vs. Cases',
                   plot_bgcolor='rgb(227, 235, 240)',
                   xaxis_title="Ruralness (8 = High Ruralness)",
                   yaxis_title="COVID-19 Cases",
                   font=dict(
                       family="Serif",
                       color="#000000"),
                   )

fige = go.Figure(go.Scatter(x = df['white'], y = df['Cases'], mode='markers',
                  name='Cases vs. Proportion of White People', marker=dict(color='#686cba')))
fige.update_layout(title='Cases vs. Proportion of White People',
                   plot_bgcolor='rgb(227, 235, 240)',
                   xaxis_title="Proportion (%) of White People",
                   yaxis_title="COVID-19 Cases",
                   font=dict(
                       family="Serif",
                       color="#000000"),
                   showlegend=True)

figf = go.Figure(go.Scatter(x = df['college_or_higher'], y = df['Cases'], mode='markers',
                  name='Cases vs. Highly Educated People', marker=dict(color='#b5454d')))
figf.update_layout(title='Cases vs. Highly Educated People',
                   plot_bgcolor='rgb(227, 235, 240)',
                   xaxis_title="Proportion of Individuals with at least a College Education",
                   yaxis_title="COVID-19 Cases",
                   font=dict(
                       family="Serif",
                       color="#000000"),
                   showlegend=True)

figg = go.Figure(go.Scatter(x = df['unemployment_rate'], y = df['Cases'], mode='markers',
                  name='Cases vs. Unemployment', marker=dict(color='#8c0b14')))
figg.update_layout(title='Cases vs. Unemployment',
                   plot_bgcolor='rgb(227, 235, 240)',
                   xaxis_title="Unemployment Rate (proportion unemployed)",
                   yaxis_title="COVID-19 Cases",
                   font=dict(
                       family="Serif",
                       color="#000000"),
                   showlegend=True)

###############################################################################

stylesheet = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=stylesheet)

tabs_styles = {
    'height': '44px'
}
tab_style = {
    'borderBottom': '1px solid #5b8eb3',
    'borderLeft' : '1px solid #000000',
    'borderRight' : '1px solid #000000',
    'padding': '6px',
    'fontWeight': 'bold',
    'fontFamily' : 'Serif'
}

tab_selected_style = {
    'borderTop': '1px solid #000000',
    'borderBottom': '1px solid #5b8eb3',
    'borderLeft' : '1px solid #000000',
    'borderRight' : '1px solid #000000',
    'fontFamily' : 'Serif',
    'backgroundColor': '#5b8eb3',
    'fontWeight' : 'bold',
    'padding': '6px'
}
app.layout =   dcc.Tabs([   
    dcc.Tab(label='Choropleth Map', style=tab_style, selected_style=tab_selected_style, children=[
             html.Div([
                    html.H1("Covid-19 and Political Affiliation Dashboard"),
                    html.P("The emergence of the novel coronavirus commonly referred to as COVID-19 indelibly transformed the face of the United States of America.  As the pandemic had progressed, researchers have noted divisions in COVID-19 prevalence, and death rates, at the state level. The differing response by states has been the topic of frequent, impassioned on national platforms. However, we too find clear differences in COVID-19 case levels at the county level; differences which may be more difficult to attribute to state health policy. This project investigates potential county-level influences on COVID-19 case and death rates in the U.S.A. The first factor we investigate suggests itself: the political swing of the county.  Leading up to the 2020 Election, COVID-19 was sublimated into the political sphere, with the two major U.S. political parties taking starkly divergent approaches to addressing it. The Democratic Party pushed for strick adherence to public health guidelines, whereas prominent members of the Republican Party (GOP) questioned and often explicitly undermined health and public safety advice (i.e., disparaging mask wearing). "),
                    html.P("The choropleth below displays the case and death count for each county, updated as of 11/22/2020, compared with the proportion of votes cast for the GOP in both the 2016 and 2020 elections. From these data, one can investigate how the political leaning of a county relates to the COVID-19 case and death rates. Furthermore, the politicization of COVID-19 lends itself to the question of whether or not counties hit heavily by COVID-19 would lean more Democratic or Republican in the 2020 election, and if these changes would be significantly different from how they voted in 2016. However, the political skew of a county does not exist in a bubble and it is possible that any relationships found between the proportion of GOP votes and COVID-19 cases may be attributable to lurking county-level demographic and environmental factors. On the next tab, we plot the relationships between several notable potential confounding variables and COVID-19 case rates.")
                         ], 
                    style = {'padding' : '20px' , 
                             'backgroundColor' : '#5b8eb3', 
                             'fontFamily' : 'Serif', 
                             'borderTop' : '1px #000000'}),
             dcc.Graph(
                 id='example-graph-1',
                 figure=fig
    )]),
        dcc.Tab(label='Demographic Figures', style=tab_style, selected_style=tab_selected_style, children=[
           html.Div([
                    html.H1("Covid-19 and Demographic Factors"),
                         ],
                    style = {'padding' : '20px' , 
                             'backgroundColor' : '#5b8eb3', 
                             'fontFamily' : 'Serif', 
                             'borderTop' : '1px #000000'}),

           dcc.Graph(figure=figa),
           dcc.Graph(figure=figc),
           dcc.Graph(figure=figd),
           dcc.Graph(figure=fige),
           dcc.Graph(figure=figf),
           dcc.Graph(figure=figg)
        ]),
    html.Div(children='''
        Data source(s): The New York Times (https://github.com/nytimes/covid-19-data), 
        Townhall (https://github.com/tonmcg/US_County_Level_Election_Results_08-16/blob/master/2016_US_County_Level_Presidential_Results.csv)
    ''')
])
             
if __name__ == '__main__':
    app.run_server(debug=True)
