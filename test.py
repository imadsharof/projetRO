
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, value, PULP_CBC_CMD
import time
import tkinter as tk
time1 = time.time()

# Fonction qui charge les données à partir des fichiers txt
def load_data(filename):
    with open(filename, 'r') as f:
        data = [[int(value) for value in line.strip()] for line in f.readlines()]
    return data


# Fonction qui crée la matrice usage_map
def create_usage_map_matrix(file_path):
    with open(file_path, 'r') as file:
        lignes = file.readlines()

    matrix = []
    for ligne in lignes:
        matrix_ligne = []
        for c in ligne:
            if c == ' ':
                matrix_ligne.append('')
            elif c == 'R':
                matrix_ligne.append('R')
            elif c == 'C':
                matrix_ligne.append('C')
        matrix.append(matrix_ligne)
        # print(ligne)
    return matrix


### Initalisation de la région : usage_map, cost_map et production_map

usage_map = create_usage_map_matrix("donnes_test/Usage_map_test.txt")
cost_map = load_data("donnes_test/Cost_map_test.txt")
production_map = load_data("donnes_test/Production_map_test.txt")
"""
usage_map = create_usage_map_matrix("donnes_V2/Usage_map.txt")
cost_map = load_data("donnes_V2/Cost_map.txt")
production_map = load_data("donnes_V2/Production_map.txt")
"""
### Indices

ColonneU = len(usage_map[0])
LigneU = len(usage_map)


### Constantes

# Fonction qui crée la matrice route
def create_route_matrix():
    matrix = []
    for l in range(LigneU):
        matrix.append([])
        for c in range(ColonneU):
            if usage_map[l][c] == "R":
                matrix[l].append(1)
            else:
                matrix[l].append(0)
    return matrix


Route = create_route_matrix()


# Fonction qui crée la matrice habitation
def create_habitation_matrix():
    matrix = []
    for l in range(LigneU):
        matrix.append([])
        for c in range(ColonneU):
            if usage_map[l][c] == "C":
                matrix[l].append(1)
            else:
                matrix[l].append(0)
    return matrix


Habitation = create_habitation_matrix()


# Fonction qui crée la matrice de distance
# Forme de l'algorithme de Dijkstra pour permettre de calculer le plus court chemin entre une parcelle et une habitation H
def create_distance_matrix():
    # Étape 1 : Initialiser la matrice de distance avec de grandes valeurs
    D = []
    for l in range(LigneU):
        row = []
        for c in range(ColonneU):
            # Nous commençons avec une grande valeur pour représenter "l'infini"
            row.append(10000)
        D.append(row)

    # Étape 2 : Mettre la distance à 0 pour toutes les cellules habitables
    for l in range(LigneU):
        for c in range(ColonneU):
            if Habitation[l][c] == 1:
                # Si la cellule est habitable, sa distance à elle-même est 0
                D[l][c] = 0

    # Étape 3 : Initialiser la file d'attente avec les cellules habitables
    queue = []
    for l in range(LigneU):
        for c in range(ColonneU):
            if Habitation[l][c] == 1:
                # Si la cellule est habitable, nous l'ajoutons à la file d'attente pour l'explorer plus tard
                queue.append((l, c))

    # Étape 4 : Parcourir la file d'attente et mettre à jour les distances
    while len(queue) > 0:
        # Nous retirons la première cellule de la file d'attente pour l'explorer
        l, c = queue.pop(0)

        # Nous explorons tous les voisins de la cellule actuelle
        for dl, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            # Nous calculons les coordonnées du voisin
            nl, nc = l + dl, c + dc

            # Nous vérifions si le voisin est dans les limites de la grille et n'est pas une route
            if 0 <= nl < LigneU and 0 <= nc < ColonneU and Route[nl][nc] != 1:
                # Nous calculons la distance à travers la cellule actuelle
                new_distance = D[l][c] + 1

                # Si cette nouvelle distance est plus petite que la distance actuelle du voisin, nous mettons à jour la distance du voisin
                if new_distance < D[nl][nc]:
                    D[nl][nc] = new_distance

                    # Nous ajoutons le voisin à la file d'attente pour explorer ses voisins plus tard
                    queue.append((nl, nc))

    # À la fin, D contient la distance minimale de chaque cellule à la cellule habitable la plus proche
    return D


Distance = create_distance_matrix()


def calculate_global_scores(LigneU, ColonneU, production_map, Distance, weight_production, weight_distance):
    production_scores = [[production_map[l][c] for c in range(ColonneU)] for l in range(LigneU)]
    distance_scores = [[Distance[l][c] for c in range(ColonneU)] for l in range(LigneU)]
    global_scores = [[weight_production * production_scores[l][c] - weight_distance * distance_scores[l][c]
                      for c in range(ColonneU)] for l in range(LigneU)]
    return global_scores


def is_adjacent(parcelle1, parcelle2):

    l1, c1 = parcelle1
    l2, c2 = parcelle2
    return (l1 == l2 and abs(c1 - c2) == 1) or (c1 == c2 and abs(l1 - l2) == 1)


def calculate_adjacent_passerelles(LigneU, ColonneU, Route, parcelle):
    l, c = parcelle
    adjacent_passerelles = 0
    if l > 0 and Route[l - 1][c] == 1:
        adjacent_passerelles += 1
    if l < LigneU - 1 and Route[l + 1][c] == 1:
        adjacent_passerelles += 1
    if c > 0 and Route[l][c - 1] == 1:
        adjacent_passerelles += 1
    if c < ColonneU - 1 and Route[l][c + 1] == 1:
        adjacent_passerelles += 1
    return adjacent_passerelles


def purchase_parcelles(LigneU, ColonneU, global_scores, Route, Habitation, cost_map, budget, costed, sorted_parcelles, purchased_parcelles):
    total_cost = costed
    total_adjacent_passerelles = 0

    for parcelle in sorted_parcelles:
        l, c = parcelle
        cost = cost_map[l][c]

        adjacent_to_purchased = any(is_adjacent(parcelle, purchased) for purchased in purchased_parcelles)

        if Route[l][c] == 0 and Habitation[l][c] == 0:
            if total_cost + cost <= budget and adjacent_to_purchased:
                purchased_parcelles.append(parcelle)
                total_cost += cost
                total_adjacent_passerelles += calculate_adjacent_passerelles(LigneU, ColonneU, Route, parcelle)

    return purchased_parcelles, total_cost, total_adjacent_passerelles
def purchasefirst(sorted_parcelles,parcelle, list_of_first):
    costed = 0
    l,c = parcelle
    cost = cost_map[l][c]
    if Route[l][c] == 0 and Habitation[l][c] == 0:
        if cost <= budget:
            list_of_first.append(parcelle)
            costed += cost

    return list_of_first, costed

def calculate_compacite(tuples_list):
    adjacent_count = 0
    total_count = len(tuples_list)

    for tpl in tuples_list:
        row, col = tpl
        adjacent_tuples = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
        for adjacent_tpl in adjacent_tuples:
            if adjacent_tpl in tuples_list:
                adjacent_count += 1

    if total_count > 0:
        compacite = adjacent_count / total_count
    else:
        compacite = 0

    return compacite*5
def solve_land_purchasing_problem(LigneU, ColonneU, production_map, Distance, Route, Habitation, cost_map, budget,
                                  weight_production, weight_distance, weight_compactness):
    global_scores = calculate_global_scores(LigneU, ColonneU, production_map, Distance, weight_production, weight_distance)

    ranked_parcelles = [(l, c) for l in range(LigneU) for c in range(ColonneU)]
    sorted_parcelles = sorted(ranked_parcelles, key=lambda p: global_scores[p[0]][p[1]], reverse=True)
    count =0
    zone = []
    list_of_first = []
    for parcelle in sorted_parcelles:
        count += 1
        l,c = parcelle
        if count < 100000:
            if Route[l][c] == 0 and Habitation[l][c] == 0:
                list_of_first, costed = purchasefirst(sorted_parcelles, parcelle, list_of_first)
        else:
            break

    for i in range(len(list_of_first)):

        purchased_parcelles, total_cost, total_adjacent_passerelles = purchase_parcelles(LigneU, ColonneU, global_scores, Route, Habitation, cost_map, budget, costed, sorted_parcelles, [list_of_first[i]])
        zone.append(purchased_parcelles)


    print("zone achetées:")
    list_of_scorezone=[]
    for x in zone:
        total_score=0
        total_zone_cost = 0
        for parcelle in x:
            l, c = parcelle
            score = global_scores[l][c]
            total_score += score
            total_zone_cost+= cost_map[l][c]
        total_score += weight_compactness * calculate_compacite(x)
        list_of_scorezone.append((zone.index(x),total_score, total_zone_cost))
        sorted_list_of_scorezone = sorted(list_of_scorezone, key=lambda x: x[1], reverse=True)


    for parcelle in zone[sorted_list_of_scorezone[0][0]]:
        l,c = parcelle
        usage_map[l][c] = 'A'
    for i in range(len(sorted_list_of_scorezone)):
        print(f"zone({i})")
        print(zone[sorted_list_of_scorezone[i][0]])
        print("score de zone: ", sorted_list_of_scorezone[i][1])
        print("prix de la zone: ", sorted_list_of_scorezone[i][2])



weight_production = 1
weight_distance = 1
weight_compactness = 1
budget = 50

solve_land_purchasing_problem(LigneU, ColonneU, production_map, Distance, Route, Habitation, cost_map, budget,
                              weight_production, weight_distance, weight_compactness)
time2 = time.time()
print("time: ", time2-time1)
color_mapping = {
    'C': 'blue',
    'R': 'gray',
    'A': 'red',
    '': 'black'
}


def draw_grid(matrix):
    root = tk.Tk()
    root.title("Grid")

    # Calcul de la taille de la grille en fonction de la matrice
    rows = len(matrix)
    cols = len(matrix[0])

    # Taille des carrés de la grille
    square_size = 1200 / len(matrix[0])

    # Création du canevas
    canvas = tk.Canvas(root, width=cols * square_size, height=rows * square_size)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Création de la barre de défilement verticale
    yscrollbar = tk.Scrollbar(root, orient=tk.VERTICAL, command=canvas.yview)
    yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Création de la barre de défilement horizontale
    xscrollbar = tk.Scrollbar(root, orient=tk.HORIZONTAL, command=canvas.xview)
    xscrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    # Configuration du canevas pour prendre en compte les défilements
    canvas.configure(yscrollcommand=yscrollbar.set, xscrollcommand=xscrollbar.set)
    canvas.configure(scrollregion=canvas.bbox(tk.ALL))

    # Parcours de la matrice et dessin des éléments
    for row in range(rows):
        for col in range(cols):
            element = matrix[row][col]
            color = color_mapping.get(element, 'black')

            # Dessin d'un rectangle avec la couleur correspondante
            canvas.create_rectangle(col * square_size, row * square_size, (col + 1) * square_size,
                                    (row + 1) * square_size, fill=color)

    root.mainloop()


draw_grid(usage_map)
