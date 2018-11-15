<html>
  <head>
	  <title>P2P File Sharing</title>
  </head>
  <body>
	<form method="post" action="/download">
		<fieldset>
			<legend>DOWNLOAD FORM</legend>
			<ul>
				<li>Filename: <input name='filename'></li>
				<li>PeerID: <input name='peerid'></li>
			</ul><input type='submit' value='Submit Form'>
		</fieldset>
	</form>
	% if message == 1:
		<p>File Downloaded successfully!!</p>
	% else:
		<p>Unable to establish connection with Peer</p>
  </body>
</html>