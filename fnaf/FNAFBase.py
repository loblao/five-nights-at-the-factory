from direct.interval.IntervalGlobal import *
from direct.gui.DirectGui import *
from direct.fsm.FSM import FSM
from panda3d.core import *
import sys, os, time, random

from Level import Level
from Camera import CameraControls
from Timer import Timer

class FNAFBase(FSM):
    def __init__(self, withinTTH=False):
        FSM.__init__(self, "FNAFBase")
        
        self.withinTTH = withinTTH
        
        if not self.withinTTH:
            base.cogFont = loader.loadFont('data/vtRemingtonPortable.ttf')
            base.accept("escape", self.handleEsc)
            base.accept("f9", self.screenshot)
            
        else:
            from toontown.toonbase import ToontownGlobals
            base.cogFont = ToontownGlobals.getSuitFont()
        
        base.level = Level()            
        base.timer = Timer()
        base.camControls = CameraControls()
        
        if not self.withinTTH:
            self.handleGotPhases()
        
        self.ray = CollisionRay()
        cNode = CollisionNode('mousePicker')
        cNode.addSolid(self.ray)
        cNode.setCollideMask(BitMask32(8))
        self.cnp = base.cam.attachNewNode(cNode)
        
        self.handler = CollisionHandlerQueue()
        self.clickTrav = CollisionTraverser('cTrav')
        self.clickTrav.addCollider(self.cnp, self.handler)
        base.accept('mouse1', self.__handleClick)
        
        self.night = 1
        
    def handleGotPhases(self):
        base.level.load()
        base.camControls.browser.load()
        
    def __handleClick(self):
        m = base.mouseWatcherNode
        if m.hasMouse():
            mpos = m.getMouse()
            self.ray.setFromLens(base.camNode, mpos.getX(), mpos.getY())
      
        self.clickTrav.traverse(render)
        numEntries = self.handler.getNumEntries()
        if numEntries > 0:
            self.handler.sortEntries()
            for i in xrange(numEntries):
                np = self.handler.getEntry(0).getIntoNodePath()
                messenger.send('click-%s' % np.getName())
        
    def enterGame(self, night=1):
        self.night = night
        self.__saveProgess()
        
        base.transitions.irisIn()
        base.level.enter(night)
        base.timer.enter(night)
        base.camControls.enter()
        base.accept("ranOutOfEnergy", self.__handleRanOutOfEnergy)
        base.accept("gameFailed", self.__doFail)
        base.accept("dayComplete", self.__doSuccess)
        
    def exitGame(self):
        base.level.exit()
        base.timer.exit()
        base.camControls.exit()
        base.ignore("ranOutOfEnergy")
        base.ignore("gameFailed")
        
    def handleEsc(self):
        sys.exit()
        
    def __handleRanOutOfEnergy(self):
        base.level.stopAllCogs()
        cog = random.choice(list(base.level.cogs))
        cog.setPos(0)
        cog.setHpr(180, 0, 0)
        base.camControls.demand('Flashlight')
        base.camControls.demand('Off')
        cog.danceAndGameOver()
        
    def __doFail(self):
        def restartNight():
            self.demand('RestartNight')
            
        Sequence(Func(base.transitions.irisOut), Wait(.5),
                 Func(restartNight)).start()
        
    def enterRestartNight(self):
        base.transitions.noTransitions()
        
        def __doEnterGame(task):
            self.request('Game', self.night)
            return task.done
        
        taskMgr.doMethodLater(0, __doEnterGame, 'fnafbase-doEnterGame')
        
    def __doSuccess(self):
        def advance():
            if self.night == 5:
                self.gameComplete()
                
            else:   
                self.demand('GoToNextNight')
            
        Sequence(Func(base.transitions.irisOut), Wait(.5),
                 Func(advance)).start()
        
    def enterGoToNextNight(self):
        def __doEnterGame(task):
            self.request('Game', self.night + 1)
            return task.done
        
        taskMgr.doMethodLater(0, __doEnterGame, 'fnafbase-doEnterGame')
        
    def screenshot(self):
        if not os.path.isdir("screenshots"):
            os.mkdir("screenshots")
            
        base.win.saveScreenshot("screenshots/five-nights-at-the-factory-%s.jpg" % time.time())
        
    def gameComplete(self):
        if self.withinTTH:
            messenger.send("FNAF-gameComplete")
            # Let TTH handle it.
            return
            
        base.transitions.noTransitions()
        self.request('Menu')
        
    def enterMenu(self):
        self.bgFrame = DirectFrame(parent=render2d, frameSize=(-1, 1, -1, 1), frameColor=(0, 0, 0, 1))
        self.title = OnscreenText(text="Five Nights at the Factory", pos=(0, .8), font=base.cogFont,
                                  fg=(1, 1, 1, 1), scale=.15, wordwrap=1.6 / .15)
        self.newGameButton = DirectButton(text="NEW GAME", pos=(0, 0, -.2), text_font=base.cogFont, relief=None,
                                          scale=.2, text_fg=(1, 1, 0, 1), command=self.demand, extraArgs=['Game'])
        self.continueButton = DirectButton(text="CONTINUE", pos=(0, 0, -.6), text_font=base.cogFont, relief=None,
                                           scale=.2, text_fg=(1, 1, 0, 1), command=self.__continue)
                                           
    def exitMenu(self):
        self.bgFrame.removeNode()
        self.title.removeNode()
        self.newGameButton.removeNode()
        self.continueButton.removeNode()
                                           
    def __continue(self):
        lastNight = 1
        if os.path.isfile('save.dat'):
            with open('save.dat', 'rb') as f:
                lastNight = ord(f.read(1))
            
        if not 1 <= lastNight <= 5:
            lastNight = 1
            
        self.demand('Game', lastNight)
        
    def __saveProgess(self):
        try:
            with open('save.dat', 'wb') as f:
                f.write(chr(self.night))
                
        except:
            pass
            
    def startGame(self):
        base.camControls.load()
        nextState = "Menu" if not self.withinTTH else "Game"
        self.demand(nextState)
        
    def leaveGame(self):
        self.demand('Off')
        base.camControls.unload()
        