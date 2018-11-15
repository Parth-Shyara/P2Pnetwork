import socket 
import argparse
import os
import sys
import json
import time
import threading
from Queue import Queue
from concurrent import futures

PUBLIC_DIR = "./Public-Files"

def get_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--ip', type = str , required = True, action = 'store', help='Central Server IP address')
	parser.add_argument('-p', '--port', type = int, required = True, action = 'store', help='Central Server port number')
	args = parser.parse_args()
	return args


class PeerOperations(threading.Thread):

	def __init__(self, threadid, name, peer):
		threading.Thread.__init__(self)
		self.threadid = threadid
		self.name = name
		self.peer = peer
		self.listener_queue = Queue()

	def get_my_ip(self):
		s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect(("8.8.8.8", 80))
		return s.getsockname()[0]

	def listener(self):
		try:
			listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			listener_host = self.get_my_ip()
			# listener_host = '10.42.0.54'
			# print '$$$$$$  ', listener_host
			listener_port = self.peer.host_port
			listener_socket.bind((listener_host,listener_port))
			listener_socket.listen(8)

			while True:
				conn, addr = listener_socket.accept()
				self.listener_queue.put((conn,addr))
		except Exception as e:
			print 'Listener on port failed: ', e
			sys.exit(1)

	def upload(self,conn,recv_data):
		try:
			file = open(PUBLIC_DIR+'/'+recv_data['file_name'],'rb')
			data = file.read()
			conn.sendall(data)
			conn.close()

		except Exception as e:
			print 'File Upload error : ', e

	def host(self):
		try:
			while True:
				while not self.listener_queue.empty():
					with futures.ThreadPoolExecutor(max_workers=4) as executor:
						conn, addr = self.listener_queue.get()
						recv_data = json.loads(conn.recv(1024))
						# print recv_data
						temp = executor.submit(self.upload, conn, recv_data)
		except Exception as e:
			print 'Hosting error : ', e

	def server(self):
		try:
			print 'peer server starting......'
			listener_thread = threading.Thread(target=self.listener)
			listener_thread.setDaemon(True)

			op_thread = threading.Thread(target=self.host)
			op_thread.setDaemon(True)

			listener_thread.start()
			op_thread.start()

			threads = []
			threads.append(listener_thread)
			threads.append(op_thread)

			for thread in threads:
				thread.join()
		except Exception as e:
			print 'Server error ', e
			sys.exit(1)

	def file_handler(self):
		try:
			while True:
				curr_filelist = []
				for file in os.listdir(PUBLIC_DIR):
					curr_filelist.append(file)

				# print curr_filelist, self.peer.file_list
				added_files = list(set(curr_filelist)-set(self.peer.file_list))

				removed_files = list(set(self.peer.file_list)-set(curr_filelist))
				# print added_files, removed_files

				if len(added_files) > 0:
					peer_to_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					peer_to_server_socket.setsockopt(
						socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
					peer_to_server_socket.connect(
						(self.peer.server_ip, self.peer.server_port))

					cmd_issue = {
						'command' : 'update',
						'task' : 'add',
						'peer_id' : self.peer.peer_id,
						'files' : added_files,
					}
					peer_to_server_socket.sendall(json.dumps(cmd_issue))
					rcv_data = json.loads(peer_to_server_socket.recv(1024))
					peer_to_server_socket.close()
					if rcv_data:
						print "File Update of Peer: %s on server successful" %(self.peer.peer_id)
					else:
						print "File Update of Peer: %s on server unsuccessful" % (self.peer.peer_id)

				if len(removed_files) > 0:
					peer_to_server_socket = \
						socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					peer_to_server_socket.setsockopt(
						socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
					peer_to_server_socket.connect(
						(self.peer.server_ip, self.peer.server_port))

					cmd_issue = {
						'command' : 'update',
						'task' : 'rm',
						'peer_id' : self.peer.peer_id,
						'files' : removed_files,
					}
					peer_to_server_socket.sendall(json.dumps(cmd_issue))
					rcv_data = json.loads(peer_to_server_socket.recv(1024))
					peer_to_server_socket.close()
					if rcv_data:
						print "File Update of Peer: %s on server successful"% (self.peer.peer_id)
					else:
						print "File Update of Peer: %s on server unsuccessful" % (self.peer.peer_id)

				self.peer.file_list = curr_filelist
				time.sleep(10)

		except Exception as e:
			print "File Handler Error, %s" % e
			sys.exit(1)

	def run(self):
		# print '........................'
		if self.name == 'PeerServer':
			self.server()
		elif self.name == 'PeerFileHandler':
			self.file_handler()

class Peer():
	def __init__(self, ip, port):
		# self.peer_hostname = socket.gethostname()
		self.server_ip = ip
		self.server_port = port
		self.file_list = []

	def fetch_file_list(self):
		try:
			for file in os.listdir(PUBLIC_DIR):
				self.file_list.append(file)
		except Exception as e:
			print "Error: fetching the file list, %s" % e

	def free_peer_socket(self):
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			s.bind(('',0))
			free_socket = s.getsockname()[1]
			s.close()
			return free_socket
		except Exception as e:
			print "Error: Creating peer socket failed, %s" % e

	def register_peer(self):
		try:
			free_socket = self.free_peer_socket()
			self.fetch_file_list()
			ps_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			ps_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			ps_socket.connect((self.server_ip, self.server_port))
			peer_info = {
				'command' : 'register', 
				'peer_port' : free_socket,
				'peer_name' : socket.gethostname() ,
				'files': self.file_list
			}
			ps_socket.sendall(json.dumps(peer_info))
			recv_data = json.loads(ps_socket.recv(1024))
			ps_socket.close()
			print recv_data
			if recv_data[1]:
				self.host_port = free_socket
				self.peer_id = recv_data[0] + ":" + str(free_socket)
				print "Registration completed with Peer ID %s:%s" %(free_socket,recv_data[0])
			else:
				print "Registration couldn't be completed, Peer ID: %s:%s" %(free_socket, recv_data[0])
				sys.exit(1)

		except Exception as e:
			print "Error while peer registration, %s" %e
			sys.exit(1)

	def list_cserver_files(self):
		try:
			ps_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			ps_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			ps_socket.connect((self.server_ip, self.server_port))
			peer_info = {
				'command' : 'list', 
			}
			ps_socket.sendall(json.dumps(peer_info))
			recv_data = json.loads(ps_socket.recv(1024))
			ps_socket.close()
			print "List of files in Central Index Server:"
			for t in recv_data:
				print t
			return recv_data

		except Exception as e:
			print "Error while listing files from Central Index Server, %s" %e

	def search_file(self, f_name):
		try:
			ps_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			ps_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			ps_socket.connect((self.server_ip, self.server_port))
			peer_info = {
				'command' : 'search',
				'file_name' : f_name 
			}
			ps_socket.sendall(json.dumps(peer_info))
			recv_data = json.loads(ps_socket.recv(1024))
			ps_socket.close()
			if len(recv_data) == 0:
				print "File not available"
			else:
				print "\nFile is present in the following peers:"
				for p in recv_data:
					if p == self.peer_id:
						print "File already present locally"
					else:
						print "Peer ID: %s" % p
			return recv_data

		except Exception as e:
			print "Error while searching files from Central Index Server, %s" %e

	def get_file(self, f_name, peer_req_id):
		try:
			peer_req_ip, peer_req_port = peer_req_id.split(":")
			ps_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			ps_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			# print peer_req_ip, peer_req_port
			ps_socket.connect((peer_req_ip, int(peer_req_port)))
			peer_info = {
				'command' : 'obtain_active',
				'file_name' : f_name 
			}
			ps_socket.sendall(json.dumps(peer_info))
			# print '####### ', ps_socket.recv(1024000)
			# recv_data = json.loads(ps_socket.recv(1024000))
			recv_data = ps_socket.recv(1024000)
			# print ps_socket.recv(1024000)
			# print '###### ',recv_data
			f = open(PUBLIC_DIR+ '/' + f_name, 'wb')
			f.write(recv_data)
			f.close()
			print "File downloaded successfully"
			ps_socket.close()
			return 1

		except Exception as e:
			print "Error while downloading file, %s" %e
			return -1

	def log_out(self):
		try:
			ps_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			ps_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			ps_socket.connect((self.server_ip, self.server_port))
			peer_info = {
				'command' : 'deregister',
				'peer_id' : self.peer_id, 
				'files' : self.file_list,
				'hosting_port': self.host_port 
			}
			ps_socket.sendall(json.dumps(peer_info))
			recv_data = json.loads(ps_socket.recv(1024))
			ps_socket.close()
			if recv_data:
				print "Logged out successfully"
			else:
				print "Logging out unsuccessful"

		except Exception as e:
			print "Error while logging out, %s" %e


if __name__ == '__main__':
	try:
		args = get_args()
		print "Initializing Peer..."
		peer = Peer(args.ip, args.port)
		# print peer.free_peer_socket()
		peer.register_peer()

		print "Starting Peer Server Deamon Thread..."
		server_thread = PeerOperations(1,'PeerServer', peer)
		# print '********************'
		server_thread.setDaemon(True)
		server_thread.start()

		print "Starting File Handler Deamon Thread..."
		file_handler_thread = PeerOperations(2, "PeerFileHandler", peer)
		file_handler_thread.setDaemon(True)
		file_handler_thread.start()

		while True:
			print "Welcome to Central Index Server"
			print "1. List available files in Central Index Server"
			print "2. Search File"
			print "3. Fetch File from other Peer/s"
			print "4. Log out"
			print "*" * 5
			print "Please enter your choice : "
			ops = raw_input()

			if int(ops) == 1:
				peer.list_cserver_files()

			elif int(ops) == 2:
				print "Enter File Name: "
				file_name = raw_input()
				peer.search_file(file_name)

			elif int(ops) == 3:
				print "Enter the required File Name: "
				file_name = raw_input()
				print "Enter Peer ID: "
				peer_request_id = raw_input()
				peer.get_file(file_name, peer_request_id)

			elif int(ops) == 4:
				peer.log_out()
				print "Logging out..."
				time.sleep(1)
				break

			else:
				print "Invaild choice...\n"
				continue

	except (KeyboardInterrupt, SystemExit):
		peer.log_out()
		print "Logging out..."
		time.sleep(1)
		sys.exit(1)

	except Exception as e:
		print e
		sys.exit(1)