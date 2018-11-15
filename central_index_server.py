import argparse
import sys
import threading
import socket
import queue
from concurrent import futures
import json

def get_arguments():
	parser = argparse.ArgumentParser(description="Arguments to run Central Index Server")
	parser.add_argument('-i','--ip',type=str,required=True,action='store',help='Server ip address')
	parser.add_argument('-p','--port',type=int,required=True,action='store',help='Server Port Number')
	return parser.parse_args()

class IndexServer(threading.Thread):

	def __init__(self,id,name,server_ip,server_port):
		threading.Thread.__init__(self)
		self.threadID = id
		self.threadName = name
		self.port = server_port
		self.ip = server_ip
		self.waiting_pool = queue.Queue()  #waiting list of available connections
		self.registered_files = {} #(file,peerids) key value pairs
		self.peer_files = {} #(peerid,files) key value pairs
		self.peer_ports = {} #(port_no, ip) key value pairs

	def listen(self):
		try:
			l_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
			l_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)	#to avoid WAIT_STATE of previously used socket
			l_sock.bind((self.ip,self.port))
			l_sock.listen(10)
			print("listening server up ...")
			while True:
				conn,addr = l_sock.accept()
				self.waiting_pool.put((conn,addr))

		except Exception as e:
			print("[ERROR] Listening server failed: %s",e)
			sys.exit(1)

	def list_files(self):
		try:
			return registered_files.keys()
		except Exception as e:
			print("[ERROR] File listing error:",e)

	def register(self,addr,port,files):
		try:
			peerID = addr[0]+":"+str(port)
			self.peer_files[peerID] = files 
			self.peer_ports[port] = addr[0]
			for file in files:
				if file in self.registered_files:
					self.registered_files[file].append(peerID)
				else:
					self.registered_files[file] = [peerID]
			return True
		except Exception as e:
			print("[ERROR] Peer registration error:",e)
			return False

	def search(self, file):
		try:
			if file in self.registered_files:
				peers = registered_files[file]
			else:
				peers=[]
			return peers
		except Exception as e:
			print("[ERROR] File searching error:",e)

	def deregister(self,request):
		try:
			peer_id = request['peer_id']
			files = request['files']
			port = request['hosting_port']

			for file in files:
				if file in self.registered_files:
					for pid in self.registered_files[file]:
						if pid==peer_id:
							self.registered_files[file].remove(peer_id)
							if len(self.registered_files[file])==0:
								self.registered_files.pop(file,None)

			if peer_id in peer_files:
				self.peer_files.pop(peer_id,None)

			if port in peer_ports:
				self.peer_ports.pop(port,None)

			return True

		except Exception as e:
			print("[ERROR] Deregister error:",e)
			return False


	def update(self, request):
		try:
			task = request['task']
			peer_id = request['peer_id']
			files = request['files']

			if task=='remove':
				for file in files:
					self.peer_files[peer_id].remove(file)
					if file in self.registered_files:
						for pid in self.registered_files[file]:
							if pid==peer_id:
								self.reistered_files[file].remove(peer_id)
								if len(self.registered_files[file])==0:
									self.registered_files.pop(file,None)
			elif task=='add':
				for file in files:
					self.peer_files[peer_id].append(file)
					if file in self.registered_files:
						self.registered_files[file].append(str(peer_id))
					else:
						self.registered_files[file] = [str(peer_id)]

			return True

		except Exception as e:
			print("File update error:",e)
			return False



	def run(self):
		try:
			listener = threading.Thread(target=self.listen)
			listener.setDaemon(True)
			listener.start()
			print("Listener thread started running ...")

			while True:
				while not self.waiting_pool.empty():
					with futures.ThreadPoolExecutor(max_workers=4) as worker:
						conn, addr = self.waiting_pool.get()
						msg_received = json.loads(conn.recv(1024))
						command = msg_received['command']
						print("Connection established from host {}:{} with request {}".format(addr[0],addr[1],command))

						if command == 'register':
							executor = worker.submit(self.register, addr,msg_received['peer_port'],msg_received['files'])
							res = executor.result(timeout=None)
							if res:
								print("Registration successful for peer {}:{}".format(addr[0],msg_received['peer_port']))
							else:
								print("Registration unsuccessful for peer {}:{}".format(addr[0],msg_received['peer_port']))

							conn.send(json.dumps([addr[0],res]).encode())

						elif command == 'deregister':
							executor = worker.submit(self.deregister,msg_received)
							res = executor.result(timeout=None)
							if res:
								print("Deregistration successful for peer {}:{}".format(addr[0],msg_received['peer_port']))
							else:
								print("Deregistration unsuccessful for peer {}:{}".format(addr[0],msg_received['peer_port']))

							conn.send(json.dumps(res))

						elif command == 'list':
							executor = worker.submit(self.list_files)
							files = executor.result(timeout=None)
							print("Files found, {}".format(files))
							conn.send(json.dumps(files))

						elif command == 'search':
							executor = worker.submit(self.search, msg_received['file_name'])
							peers = executor.result(timeout=None)
							print("Peers found, {}".format(peers))
							conn.send(json.dumps(peers))

						elif command == 'update':
							executor = worker.submit(self.update,msg_received)
							res = executor.result(timeout=None)
							if res:
								print("update successfull for peer {}".format(msg_received['peer_id']))
							else:
								print("update unsuccessfull for peer {}".format(msg_received['peer_id']))

							conn.send(json.dumps(res))

						print("Registered files || {}".format(self.registered_files))
						print("Peer ports || {}".format(self.peer_ports))
						print("Peer Files || {}".format(self.peer_files))

		except Exception as e:
			print("[ERROR] Index Server Error: {}".format(e))
			sys.exit(1)


if __name__ == '__main__':
	
	try:
		args = get_arguments()
		print("Creating Index Server Thread...")
		server_thread = IndexServer(1,"server",args.ip,args.port)
		server_thread.start()
		while True:
			a=0

	except Exception as e:
		print("[ERROR] main error: {}".format(e))
		sys.exit(1)
