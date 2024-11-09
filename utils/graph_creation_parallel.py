import momepy
from momepy.datasets import get_path
import geopandas as gpd
import networkx as nx
from geopy.distance import geodesic
from shapely.geometry import Point
from rtree import index


def create_road_graph(path):
    roads = gpd.read_file(path)
    # Преобразуем данные в проекцию, которая использует метры (например, EPSG:32633)
    roads = roads.to_crs(epsg=32633)

    # Фильтрация дорог, где колонка 'Foot' равна 1 (пешеходные дороги)
    roads_filtered = roads[roads['Foot'] == 1]

    # Преобразуем обратно в EPSG:4326 для отображения на карте
    roads_filtered = roads_filtered.to_crs(epsg=4326)
    G = momepy.gdf_to_nx(roads_filtered, multigraph=False)
    components = list(nx.connected_components(G))

    # Находим самую крупную компоненту
    largest_component = max(components, key=len)

    # Создаем новый граф, содержащий только вершины и рёбра самой крупной компоненты
    G_largest = G.subgraph(largest_component).copy()

    for node in G.nodes:
        G.nodes[node]['type'] = 'road'

    return G_largest


def add_nodes_to_graph(G, path, threshold, **kwarg):
    """
    Добавляем вершины в граф дорог (метро, остановки, школы)
    :param threshold: дистанция для присоединения к вершине
    :param G: граф дорог
    :param path: путь до файла .shp
    :param kwarg: словарь с id, формой, названием, типом вершины
        stops : {id: TrStopId, geometry: geometry, name: Name, type: stop}
        metro : {id: Number, geometry: geometry, name: Text, type: metro}
        school : {id: HouseId, geometry: geometry, name: Name, type: school}
    :return: новый граф
    """
    # Загрузим данные из .shp
    df = gpd.read_file(path)
    df = df.to_crs(epsg=4326)

    # Создаем индекс R-tree для всех точек в графе
    idx = index.Index()

    # Добавляем все вершины графа в индекс
    for i, node in enumerate(G.nodes):
        point = node  # точки в графе (x, y)
        idx.insert(i, (point[0], point[1], point[0], point[1]))

    if kwarg['type'] != 'school':
        G = paralell(G, df, threshold, idx, kwarg)

    else:  # для школ
        df = df[df['Type'] == 'Школы']
        df = df.reset_index(drop=True)
        for i in range(len(df)):
            centroid = df.loc[i]['geometry'].centroid  # получаем центр школы
            G.add_node((centroid.x, centroid.y), type=kwarg['type'], name=df.loc[i][kwarg['name']],
                       id=df.loc[i][kwarg['id']])
            print(i)
            # Ищем ближайшие вершины в графе с помощью индекса
            possible_matches_index = list(idx.nearest((centroid.x, centroid.y, centroid.x, centroid.y), 20))

            matches_found = False
            for j in possible_matches_index:
                neighbor = list(G.nodes)[j]
                distance = geodesic((centroid.y, centroid.x), (neighbor[1], neighbor[0])).meters
                if distance < threshold and G.nodes[neighbor].get('type', None) == 'road':
                    G.add_edge((centroid.x, centroid.y), neighbor)
                    matches_found = True

            # Если не нашли, присоединяем ближайшую вершину
            if not matches_found:
                min_distance = float('inf')
                nearest_node = None
                for j in range(len(list(G.nodes))):
                    neighbor = list(G.nodes)[j]
                    distance = geodesic((centroid.y, centroid.x), (neighbor[1], neighbor[0])).meters
                    if distance < min_distance:
                        min_distance = distance
                        nearest_node = neighbor
                if nearest_node:
                    G.add_edge((centroid.x, centroid.y), nearest_node)

    return G


def paralell(G, df, threshold, idx, kwarg):
    for i in range(len(df)):
        point = df.loc[i]['geometry']  # получаем точку для каждого объекта в .shp
        G.add_node((point.x, point.y), type=kwarg['type'], name=df.loc[i][kwarg['name']], id=df.loc[i][kwarg['id']])

        # Ищем ближайшие вершины в графе с помощью индекса
        possible_matches_index = list(idx.nearest((point.x, point.y, point.x, point.y), 20))

        # Смотрим на все вершины, которые находятся в радиусе 100 метров
        matches_found = False  # флаг для проверки, нашли ли подходящие вершины
        for j in possible_matches_index:
            neighbor = list(G.nodes)[j]  # Получаем точку из графа
            distance = geodesic((point.y, point.x), (neighbor[1], neighbor[0])).meters  # Вычисляем расстояние
            if distance < threshold and G.nodes[neighbor].get('type', None) == 'road':
                G.add_edge((point.x, point.y), neighbor)
                matches_found = True  # нашли подходящее ребро

        # Если не нашли, присоединяем ближайшую вершину
        if not matches_found:
            # Ищем ближайшую вершину в графе
            min_distance = float('inf')
            nearest_node = None
            for j in range(len(list(G.nodes))):
                neighbor = list(G.nodes)[j]
                distance = geodesic((point.y, point.x), (neighbor[1], neighbor[0])).meters
                if distance < min_distance:
                    min_distance = distance
                    nearest_node = neighbor
            # Добавляем ближайшее ребро
            if nearest_node:
                G.add_edge((point.x, point.y), nearest_node)
    return G


def paralell_centroid(G, df, threshold, idx, kwarg):
    for i in range(len(df)):
        centroid = df.loc[i]['geometry'].centroid  # получаем центр школы
        G.add_node((centroid.x, centroid.y), type=kwarg['type'], name=df.loc[i][kwarg['name']],
                   id=df.loc[i][kwarg['id']])
        print(i)
        # Ищем ближайшие вершины в графе с помощью индекса
        possible_matches_index = list(idx.nearest((centroid.x, centroid.y, centroid.x, centroid.y), 20))

        matches_found = False
        for j in possible_matches_index:
            neighbor = list(G.nodes)[j]
            distance = geodesic((centroid.y, centroid.x), (neighbor[1], neighbor[0])).meters
            if distance < threshold and G.nodes[neighbor].get('type', None) == 'road':
                G.add_edge((centroid.x, centroid.y), neighbor)
                matches_found = True

        # Если не нашли, присоединяем ближайшую вершину
        if not matches_found:
            min_distance = float('inf')
            nearest_node = None
            for j in range(len(list(G.nodes))):
                neighbor = list(G.nodes)[j]
                distance = geodesic((centroid.y, centroid.x), (neighbor[1], neighbor[0])).meters
                if distance < min_distance:
                    min_distance = distance
                    nearest_node = neighbor
            if nearest_node:
                G.add_edge((centroid.x, centroid.y), nearest_node)
    return G
