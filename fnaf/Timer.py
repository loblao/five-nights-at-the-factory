from direct.gui.DirectGui import *
from panda3d.core import *

class EnergyBar(DirectFrame):
    def __init__(self, parent):
        _pos = (.5, 0, .075)
        
        DirectFrame.__init__(self, pos=_pos, frameColor=(0, 0, 0, 1),
                             frameSize=(-.3, .125, 0, .075), parent=parent)
        self.initialiseoptions(EnergyBar)
        
        self.overlappingFrame = DirectFrame(pos=_pos, frameColor=(1, 0, 0, 1),
                                            frameSize=(-.3, .125, 0, .075), parent=parent)
                                            
        self.text = OnscreenText(text="Energy", fg=(1, 1, 1, 1), parent=self.overlappingFrame,
                                 font=base.cogFont, scale=.035, pos=(-.085, .025))
                     
        self.hide()
        
    def setValue(self, value):
        x = -.3 + .425 * value
        self.overlappingFrame['frameSize'] = (-.3, x, 0, .075)
        
    def hide(self):
        self.overlappingFrame.hide()
        DirectFrame.hide(self)
        
    def show(self):
        self.overlappingFrame.show()
        DirectFrame.show(self)

class Timer:
    secondsPerHour = 60
    endHour = 6
    totalEnergy = int(secondsPerHour * endHour * 2.2)
    
    def __init__(self):        
        self.infoText = OnscreenText(text="12 AM\nNight 1", align=TextNode.ARight, pos=(-.1, -.1),
                                     parent=base.a2dTopRight, fg=(1, 1, 1, 1), font=base.cogFont)
        self.energyBar = EnergyBar(base.a2dBottomLeft)
        
        self.infoText.hide()
        
    def enter(self, night=1):
        self.infoText.show()
        self.energyBar.show()
        
        self.energy = Timer.totalEnergy
        self.consume = 0
        self.hour = 0
        self.consumptionTable = {}
        
        self.addEnergyConsumption('base', 1)
        
        taskMgr.add(self.energyTask, 'Timer-energyTask')
        taskMgr.doMethodLater(self.secondsPerHour, self.nextHour, 'Timer-nextHour')
        
        self.night = night
        self.infoText['text'] = "12 AM\nNight %d" % self.night
        
    def exit(self):
        self.infoText.hide()
        self.energyBar.hide()
        taskMgr.remove('Timer-energyTask')
        taskMgr.remove('Timer-nextHour')
       
    def energyTask(self, task):
        self.energy -= self.consume * min(1, globalClock.getDt())
        if self.energy <= 0:
            messenger.send("ranOutOfEnergy")
            return task.done
            
        self.energyBar.setValue(self.energy / Timer.totalEnergy)
        
        if __debug__ and 0:
            text = "%d AM\nNight %d" % (0 if self.hour == 12 else self.hour, self.night)
            _minute = (task.time % self.secondsPerHour) / (self.secondsPerHour / 60.0)
            text += "\n\n%d:%d" % (0 if self.hour == 12 else self.hour, _minute)
            self.infoText['text'] = text
        
        return task.cont
        
    def nextHour(self, task):
        self.hour += 1
        if self.hour == self.endHour:
            messenger.send("dayComplete")
            return task.done
            
        messenger.send("enterHour", [self.hour])
        
        text = "%d AM\nNight %d" % (self.hour, self.night) 
        self.infoText['text'] = text
        
        return task.again
        
    def addEnergyConsumption(self, hash, consumption):
        if hash in self.consumptionTable:
            self.removeEnergyConsumption(hash)
            
        self.consumptionTable[hash] = consumption
        self.consume += consumption
        
    def removeEnergyConsumption(self, hash):
        if hash not in self.consumptionTable:
            return
            
        consumption = self.consumptionTable[hash]
        self.consume -= consumption
        del self.consumptionTable[hash]
        