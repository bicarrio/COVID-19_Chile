# import os
import json
import pandas as pd
import geopandas
import altair as alt
# from vega_datasets import data
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

NOT_DATE_COLS = ['Province/State', 'Country/Region', 'latitude', 'longitude']

@st.cache
def read_hopkins_time_series():
    '''
    Reads time series from the John Hopkins University github.
    These are curated from individual daily reports to the WHO, and are considered fairly complete and robust.
    Small deviations from particular countries are expected.

    Returns a dictionary with dataframes for Confirmed, Dead, and Recovered cases.
    '''

    DIR = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series' 

    cases = dict()

    cases['Confirmados']    = pd.read_csv('{}/time_series_covid19_confirmed_global.csv'.format(DIR))   
    cases['Muertos']        = pd.read_csv('{}/time_series_covid19_deaths_global.csv'.format(DIR))
    cases['Recuperados']    = pd.read_csv('{}/time_series_covid19_recovered_global.csv'.format(DIR))

    for i in cases.keys():
        cases[i] = cases[i].rename(columns={'Lat':'latitude', 'Long':'longitude'})

    return (cases)

@st.cache
def read_minsal_table():
    '''
    reads a table with latest data on confirmed cases, by region
    '''

    URL = 'https://www.minsal.cl/nuevo-coronavirus-2019-ncov/casos-confirmados-en-chile-covid-19/'

    minsal = pd.read_html(URL)[0].iloc[2:]
    minsal.columns = minsal.iloc[0]
    minsal = minsal.iloc[1:-1]
    minsal['codregion'] = [15, 1, 2, 3, 4, 5, 13, 6, 7, 16, 8, 9, 14, 10, 11, 12]

    ### reads shapefile with chilean regions
    # URL = 'https://www.bcn.cl/obtienearchivo?id=repositorio/10221/10398/2/Regiones.zip'
    # regions = geopandas.read_file(URL)
    
    shape = 'data/Regional'
    regions = geopandas.read_file(shape)

    regions = regions.merge(minsal, on='codregion')

    choro_json = json.loads(regions.to_json())
    choro_data = alt.Data(values=choro_json['features'])

    return choro_data


def transform_cases(cases):
    '''
    Adds per country, and transform columns to datetime
    '''

    cases_times = dict()
    for i in cases.keys():
        df = cases[i].groupby('Country/Region').sum()
        df.index.name = 'País'
        df.drop(['latitude', 'longitude'], axis=1, inplace=True)
        # df.columns = pd.to_datetime(df.columns, infer_datetime_format=True)
        # df.reset_index(inplace=True)
        cases_times[i] = df

    return cases_times

def agreggate_time_series(cases, country=None):
    '''
    Takes in a dictionary with Confirmed, Dead, and Recovered cases from read_hopkins_time_series(), and the selection of a country.
    Returns a time series for the three categories for the specified country.
    If coutry==None (default) it returns global data.
    '''

    if country==None:
        df = pd.concat(
            [cases[key][[x for x in cases[key].columns if x not in NOT_DATE_COLS]].sum().T for key in cases.keys()], 
            axis=1
        )

    else:
        df = pd.concat(
            [cases[key][cases[key]['Country/Region']==country][[x for x in cases[key].columns if x not in NOT_DATE_COLS]].sum().T for key in cases.keys()], 
            axis=1
        )

    df.columns = cases.keys()
    df.index = pd.to_datetime(df.index, infer_datetime_format=True)
    df = df.rename_axis('Fecha').reset_index()

    return df

def plot_time_series(cases, country=None, plot=True):
    '''
    Generate a time series plot for Confirmed, Dead, and Recovered cases for the world or a specific country.
    It optionally shows the data.
    '''

    ts = agreggate_time_series(cases, country=country)

    fig = go.Figure()
    for key in cases.keys():
        fig.add_trace(go.Scatter(x=ts.Fecha, y=ts[key], name=key))
    
    if plot:
        st.plotly_chart(fig)
        if st.checkbox('Mostrar datos'):
            st.write(ts)
    if country==None:
        return {'World': ts}
    else:
        return {country: ts}

def plot_comparative_time_series(principal_ts, compared, cases):

    main_country = list(principal_ts.keys())[0]
    ts = principal_ts[main_country]
    tsshort = ts[ts.Confirmados >0]
    tsshort['Días desde contagio']  = tsshort.index - tsshort.index[0]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tsshort['Días desde contagio'], 
        y=tsshort.Confirmados, 
        name=main_country,
        mode='lines+markers',
        line=dict(color='black', width=2),
        ))

    for country in compared:
        tsi = plot_time_series(cases, country=country, plot=False)
        tsi = tsi[country]
        tsishort = tsi[tsi.Confirmados > 0]
        tsishort['Días desde contagio'] = tsishort.index - tsishort.index[0]

        fig.add_trace(go.Scatter(
            x=tsishort['Días desde contagio'], 
            y=tsishort.Confirmados, 
            name=country,
            mode='lines'
        ))
    
    fig.update_layout(
        xaxis_title='Días desde contagio',
        yaxis_title='Casos confirmados'
    )
    st.plotly_chart(fig)
    #st.write(tsshort)
    #principal_ts[0] 
    


    return None

def plot_world_map(cases):

    cases_times = transform_cases(cases)   
    variable = st.selectbox('', list(cases_times.keys()))
    
    time0 = cases_times['Confirmados'].columns[0]
    days = cases_times['Confirmados'].columns
    time = st.slider(
        'Días desde el comienzo de la pandemia ({})'.format(pd.to_datetime(time0, infer_datetime_format=True)), 
        min_value = 0,
        max_value = len(days)-1, 
        step=1
    )
    current_time = days[time]

    if variable == 'Confirmados':
        scale = px.colors.sequential.Viridis
    if variable == 'Muertos':
        scale = px.colors.sequential.Inferno_r
    if variable == 'Recuperados':
        scale = px.colors.sequential.algae


    fig0 = px.choropleth(
        cases_times[variable][current_time].reset_index(), 
        locations = 'País',
        locationmode = 'country names',
        color = days[time], 
        hover_name='País',
        #hover_data=[current_time],
        color_continuous_scale=scale,
        range_color=[0, cases_times[variable][days[-1]].max()],
    )

    fig0.update_layout(
        title_text = '{} hasta {}'.format(variable, pd.to_datetime(current_time, infer_datetime_format=True).strftime('%Y-%m-%d')), 
        geo = dict(
            showframe=False,
            showcoastlines=False, 
            projection_type='equirectangular',
        )
    )

    st.plotly_chart(fig0)   

    return None


def main():
    ### sidebar
    st.sidebar.title('Navegación')
    section = st.sidebar.radio(
        'Escoja análisis', 
        ['Mundo', 'Chile', 'Otros países']
    )
    st.sidebar.info(
        """
        Desarrollado por [Benjamín Carrión](https://www.linkedin.com/in/bencarrion/)\n
        Fuente de datos: [John Hopkins University](https://github.com/CSSEGISandData/COVID-19) \n
        Código fuente: [github.com/bicarrio](https://github.com/bicarrio/COVID-19_Chile)
        """
    )

    ### main body
    cases = read_hopkins_time_series()
    st.title('Panel COVID-19 para Chile')

    # choro_data = read_minsal_table()

    # chart = alt.Chart(choro_data).mark_geoshape().encode(
    #     color = 'Casos totales:Q',
    #     #tooltip = ['Casos totales', 'Fallecidos']
    # )

    # st.altair_chart(chart)


    #world = geopandas.read_file(geopandas.datasets.get_path('naturalearth_lowres'))
  


    ### sections
    if section == 'Mundo':
        st.header('Series de tiempo en el mundo')
        world_ts = plot_time_series(cases)

        st.header('Mapa de infección en el mundo')
        plot_world_map(cases)   
        

    elif section == 'Chile':
        st.header('Series de tiempo en Chile')
        chile_ts = plot_time_series(cases, country='Chile')


        st.header('Comparación entre Chile y otros países')
        compared = st.multiselect('Seleccione países para comparar', sorted(cases['Confirmados']['Country/Region'].unique()))

        plot_comparative_time_series(chile_ts, compared, cases)
        
        st.header('Mapa de infección en Chile')
        'EN CONSTRUCCIÓN'

    elif section == 'Otros países':
        st.header('Series de tiempo en otros países')
        country = st.selectbox('Seleccione un país', sorted(cases['Confirmados']['Country/Region'].unique()))
        plot_time_series(cases, country=country, plot=True)


if __name__ == "__main__":
    main()