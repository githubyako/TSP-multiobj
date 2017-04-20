Nicolas Roux


____________________________________

PRESENTATION
____________________________________


Cet algorithme sert à la résolution mono ou multi-objectifs du problème du voyageur de commerce.

Il comprend:

1) Lecture du (des) fichiers .tsp

2) Calcul unique des distances entre chaque paire de ville, problème par problème

3) Création d'une solution aléatoire

4) Enumération des solutions voisines via l'opérateur 2_opt

5) Choix de la dominance de Pareto à utiliser: "weak", "normal" ou "strong"

6) Choix de stratégie d'exploration: 
	"first" pour "premier améliorant"
		==> renvoie la première solution non dominée trouvée
		==> trouve rapidement un (mais un seul) optimum local
	"best" pour "meilleur améliorant"
		==> pour un problème multi-objectifs, renvoie un ensemble de solutions non-dominées
		==> trouve moins rapidement un front de Pareto de taille convenable
	[aucun]
		==> mélange des deux stratégies énoncées ci-dessus.

	Note: comme souvent en optimisation combinatoire, la quête d'un bon optimum nécessite un compromis intensification / exploration, notions ici incarnées par les deux stratégies d'exploration.
	La combinaison des deux stratégies offre ici le meilleur compromis temps de calcul / qualité des solutions.
	A la manière des algorithmes adaptatifs (AGA par ex.), il serait envisageable de déterminer dynamiquement quelle stratégie utiliser, mais ceci sort largement du sujet.

7) Filtrage: Le filtrage des solutions (cf domination de Pareto) en multi-objectif s'effectue à deux niveaux: 
	Un premier filtre agressif dans l'évaluation des voisins d'une solution (via 2_opt) s'assure que chaque solution voisine considérée domine la solution initiale, sinon cette solution voisine est rejetée. Elle est aussi comparée aux autres solutions voisines trouvées jusque là, est rejetée si elle est dominée, et chaque autre voisin est rejeté s'il est dominé.
	Il est envisageable d'assouplir ce filtre en ne requiérant pas que la solution voisine domine la solution initiale.

	La recherche de voisins (fonction getBetterNeighbor) est effectuée de façon simultanée sur plusieurs solutions, il faut donc s'assurer de la cohérence entre les solutions conservées et celles renvoyées par les différentes recherches locales, d'où la nécessité d'un second filtre:
	
	Un second filtre s'applique lorsque l'on essaye d'intégrer les solutions renvoyées par une instance de recherche locale à l'ensemble général de solutions.
	Ce second filtre supprime toutes les solutions dominées, dans un sens ou dans l'autre (solution existante dominée par un voisin d'une solution, ou bien voisin d'une solution dominé par une solution existante).

	Ce système de filtrage semble parfois légèrement dysfonctionner (sans impact notable sur la recherche en général), permettant à des solutions de moindre qualité d'être brièvement conservées à tord, probablement au niveau du second filtre.

8) Fonction d'évaluation "améliorée", utilisant les propriétés de 2_opt pour drastiquement réduire le nombre de calculs à effectuer.

9) Visualisation graphique des résultats pour un problème bi-objectif. Il est recommandé de lancer Firefox avant d'exécuter le script pour éviter de voir les logs d'erreurs de Firefox s'afficher dans le terminal.

____________________________________

PREREQUIS LOGICIELS
____________________________________
python3 (testé sous 3.5)

Modules python3:

numpy (pip3 install numpy)
scipy (pip3 install scipy)
plotly (pip3 install plotly)
argparse (pip3 install argparse)
____________________________________

USAGE
____________________________________

python3.5 nicolasroux.py [tsp file 1] [tsp file 2] ... [tsp file n]

Dominance types:
	weak, normal, strong

Arguments optionnels:
	--strategy {first, best}
	--pdominance {weak, normal, strong}

	==> si aucune stratégie n'est spécifiée, un mélange des deux est utilisé.
	==> si aucune dominance n'est spécifiée, la dominance "normale" est utilisée.

Exemples:

python3.5 nicolasroux.py kroA100.tsp

python3.5 nicolasroux.py kroC100.tsp kroB100.tsp

python3.5 nicolasroux.py kroC100.tsp kroB100.tsp --strategy best --pdominance strong
