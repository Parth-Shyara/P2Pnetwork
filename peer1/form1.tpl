<html>
  <head>
	  <title>P2P File Sharing</title>
  </head>
  <body>
	<form method="post" action="/">
		<fieldset>
			<legend>CONNECT TO THE CENTRAL INDEX SERVER</legend>
			<h4>Enter the IP address and port number of the central index server.</h4>
			<ul>
				<li>IP: <input name='ip'></li>
				<li>Port: <input name='port'></li>
			</ul><input type='submit' value='Submit Form'>
		</fieldset>
	</form>
	% if message == 'error':
		<p>Invalid IP address or port number.</p>
  </body>
</html>