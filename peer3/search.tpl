<html>
  <head>
	  <title>P2P File Sharing</title>
  </head>
  <body>
	<form method="post" action="/search">
		<fieldset>
			<legend>ENTER FILENAME</legend>
			<ul>
				<li>Filename: <input name='filename'></li>
			</ul><input type='submit' value='Submit Form'>
		</fieldset>
	</form>
	<ul>
	% for req in message:
		<li>{{req}}</li>
	</ul>
  </body>
</html>