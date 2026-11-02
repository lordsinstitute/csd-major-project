package com;
import java.io.IOException;
import java.io.PrintWriter;
import javax.servlet.RequestDispatcher;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;
public class UserLoginAction extends HttpServlet {
public void doPost(HttpServletRequest request, HttpServletResponse response)	throws ServletException, IOException {
	response.setContentType("text/html");
	PrintWriter out = response.getWriter();
	String user=request.getParameter("t1").trim();
	String pass=request.getParameter("t2").trim();
	try{
		String input[]={user,pass};
		String msg=DBCon.userLogin(input);
		if(msg.equals("valid login")){
			HttpSession session=request.getSession();
			session.setAttribute("user",user);
			RequestDispatcher rd=request.getRequestDispatcher("UserScreen.jsp?t1=Welcome "+user+"<br/>You have successfully Logged in");
			rd.forward(request, response);
		}else{
			response.sendRedirect("UserLogin.jsp?t1=Invalid Login details");
		}
	}catch(Exception e){
		e.printStackTrace();
	}
	}

}
