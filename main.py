from direct.showbase.ShowBase import ShowBase
from fnaf.FNAFBase import FNAFBase
from pandac.PandaModules import loadPrcFile

if __debug__:
    loadPrcFile('config.prc')

class GameBase(FNAFBase, ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        FNAFBase.__init__(self)
        self.disableMouse()
        
        if not __debug__:
            self.transitions.IrisModelName = "data/iris.egg.pz"
            self.transitions.FadeModelName = "data/fade.egg.pz"

GameBase()

# from fnaf import Timer
# Timer.Timer.secondsPerHour = 6

base.startGame()
run()
