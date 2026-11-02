<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta name="description" content="" />
<meta name="keywords" content="" />
<title>Graphical Password Authentication</title>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
<div id="wrapper">
	<div id="header">
		<div id="logo">
			<center><font size="4" color="yellow">Graphical Password Authentication</font></center>
		</div>
		<div id="slogan">
			
		</div>
	</div>
	<div id="menu">

	<ul><center>
			
		<li class="first current_page_item"><a href="index.jsp"><font size="" color="yellow">Logout</font></a></li>
		</center></ul>
		<br class="clearfix" />
	</div>
	<div id="splash">
		<img class="pic" src="images/investor.jpg" width="870" height="230" alt="" />
	</div>
	<br/>
	<%
	 String data=request.getParameter("t1");
	 if(data!=null){
		 out.println("<center> <font size=3 color=red>"+data+"</center>");
	 }
	 %><br/>

<p align="justify"><font size="3" color="black"  style="font-family: Comic Sans MS">
	Graphical Password Authentication</p>
</body>
</html>