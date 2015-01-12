from direct.interval.IntervalGlobal import *
from direct.fsm.FSM import FSM
from panda3d.core import *
from Cog import Cog

class CogDoor(NodePath, FSM):
    def __init__(self, model, **kw):
        NodePath.__init__(self, self.__class__.__name__)
        FSM.__init__(self, self.__class__.__name__)
        self.pos = kw.get('pos', (0, 0, 0))
        self.hpr = kw.get('hpr', (0, 0, 0))
        self.scale = kw.get('scale', 1)
        self.color = kw.get('color')
        
        self.setPos(self.pos)
        self.setHpr(self.hpr)
        self.setScale(self.scale)
        if self.color:
            self.setColor(self.color)
        
        if model:
            doorway = model.find('**/Doorway1')
            doorway.find('**/doortop').removeNode()
            doorway.find('**/doorbottom').removeNode()        
            doorway.reparentTo(self)
            
            self.doorLeft = doorway.find('**/doorLeft')
            self.doorRight = doorway.find('**/doorRight')
            
    def enterOpen(self):
        self.doorLeft.hide()
        self.doorRight.hide()
        
    def enterClosed(self):
        self.doorLeft.show()
        self.doorRight.show()

    def enterOpening(self):
        time = 1
        offset = 7.5
        
        leftDoorSeq = self.doorLeft.posInterval(time, (-offset, 0, 0), (0, 0, 0))
        rightDoorSeq = self.doorRight.posInterval(time, (offset, 0, 0), (0, 0, 0))
        
        self.ival = Sequence(Parallel(leftDoorSeq, rightDoorSeq), Func(self.demand, 'Open'))
        self.ival.start()
        
    def exitOpening(self):
        self.ival.pause()
        del self.ival
        
    def enterClosing(self):
        time = 1
        offset = 7.5
        
        self.doorLeft.show()
        self.doorRight.show()
        
        leftDoorSeq = self.doorLeft.posInterval(time, (0, 0, 0), (-offset, 0, 0))
        rightDoorSeq = self.doorRight.posInterval(time, (0, 0, 0), (offset, 0, 0))
        
        self.ival = Sequence(Parallel(leftDoorSeq, rightDoorSeq), Func(self.demand, 'Closed'))
        self.ival.start()
        
    def exitClosing(self):
        self.ival.pause()
        del self.ival
        
class DynamicCogDoor(CogDoor): 
    def __init__(self, model, **kw):
        CogDoor.__init__(self, model, **kw)
        buttonPos = kw.get('buttonPos')
        if not buttonPos:
            raise ValueError("DynamicDoor requires buttonPos kw arg!")
            
        self.button = loader.loadModel(self.getButtonModel())
        self.button.reparentTo(self)
        self.button.setPos(buttonPos)
        self.button.setScale(3.5)
        self.buttonNode = self.button.find('**/button')
        
        self.buttonName = 'Button-%s' % id(self)
        self.buttonEvent = 'click-' + self.buttonName
        cNode = CollisionNode(self.buttonName)
        cNode.addSolid(CollisionSphere(0, 0, 0, .8))
        cNode.setCollideMask(BitMask32(8))
        cnp = self.buttonNode.attachNewNode(cNode)
        
    def trigger(self):
        nextState = None
        if self.state == 'Open':
            nextState = 'Closing'
            
        elif self.state == 'Closed':
            nextState = 'Opening'
        
        if not nextState:
            return
            
        self.request(nextState)
        
    def enterOpening(self):
        CogDoor.enterOpening(self)
        self.sinkButton()
        
    def enterClosing(self):
        CogDoor.enterClosing(self)
        self.sinkButton()
        
    def exitOpening(self):
        CogDoor.exitOpening(self)
        self.releaseButton()
        
    def exitClosing(self):
        CogDoor.exitClosing(self)
        self.releaseButton()
        
    def enterClosed(self):
        CogDoor.enterClosed(self)
        base.timer.addEnergyConsumption(self.buttonName, 3)
        
    def exitClosed(self):
        base.timer.removeEnergyConsumption(self.buttonName)
        
    def sinkButton(self):
        self.buttonNode.setZ(-.1)
        self.buttonNode.setColor(1, 0, 0, 1)
        
    def releaseButton(self):
        self.buttonNode.setZ(0)
        self.buttonNode.setColor(0, 1, 0, 1)
        
    def isOpen(self):
        return self.state == 'Open'
        
    def getButtonModel(self):
        if not base.withinTTH:
            return 'data/door_btn.bam'
            
        return "phase_9/models/cogHQ/CogDoor_Button"
            
class Level:
    def __init__(self):
        self.quadrants = set()
        self.np = NodePath("quadrants")
       
    def load(self):
        self.addQuadrant("15", (0, 0, 0))
        self.addQuadrant("17", (66.5, 97, 0))
        self.addQuadrant("08", (-111, 0, 0))
        self.addQuadrant("04", (-111, 150, 10))
        self.addQuadrant("03", (67, 238, 0), (180, 0, 0), zScale=.5)
        
        self.addStaticDoor(pos=(-111, 90, 10), scale=(.8, 1, .75), state='Open')
        self.addStaticDoor(pos=(-111, 220, 10), scale=(.8, 1, .75), state='Closed')
        
        self.dynamicDoors = []
        self.addDynamicDoor(pos=(45, 0, 0), hpr=(90, 0, 0), scale=.65, buttonPos=(0, 20, 0), state='Open')
        self.addDynamicDoor(pos=(-45, 0, 0), hpr=(90, 0, 0), scale=.65, buttonPos=(0, -20, 0), state='Open')
        
        self.cogs = set()
        self.addCog('A', (-140, 170, 10), 220)
        self.addCog('B', (72, 247, 0), 40)
        self.addCog('C', (-100, 150, 10), 155)
        
        self.fog = Fog("darknessFog")
        self.fog.setColor(0, 0, 0)
        self.fog.setExpDensity(.03)
        self.np.setFog(self.fog)
        
        self.bgm = loader.loadMusic(self.getBgm())
        self.bgm.setLoopCount(0)
        
    def addCog(self, type, pos, h=0):
        cog = Cog(type)
        cog.reparentTo(self.np)
        cog.loop('neutral')
        cog.setPos(pos)
        cog.setH(h)
        cog.setScale(1.75)
        self.cogs.add(cog)
        
    def enter(self, night=1):
        self.np.reparentTo(render)
        base.camLens.setNear(5)
        base.camLens.setFov(52)
        self.bgm.play()
        
        for door in self.dynamicDoors:
            door.accept(door.buttonEvent, door.trigger)
            
        for cog in self.cogs:
            cog.resetPos()
            
            if cog.type == "A": quad = "ControlRoomCamera2"
            elif cog.type == "B": quad = "SafeRoom"
            elif cog.type == "C": quad = "ControlRoomCamera1"
                
            cog.initialiseAIBehaviours(night, quad)
            
        self.night = night
        
    def exit(self):
        self.np.detachNode()
        self.bgm.stop()
        
        for door in self.dynamicDoors:
            door.ignore(door.buttonEvent)
            door.demand('Open')
            
        self.stopAllCogs()
            
    def stopAllCogs(self):
        for cog in self.cogs:
            cog.stopAIBehaviours()
        
    def unload(self):
        for quad in self.quadrants:
            quad.removeNode()
            
        self.quadrants = set()
        
        self.np.removeNode()
        
    def loadQuadrant(self, code):
        modelPrefix = 'data/'
        if base.withinTTH:
            modelPrefix = 'phase_10/models/cashbotHQ/'
            
        return loader.loadModel('%sZONE%sa.bam' % (modelPrefix, code))
       
    def addQuadrant(self, code, pos, hpr=(0, 0, 0), zScale=1):
        quad = self.loadQuadrant(code)
        quad.reparentTo(self.np)
        quad.setPos(pos)
        quad.setHpr(hpr)
        quad.setSz(zScale)
        self.quadrants.add(quad)

    def addStaticDoor(self, **kw):
        doorModel = loader.loadModel(self.getDoorModel())
        for x in doorModel.findAllMatches('**/Slide_*'):
            x.removeNode()
            
        door = CogDoor(doorModel, **kw)
        door.reparentTo(self.np)
        door.demand(kw.get('state', 'Closed'))
        
    def addDynamicDoor(self, **kw):
        doorModel = loader.loadModel(self.getDoorModel())
        for x in doorModel.findAllMatches('**/Slide_*'):
            x.removeNode()
            
        door = DynamicCogDoor(doorModel, **kw)
        door.reparentTo(self.np)
        door.demand(kw.get('state', 'Closed'))
        door.releaseButton()
        self.dynamicDoors.append(door)
        
    def getDoorModel(self):
        if not base.withinTTH:
            return "data/door.bam"
            
        return "phase_9/models/cogHQ/CogDoorHandShake"
        
    def getBgm(self):
        if not base.withinTTH:
            return 'data/bgm.ogg'
        
        return "phase_12/audio/bgm/Bossbot_Entry_v2.ogg"
        