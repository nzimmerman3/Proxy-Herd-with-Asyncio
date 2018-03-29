import asyncio
import json
import sys
import time
import functools
import aiohttp

#API Key
# AIzaSyBwhRI0LD4EPBfEm4SjRsEuILreWwra05M
clientDict = {}

class TCP_Protocol(asyncio.Protocol):

	def __init__(self):
		self.transport = None
		self.server_name = "" 
		#self.clientDict = {}
		self.log = ""
		self.logP = None

	def connection_made(self, transport):
		self.transport = transport
		port = transport.get_extra_info('sockname')
		port = port[1]
		if(port == 16725):
			self.server_name = "Goloman"
			self.log = "Goloman.txt"
		elif(port == 16726):
			self.server_name = "Hands"
			self.log = "Hands.txt"
		elif(port == 16727):
			self.server_name = "Holiday"
			self.log = "Holiday.txt"
		elif(port == 16728):
			self.server_name = "Welsh"
			self.log = "Welsh.txt"
		elif(port == 16729):
			self.server_name = "Wilkes"
			self.log= "Wilkes.txt"
		else:
			#error
			exit(-1) #need to fix

		self.logP = open(self.log, "a")#opens file for appending
		self.logP.write("Connection made\n\n")
		self.logP.close()

	def handleTimeDiff(self, ti):
		t = str(time.time() - float(ti))
		if(t[0] != '-'):
			t = "+" + t
		return t


	def geoToCoords(self, coords):
		latS = ""
		lonS = ""
		first = True
		change = False
		for letter in coords:
			if(first == True):
				first = False
				if(letter == '-'):
					latS += letter
			elif(letter == '+'):
				change = True
			elif(letter == '-'):
				change = True
				lonS += letter
			elif(change == False):
				latS += letter
			elif(change == True and (letter == "-" or letter == "+")):
				return ("300", "300")
			else:
				lonS += letter

		return (latS, lonS)

	def validCoord(self, coords):

		convert = self.geoToCoords(coords)
		latS = convert[0]
		lonS = convert[1]

		try:
			lat = float(latS)
			lon = float(lonS)

			if(lat > 90 or lat < -90 or lon > 180 or lon < -180):
				return False
		except ValueError:
			return False
		return True


	def validIAMAT(self, message):
		try:
			if (self.validCoord(message[2]) and float(message[3]) > 0):
				return True
			else:
				return False

		except ValueError:
			return False

	def validWHATSAT(self, message):
		try:
			if(float(message[2]) > 50 or int(message[3]) > 20):
				return False
			else:
				return True
		except ValueError:
			return False


	def checkData(self, message):
		l = len(message)
		if(l == 4):
			if(message[0] == "IAMAT"):
				if(self.validIAMAT(message)):
					return "IAMAT"
				else:
					return "Error"
			elif(message[0] == "WHATSAT"):
				if(self.validWHATSAT(message)):
					return "WHATSAT"
				else:
					return "Error"
			else:
				return "Error"
		elif(l == 6 and message[0] == "AT"):
			return "AT"
		else:
			return "Error"

	async def opener(self, future, response , num):
		await loop.create_connection(functools.partial(ServerHelper, response), '127.0.0.1', num)

	def prop(self, response):
		if(self.server_name == "Goloman"):
			talk = ["Hands", "Holiday", "Wilkes"]
		elif(self.server_name == "Hands"):
			talk = ["Wilkes", "Goloman"]
		elif(self.server_name == "Holiday"):
			talk = ["Welsh", "Wilkes", "Goloman"]
		elif(self.server_name == "Wilkes"):
			talk = ["Goloman", "Hands", "Holiday"]
		else:
			#Welsh
			talk = ["Holiday"]

		portDic = {}
		portDic["Goloman"] = 16725
		portDic["Hands"] = 16726
		portDic["Holiday"] = 16727
		portDic["Wilkes"] = 16729
		portDic["Welsh"] = 16728

		self.logP = open(self.log, "a")

		#if(self.server_name == "Welsh"):
		#	serv = "Holiday"
		#	try:
		#		future = asyncio.Future()
		#		asyncio.ensure_future(self.opener(future, response, portDic[serv]))
				#loop.run_until_complete(future)
		#		self.logP.write("Relay message:" + response + "to server " + serv + "\n\n")

		#	except ConnectionRefusedError:
				#self.logP = open(self.log, "a")
		#		self.logP.write("Failed to connect to server " + serv + " with message:" + response + "\n")
		#		self.logP.close()
		#else:

		for serv in talk:
			try:
				future = asyncio.Future()
				asyncio.ensure_future(self.opener(future, response, portDic[serv]))
				#loop.run_until_complete(future)
				self.logP.write("Relay message:" + response + "to server " + serv + "\n\n")

			except ConnectionRefusedError:
				#self.logP = open(self.log, "a")
				self.logP.write("Failed to connect to server " + serv + " with message:" + response + "\n")
				
		self.logP.close()

		

	#message is already split
	def handleIAMAT(self, dec):
		message = dec.split()
		#format response
		name = self.server_name
		response = "AT " + name + " " + self.handleTimeDiff(message[3]) + " " + message[1] + " " + message[2] + " " + message[3] + "\n"
		self.transport.write((bytes(response, 'utf-8')))
		self.logP = open(self.log, "a")
		self.logP.write("Client:" + dec + "\n")
		self.logP.write("Server:" + response + "\n")
		#self.logP.close()
		t = float(message[3])

		#dict will be (lat, lon, timestamp, response)
		if(message[1] in clientDict):
			if((clientDict[message[1]])[2] < t):
				self.addAtToDic(response)
				#self.logP = open(self.log, "a")
				self.logP.write("Updated client:" + message[1] + "based on " + dec + "\n")
				self.logP.close()

				self.prop(response)
			else:
				self.logP.write("Did not update client:" + message[1] + "based on " + dec + "\n")
				self.logP.close()


		else:
			#self.clientDict[message[1]] = (lat, lon, time, response)
			self.addAtToDic(response)
			self.logP.write("Updated client:" + message[1] + "based on " + dec + "\n")
			self.logP.close()
			self.prop(response)


		#propogate

	async def fetch(self, session, url):
		async with session.get(url) as response:
			return await response.text()

	def handleWHATSAT(self, dec):
		message = dec.split()

		if(message[1] in clientDict):
			future = asyncio.Future()
			asyncio.ensure_future(self.ghelp(future, dec)) #inputs
			self.logP = open(self.log, "a")
			self.logP.write("Handled:" + dec + "\n")
			self.logP.close()

			#log TODO
		else:
			self.logP = open(self.log, "a")
			self.logP.write("Recieved WHATSAT from invalid user:" + dec + "\n")
			self.logP.close()
			self.transport.write(bytes("?\n", 'utf-8'))


	def format(self, response, maxResults):
		j = json.loads(response)
		places = j["results"][: maxResults]
		j["results"] = places
		return json.dumps(places, indent = 3)


	#async def opener(self, future, response , num):
		#await loop.create_connection(functools.partial(ServerHelper, response), '127.0.0.1', num)

	async def ghelp(self, future, dec):
		message = dec.split()
		async with aiohttp.ClientSession() as session:
			response = clientDict[message[1]][3]
			google = self.createGoogle(message)
			self.logP = open(self.log, "a")
			self.logP.write("Sent request to Google from " + dec + "\n")
			self.logP.close()
			googleResponse = await(self.fetch(session, google))
			self.logP = open(self.log, "a")
			self.logP.write("Recieved response from Google from " + dec + "\n")
			self.logP.close()
			#response = response + googleResponse
			formatted = self.format(googleResponse, int(message[3]))
			response = response + "\n" + formatted + "\n"

			self.logP = open(self.log, "a")
			self.logP.write("Message:" + formatted)
			self.transport.write(bytes(response, 'utf-8'))
			self.logP.close()

	def addAtToDic(self, dec):
		message = dec.split()
		t = self.geoToCoords(message[4])
		latS = t[0]
		lonS = t[1]
		lat = float(latS)
		lon = float(lonS)
		time = float(message[5])

		clientDict[message[3]] = (lat, lon, time, dec)


	def quickLog(self, message):
		self.logP = open(self.log, "a")
		self.logP.write(message + "\n")
		self.logP.close()

	def handleAT(self, dec):
		#update dic if necessary (time stamp)
		#propogate if updated, if not done TODO
		#log

		message = dec.split()
		time = float(message[5])

		if(message[3] in clientDict):
			if(clientDict[message[3]][2] >= time):
				self.logP = open(self.log, "a")
				self.logP.write("Recieved " + dec)
				self.logP.write("Not Updated" + "\n\n")
				self.logP.close()	

			else:
				self.addAtToDic(dec)
				self.logP = open(self.log, "a")
				self.logP.write("Recieved " + dec)
				self.logP.write("Updated" + "\n\n")
				self.logP.close()
				self.prop(dec)
			
		else:
			self.addAtToDic(dec)
			self.logP = open(self.log, "a")
			self.logP.write("Recieved " + dec + "\n")
			self.logP.write("Updated" + "\n\n")
			self.logP.close()
			self.prop(dec)
			

	def data_received(self, data):
		allData = data.decode()
		allDataList = str(allData).splitlines()

		#dec = data.decode()
		for dec in allDataList:
			message = dec.split()
			typeData = self.checkData(message)
			if(typeData == "Error"):
				self.transport.write(bytes(("? " + dec), 'utf-8'))
			elif(typeData == "IAMAT"):
				self.handleIAMAT(dec)
			elif(typeData == "WHATSAT"):
				self.handleWHATSAT(dec)
			elif(typeData == "AT"):
				self.handleAT(dec)
	#(lat, lon, time, response/AT)
	#https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=-33.8670522,151.1957362&radius=500&key=YOUR_API_KEY
	def createGoogle(self, WHATSAT):
		key = "AIzaSyBwhRI0LD4EPBfEm4SjRsEuILreWwra05M"
		name = WHATSAT[1]
		info = clientDict[name]

		
		lat = info[0]
		lon = info[1]
		radius = WHATSAT[2]
		#maxResults = WHATSAT[3]
		return "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=" + str(lat) + "," +  str(lon) + "&radius=" + str(radius) + "&key=" + key


class ServerHelper(asyncio.Protocol):
	def __init__(self, message):
		self.message = message

	def connection_made(self, transport):
		self.transport = transport
		self.transport.write(self.message.encode())
		self.transport.close()


if __name__ == '__main__':
	server_name = sys.argv[1]
	port_num = 0
	if(server_name == "Goloman"):
		port_num = 16725
	elif(server_name == "Hands"):
		port_num = 16726
	elif(server_name == "Holiday"):
		port_num = 16727
	elif(server_name == "Welsh"):
		port_num = 16728
	elif(server_name == "Wilkes"):
		port_num = 16729
	else:
		exit(1)
	#Goloman only
	#ports 16725-16729

	loop = asyncio.get_event_loop()

	coroutine = loop.create_server(TCP_Protocol,'127.0.0.1', port_num)
	server = loop.run_until_complete(coroutine)

	#for now run until Ctrl+C is pressed

	try:
		loop.run_forever()
	except KeyboardInterrupt:
		pass

	#Close server
	server.close()
	loop.run_until_complete(server.wait_closed())
	loop.close()