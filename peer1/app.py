from bottle import *
# from server import *
from peer import *
import time
import sys

app = Bottle()
p = 1

# In[97]:

@app.route('/')
def index():
	"""Home page"""
	
	return template('form1.tpl', message = 'Peer to Peer file sharing system.')


# In[ ]:
@app.route('/', method="POST")
def formhandler():
		"""Handle the form submission"""
		
		ip = request.forms.get('ip')
		port = request.forms.get('port')
		# try:
		print 'Starting Peer....'
		global p
		p = Peer(ip,int(port))
		p.register_peer()

		print 'Starting Peer Server Daemon Thread...'
		server_thread = PeerOperations(1, "PeerServer", p)
		server_thread.setDaemon(True)
		server_thread.start()

		print "Starting File Handler Deamon Thread..."
		file_handler_thread = PeerOperations(2, "PeerFileHandler", p)
		file_handler_thread.setDaemon(True)
		file_handler_thread.start()
		redirect('/choose')
		# except:
		# 	return template('form1.tpl',message='error')

@app.route('/choose')
def choose():
	return template('form2.tpl',message='')

@app.route('/choose',method='POST')
def handle_choice():

	global p
	choice = request.forms.get('choice')

	if choice == '1':
		# code for listting all files
		req = p.list_cserver_files()
		# print '##############'
		# print req
		# print '##############'
		return template('form2.tpl',message=req)
		
	elif choice == '2':
		# code for searching a file
		redirect('/search')

	elif choice == '3':
		#code for downloading a file
		redirect('download')
	elif choice == '4':
		p.log_out()
		time.sleep(1)
		redirect('/')
	# print choice
	return template('form2.tpl',message=['Invalid choice'])


@app.route('/search')
def search_files():
	return template('search.tpl',message='')

@app.route('/search',method='POST')
def do_search():
	filename = request.forms.get('filename')
	req = p.search_file(filename)
	return template('search.tpl',message=req)

@app.route('/download')
def download_get():
	return template('download.tpl',message='')

@app.route('/download',method='POST')
def do_download():
	filename = request.forms.get('filename')
	# peerid = request.forms.get('peerid')
	global p
	req = p.get_files_concurrently(filename)
	return template('download.tpl',message=req)

app.run(port=4324)
