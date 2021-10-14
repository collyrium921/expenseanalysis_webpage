using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Threading.Tasks;
using System.Linq;
using System.Web;
using System.Web.UI;
using System.Web.UI.WebControls;
using System.Data;

namespace WebExcelUpload
{
    public partial class WebForm1 : System.Web.UI.Page
    {
        public object UploadStatusLabel { get; private set; }

        protected void Page_Load(object sender, EventArgs e)
        {

        }

        protected void Button1_Click(object sender, EventArgs e)
        {
            if (FileUpload1.HasFile)
                saveFile(FileUpload1.PostedFile);
            run_cmd();
        }

        void saveFile(HttpPostedFile file)
        {
            string savePath = "D:\\webpage\\";
            string fileName = FileUpload1.FileName;
            string pathToCheck = savePath + fileName;
            string tempfileName = "";

            if (System.IO.File.Exists(pathToCheck))
            {
                int counter = 2;
                while (System.IO.File.Exists(pathToCheck))
                {
                    tempfileName = counter.ToString() + fileName;
                    pathToCheck = savePath + tempfileName;
                    counter++;
                }
                fileName = tempfileName;
            }
            savePath += fileName;
            FileUpload1.SaveAs(savePath);
        }
        private void run_cmd()
        {

            ProcessStartInfo pro = new ProcessStartInfo();
            var file = "D:\\webpage\\" + FileUpload1.FileName;

            pro.FileName = "C:\\Users\\Admin\\AppData\\Local\\Programs\\Python\\Python39\\python.exe";
            pro.Arguments = @"C:\Users\Admin\Desktop\IndvAnlTest.py " + file + " IMPS";
            pro.RedirectStandardOutput = true;
            pro.UseShellExecute = false;
            Process p = Process.Start(pro);

            string output = p.StandardOutput.ReadToEnd();
            Console.WriteLine(output);

            response.InnerHtml = output;
            p.WaitForExit();
        }

        


    }
}