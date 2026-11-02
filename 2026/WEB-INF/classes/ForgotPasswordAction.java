package com;
import java.io.IOException;
import java.io.PrintWriter;
import javax.servlet.RequestDispatcher;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
public class ForgotPasswordAction extends HttpServlet {
public void doPost(HttpServletRequest request, HttpServletResponse response)	throws ServletException, IOException {
	response.setContentType("text/html");
	PrintWriter out = response.getWriter();
	try{
		String user=request.getParameter("t1").trim();
		String pass=request.getParameter("t2").trim();
		
		String input[]={user,pass};
		String register = DBCon.updatePassword(input);
		RequestDispatcher rd=request.getRequestDispatcher("index.jsp?t1= "+register);
		rd.forward(request, response);
		
			
	}catch(Exception e){
		e.printStackTrace();
	}
}

}
