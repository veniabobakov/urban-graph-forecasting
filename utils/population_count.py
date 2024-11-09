import momepy
from momepy.datasets import get_path
import geopandas as gpd
import networkx as nx
from geopy.distance import geodesic
from shapely.geometry import Point
from rtree import index

'''
Количество квартир умножаем на коэффициент 3
15% - дети и пенсионеры(передвижение внутри района)
30% - взрослые(передвижение на личном транспорте вне района)
45% - взрослые(передвижение на ОТ вне района)
10% - взрослые(используют каршеринг, СИМ)
'''


def count_population_for_houses(path, G):
    df = gpd.read_file(path)
    df = df[df['Type'] in ['Жилые дома', 'Частные дома', 'Дома новостройки']]
    df = df.to_crs(epsg=4326)
    df = df.reset_index(drop=True)
    df['Nearest_Node'] = None
    df['Population'] = None
    idx = index.Index()

    # Добавляем все вершины графа в индекс
    for i, node in enumerate(G.nodes):
        point = node  # точки в графе (x, y)
        idx.insert(i, (point[0], point[1], point[0], point[1]))
    for i in range(len(df)):
        print(i)
        point = df.loc[i]['geometry']  # получаем точку для каждого объекта в .shp

        # Ищем ближайшие вершины в графе с помощью индекса
        possible_matches_index = list(idx.nearest((point.x, point.y, point.x, point.y), 20))

        min_distance = float('inf')
        nearest_node = None
        for j in possible_matches_index:
            neighbor = list(G.nodes)[j]  # Получаем точку из графа
            distance = geodesic((point.y, point.x), (neighbor[1], neighbor[0])).meters  # Вычисляем расстояние
            if min(distance, min_distance) < min_distance and G.nodes[neighbor].get('type', None) == 'road':
                nearest_node = neighbor
                min_distance = distance, min_distance
        df.loc[i]['Nearest_Node'] = nearest_node
        if type(df['Floar']) is int:
            df.loc[i]['Population'] = df['Floar'] * 3
        else:
            df.loc[i]['Population'] = 3
    return df




