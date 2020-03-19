import os
import pandas as pd
import altair as alt
import plotly.graph_objects as go
import streamlit as st

NOT_DATE_COLS = ['Province/State', 'Country/Region', 'Lat', 'Long']

@st.cache
def read_hopkins_time_series():
    DIR = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series"    

    cases = dict()

    cases['Confirmados']    = pd.read_csv('{}/time_series_19-covid-Confirmed.csv'.format(DIR))
    cases['Muertos']        = pd.read_csv('{}/time_series_19-covid-Deaths.csv'.format(DIR))
    cases['Recuperados']    = pd.read_csv('{}/time_series_19-covid-Recovered.csv'.format(DIR))

    return (cases)

def agreggate_time_series(cases, country=None):

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

def plot_time_series(cases):

    world = pd.concat(
        [cases[key][[x for x in cases[key].columns if x not in NOT_DATE_COLS]].sum().T for key in cases.keys()], 
        axis=1
    )

    world.columns = cases.keys() #['Confirmados', 'Muertos', 'Recuperados']
    world.index = pd.to_datetime(world.index, infer_datetime_format=True)
    world = world.rename_axis('Fecha').reset_index()


    world = agreggate_time_series(cases, country='Chile')

    world_long = world.melt(
        id_vars = ['Fecha'], 
        value_vars = ['Confirmados', 'Muertos', 'Recuperados'], 
        var_name = 'Tipo',
        value_name = 'Casos'
    )

    chart = alt.Chart(world_long).mark_line().encode(
        x = 'Fecha',
        y = 'Casos',
        color = 'Tipo'
    )

    #st.altair_chart(chart)

    fig = go.Figure()
    for key in cases.keys():
        fig.add_trace(go.Scatter(x=world.Fecha, y=world[key], name=key))
    
    fig.update_layout(
        title_text='Casos en todo el mundo',  
    #    xaxis_rangeslider_visible=True
    )
    st.plotly_chart(fig)
    if st.checkbox('Mostrar datos'):
        st.subheader('Datos mundiales')
        st.write(world)
    #st.line_chart(world)





    return None

def main():
    cases = read_hopkins_time_series()

    st.title('COVID-19 Dashboard para Chile')

    section = st.sidebar.selectbox(
        'Escoja análisis', 
        ['Series de tiempo', 'Mapas', 'Proyecciones']
            
    )

    if section == 'Series de tiempo':
        #st.write(confirmed[confirmed['Country/Region'] == 'Chile'].T)        
        #st.line_chart(confirmed[confirmed['Country/Region'] == 'Chile'].T)

        plot_time_series(cases)

    elif section == 'Mapas':
        st.markdown('En construcción')

    elif section == 'Proyecciones':
        st.markdown('En construcción')

    st.info(
        """
        Desarrollado por [Benjamín Carrión](https://www.linkedin.com/in/bencarrion/) 
        | Fuente de datos: [John Hopkins University](https://github.com/CSSEGISandData/COVID-19) \n
        Código fuente: [github.com/bicarrio](https://github.com/bicarrio/COVID-19_Chile)
        """
    )
    


if __name__ == "__main__":
    main()