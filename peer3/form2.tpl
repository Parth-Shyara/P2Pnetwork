<html>
  <head>
	  <title>P2P File Sharing</title>
  </head>
  <body>
	<form method="post", action='/choose'>
		<fieldset>
			<legend>WELCOME</legend>
			<h4>Select one of the options.</h4>
			<ol>
				<li>List all available files.</li>
				<li>Search for a file.</li>
				<li>Download a file</li>
				<li>Exit</li>
			</ol>
			Choice <input name='choice'><br><br>
			<input type='submit' value='Submit Form'>
		</fieldset>
	</form>

	<ul>
	% for file in message:
		<li>{{file}}</li>
	% end
	</ul>

  </body>
</html>