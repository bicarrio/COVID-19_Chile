import os
import pandas as pd
import altair as alt
import plotly.graph_objects as go
import streamlit as st

NOT_DATE_COLS = ['Province/State', 'Country/Region', 'Lat', 'Long']

@st.cache
def read_hopkins_time_series():
    '''
    Reads time series from the John Hopkins University github.
    These are curated from individual daily reports to the WHO, and are considered fairly complete and robust.
    Small deviations from particular countries are expected.

    Returns a dictionary with dataframes for Confirmed, Dead, and Recovered cases.
    '''

    DIR = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series"    

    cases = dict()

    cases['Confirmados']    = pd.read_csv('{}/time_series_19-covid-Confirmed.csv'.format(DIR))
    cases['Muertos']        = pd.read_csv('{}/time_series_19-covid-Deaths.csv'.format(DIR))
    cases['Recuperados']    = pd.read_csv('{}/time_series_19-covid-Recovered.csv'.format(DIR))

    return (cases)

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




def main():
    cases = read_hopkins_time_series()

    st.title('Panel COVID-19 para Chile')

    st.sidebar.title('Navegación')

    

    section = st.sidebar.radio(
        'Escoja análisis', 
        ['Mundo', 'Chile', 'Otros países']
            
    )

    if section == 'Mundo':
        st.header('Series de tiempo en el mundo')
        world_ts = plot_time_series(cases)

        st.header('Mapa de infección en el mundo')
        
        

    elif section == 'Chile':
        st.header('Series de tiempo en Chile')
        chile_ts = plot_time_series(cases, country='Chile')

        st.header('Mapa de infección en Chile')

        st.header('Comparación entre Chile y otros países')
        compared = st.multiselect('Seleccione países para comparar', sorted(cases['Confirmados']['Country/Region'].unique()))

        plot_comparative_time_series(chile_ts, compared, cases)
        

    elif section == 'Otros países':
        st.header('Series de tiempo en otros países')
        country = st.selectbox('Seleccione un país', sorted(cases['Confirmados']['Country/Region'].unique()))
        plot_time_series(cases, country=country, plot=True)

    
    st.sidebar.info(
        """
        Desarrollado por [Benjamín Carrión](https://www.linkedin.com/in/bencarrion/)\n
        Fuente de datos: [John Hopkins University](https://github.com/CSSEGISandData/COVID-19) \n
        Código fuente: [github.com/bicarrio](https://github.com/bicarrio/COVID-19_Chile)
        """
    )


if __name__ == "__main__":
    main()