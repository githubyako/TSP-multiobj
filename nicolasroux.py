import sys
import time
import argparse
import random
import numpy as np

from scipy.special import comb
from tools import *

# parsing command line args

parser = argparse.ArgumentParser()
parser.add_argument('tspfiles', nargs='+', help="Enter the path of at least one tsp file.")
parser.add_argument('--pdominance', type=str, choices=['weak', 'normal', 'strong'], 
	help="Pareto dominance type. Default = normal.")
parser.add_argument("--strategy", type=str, help="One out of \{first,best\}. The algorithm uses both by default.")
args = parser.parse_args()

tsp = readtsp(args.tspfiles[0])
for i,fname in enumerate(args.tspfiles[1:]):
	tsp = np.concatenate((tsp, readtsp(fname)), axis=1)

if not args.pdominance:
	dominance = "normal"
else:
	dominance = args.pdominance

# pre-calculating distances
print("Pre-calculating distances...")
dists = distance_matrix(tsp)

print("Generating initial solutions...")
#generating initial random solutions
start = time.time()
sols = []
to_pr, pr, to_plot = init_threading(nbthreads=8,strategy=args.strategy,pbnames=args.tspfiles)
for i in range(50):
	sols.append(Solution(problem=tsp, dists=dists, rdm=True, dom=dominance))
	sols[i].evaluate()
	to_pr.put(sols[i])

#Si bi-objectif, affichage des résultats
if len(sols[0].evals) == 2:
	print("Plotting solutions...")
	to_plot.put(list(sols))

print("Iterating...")
#iterating 
try:
	while (time.time() - start < 3600):
		bss = pr.get()
		if bss is None:
			continue
		avant = time.time()
		for sol in sols:
			better = True
			for bs in bss:
				if bs.dominates(sol):
					sols.remove(sol)
					break
				elif sol.dominates(bs):
					bss.remove(bs)
		sols += bss
		for bs in bss:
			to_pr.put(bs)
		
		if len(sols) < 10:
			for sol in sols:
				if not sol.tested:
					to_pr.put(sol)		
		pr.task_done()
		if len(args.tspfiles) == 1:
			print("Best solution cost: ", end = "")
			print(sols[0].evals, end = "\r")
		else:
			a = 1
			print(str(len(sols)) + " non-dominated solution(s) so far...", end = "\r")
		if to_plot.qsize() == 0:
			to_plot.put(list(sols))

except KeyboardInterrupt:
	end = time.time()
	print("\nSearch finished in " + str("{0:.2f}".format(end-start)) + " seconds.")
	with open("output.txt", 'w') as out_file:
		a = 0
		for sol in sols:
			out_file.write(' '.join(str(e) for e in sol.cityorder) + "\n")
			out_file.write(', '.join(str(e) for e in sol.evals) + "\n\n")
		to_plot.put(sols)
	print("Results saved in \"output.txt\"")
	if len(sols[0].evals) == 2:
		print("Graph available in \"scatter_plot.html\"")