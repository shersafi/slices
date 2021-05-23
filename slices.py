#First public build of Slices
import random #basic random image num gen
import os #for google auth 
import io #for byte images
import sys #sys.argv
from io import BytesIO #byte images

#notifications to desktop
try:
    from pynotifier import Notification
except ImportError:
    pass

######## external
from google.cloud import storage #for uploading images to cloud
import win32clipboard #putting image in clipboard
from pynput import keyboard #hotkeys, later build
from tkinter import * #gui
from PIL import Image #image processing
from PyQt5.QtCore import Qt #frameless window
from PyQt5 import QtCore, QtGui, QtWidgets #widgets

class SnippingTool(QtWidgets.QWidget):
     def __init__(self, parent=None, flags=Qt.WindowFlags()):
        super().__init__(parent=parent, flags=flags)

        self.setWindowTitle("Slices")
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog
        )
        self.setWindowState(self.windowState() | Qt.WindowFullScreen) #frameless window full screen
        allScreens = QtWidgets.QApplication.desktop().geometry() #check for multiple monitors

        self.screen = QtWidgets.QApplication.screenAt(QtGui.QCursor.pos()).grabWindow(0, allScreens.x(), allScreens.y(), allScreens.width(), allScreens.height()) #supports multiple monitors
        palette = QtGui.QPalette()
        palette.setBrush(self.backgroundRole(), QtGui.QBrush(self.screen))
        self.setPalette(palette)
        
        self.setGeometry(allScreens) #size to all monitors
        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))

        self.start, self.end = QtCore.QPoint(), QtCore.QPoint() #start

     def paintEvent(self, event): #region selection for screenshot
        painter = QtGui.QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QtGui.QColor(0, 0, 0, 100))
        painter.drawRect(0, 0, self.width(), self.height())

        if self.start == self.end:
            return super().paintEvent(event)

        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 3)) #pen colour
        painter.setBrush(painter.background()) #greyed out background
        painter.drawRect(QtCore.QRect(self.start, self.end))
        return super().paintEvent(event)

     def mousePressEvent(self, event): #update region selection
        self.start = self.end = event.pos()
        self.update()
        return super().mousePressEvent(event)

     def mouseMoveEvent(self, event): #update region selection
        self.end = event.pos()
        self.update()
        return super().mousePressEvent(event)
    

     def mouseReleaseEvent(self, event): #when released, get rid of frameless window, pass to gui to execute functs
        if self.start == self.end:
            return super().mouseReleaseEvent(event)

        self.hide()
        QtWidgets.QApplication.processEvents()
        shot = self.screen.copy(QtCore.QRect(self.start, self.end))
        
        global gui 

        gui = Tk(className='Select an option.') #tkinter
        gui.geometry("300x100") #small window

        btn1 = Button(gui, text='Send to clipboard', command= lambda: processImage(shot)) #btn for clipboard
        btn1.pack(side=LEFT, padx=15,pady=20)

        btn2 = Button(gui, text='Upload to server', command= lambda: processImage2(shot)) #btn for google cloud upload
        btn2.pack(side=RIGHT, padx=15,pady=20)

        gui.mainloop()
        
        QtWidgets.QApplication.quit()

def processImage(img): #clipboard event
    buffer = QtCore.QBuffer()
    buffer.open(QtCore.QBuffer.ReadWrite)
    img.save(buffer, "PNG")
    pil_img = Image.open(io.BytesIO(buffer.data()))
    buffer.close()
    gui.destroy() #get rid of gui after successful
    
    sendToClipboard(pil_img) #pass to clipboard funct

def processImage2(img): #for storing on google cloud
    buffer = QtCore.QBuffer()
    buffer.open(QtCore.QBuffer.ReadWrite)
    img.save(buffer, "PNG")
    pil_img = Image.open(io.BytesIO(buffer.data()))
    b = io.BytesIO()
    pil_img.save(b, 'jpeg')
    pil_img.close()
    buffer.close()

    try:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="yourgooglejsonhere" #include in slices folder
        client = storage.Client() #using google cloud, remember to setup google cloud platform
        bucket = client.bucket('yourbuckethere') #bucket to send img to

        blob = bucket.blob('image-' + str(random.randrange(1000))) #image-randomnum
        blob.upload_from_string(b.getvalue(), content_type='image/jpeg') #save as jpg image
        blob.make_public() #make public screenshot url
        sendTextClipboard(blob.public_url) #send blob url to clipboard funct
    except Exception as e:
        print(e)

    gui.destroy() #get rid of gui after successful
    return None
    
    
def sendTextClipboard(text): #send google cloud link to clipboard
    i = text
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardText(i)
    win32clipboard.CloseClipboard()
    notify("Link sent to clipboard, try pressing CTRL+V to send it somewhere.")

def sendToClipboard(image): #send image to clipboard, using win32clipboard
    output = BytesIO()
    image.convert('RGB').save(output, 'BMP')
    data = output.getvalue()[14:]
    output.close()

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()
    notify("Picture sent to clipboard, try pressing CTRL+V to send it somewhere.")


def notify(msg): #desktop notification when sent to clipboard or google cloud
    try:
        Notification(title="Slices", description=msg).send()
    except (SystemError, NameError):
        trayicon = QtWidgets.QSystemTrayIcon(
            QtGui.QIcon(
                QtGui.QPixmap.fromImage(QtGui.QImage(1, 1, QtGui.QImage.Format_Mono))
            )
        )
        trayicon.show()
        trayicon.showMessage("Slices", msg, QtWidgets.QSystemTrayIcon.NoIcon)
        trayicon.hide()



if __name__ == "__main__": #exec program
    QtCore.QCoreApplication.setAttribute(Qt.AA_DisableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)

    window = QtWidgets.QMainWindow()
    snipping = SnippingTool(window)
    snipping.show()
    sys.exit(app.exec_())
