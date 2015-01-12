from direct.gui.DirectGui import *
from direct.fsm.FSM import FSM
from panda3d.core import *
import random, math

CameraPoints = (
                ((66.6, -20.7, 7.2), (0, 0, 0), "Hallway"),
                ((-112.694, -35.0187, 23.3818), (-3.71871, -19.9784, -0.604477), "Left Room"), 
                ((-110, 95, 40), (0, -25.9784, -0.604477), "Control Room (Camera 1)"),
                ((-130, 95, 40), (0, -25.9784, -0.604477), "Control Room (Camera 2)"),
                ((65.0658, 195.454, 13.3796), (-3.71871, -19.9784, -0.604477), "Safe Room")
)

CameraButtonPos = {
    "Hallway": (.825, 0, .15),
    "LeftRoom": (.28, 0, .2),
    "SafeRoom": (.825, 0, .865),
    "ControlRoomCamera1": (.38, 0, .625),
    "ControlRoomCamera2": (.2, 0, .625),
}

class CameraBrowser(NodePath):
    def __init__(self, controls):
        NodePath.__init__(self, "CameraBrowser")
        self.reparentTo(render2d)
        
        self.controls = controls
        
        frameColor = (1, 1, 1, .95)
        
        # Generate 4 frames around the display region
        leftFrame = DirectFrame(frameSize=(-.98, -.96, -.98, .98), frameColor=frameColor, parent=self)
        rightFrame = DirectFrame(frameSize=(.96, .98, -.98, .98), frameColor=frameColor, parent=self)
        bottomFrame = DirectFrame(frameSize=(-.98, .98, -.98, -.96), frameColor=frameColor, parent=self)
        topFrame = DirectFrame(frameSize=(-.98, .98, .98, .96), frameColor=frameColor, parent=self)
        
        self.title = OnscreenText(parent=topFrame, pos=(-.6, .8), fg=(1, 1, 1, 1), text="REC",
                                  font=base.cogFont, scale=.16)
        
        self.titleSquare = DirectFrame(parent=self.title, frameColor=(1, 0, 0, .85), frameSize=(-.08, .08, -.08, .08),
                                       pos=(-.85, 0, .84))
        
        self.exitButton = DirectButton(parent=base.a2dTopRight, pos=(-.2, 0, -.35), command=self.controls.request,
                                       text="X", text_fg=(1, 1, 0, 1), text_font=base.cogFont, relief=None,
                                       scale=.15, extraArgs=['Flashlight'])
                  
    def load(self):
        self.map = base.a2dBottomRight.attachNewNode(CardMaker("fnaf-map").generate())
        texture = "phase_9/maps/tt_fnaf_map.png" if base.withinTTH else "data/fnafmap.png"
        self.map.setTexture(loader.loadTexture(texture))
        self.map.setTransparency(1)
        self.map.setPos(self.map, (-1.25, 0, 0))
        self.map.setScale(1.15)
        
        self.map.stash()
        
        self.cameras = []
        for index, (pos, hpr, name) in enumerate(CameraPoints):
            self.createCamera(index, pos, hpr, name)
            
        self.__cameraIndex = 0
        
    def setCamera(self, index):
        self.disableCurrentCamera()
        self.__cameraIndex = index
        self.enableCurrentCamera()
        
    def disableCurrentCamera(self):
        dr, name, button = self.cameras[self.__cameraIndex]
        dr.setActive(0)
        button['state'] = DGG.NORMAL
        
    def enableCurrentCamera(self):
        dr, name, button = self.cameras[self.__cameraIndex]
        dr.setActive(1)
        
        cleanName = name.replace(' ', '')
        cleanName = cleanName.replace('(', '')
        cleanName = cleanName.replace(')', '')
        messenger.send("cameraSeeing%s" % cleanName)
        
        button['state'] = DGG.DISABLED
                    
    def createCamera(self, index, pos, hpr, name):
        camNP = render.attachNewNode(Camera('cam'))
        camNP.setPos(pos)
        camNP.setHpr(hpr)
        
        displayRegion = base.win.makeDisplayRegion(0, 1, 0, 1)
        displayRegion.setCamera(camNP)
        displayRegion.setClearColor((0, 0, 0, 1))
        displayRegion.setClearColorActive(True)
        displayRegion.setClearDepthActive(True)
        displayRegion.setActive(0)
        
        cleanName = name.replace(' ', '')
        cleanName = cleanName.replace('(', '')
        cleanName = cleanName.replace(')', '')
        
        pos = CameraButtonPos.get(cleanName)
        button = DirectFrame(parent=self.map,
                             frameColor=(1, 1, 1, 0),
                             frameSize=(-.16, .29, -.15, .15),
                             pos=pos, scale=.2,
                             state=DGG.NORMAL)
        button.bind(DGG.B1PRESS, lambda x: self.setCamera(index))
        button.setTextureOff()
        
        self.cameras.append((displayRegion, name, button))
        
    def blinkSquare(self, task):
        time = int(task.time)
        method = (self.titleSquare.hide, self.titleSquare.show)[time % 2]
        method()
        return task.cont
        
    def show(self):
        NodePath.show(self)
        self.exitButton.unstash()
        self.map.unstash()
        self.titleSquare.show()
        taskMgr.doMethodLater(1, self.blinkSquare, 'fnaf-camera-blinkSquare')
        self.enableCurrentCamera()
        
    def hide(self):
        NodePath.hide(self)
        self.exitButton.stash()
        if hasattr(self, 'map'):
            self.map.stash()
            self.disableCurrentCamera()
        taskMgr.remove('fnaf-camera-blinkSquare')

class CameraControls(FSM):
    def __init__(self):
        FSM.__init__(self, "CameraControls")
        self.taskName = "CameraControls-task"
        self.browser = CameraBrowser(self)
        self.browser.hide()
        self.browserButton = DirectButton(text="Cameras", text_fg=(1, 1, 1, 1), scale=.07,
                                          pos=(0, 0, -.9), text_bg=(0, 0, 0, .75),
                                          text_font=base.cogFont, command=self.request,
                                          extraArgs=['Browser'])
        self.browserButton.hide()
        
    def load(self):
        if base.withinTTH:
            self.leaveGameButton = DirectButton(text="Quit", text_fg=(1, 1, 1, 1), scale=.07,
                                                pos=(-.4, 0, -.9), text_bg=(0, 0, 0, .75),
                                                text_font=base.cogFont, command=base.cr.fnafMgr.leaveMinigame)
                                                
    def unload(self):
        if base.withinTTH:
            self.leaveGameButton.destroy()
       
    def enter(self):
        self.demand('Flashlight')
        
        # Reset the camera index
        self.browser.setCamera(0)
        self.browser.disableCurrentCamera()
        
    def exit(self):
        self.demand('Off')

    def enterFlashlight(self):
        taskMgr.add(self.updateTask, self.taskName)
        base.cam.setPos(0, -27, 5)
        base.cam.setH(0)
        self.browserButton.show()
        
    def exitFlashlight(self): 
        taskMgr.remove(self.taskName)
        self.browserButton.hide()
        
    def enterBrowser(self):
        base.timer.addEnergyConsumption('cameraBrowser', 2)
        self.browser.show()
        
    def exitBrowser(self):
        base.timer.removeEnergyConsumption('cameraBrowser')
        self.browser.hide()
        
    def updateTask(self, task):
        m = base.mouseWatcherNode
        if m.hasMouse():
            x = m.getMouseX()
            
            offset = 45
            
            h = min((x + 1) * offset, 2 * offset)
            h = max(h, -offset)
            h = offset - h

            base.cam.setH(h)
            
        return task.cont