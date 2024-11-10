import numpy as np
import pandas as pd
import networkx as nx
from pykrige.ok import OrdinaryKriging
from geopy.distance import geodesic
import matplotlib.pyplot as plt

# === 1. Подготовка данных ===

# Данные о дорожной сети (узлы и рёбра)
nodes_data = pd.DataFrame({
    'node_id': [1, 2, 3, 4],
    'x': [100, 200, 300, 400],  # Координата x (долгота)
    'y': [100, 200, 300, 400]   # Координата y (широта)
})

edges_data = pd.DataFrame({
    'start_node': [1, 2, 3],
    'end_node': [2, 3, 4],
    'traffic': [50, 80, 60]     # Трафик на каждом участке дороги
})

# Данные о точках интереса (например, школы или больницы)
points_of_interest = pd.DataFrame({
    'poi_id': [1, 2],
    'x': [150, 350],
    'y': [150, 350]
})

# === 2. Создание графа дорожной сети ===

G = nx.Graph()

# Добавляем узлы в граф
for _, row in nodes_data.iterrows():
    G.add_node(row['node_id'], pos=(row['x'], row['y']))

# Добавляем рёбра в граф
for _, row in edges_data.iterrows():
    G.add_edge(row['start_node'], row['end_node'], traffic=row['traffic'])

# === 3. Построение модели кригинга ===

# Извлечение координат и значений трафика для кригинга
x_coords = nodes_data['x'].values
y_coords = nodes_data['y'].values
traffic_data = edges_data['traffic'].values

# Создание модели кригинга
ok = OrdinaryKriging(
    x_coords, y_coords, traffic_data,
    variogram_model="linear",
    verbose=False,
    enable_plotting=False
)

# === 4. Интерполяция трафика на потенциальных новых дорожках ===

# Задаем сетку координат для предсказания значений
gridx = np.linspace(0, 500, 100)
gridy = np.linspace(0, 500, 100)

# Выполняем интерполяцию кригинга
z, ss = ok.execute("grid", gridx, gridy)

# Визуализация предсказаний
plt.imshow(z, origin="lower", extent=(0, 500, 0, 500))
plt.scatter(points_of_interest['x'], points_of_interest['y'], color='red', label='POI')
plt.colorbar(label="Предсказанный трафик")
plt.legend()
plt.title("Карта предсказанного трафика для новых дорожек")
plt.xlabel("Долгота")
plt.ylabel("Широта")
plt.show()

# === 5. Добавление новых дорожек в граф ===

# Добавляем новый узел и ребро на основе предсказаний кригинга
new_node_id = max(nodes_data['node_id']) + 1
G.add_node(new_node_id, pos=(250, 250))  # Пример новой точки с координатами (250, 250)
G.add_edge(2, new_node_id, traffic=70)   # Пример нового ребра с предсказанным трафиком

# === 6. Пересчёт детур индекса ===

def calculate_detour_index(graph, source, target, weight='traffic'):
    """
    Рассчитывает детур индекс между двумя узлами в графе.
    """
    try:
        network_distance = nx.shortest_path_length(graph, source=source, target=target, weight=weight)
        source_coords = (graph.nodes[source]['pos'][1], graph.nodes[source]['pos'][0])
        target_coords = (graph.nodes[target]['pos'][1], graph.nodes[target]['pos'][0])
        euclidean_distance = geodesic(source_coords, target_coords).meters
        return network_distance / euclidean_distance
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None

# Пример расчёта детур индекса для нового пути
source_node = 1
target_node = new_node_id
detour_index = calculate_detour_index(G, source_node, target_node)
print(f"Детур индекс между узлами {source_node} и {target_node}: {detour_index}")
