from scipy.spatial import distance as dist
from collections import OrderedDict
import numpy as np

from objectEventLogger import ObjectEventLogger

class CentroidTracker():
	def __init__(self, gates, maxDisappeared=30):
		self.nextObjectID = 0
		self.objects = OrderedDict()
		self.disappeared = OrderedDict()
		self.maxDisappeared = maxDisappeared
		self.gates = gates

	def register(self, object):
		self.objects[self.nextObjectID] = object
		self.disappeared[self.nextObjectID] = 0
		self.nextObjectID += 1

	def deregister(self, objectID):
		del self.objects[objectID]
		del self.disappeared[objectID]

	def update(self, objects, eventLogger = None):
		intersectObjID = []

		# controllo se la lista degli oggetti passati è vuota
		if len(objects) == 0:
			# leggo tutta la lista degli oggetti e incremento di 1 tutti gli elementi
			for objectID in list(self.disappeared.keys()):
				self.disappeared[objectID] += 1

				# se un oggetto ha superato il numero massimo di frame consecutivi lo cancello
				if self.disappeared[objectID] > self.maxDisappeared:
					self.deregister(objectID)

			# mi fermo con la gestione degli oggetti
			return (self.objects, intersectObjID)

		# la lista degli oggetti non è vuota creo la mappa dei centroidi
		inputCentroids = np.zeros((len(objects), 4), dtype="int")

		# controllo tutti gli oggetti dentro la lista degli oggetti da tracciare
		for (i, (startX, startY, endX, endY,clazz,confidence)) in enumerate(objects):
			# use the bounding box coordinates to derive the centroid
			cX = int((startX + endX) / 2.0)
			cY = int((startY + endY) / 2.0)
			inputCentroids[i] = (cX, cY,clazz,confidence)

		# se siamo al primo frame senza oggetti tracciati 
		# registro tutti i centroidi 
		if len(self.objects) == 0:
			for i in range(0, len(inputCentroids)):
				self.register(inputCentroids[i])

		# altrimenti sono nel caso in cui degli oggetti sono già stati tracciati
		# provvedo ad abbinarli al vecchio id
		else:
			# ottengo la lista degli id e degli oggetti
			objectIDs = list(self.objects.keys())

			values = self.objects.values()
			values = np.array(list(values))
			objectCentroids = values[:,:2]

			# calcolo le distanze dei centroidi
			D = dist.cdist(objectCentroids, np.array(inputCentroids)[:,:2])
			
			rows = D.min(axis=1).argsort()
			cols = D.argmin(axis=1)[rows]

			# per decidere quali oggetti inserire/aggiornare e cancellare mi traccio tutti
			# gli abbinamenti
			usedRows = set()
			usedCols = set()

			# itero su tutte le righe e colonne
			for (row, col) in zip(rows, cols):
				# se abbiamo già analizzato la riga non serve lavorarla
				if row in usedRows or col in usedCols:
					continue

				# altrimenti prendiamo la riga e resettiamo il contatore
				objectID = objectIDs[row]
				old = self.objects[objectID] 
				new = inputCentroids[col]

				result = self.detectGate(objectID,old,new)
				if result != None and len(result) > 0 and eventLogger != None:
					intersectObjID.append(objectID)
					for r in result:
						eventLogger.logObjectEvent(objClass = r[2], confidence = r[3], gateNumber = r[1], direction = r[4])

				self.objects[objectID] = new

				self.disappeared[objectID] = 0

				# segnamo gli oggetti come selezionati
				usedRows.add(row)
				usedCols.add(col)

			# trovo gli oggetti che non sono stati tracciati prima
			unusedRows = set(range(0, D.shape[0])).difference(usedRows)
			unusedCols = set(range(0, D.shape[1])).difference(usedCols)

			# controllo se sono spariti degli oggetti
			if D.shape[0] >= D.shape[1]:
				# controllo le righe non abbinate
				for row in unusedRows:
					objectID = objectIDs[row]
					self.disappeared[objectID] += 1

					if self.disappeared[objectID] > self.maxDisappeared:
						self.deregister(objectID)

			
			else:
				for col in unusedCols:
					self.register(inputCentroids[col])

		# ritorno la lista degli oggetti tracciati
		return (self.objects, intersectObjID)

	#https://bryceboe.com/2006/10/23/line-segment-intersection-algorithm/
	def ccw(self, a, b, c):
		return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])
	
	def cross(self, s1, s2):
		a, b = s1
		c, d = s2
		return self.ccw(a, c, d) != self.ccw(b, c, d) and self.ccw(a, b, c) != self.ccw(a, b, d)

	def detectGate(self,objectID,old,new):
		# DA NUMPY A OPENCV: "scambio" le x e y
		sx = old[1]
		sy = old[0]
		ex = new[1]
		ey = new[0]

		ss = (sx,sy)
		es = (ex,ey)

		clazz = new[2]
		confidence = new[3]

		intersections = []

		for gate in self.gates:
			sg = gate[0]
			eg = gate[1]
			gn = gate[2]

			if self.cross([sg,eg],[ss,es]):
				direction = 1 if self.ccw(sg, eg, es) else 0
				intersections.append((objectID, gn, clazz, confidence, direction))
				print(objectID, gn, clazz, confidence, direction)

		return intersections

