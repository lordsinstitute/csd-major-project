package com;
import java.io.IOException;
import java.io.PrintWriter;
import javax.servlet.RequestDispatcher;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
public class SignupAction extends HttpServlet {
public void doPost(HttpServletRequest request, HttpServletResponse response)	throws ServletException, IOException {
	response.setContentType("text/html");
	PrintWriter out = response.getWriter();
	try{
		String user=request.getParameter("t1").trim();
		String pass=request.getParameter("t2").trim();
		String contact=request.getParameter("t3").trim();
		String email=request.getParameter("t4").trim();
		String address=request.getParameter("t5").trim();
		String input[]={user,pass,contact,email,address};
		String register = DBCon.register(input);
		if(register.equals("success")){
			response.sendRedirect("Register.jsp?t1=Registration Successful you can Login now");
		}else{
			RequestDispatcher rd=request.getRequestDispatcher("Register.jsp?t1= "+register);
			rd.forward(request, response);
		}
			
	}catch(Exception e){
		e.printStackTrace();
	}
}

}
