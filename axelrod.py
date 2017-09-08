#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from igraph import *
import numpy as np
import time

import itertools
import random
import math
import networkx as nx
from networkx.generators.classic import empty_graph, path_graph, complete_graph

#tworzenie grafu regularnego
def regular_graph(N):
	g = Graph()
	g.add_vertices(N)	# wierzcholki
	for i in range(N):	# krawedzie
		g.add_edges([(i,(i+1)%N),(i,(i+2)%N)])
	return g

def regular_graph_matrix(N): # siatka N*N

	g = Graph()

	g.add_vertices(N*N)	# wierzcholkibara

	for i in range(N):	# krawedzie
		for j in range(N-1):
			g.add_edges([(i*N+j,i*N+j+1)])

	for i in range(N-1):	# krawedzie
		for j in range(N):
			g.add_edges([(i*N+j,(i+1)*N+j)])
	return g

def regular_graph_matrix_wrapping_toroid(N):

	g = Graph()

	g.add_vertices(N*N)	# wierzcholki

	for i in range(N):	# krawedzie
		for j in range(N):
			g.add_edges([(i*N+j,i*N+((j+1)%N)),(i*N+j,((i+1)%N)*N+j)])
	return g

def barabasi(N):
	return Graph.Barabasi(N)
def ws(N,praw):
	return Graph.Watts_Strogatz(dim=1, size=N,p=praw,nei=5)

def ke(N,m):
	g = Graph.Full(m)
	active = []
	for i in range(m):
		active.append(i)
	for i in range(m,N):
		g.add_vertices(1)	# 1
		for j in active:	# 2
			g.add_edges([(i,j)])			
		suma = 0
		for j in active:
			suma = suma+1./(g.degree()[j]+m)
		random = np.random.rand()*suma
		suma = 0
		j = 0		
		while suma<=random:
			suma=suma+1./(g.degree()[active[j]]+m)
			j = j+1
		active[j-1]=i
	return g

# losowanie sasiadow z prawdopodobienstwem p
def small_world_generator(g,p,N):
	to_erase = []
	for i in range(len(g.es)): # szuka, ktore do usuniecia i pakuje je do listy
		if np.random.rand()<=p:
			to_erase.append(g.es[i].tuple)

	for i in to_erase:	# usuwa, a potem tworzy nowe, losowe polaczenie
		g.delete_edges(i)
		j = int(np.random.rand()*N)
		while i[0] == j or g.are_connected(i[0], j): # tutaj unikamy autopolaczen i tworzenia drugiego polaczenia w tym samym miejscu
			j = int(np.random.rand()*N)
		g.add_edges([(i[0],j)])
	return g

def load_features(g,F,q,N):
	for i in range(F):
		tab = []
		for j in range(N):
			tab.append(int(np.random.rand()*q)) # losowanie 0...q-1
		g.vs[str(i)]= tab

def axelrod(g,q,F,N):
	frozen_state = False
	n = 0
	number_of_interaction = 0
	number_of_interaction_old = 0
	while (not frozen_state):
		n = n + 1
		# krok 2
		i = int(1.*np.random.rand()*N)
		if g.degree()[i] != 0: # tylko jesli jakas krawedz istnieje
			k = int(1.*np.random.rand()*g.degree()[i])
			j = g.vs[i].neighbors()[k].index
			# krok 2	
			l = 0
			for m in range(F):
				if g.vs[str(m)][i] == g.vs[str(m)][j]:
					l = l + 1
			#print l
			if 0 < l < F:

				if 1.*l/F>np.random.rand():
					number_of_interaction = number_of_interaction + 1				
					c = int(np.random.rand()*F) #wybranie losowej cechy
					while(g.vs[str(c)][i] == g.vs[str(c)][j]): #pod warunkiem, ze nie jest ona cecha wspolna
						c = int(np.random.rand()*F)
					# przepisanie cechy (proste rowna sie nie dzialalo, a tak dziala
					tab = g.vs[str(c)][0:i]
					tab.append(g.vs[str(c)][j])
					tab = tab + g.vs[str(c)][i+1:]
					g.vs[str(c)] = tab
			if (n%100000)==0:
				if number_of_interaction_old == number_of_interaction:
					frozen_state = True
				else:
					number_of_interaction_old = number_of_interaction

def get_domains_size(g,N,q,F):
	def visit(g,a,q,F,visited):
		visited[a] = True
		suma = 1
		for i in range(g.degree()[a]):
			next = g.vs[a].neighbors()[i].index
			w_domenie = True
			for j in range(F):
				if g.vs[str(j)][a] != g.vs[str(j)][next]:
					w_domenie = False
			if w_domenie and not visited[next]:
				suma = suma + visit(g,next,q,F,visited)
		return suma
	result = []	
	visited = []

	for i in range(N):
		visited.append(False)

	for i in range(N):
		if not visited[i]:
			result.append(visit(g,i,q,F,visited))
	return result


# TU ZACZYNA SIE WLASCIWY PROGRAM
if len(sys.argv) != 6:
	print "Program przyjmuje 5 zmiennych, wpisz: python small_world.py N F q p small-world" # dla modelu small-world
else:
	N = int(sys.argv[1])
	F = int(sys.argv[2])
	q = int(sys.argv[3])
	p = float(sys.argv[4])
	x = sys.argv[5]
	
	if x == "small-world":
		g = regular_graph_matrix(N)
		N = N*N
	elif x == "barabasi-albert":
		g = barabasi(N)
	elif x =="klemm-eguiluz":
		g = ke(N,5)

	g = small_world_generator(g,p,N)
	load_features(g,F,q,N)

	axelrod(g,q,F,N)
	print 1.*max(get_domains_size(g,N,q,F))/N, len(get_domains_size(g,N,q,F))#, g.transitivity_undirected()

	# RYSOWANIE
	'''g.vs["label"] = g.vs["1"]
	tab_labels = []
	for i in range(N):	# dodawanie etykiet
		label = ""	
		for j in range(F):
			label = label+str(g.vs[str(j)][i])+"  "
		tab_labels.append(label)
	g.vs["label"]=tab_labels

	plot(g)#, layout = g.layout("circle"))'''
	###########