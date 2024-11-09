import momepy
from momepy.datasets import get_path
import geopandas as gpd
import networkx as nx


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

    return G_largest

def add_nodes_to_graph(G, path, **kwarg):
    """
    Добавляем вершины в граф дорог(метро, остановки, школы)
    :param G: граф дорог
    :param path: путь до файла .shp
    :param kwarg: словарь с id, формой, названием, типом вершины
    :return: новый граф
    """



