
import sys
import socket
import json

from PyQt5 import uic
from PyQt5.Qt import QAction, QApplication, QMainWindow
from PyQt5.QtCore import QThread

default_port = 41341

class game(QThread):
    def __init__(self, classe, ip=None, parent=None):
        super(game, self).__init__(parent)
        # Dichiarazione variabili
        self.mainClass = classe
        self.ip = ip
        self.continuealive = True
        # Creo il socket sull'interfaccia di rete e uso TCP
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Se non viene passato l'ip dalla gui significa che si sta giocando come server
        if self.ip == None:
            #print("server")
            # Apro il socket a tutti gli ip su default_port
            self.sock.bind(("0.0.0.0", default_port))
            self.sock.listen(5)
            # Associo alla funzione del thread (self.run()) la funzione self.server()
            self.run = self.server
        else:
            #print("client")
            # Se viene passato l'ip dalla gui si sta giocando come client
            self.ip = ip
            # Mi collego all'ip specificato e porta di default
            self.sock.connect((self.ip, default_port))
            # Associo alla funzione del thread (self.run()) la funzione self.client()
            self.run = self.client

    def closeconn(self):
        self.continuealive = False
        self.sock.close()

    def server(self):
        # Quando il server è pronto accetta la prima richiesta in entrata e giocherà contro quel client
        self.conn, addr = self.sock.accept()
        from_client = ""

        # Inizio il ciclo di partita
        while self.continuealive:
            # Aspetto la mossa dall'aversario
            data = self.conn.recv(4096)
            if not data:
                #print("no data")
                break
            # Trasformo la richiesta in json
            from_client = json.loads(data.decode("utf-8"))
            #print(list(addr),"\n-- ",from_client["message"])
            # Scrivo sulla gui la mossa dell'aversario
            self.mainClass.getMossa(from_client["xy"])

    def client(self):
        # Inizio il ciclo di partita
        while self.continuealive:
            # Aspetto la mossa dall'aversario
            data = self.sock.recv(4096)
            if not data:
                #print("no data")
                break
            # Trasformo la richiesta in json
            from_server = json.loads(data.decode("utf-8"))
            #print("\n-- ",from_server["message"])
            # Scrivo sulla gui la mossa dell'aversario
            self.mainClass.getMossa(from_server["xy"])

    def mossa(self,xy):
        # Compongo il dizionario per l'invio della mossa
        js = dict()
        js["xy"] = xy
        js["message"] = "mossa"
        a = bytes(json.dumps(js), "UTF-8")

        # Invio mossa
        if self.ip == None:
            self.conn.send(a)
        else:
            self.sock.send(a)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.gamethread = None

        # Quando un utente chiude la finestra di gioco, invia un segnale di chiusura socket
        uscire = QAction("Quit")
        uscire.triggered.connect(lambda: self.closeEvent())

        self.changeScreen("mainWin.ui",self.mainWin)
        self.show()
    
    def changeScreen(self, fileUi, nextFunct=""):
        # Memorizza la funzione da chiamare
        self.__nextFunct = nextFunct
        # Carica file ui
        uic.loadUi(fileUi, self)
        # Se la funzione successiva è impostata chiamala
        if self.__nextFunct != "":
            self.__nextFunct()
        # Mostra GUI
        self.show()
    
    def closeEvent(self, event):
        if self.gamethread != None:
            self.gamethread.closeconn()
        event.accept()

    def config(self, thread):
        # Metto la classe thread passata dentro self.gamethread
        self.gamethread = thread
        # Avvio il thread
        self.gamethread.start()

    def serverConfig(self):
        # Invio la classe thread per iniziare la partita da server
        self.config( game(self) )
        # Cambio componenti sullo schermo per iniziare la parita come seconda mossa
        self.changeScreen("partita.ui",lambda: self.partita(1))

    def clientConfig(self,ip):
        # Invio la classe thread con IP per iniziare la partita da client
        self.config( game(self, ip) )
        # Cambio componenti sullo schermo per iniziare la parita come prima mossa
        self.changeScreen("partita.ui",self.partita)

    # Schermata principale
    def mainWin(self):
        # l'utente sceglie se essere server o client
        self.btnServer.clicked.connect(lambda: self.serverConfig())
        self.btnClient.clicked.connect(lambda: self.changeScreen("hostplay.ui",self.clientConnet))

    def clientConnet(self):
        # Prendo l'ip immesso dall'utente e avvio la funzione per impostare il client
        self.btnConnect.clicked.connect(lambda: self.clientConfig(self.ipField.text()))

    def getMossa(self, xy):
        #print(xy)
        # L'avversario ha fatto una mossa, disabilito il pulsante, segno con ⭕ e sblocco i restanti pulsanti
        self.btnlist[xy[0]][xy[1]].setEnabled(False)
        self.btnlist[xy[0]][xy[1]].setText("⭕")
        self.unlockbtn()

    def mossa(self, btn, xy):
        # l'utente fa la sua mossa, disabilito il pulsante, segno con ❌, invio la mossa all'avversario e blocco tutti i pulsanti
        btn.setEnabled(False)
        btn.setText("❌")
        self.gamethread.mossa(xy)
        self.lockbtn()

    def unlockbtn(self):
        for line in self.btnlist:
            for i in line:
                if i.text():
                    i.setEnabled(False)
                else:
                    i.setEnabled(True)

    def lockbtn(self):
        for line in self.btnlist:
            for i in line:
                i.setEnabled(False)

    def partita(self,i=0):
        # creo la matrice di pulsanti
        self.btnlist = [[self.btn11,self.btn12,self.btn13],[self.btn21,self.btn22,self.btn23],[self.btn31,self.btn32,self.btn33]]
        # se i=1 significa che sono il server e parto per secondo
        if i:
            # Blocco tutti i pulsanti
            self.lockbtn()
        
        # Assegno ad ogni pulsante la corrispettiva mossa
        self.btn11.clicked.connect(lambda: self.mossa(self.btn11, [0,0]))
        self.btn12.clicked.connect(lambda: self.mossa(self.btn12, [0,1]))
        self.btn13.clicked.connect(lambda: self.mossa(self.btn13, [0,2]))
        self.btn21.clicked.connect(lambda: self.mossa(self.btn21, [1,0]))
        self.btn22.clicked.connect(lambda: self.mossa(self.btn22, [1,1]))
        self.btn23.clicked.connect(lambda: self.mossa(self.btn23, [1,2]))
        self.btn31.clicked.connect(lambda: self.mossa(self.btn31, [2,0]))
        self.btn32.clicked.connect(lambda: self.mossa(self.btn32, [2,1]))
        self.btn33.clicked.connect(lambda: self.mossa(self.btn33, [2,2]))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
