#python -m nuitka --standalone Dynamix_Chart_Merging.py --enable-plugin=tk-inter --enable-plugin=numpy --windows-icon-from-ico=./logo.ico
from delphivcl import *
from tkinter import filedialog
import os, threading, io, zipfile
from pydub import AudioSegment
from lib.reader import *
from io import BytesIO

def find_in_zipfiles(chartzip):
    for file in chartzip.namelist():
        filepath = file
        # 获取文件的扩展名
        _, extension = os.path.splitext(file)
        if extension in ['.mp3', '.wav', '.m4a', '.ogg', '.aac']:
            audio = AudioSegment.from_file(BytesIO(chartzip.read(filepath)), format=extension.split('.')[0])
            # print(audio)
        if extension in ['.json', '.xml']:
            with chartzip.open(filepath, 'r') as f:
                chart = f.read().decode("utf-8")
    return chart, audio

def merge_audio(audio1, audio2):
    len1 = audio1.duration_seconds
    len2 = audio2.duration_seconds
    output = AudioSegment.silent(duration=(len1 + len2) * 1000)
    output = output.overlay(audio1, position=0)
    output = output.overlay(audio2, position=len1 * 1000)
    return output

class MyThread(threading.Thread):
    def __init__(self, func, args = ()):
        super(MyThread, self).__init__()
        self.func = func
        self.args = args
     
    def run(self):
        self.result = self.func(*self.args)
    def get_result(self):
        try:
            return self.result
        except Exception:
            return None

class MainForm(Form):
    def __init__(self, owner) -> None:
        self.Chart1 = ""
        self.Chart2 = ""
        
        # self.Chart1 = "Z:/files/[0]code/Dynamix_Chart_Merging/[G16]Parousia G16.zip"
        # self.Chart2 = "Z:/files/[0]code/Dynamix_Chart_Merging/[g]iL v3.zip"
        
        self.ITag : int = 0

        self.Caption = "Dynamix谱面合并器"
        self.SetBounds(10, 10, 600, 400)
        self.Position = "poScreenCenter"

        self.Chart1Hint = Label(self)
        self.Chart1Hint.SetProps(Parent = self, Caption = "谱面文件压缩包1")
        self.Chart1Hint.SetBounds(10, 10, 300, 24)

        self.Chart1Box = Edit(self)
        self.Chart1Box.SetProps(Parent = self)
        self.Chart1Box.SetBounds(10, 30, 420, 20)
        self.Chart1Box.Text = "Chart1 Here"

        self.Chart1Btn = Button(self)
        self.Chart1Btn.SetProps(Parent = self, Caption = "选择谱面压缩包1")
        self.Chart1Btn.SetBounds(450, 30, 120, 25)
        self.Chart1Btn.OnClick = self.__set_Chart1

        self.Chart2Hint = Label(self)
        self.Chart2Hint.SetProps(Parent = self, Caption = "谱面文件压缩包2")
        self.Chart2Hint.SetBounds(10, 65, 300, 24)  
        
        self.Chart2Box = Edit(self)
        self.Chart2Box.SetProps(Parent = self)
        self.Chart2Box.SetBounds(10, 85, 420, 20)
        self.Chart2Box.Text = "Chart2 Here"

        self.Chart2Btn = Button(self)
        self.Chart2Btn.SetProps(Parent = self, Caption = "选择谱面压缩包2")
        self.Chart2Btn.SetBounds(450, 85, 120, 25)
        self.Chart2Btn.OnClick = self.__set_Chart2


        self.MergeChartBtn = Button(self)
        self.MergeChartBtn.SetProps(Parent = self, Caption = "一键合并谱面")
        self.MergeChartBtn.SetBounds(10, 130, 560, 25)
        self.MergeChartBtn.OnClick = self.__on_merge_Click

        self.logOutput = Memo(self)
        self.logOutput.SetProps(Parent = self)
        self.logOutput.SetBounds(10, 170, 560, 150)
        self.logOutput.Lines.Add("正在使用Dynamix谱面合成器")

        self.btnClose = Button(self)
        self.btnClose.SetProps(Parent = self, Caption = "关闭")
        self.btnClose.SetBounds(10, 330, 560, 25)
        self.btnClose.OnClick = self.__on_btnClose_Click

        self.OnClose = self.__on_form_close

    def __set_Chart1(self, sender) -> None:
        self.Chart1 = filedialog.askopenfilename(filetypes=[('dy谱面压缩包',('.zip'))])
        if(self.Chart1 == ""):
            self.logOutput.Lines.Add(f"请选择文件")
            return 
        self.Chart1Box.Text = self.Chart1
        self.logOutput.Lines.Add(f"已选择{self.Chart1}作为谱面1")
    
    def __set_Chart2(self, sender) -> None:
        self.Chart2 = filedialog.askopenfilename(filetypes=[('dy谱面压缩包',('.zip'))])
        if(self.Chart2 == ""):
            self.logOutput.Lines.Add(f"请选择文件")
            return 
        self.Chart2Box.Text = self.Chart2
        self.logOutput.Lines.Add(f"已选择{self.Chart2}作为谱面2")   
        
    def __on_merge_Click(self, sender) -> None:
        if(self.Chart1 == "" or self.Chart2 == ""):
            self.logOutput.Lines.Add(f"请选择所有谱面压缩包")
            return
        c1 = os.path.split(self.Chart1)[1]
        c2 = os.path.split(self.Chart2)[1]
        self.logOutput.Lines.Add(f"正在合成{c1}与{c2}")

        Chart1zip = zipfile.ZipFile(self.Chart1)
        Chart2zip = zipfile.ZipFile(self.Chart2)
        
        chart1, audio1 = find_in_zipfiles(Chart1zip)
        self.logOutput.Lines.Add("在谱面压缩1中找到谱面与音频文件")
        chart2, audio2 = find_in_zipfiles(Chart2zip)
        self.logOutput.Lines.Add("在谱面压缩2中找到谱面与音频文件")
        
        self.logOutput.Lines.Add("正在拼接音频")
        len1 = audio1.duration_seconds
        len2 = audio2.duration_seconds
        self.logOutput.Lines.Add(f"两曲目时长分别为{str(len1)}s和{str(len2)}s")
        audio = merge_audio(audio1, audio2)
        audfile = io.BytesIO()
        audio.export(audfile, 'mp3')
        self.logOutput.Lines.Add(f"音频合成完成")
        
        self.logOutput.Lines.Add(f"正在拼接谱面")
        chart1 = read(chart1)
        chart2 = read(chart2)
        chart1.concat(chart2, len1)
        chart = chart1.to_xml()
        self.logOutput.Lines.Add(f"谱面拼接完成")
        
        self.logOutput.Lines.Add(f"正在将文件加入压缩包")
        MergedZIP = zipfile.ZipFile('merged.zip', 'w')
        MergedZIP.writestr("chart.xml", str(chart))
        MergedZIP.writestr("audio.mp3", audfile.getbuffer().tobytes())
        self.logOutput.Lines.Add(f"全部流程已完成，已生成merged.zip")

    def __display_progress_bar(self, bytes_received : int, filesize : int) -> None:
        percent = round(100.0 * bytes_received / float(filesize), 1)
        self.logOutput.Lines.Add(str(percent) + "%")

    def __on_btnClose_Click(self, sender) -> None:
        Application.Terminate()

    def __on_form_close(self, sender, action) -> None:
        action.Value = caFree

def main():

    Application.Initialize()
    Application.Title = "Dynamix谱面合并器"
    Main = MainForm(Application)
    Main.Show()
    FreeConsole()
    Application.Run()
    # print(Main.qqid)
    
    # if(Main.filename.endswith(".xml")):
    #     Main.thread1.join()
    # elif(Main.filename.endswith(".plist")):
    #     Main.thread2.join()
    # archive = Main.thread1.result()
    Main.Destroy()

if __name__=='__main__':
    main()