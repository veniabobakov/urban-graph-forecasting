import momepy
from momepy.datasets import get_path
import geopandas as gpd
import networkx as nx
from geopy.distance import geodesic
from shapely.geometry import Point
from rtree import index
import tqdm

'''
Количество квартир умножаем на коэффициент 3
15% - дети и пенсионеры(передвижение внутри района)
30% - взрослые(передвижение на личном транспорте вне района)
45% - взрослые(передвижение на ОТ вне района)
10% - взрослые(используют каршеринг, СИМ)
'''


def balance_dict(values):
    """
    Корректирует значения словаря так, чтобы их сумма была равна нулю,
    добавляя равномерно распределенную разницу к каждому значению.

    Args:
        values (dict): Словарь с числовыми значениями.

    Returns:
        dict: Скорректированный словарь с суммой значений, равной нулю.
    """
    total_sum = sum(values.values())

    # Проверка, требуется ли корректировка
    if total_sum != 0:
        adjustment = -total_sum / len(values)
        values = {k: v + adjustment for k, v in values.items()}

    return values


def shortest_path_to_type(graph,
                          start,
                          target_type
                          ):
    # Проходим по всем путям от начальной вершины
    for node in nx.bfs_tree(graph, start):
        # Если достигли вершины с нужным типом, возвращаем путь
        if graph.nodes[node].get('type') == target_type:
            return nx.shortest_path(graph, start, node)[-1]
    return None  # Если такой вершины нет


def create_flow_graph(G,
                      house_dataframe,
                      target_types=('school', 'stop', 'metro'),
                      population_types_summer=None,
                      population_types_winter=None,
                      season=True
                      ):
    """
    Create a flow graph from a house df with counted population and nearest roads
    :param population_types_winter:
    :param population_types_summer:
    :param G:
    :param house_dataframe: датафрейм с ближайшими дорогами для домов
    :param target_types: категории для стоков
    :param season: пересчет в зависимости от погоды
    :return: demands
    """

    if population_types_summer is None:
        population_types_summer = {'school': 0.1,
                                   'stop': 0.25,
                                   'metro': 0.25}
    if population_types_winter is None:
        population_types_winter = {'school': 0.1,
                                   'stop': 0.3,
                                   'metro': 0.3}

    sources = set(house_dataframe['Nearest_Node'].to_list())  # Источники
    sinks = set([node for node, data in G.nodes(data=True) if data['type'] in target_types])  # Стоки
    demands_keys = sources | sinks
    demands = dict.fromkeys(demands_keys, 0)
    for key in tqdm.tqdm(demands_keys):
        near = house_dataframe[house_dataframe['Nearest_Node'] == key]
        near_list = near['Population'].to_list()
        if season:
            demands[key] -= int(sum(near_list) * 0.6)
        else:
            demands[key] -= int(sum(near_list) * 0.5)
        if season:
            population = sum(near['Population'].to_list())
            target_nodes = dict.fromkeys(demands_keys, None)
            for node_type in target_types:
                target_nodes[node_type] = shortest_path_to_type(G, key, node_type)
            for keys in target_types:
                try:
                    demands[target_nodes[keys]] += int(population_types_summer[keys] * population)
                except:
                    pass
        else:
            population = near['Population'].to_list()
            target_nodes = dict.fromkeys(demands_keys, None)
            for node_type in target_types:
                target_nodes[node_type] = shortest_path_to_type(G, key, node_type)
            for keys in target_types:
                demands[target_nodes[keys]] += int(population_types_winter[keys] * population)

    demands = balance_dict(demands)
    return demands

















