'''
Created on 29 december 2023
utf8 encoding
@author: cplumejeaud
'''

import os
import sys
from sys import platform
if platform == "linux" or platform == "linux2":
    # linux
    #sys.path.append('/opt/tljh/user/lib/python3.7/site-packages')
    sys.path.append('/home/cperreau/elenie/py310-venv/lib/python3.10/site-packages/')
import warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore",category=DeprecationWarning)
    from bokeh.models import ColumnDataSource, CustomJS, DateSlider, LinearAxis, HoverTool, DatetimeTickFormatter, Range1d, DatetimeTicker
from bokeh.plotting import figure, show
from bokeh.layouts import column
from bokeh.models.ranges import Range1d
from bokeh.resources import INLINE
from bokeh.embed import components
from bokeh.transform import factor_cmap
import bokeh.palettes as bp

from flask import Flask, render_template, request, jsonify


from datetime import datetime
import math

import json
import folium
from folium import plugins
from folium.features import GeoJsonPopup as mi

import pandas as pd
import numpy as np
from shapely.geometry import Point, Polygon
import geopandas as gpd


data_loaded = False
data = None

app = Flask(__name__)


# Variables globales    (this will be affected after the call to load_data)
dataArretDeBus  = None
dataArriveesRegions  = None
dataCoquelles  = None
dataDepartsArrivees  = None
dataEmprise = None
dataBateau = None
geodataBateau = None
data_people_T = None
glignes_bus = None
dataCamps = None
dataGame  = None
geodataCom1 = None
geodataCom2 = None
dataWeather = None

# Variables globales
# Liste actuelle des villes de départ de bateaux
liste_villes = ['Boulogne', 'Calais', 'Gravelines', 'Dunkerque']
# épaisseur max des flèches de départ de bateau en pixels
max_epaisseur_fleche = 50
# Jour du mois à afficher
day_to_display = 16
# Bus colors
['23_01_R19' '17_08_A_22' 'B_51_R_18T' 'C1_51_RTRAV_22' 'A_51_R_18_T']
bus_colors = { 'C1_51_RTRAV_22':'pink', '23_01_R19': 'blue', '17_08_A_22':'orange','B_51_R_18T':'grey', 'A_51_R_18_T':'green' }


#Emprise en EPSG 3857 (pseudo-mercator)
minx = 594577.6290221793
miny = 7066681.60721594
maxx = 675887.2790512822
maxy = 7117714.1396148475


def get_packages_requirements():
    #https://stackoverflow.com/questions/4858100/how-to-list-imported-modules
    #https://docs.python.org/3/library/types.html
    #https://stackoverflow.com/questions/301134/how-can-i-import-a-module-dynamically-given-its-name-as-string
    import types, importlib
    from getversion import get_module_version
    
    #from importlib.metadata import version
    #print(version('lxml'))
    #print(version('os')) 
    ''' version DOES NOT work for
        built-in modules
        modules not installed but just added to the python path (by your IDE for example)
        two versions of the same module available (one in python path superseding the one installed)'''
    with open("requirements.txt", "w") as filin:
        for name, val in globals().items():
            if isinstance(val, types.ModuleType):
                package_name= val.__name__
                #Load dynamically the module from its name
                my_module = importlib.import_module(package_name)
                #Get its version
                my_version, details = get_module_version(my_module)
                if not 'final.0' in my_version:
                    filin.write(package_name+'=='+my_version+'\n')

def load_data():

    #Init a container for data to get back in global scope
    data = {}
    
    current_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
    #Récupération des données
    if platform == "win32" :
        # change the current directory to specified directory
        os.chdir(r"C:\Travail\Enseignement\Cours_M2_python\Projet_Elenie")
    if platform == "linux":
        #current_dir = os.path.dirname(__file__)
        #os.chdir(os.path.dirname(__file__))
        print(current_dir)
        print('load_data -  Current working directory changed to : '+current_dir)
        os.chdir(current_dir) #Mais cela ne marchait pas, j'ai du ajouter la lecture depuis current_dir+'/ressources/arret_bus_camp.geojson'
        print('load_data -  Current working directory changed to : '+os.curdir)

    with open(current_dir+'/ressources/arret_bus_camp.geojson', encoding='UTF-8') as fArretDeBus:
        dataArretDeBus = json.load(fArretDeBus)
        data['dataArretDeBus'] = dataArretDeBus
    with open(current_dir+'/ressources/arrivees_region.geojson', encoding='UTF-8') as fArriveesRegions:
        dataArriveesRegions = json.load(fArriveesRegions)
        data['dataArriveesRegions'] = dataArriveesRegions
    with open(current_dir+'/ressources/CRA_coquelles.geojson', encoding='UTF-8') as fCoquelles:
        dataCoquelles = json.load(fCoquelles)
        data['dataCoquelles'] = dataCoquelles
    with open(current_dir+'/ressources/depart_arrivee_camps.geojson', encoding='UTF-8') as fDepartsArrivees:
        dataDepartsArrivees = json.load(fDepartsArrivees)
        data['dataDepartsArrivees'] = dataDepartsArrivees
    with open(current_dir+'/ressources/emprise_2154_ok_buffer5.geojson', encoding='UTF-8') as fEmprise:
        dataEmprise = json.load(fEmprise)
        data['dataEmprise'] = dataEmprise
    with open(current_dir+'/ressources/Try_bateau_commune.geojson', encoding='UTF-8') as fBateau:
        dataBateau = json.load(fBateau)
        data['dataBateau'] = dataBateau
    
    
    geodataBateau = gpd.read_file(current_dir+'/ressources/Try_commune.geojson', encoding='utf-8')
    geodataBateau.sort_values(by=['sens'], inplace=True) #Important pour faire les flêches
    data['geodataBateau'] = geodataBateau
    
    ## Lire les mouvements de personnes
    data_people = pd.read_excel(current_dir+'/Donnees_carte.xlsx', sheet_name='mouvements')  
    data_people.rename(columns={"Date (mois d'aout)": "dates"}, inplace=True)#"Vent km/h ": "wind_speed", "Vagues m ": "wave"
    data_people.drop('Unnamed: 17', axis=1, inplace=True) #Supprimer  les colonnes inutiles et vides
    data_people.drop('Unnamed: 18', axis=1, inplace=True) #Supprimer  les colonnes inutiles et vides
    data_people.drop([0, 1, 15, 18, 19, 20, 21], axis=0, inplace=True) #Supprimer  les lignes inutiles et vides
    index =  ['dates'] + data_people['dates'].tolist() #Sauver la future liste de noms de colonnes
    #print(index)
    data_people_T = data_people.transpose() #Inverser lignes et colonnes
    data_people_T.reset_index(inplace=True) #Supprime l'index
    data_people_T.drop(0, axis=0, inplace=True) #Supprime la première ligne
    data_people_T.columns = index #Renomme les colonnes avec la colonne 'dates' du départ
    data_people_T.set_index('dates', inplace=True)#Dates devient un index
    data_people_T.fillna(0, inplace=True) #values = {"A": 0, "B": 1, "C": 2, "D": 3}

    data['data_people_T'] = data_people_T
    
    ## Lire les données des bus et les manipuler

    lignes_bus = pd.read_table(current_dir+'/ressources/shape2.txt', sep=',', header=0, names=['bus', 'long', 'lat', 'i', 'order'])
    lignes_bus.set_index('bus', inplace=True, drop=False)
    #https://geopandas.org/en/stable/gallery/create_geopandas_from_pandas.html
    glignes_bus = gpd.GeoDataFrame(
        lignes_bus, geometry=gpd.points_from_xy(lignes_bus.long, lignes_bus.lat), crs="EPSG:4326"
    )
    #https://stackoverflow.com/questions/51071365/convert-points-to-lines-geopandas
    data['glignes_bus'] = glignes_bus
    
    ## For camp map
    with open(current_dir+'/ressources/Camp.geojson', encoding='utf-8') as fCamps:
        dataCamps = json.load(fCamps)
        data['dataCamps'] = dataCamps   
        print('Number of camps loaded: '+str(len(dataCamps['features'])))
    with open(current_dir+'/ressources/Try_game.geojson', encoding='utf-8') as fGame:
        dataGame = json.load(fGame)
        data['dataGame'] = dataGame
    #version 2 : read a geodataframe with geopandas
    geodataCom1 = gpd.read_file(current_dir+'/ressources/communautes_T1.geojson', encoding='utf-8')
    geodataCom2 = gpd.read_file(current_dir+'/ressources/communautes_T2.geojson', encoding='utf-8')
    data['geodataCom1'] = geodataCom1
    data['geodataCom2'] = geodataCom2
    
    dataWeather=pd.read_csv(current_dir+'/weather.csv', sep=';')
    data['dataWeather'] = dataWeather

    
    return data    

def compute_max_boat(data_people_T):
    #max_boat : nombre max de personnes arrivées en UK depuis une commune
    max_boat = 0
    ## Max d'épaisseur des flèches pour les bateaux
    for k in liste_villes:
        if data_people_T.max()[k] > max_boat : 
            max_boat = data_people_T.max()[k]
    #print('max size fleche : '+str(max_boat))
    return max_boat

def compute_epaisseur_fleche(col, max_boat, max_size):
    if isinstance(col, pd.core.series.Series):
        return col.apply(lambda x: (math.pow(x  / max_boat, 0.7)*max_size))
    else : 
        return (math.pow(col  / max_boat, 0.7)*max_size)
    
# CARTE DU CAMP

def function_get_human_points_from_geo(day_to_display):
    '''With GeoPandas and a GeoDataFrame in parameter
    return a list of points to put inside polygons
    
    Note : 
    - number of points should be a parameter related to the total number of points is proportional to camps size
    - total number of points should be proportional to camps size, given in parameter
    - number of points per feature could be proportional to the area of the feature.
    - polygones could be dilated/contracted according the "normal" size of the camp (take the average)
    '''
    #Nombre de personnes totale au camp
    camp_size = data_people_T.loc[day_to_display, 'pop_campG5']
    #print('retailler le camps pour cette taille : '+str(camp_size))
    #print(math.log10(data_people_T.loc[day_to_display, 'pop_campG5']))
    #print(data_people_T.mean(numeric_only=True)['pop_campG5'])
    
    #Facteur de dilatation/contraction : (ratio de la taille / taille moyenne)^2
    factor = math.pow(camp_size / data_people_T.mean(numeric_only=True)['pop_campG5'], 2)
    #print('facteur de dilatation/contraction : '+str(factor))
    #print(camp_size * factor)
    #print('----------')
    
    #Select polygons matching the period
    if day_to_display > 23 : #Periode T2
        dataCom = geodataCom2
    else : 
        dataCom = geodataCom1
        
    # List to store all points to put inside polygones
    all_human_points = []

    # with GeoDataFrame
    for index, row in dataCom.iterrows():
        polygon = row['geometry']
        
        #Get bounds of the polygon
        minx, miny, maxx, maxy = polygon.bounds
            
        # Number of points to generate (à la place de 50)
        #print(row['Id'])
        #print(row['percent_surface'])
        num_points = factor * camp_size *row['percent_surface'] /100.0
        # Change here : total number of points is proportional to camps size (camp_size), and number of points per feature is proportional to the area of the feature (percent_surface). 
        
        # Points inside the current polygon
        human_points = []
        # Generate randomly points inside the bounding box of the current polygon
        while len(human_points) < num_points:
            point = Point(minx + (maxx - minx) * np.random.random(), miny + (maxy - miny) * np.random.random())
            if polygon.contains(point):
                human_points.append(point)
        
        # Add those points to the result 
        all_human_points.extend(human_points)
    return all_human_points
    
def create_map_camp(day_to_display):
    # Global parameters to be set through a Web interface 
    day = day_to_display
    periode = 'T1'
    if day_to_display > 23 : 
        periode = 'T2'
    
    #Centre du code
    m = folium.Map(location=[51.000766, 2.256553], zoom_start=15)
    
    folium.TileLayer(tiles='OpenStreetMap').add_to(m)
    #folium.TileLayer(tiles='Stamen Terrain').add_to(m)
    #folium.TileLayer(tiles='Stamen Toner').add_to(m)
    #folium.TileLayer(tiles='Ma BDTopo', attr='https://wxs.ign.fr/topographie/geoportail/tms/1.0.0/BDTOPO/{z}/{x}/{y}.pbf').add_to(m)
        
        
    #Style Polygon for distro zones
    def polygon_style(feature):
        return {
            "fillColor": "green",
            "color": "black",
            "weight": 2,
            "fillOpacity": 0.5
        }
    #Style polygones T1
    def polygon_style2(feature):
        return {
            "fillColor": "cyan",
            "color": "black",
            "weight": 2,
            "fillOpacity": 0.5
        }
    #Style polygones T2
    def polygon_style3(feature):
        return {
            "fillColor": "pink",
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.5
        }
        
    #Points for distro zones in camp
    folium.GeoJson(dataCamps, 
        name="Camps",
        marker = folium.Marker(
            icon=folium.Icon(
                icon_color='black',icon='fa-solid fa-tents',color="green",prefix='fa'
        )),
        style_function=polygon_style,
        popup=mi(
            fields=['name', 'description'],
            aliases=['Nom', 'Description'],
            labels=True,
            style='width: 200px;',
            sticky=False
            )
        ).add_to(m)
    
    #Polygones for communauties
    if periode == 'T1':
        folium.GeoJson(geodataCom1, 
                    name="Communauté T1",
                    style_function=polygon_style3,
                    tooltip="Communauté T1"
            ).add_to(m)
    else:
        folium.GeoJson(geodataCom2, 
            name="Communauté T2",
            style_function=polygon_style3,
            tooltip="Communauté T2"
            ).add_to(m)
    
    #Add game enclosure, only if people are going to game
    if (data_people_T.at[day_to_display, 'conditions_navigation'] > 0):
        folium.GeoJson(dataGame,
            name='Game',
            tooltip='Game',
            marker = folium.Marker(
                icon=folium.Icon(
                    icon_color='black',icon='fa-solid fa-gamepad',color="beige",prefix='fa'
                )),
            popup=mi(
                fields=['name', 'description'],
                aliases=['Nom', 'Description'],
                labels=True,
                style='width: 350px;',
                sticky=False
            )
        ).add_to(m)
    
    # Create humans points inside T1/T2 polygons of communauties
    all_human_points = function_get_human_points_from_geo(day_to_display)
    
        
    # Add all humans like circles to Folium map
    fill_color_param = 'purple'
    '''#Finalement, changer la couleur des points suivant les jours n'est pas super bien fait, il faut faire autrement
    if day%2 == 0 :
        #day even
        print('even day '+str(day)+' during period: '+periode)
        fill_color_param = 'blue'
    else : 
        #odd day
        print('odd day '+str(day)+' during period: '+periode)
        fill_color_param = 'red'
    '''
        
    for point in all_human_points:
        folium.CircleMarker(location=[point.y, point.x], radius=1, color=fill_color_param, fill=True, fill_color=fill_color_param).add_to(m)
    
    # Add a control to select tiles layers
    folium.LayerControl().add_to(m)
    
    return m

    
# CARTE LITTORAL
def init_center_map_litto():

    centre_carte_litto = [50.924, 2.085]
    #centre_carte_litto = [51.000766, 2.256553]

    #Centre du code
    m = folium.Map(location=centre_carte_litto, zoom_start=10)

    folium.TileLayer(tiles='OpenStreetMap').add_to(m)
    folium.TileLayer(tiles='Ma BDTopo', attr='https://wxs.ign.fr/topographie/geoportail/tms/1.0.0/BDTOPO/{z}/{x}/{y}.pbf').add_to(m)
    # Ajouter un contrôle de couches pour sélectionner les tuiles
    
    return m

def create_map_lit(day_to_display):  
    m = init_center_map_litto()
    
    #Points pour les arrêts de bus
    folium.GeoJson(dataArretDeBus, 
        name="Arrets de bus",
        marker = folium.Marker(
            icon=folium.Icon(
                icon_color='black',icon='fa-solid fa-bus',color="white",prefix='fa'
        )),
        popup=mi(
            fields=['accessible', 'nom_arret','desserte',],
            aliases=['Accessibilité', 'Nom', 'Dessertes'],
            labels=True,
            style='width: 200px;',
            sticky=False
            )
        ).add_to(m)

    #Points pour les arrivees regions, point d'arrivées vers le camps.
    folium.GeoJson(dataArriveesRegions,
        name="Arrivées Régions",
        marker = folium.Marker(
            icon=folium.Icon(
                icon_color='black',icon='fa-solid fa-map-pin',color="darkblue",prefix='fa'
        )),
        popup=mi(
            fields=['name', 'description'],
            aliases=['Nom', 'Description'],
            labels=True,
            style='width: 200px;',
            sticky=False
            )
        ).add_to(m)

    #Point destinations des mises à l'abri
    if (data_people_T.at[day_to_display, 'conditions_navigation'] < 0):
        folium.GeoJson(dataCoquelles, 
            name='Coquelles',
            marker = folium.Marker(
                icon=folium.Icon(
                    icon_color='black',icon='fa-solid fa-city',color="darkpurple",prefix='fa',
            )),
            popup=mi(
                fields=['name', 'description'],
                aliases=['Nom', 'Description'],
                labels=True,
                style='width: 200px;',
                sticky=False
            )
        ).add_to(m)

    #Departs arrivées : point de depart/arrivée situé au camp
    if (data_people_T.at[day_to_display, 'conditions_navigation'] < 0):
        folium.GeoJson(dataDepartsArrivees, 
            tooltip='Départs Arrivées',
            name='Depart arrivees',
            marker = folium.Marker(
                icon=folium.Icon(
                    icon_color='black',icon='fa-solid fa-map',color="cadetblue",prefix='fa'
                )),
            popup=mi(
                fields=['name', 'description'],
                aliases=['Nom', 'Description'],
                labels=True,
                style='width: 200px;',
                sticky=False
                )
        ).add_to(m)
        
    #Bateaux point des départs vers l'angleterre : 
    # fleche courte, orientée avec Douvres (en angleterre) d'épaisseur proportionnelle à la commune du point (Boulogne, Calais, Dunkerque ou ...) / arrivees_UK
    if (data_people_T.at[day_to_display, 'conditions_navigation'] > 0):
        
        #max_boat : nombre max de personnes arrivées en UK depuis une commune
        max_boat = compute_max_boat(data_people_T)
        
        depart_point = None
        for sens, g, commune  in geodataBateau[['sens', 'geometry', 'commune']].values:
            #print(sens)
            #print(g)
            #print(commune)
            people = data_people_T.at[day_to_display, commune]
            #print(x)
            if sens%2==0:
                depart_point = g
                folium.Marker(
                    location=[depart_point.y, depart_point.x],
                    name=commune,
                    tooltip=str(people) + ' arrivées en UK partant des plages de '+commune,
                    icon=folium.Icon(
                        icon_color='black',icon='fa-solid fa-ship',color="blue",prefix='fa'
                    )   
                ).add_to(m) 
            else :
                #print('max_boat : ')
                #print(max_boat)
                thickness = compute_epaisseur_fleche(people, max_boat, max_epaisseur_fleche)
                #print(thickness)
                arrow = plugins.AntPath(
                    locations=[[depart_point.y, depart_point.x], [g.y, g.x]],
                    color='red', weight=thickness
                    #dash_array=[10, 20], pulse_color='yellow'
                ).add_to(m)

        #Dessiner les lignes de bus
        current_bus = None
        coordinates  = []
        for bus, g in glignes_bus[['bus', 'geometry']].values:
            if bus!=current_bus:
                #print(current_bus)
                #print(len(coordinates))
                if len(coordinates) > 1:#None pour le premier a une liste vide
                    arrow = plugins.AntPath(
                        locations=coordinates,
                        color=bus_colors[current_bus], weight=5,delay=1000
                        #dash_array=[10, 20], pulse_color='yellow'
                    ).add_to(m)
                current_bus = bus
                coordinates  = []
            coordinates.append([g.x, g.y])    
        #dernier bus
        if len(coordinates) > 1: #Precaution
            arrow = plugins.AntPath(
                locations=coordinates,
                color=bus_colors[current_bus], weight=5,delay=1000
            ).add_to(m)        

    folium.LayerControl().add_to(m)
    
    return m



# GRAPHIQUE DONNÉES MÉTÉO

def create_graph_weather(day_to_display):
    chosen_date = pd.to_datetime(str(day_to_display)+'/08/2022  00:00:00')
    print(chosen_date)
    
    #df = pd.read_excel('Donnees_carte.xlsx', sheet_name='meteo_graphique')
    # if platform == "linux":
    #     os.chdir(os.path.dirname(__file__))
    #     print(os.curdir)
    #     df=pd.read_csv('weather.csv', sep=';')
    # else : 
    #     df=pd.read_csv('C:/Travail/Enseignement/Cours_M2_python/Projet_Elenie/weather.csv', sep=';')
    df = dataWeather.rename(columns={"Dates (mois d'aout)": "date", "Vent km/h ": "wind_speed", "Vagues m ": "wave"})
    df['date'] = pd.to_datetime(df['date'])
    #print('Max wind speed' + str(df['wind_speed'].max()))
    
    source = ColumnDataSource(df)
    original_source = ColumnDataSource(df.copy())
    p = figure(title="Vitesse du vent et hauteur des vagues durant Aout 2022", x_axis_label='Date et heure', y_axis_label='Vitesse du Vent (km/h)',
               x_axis_type='datetime', width=700, height=400)

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore",category=DeprecationWarning)
        p.xaxis.formatter = DatetimeTickFormatter(
            hours=["%d %B %Y %H:%M"],
            days=["%d %B %Y %H:%M"],
            months=["%d %B %Y %H:%M"],
            years=["%d %B %Y %H:%M"],
        )
        #except bokeh.BokehDeprecationWarning:
        #Passing lists of formats for DatetimeTickFormatter scales was deprecated in Bokeh 3.0. Configure a single string format for each scale

    p.xaxis.major_label_orientation = "vertical"

    p.line('date', 'wind_speed', source=source, legend_label="Vitesse du Vent (km/h)", color="blue", line_width=2)
    p.extra_y_ranges = {"wave": Range1d(start=df['wave'].min() - 0.1, end=df['wave'].max() + 0.2)}
    p.add_layout(LinearAxis(y_range_name="wave", axis_label="Hauteur des Vagues (m)"), 'right')
    p.line('date', 'wave', source=source, legend_label="Hauteur des Vagues (m)", color="red", line_width=2, y_range_name="wave")
    #https://docs.bokeh.org/en/latest/docs/user_guide/basic/lines.html
    p.vspan(x=[chosen_date], line_width=[2], line_color="grey")#, line_dash=[6, 3]
    #https://docs.bokeh.org/en/latest/docs/user_guide/styling/plots.html
    p.legend.location = "top_center"

    hover = HoverTool(tooltips=[
        ("Date", "@date{%F %T}"),
        ("Vitesse du Vent (km/h)", "@wind_speed"),
        ("Hauteur des Vagues (m)", "@wave")
    ], formatters={'@date': 'datetime'})

    p.add_tools(hover)

    slider = DateSlider(title="Select Date", start=df['date'].min(), end=df['date'].max(), value=chosen_date, step=1, width=550, align='center')
    # df['date'].min()
    
    # align, aspect_ratio, bar_color, context_menu, css_classes, direction, disabled, end, flow_mode, format, height, height_policy, 
    # js_event_callbacks, js_property_callbacks, margin, max_height, max_width, min_height, min_width, name, orientation, resizable, 
    # show_value, sizing_mode, start, step, 
    # styles, stylesheets, subscribed_events, syncable, tags, title, tooltips, value, value_throttled, visible, width or width_policy
    
    callback = CustomJS(args=dict(original_source=original_source, source=source, slider=slider), code="""
        var data = original_source.data;  // Use the original full dataset
        var f = slider.value;
        console.log(slider.value);
        var date = new Date(f);
        
        
        //Added by Christine : make an ajax call to send to the server the slider.value  (with the request param 'chosen_date')
        //#https://stackoverflow.com/questions/50853416/how-to-trigger-ajax-call-after-a-box-selection-is-done-in-python-bokeh-plot
        (function($){
            $.getJSON('/ajaxviz', {
                chosen_date: slider.value, //this route will call change_the_date() function
                }, function(data) {
                    //when change_the_date() function returns
                    //data is a json composite object made of msg_plot, litto_map_plot, graph_weather_plot, camp_map_plot
                    //This following code update the divs with corresponding objects that we sent in change_the_date() function, using jsonify
                    $('#date-param').html(data.msg_plot);
                    $('#map_lit').html(data.litto_map_plot);
                    $('#graph_weather').html(data.graph_weather_plot);
                    $('#map_camp').html(data.camp_map_plot)
                    
            })
        })(jQuery);
    """)
    slider.js_on_change('value', callback)
    layout = column(slider, p)
    return layout

def javascript_deprecated():
    """
        var wind_speed = data['wind_speed'];
        var wave = data['wave'];
        var dates = data['date'];

        var new_wind_speed = [];
        var new_wave = [];
        var new_dates = [];

        for (var i = 0; i < dates.length; i++) {
            if ((new Date(dates[i])).getTime() <= date.getTime()) {
                new_dates.push(dates[i]);
                new_wind_speed.push(wind_speed[i]);
                new_wave.push(wave[i]);
            }
        }
        source.data = {'date': new_dates, 'wind_speed': new_wind_speed, 'wave': new_wave};
        source.change.emit();
    """

@app.route('/ajaxviz', methods=['GET','POST'])
def change_the_date():
    #Parse the param
    param = request.args.get("chosen_date")
    chosen_date = datetime.fromtimestamp(int(param)/1e3)
    #print(chosen_date)
    #print(chosen_date.day)
    day_to_display=chosen_date.day
    
    #Here, change the maps and graphic
    #Appeler la redéfinition du graphique avec ce paramètre - ici changer les cartes donc ! 
    lit_map = create_map_lit(day_to_display)
    camp_map = create_map_camp(day_to_display)
    graphic = create_graph_weather(day_to_display)
    graphic_script, graphic_div = components(graphic)
    
    message = ' - Nombre de personnes présentes au camp : '+str(data_people_T.loc[day_to_display, 'pop_campG5'])
    # render template : pass the div and script to render_template    
    return jsonify(
        msg_plot=render_template('update_message.html', p_msg=str(chosen_date)+message),
        litto_map_plot=render_template('update_message.html', p_msg=lit_map._repr_html_()),
        camp_map_plot=render_template('update_message.html', p_msg=camp_map._repr_html_()),
        graph_weather_plot=render_template('update_graphic.html', plot_script=graphic_script, plot_div=graphic_div)
    )    
    
@app.route('/')
def bokeh():
    global data_loaded
    global dataArretDeBus, dataArriveesRegions, dataCoquelles, dataDepartsArrivees, dataEmprise
    global dataBateau, geodataBateau, data_people_T, glignes_bus
    global dataCamps, dataGame, geodataCom1, geodataCom2, dataWeather  
    
    print(data_loaded)
    if not data_loaded:
        print('Loading data...was not done yet, in / route bokeh()')
        data = load_data()  
        dataArretDeBus = data['dataArretDeBus']
        dataArriveesRegions = data['dataArriveesRegions']
        dataCoquelles = data['dataCoquelles']
        dataDepartsArrivees = data['dataDepartsArrivees']
        dataEmprise = data['dataEmprise']
        dataBateau = data['dataBateau']
        geodataBateau = data['geodataBateau']
        data_people_T = data['data_people_T']
        glignes_bus = data['glignes_bus']
        dataCamps =  data['dataCamps']
        dataGame =  data['dataGame']
        geodataCom1 = data['geodataCom1']
        geodataCom2 = data['geodataCom2']
        dataWeather = data['dataWeather']
        data_loaded = True

    
    #Init the graphic and maps
    graph = create_graph_weather(day_to_display)
    camp_map = create_map_camp(day_to_display)
    lit_map = create_map_lit(day_to_display)
    #show(layout)
    
    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()
    script, div = components(graph)
    m_html = camp_map._repr_html_()
    m2_html = lit_map._repr_html_()
    
    msg = str(day_to_display) + ' Aout 2022'
    return render_template(
        'dunkerque.html',
        p_script=script,
        p_div=div,
        p_msg=msg,
        m_html=m_html,
        m2_html=m2_html,
        js_resources=js_resources,
        css_resources=css_resources,
    )

if __name__ == '__main__':   
    #get_packages_requirements()
    data_loaded = False
    
    #Loading data
    data = load_data()
    dataArretDeBus = data['dataArretDeBus']
    dataArriveesRegions = data['dataArriveesRegions']
    dataCoquelles = data['dataCoquelles']
    dataDepartsArrivees = data['dataDepartsArrivees']
    dataEmprise = data['dataEmprise']
    dataBateau = data['dataBateau']
    geodataBateau = data['geodataBateau']
    data_people_T = data['data_people_T']
    glignes_bus = data['glignes_bus']
    dataCamps =  data['dataCamps']
    dataGame =  data['dataGame']
    geodataCom1 = data['geodataCom1']
    geodataCom2 = data['geodataCom2']
    dataWeather = data['dataWeather']
    data_loaded = True
    
    app.run(debug=False, port=8086)
