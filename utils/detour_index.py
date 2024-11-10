import networkx as nx
from geopy.distance import geodesic


def calculate_detour_index(graph, source, target, weight='length'):
    """
    Рассчитывает детур индекс между двумя узлами в графе дорожной сети.

    Параметры:
        graph (networkx.Graph): Граф, представляющий дорожную сеть.
        source (node): Исходный узел.
        target (node): Конечный узел.
        weight (str): Атрибут рёбер, используемый как вес для расчета кратчайшего пути (например, 'length').

    Возвращает:
        float: Детур индекс или None, если путь не существует.
    """
    try:
        # Рассчитываем длину кратчайшего пути в графе
        network_distance = nx.shortest_path_length(graph, source=source, target=target, weight=weight)

        # Рассчитываем евклидово расстояние на основе координат
        source_coords = (graph.nodes[source]['y'], graph.nodes[source]['x'])
        target_coords = (graph.nodes[target]['y'], graph.nodes[target]['x'])
        euclidean_distance = geodesic(source_coords, target_coords).meters

        # Рассчитываем детур индекс
        detour_index = network_distance / euclidean_distance
        return detour_index

    except (nx.NetworkXNoPath, nx.NodeNotFound):
        # Если пути нет или узлы не найдены, возвращаем None
        return None
