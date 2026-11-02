package com;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.Calendar;
import java.sql.Statement;
public class DBCon{
    private static Connection con;

public static Connection getCon()throws Exception {
    Class.forName("com.mysql.jdbc.Driver");
    con = DriverManager.getConnection("jdbc:mysql://localhost:3306/PasswordApp","root","root");
    return con;
}
public static String register(String[] input)throws Exception{
    String msg="Error in registeration";
    boolean flag=false;
    con = getCon();
    Statement stmt=con.createStatement();
    ResultSet rs=stmt.executeQuery("select username from register where username='"+input[0]+"'");
    if(rs.next()){
        flag=true;
        msg = "Username already exist";
    }
    if(!flag){
		PreparedStatement stat=con.prepareStatement("insert into register values(?,?,?,?,?)");
		stat.setString(1,input[0]);
		stat.setString(2,input[1]);
		stat.setString(3,input[2]);
		stat.setString(4,input[3]);
		stat.setString(5,input[4]);
	    int i=stat.executeUpdate();
		if(i > 0)
			msg = "success";
	}
    return msg;
}

public static String userLogin(String input[])throws Exception{
    String msg="invalid login";
    con = getCon();
    System.out.println(input[0]);
    Statement stmt=con.createStatement();
    ResultSet rs=stmt.executeQuery("select username,password from register where username='"+input[0]+"' && password='"+input[1]+"'");
    if(rs.next()){
        msg = "valid login";
    }
    return msg;
}


public static String updatePassword(String input[])throws Exception{
    String msg = "Given username does not exists. Please Try Again";
    con = getCon();
    System.out.println(input[0]);
    Statement stmt=con.createStatement();
    ResultSet rs=stmt.executeQuery("select username from register where username='"+input[0]+"'");
    if(rs.next()){
        msg = "success";
    }
	if(msg.equals("success")) {
		PreparedStatement stat=con.prepareStatement("update register set password=? where username=?");
		stat.setString(1,input[1]);
		stat.setString(2,input[0]);
		 int i=stat.executeUpdate();
		 if(i > 0)
			 msg = "Password successfully Reset";
	}
	return msg;
}
}
