import sys
import re
import random
import time
import numpy as np
import math
import threading
from queue import Queue
from scipy.spatial import distance
import plotly
from plotly.graph_objs import Scatter, Layout

compcounter = 0


class Solution():
	def __init__(self, problem=None,order=None, rdm=False, dom="normal", evals=None,dists=None):
		if problem is not None:
			self.dom=dom
			self.problem = problem
			self.dists = dists
			self.tested = False
			if order is not None: self.cityorder = order.copy()
			else: self.cityorder = np.arange(problem.shape[0], dtype=np.int32)
			if rdm : np.random.shuffle(self.cityorder)
			if evals is None: self.evals = []
			else: self.evals = evals.copy()
		else:
			raise ValueError("Please provide a valid problem.")
				
	
	def dominates(self,sol):
		global compcounter
		compcounter += 1
		r, strict = True, False
		if self.dom == "weak":
			for pb in range(len(self.evals)):
				r &= (self.evals[pb] <= sol.evals[pb])
			return r
		elif self.dom == "normal":
			strict = False
			for pb in range(len(self.evals)):
				r &= (self.evals[pb] <= sol.evals[pb])
				strict |= (self.evals[pb] < sol.evals[pb])
			return r and strict
		elif self.dom == "strong":
			for pb in range(len(self.evals)):
				r &= (self.evals[pb] < sol.evals[pb])
			return r

	def evaluate(self):
		"""
		returns the path's total distance
		"""
		self.evals=[]
		for pb in range((int)(self.problem.shape[1]/2)):
			r = 0.0
			# using pre-calculated distance matrix:
			for i in range(len(self.cityorder)-1):
				r += self.dists[pb][self.cityorder[i]][self.cityorder[i+1]]
			
			"""
			# online calculation of distances
			for i in range(len(self.cityorder)): # i = rank of city, c = city id
				coords1 = self.problem[self.cityorder[i]][2*pb:2*pb+2] #current city coords (starting from the 2nd city)
				coords2 = self.problem[self.cityorder[i-1]][2*pb:2*pb+2] #last city coords
				#r += np.linalg.norm(coords1 - coords2) # total distance += distance between those two cities
				r += distance.euclidean(coords1, coords2)
			"""

			self.evals.append(r)
		return self.evals
	
	def evaluate_limited(self, btm, top):
		for pb in range((int)(self.problem.shape[1]/2)):
			coords1 = self.problem[self.cityorder[btm-1]][2*pb:2*pb+2]
			coords2 = self.problem[self.cityorder[top-1]][(2*pb):(2*pb)+2]
			coords3 = self.problem[self.cityorder[btm]][2*pb:2*pb+2]
			coords4 = self.problem[self.cityorder[top]][(2*pb):(2*pb)+2]	
			if btm > 0:
				self.evals[pb] += distance.euclidean(coords1, coords3)
				self.evals[pb] -= distance.euclidean(coords1, coords2)
			if top < len(self.cityorder) - 2:
				self.evals[pb] -= distance.euclidean(coords3, coords4)
				self.evals[pb] += distance.euclidean(coords2, coords4)
			
			#print(temp, end = " ")
			"""
			if btm > 0:
				self.evals[pb] += self.dists[pb][self.cityorder[btm-1]-1][self.cityorder[btm]-1]
				self.evals[pb] -= self.dists[pb][self.cityorder[btm-1]-1][self.cityorder[top-1]-1]
			if top < len(self.cityorder) - 2:
				self.evals[pb] -= self.dists[pb][self.cityorder[btm]-1][self.cityorder[top]-1]
				self.evals[pb] += self.dists[pb][self.cityorder[top-1]-1][self.cityorder[top]-1]
			"""

		return self.evals
		


def opt_2(sol,pos1,pos2):
	"""
	Inverts the sequence located from pos1 to pos2 in sol.cityorder
	"""
	btm = min(pos1,pos2)
	top = max(pos1,pos2)		
	subarray = sol.cityorder[btm:top][::-1] # extract and reverse the sequence
	solordercopy = sol.cityorder.copy()
	solordercopy[btm:top] = list(subarray)
	solcopy = Solution(rdm=False, order=solordercopy, problem=sol.problem, evals=sol.evals, dists=sol.dists, dom=sol.dom)
	solcopy.evaluate_limited(btm,top)
	

	return solcopy


def readtsp(filename):
	"""
	reads a tsp file and extracts
	"""
	prog = re.compile("\d")
	with open(filename, "r") as file:
		cities = []
		rows = file.read().splitlines()
		for i, row in enumerate(rows):
			if prog.match(row):
				cities.append(np.fromstring(" ".join(row.split(" ")[1:]), dtype=np.int32, sep=" "))
	return np.asarray(cities)

def getBetterNeighbor(inq,outq,strategy):
	"""
	Randomly tries 2_opt until all possibilities have been exhausted.
	opt_2() and evaluate() operations at tried at most (2 choose number of cities) times.
	"""	
	while True:
		sol = inq.get()
		if sol.tested:
			outq.put([])
			inq.task_done()
			inq.put(sol)
			time.sleep(0.1)
			continue
		betternbs = []
		pos1list = [i for i in range(sol.cityorder.size-1)]
		pos2list = [j for j in range(1,sol.cityorder.size)]
		better = False

		# randomisation des positions à envoyer à 2_opt, permet d'éviter un biais de recherche
		random.shuffle(pos1list)
		random.shuffle(pos2list)
		for i in pos1list:
			if i in pos2list:
				pos2list.remove(i)
			for j in pos2list:
				better = False
				neighbor = opt_2(sol,i,j)
				if neighbor.dominates(sol):
					better = True
					if strategy == "first": # stratégie == premier améliorant, on a trouvé, on arrête la recherche
						betternbs.append(neighbor)
						break
					for bn in betternbs: # stratégie == meilleur améliorant, on compare aux autres voisins
						if bn.dominates(neighbor):
							better = False
						elif neighbor.dominates(bn):
							betternbs.remove(bn)
					if better:
						betternbs.append(neighbor)
			if better and strategy == "first":
				break
		outq.put(betternbs)
		if strategy == "best":
			sol.tested = True
		inq.task_done()

def init_threading(nbthreads=1,strategy=None,pbnames=None):
	to_process = Queue()
	processed = Queue()
	to_plot = Queue()
	if not strategy:
		s1,s2 = "best","first"
	else:
		s1,s2 = strategy,strategy
	for i in range(math.ceil(nbthreads/2)):
		t = threading.Thread(target=getBetterNeighbor, args=(to_process, processed, "best"))
		t.daemon = True
		t.start()
	for i in range(math.ceil(nbthreads/2)):
		t = threading.Thread(target=getBetterNeighbor, args=(to_process, processed, "first"))
		t.daemon = True
		t.start()
	t = threading.Thread(target=plot_solutions, args=(to_plot,pbnames))
	t.daemon = True
	t.start()
	return to_process, processed, to_plot

def distance_matrix(problem):
	dists = []
	counter = 0
	for pb in range((int)(problem.shape[1]/2)):
		dists.append([])
		pos1list = [i for i in range(problem.shape[0])]
		pos2list = [j for j in range(problem.shape[0])]
		for i in pos1list:
			dists[pb].append([])
			coords1 = problem[i][2*pb:2*pb+2]
			for j in pos2list:
				coords2 = problem[j][2*pb:2*pb+2]
				dists[pb][i].append(distance.euclidean(coords1, coords2))
				counter += 1
	return dists

def plot_solutions(plotqueue, pbnames):
	openweb=True
	while True:
		try:
			sols = plotqueue.get()
			if len(sols[0].evals) == 2:
				trace = Scatter(
				    x = [sol.evals[0] for sol in sols],
				    y = [sol.evals[1] for sol in sols],
				    mode = 'markers'
				)
				plotly.offline.plot({
				    "data": [trace],
				    "layout": Layout(title="Pareto front for TSP instances " + pbnames[0] + " and " + pbnames[1])
				},output_type="file",filename="scatter_plot.html",auto_open=openweb)
				openweb = False
			plotqueue.task_done()
		except:
			plotqueue.task_done()
