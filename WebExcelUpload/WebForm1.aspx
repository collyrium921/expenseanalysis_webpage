<%@ Page Language="C#" AutoEventWireup="true" CodeBehind="WebForm1.aspx.cs" Inherits="WebExcelUpload.WebForm1" %>

<!DOCTYPE html>

<html xmlns="http://www.w3.org/1999/xhtml">
<head runat="server">
    <title></title>
    <style>
        table, th, td {
            border: 1px solid black;
            border-collapse: collapse;
        }
        th, td {
            padding: 5px;
        }
        table{
            margin: 10px;
        }
        #Button1, #FileUpload1{
            color: white;
            background-color: teal;
            padding: 5px;
            cursor: pointer;
            margin: 10px;
            border: none;
        }
    </style>
</head>
<body>
    
    <form id="form1" runat="server">
        <div><asp:FileUpload ID="FileUpload1" runat="server" />

        </div>
        <asp:Button ID="Button1" runat="server" OnClick="Button1_Click" Text="Button" />

        <div id="response" runat="server"></div>
    </form>
    <script>

</script>
</body>
</html>
