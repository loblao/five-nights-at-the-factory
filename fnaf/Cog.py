from direct.interval.IntervalGlobal import *
from direct.actor.Actor import Actor
from panda3d.core import *

from Timer import Timer
import random

RIGHT_DOOR = 0
LEFT_DOOR = 1

PointMap = {
1: (Vec3(0, 0, 0), None),
2: (Vec3(-50, 0, 0), {1: LEFT_DOOR}),
3: (Vec3(-100, 30, 0), None),
4: (Vec3(-100, -30, 0), None),
5: (Vec3(-100, 0, 0), None),
6: (Vec3(-150, 0, 0), None),
7: (Vec3(-172, 25, 0), None),
8: (Vec3(-172, 45, 10), None),
9: (Vec3(-165, 50, 10), None),
10: (Vec3(-150, 55, 10), None),
11: (Vec3(-100, 60, 10), None),
12: (Vec3(-80, 65, 10), None),
13: (Vec3(-110, 90, 10), None),
14: (Vec3(-140, 170, 10), None),
15: (Vec3(-100, 150, 10), None),
16: (Vec3(70, 0, 0), None),
17: (Vec3(49, 0, 0), {1: RIGHT_DOOR}),
18: (Vec3(72, 247, 0), None),
19: (Vec3(71, 100, 0), None)
}

Connections = {
1: [],
2: [1, 3, 4, 5],
3: [4, 5, 2, 6],
4: [5, 2, 6],
5: [2, 3, 4, 6],
6: [5, 4, 3],
7: [6, 4], # Add 8 to allow cogs to go stairs up.
8: [7, 9],
9: [8, 10],
10: [9, 11, 12],
11: [9, 12, 13],
12: [13, 9],
13: [12],
14: [13],
15: [13],
16: [17, 18],
17: [1, 16],
18: [19],
19: [16, 18]
}

class CogPoint:
    def __init__(self, pointIndex, prevIndex=0):
        self.pointIndex = pointIndex
        self.prevIndex = None
        self.pointDesc = PointMap[self.pointIndex]
        
    def getPos(self):
        return self.pointDesc[0]
        
    def getNextPoint(self):
        possiblePoints = []
        for point in Connections[self.pointIndex]:
            doorCondition = self.pointDesc[1]
            
            if doorCondition is None:
                possiblePoints.append(point)
                continue
                
            doorIndex = doorCondition.get(point, None)
            if doorIndex is None:
                possiblePoints.append(point)
                continue
                
            # Trying to reach a point that depends on a door being open.
            # If it's open, go ahead. Else, ignore this point.
            if base.level.dynamicDoors[doorIndex].isOpen():
                return self.__class__(point, self.pointIndex)
                
        if len(possiblePoints) > 1 and self.prevIndex in possiblePoints:
            possiblePoints.remove(self.prevIndex)
                
        random.shuffle(possiblePoints)

        return self.__class__(possiblePoints[0], self.pointIndex)
        
    def reached(self, cog):
        if self.pointIndex == 1:
            # Game over
            base.level.stopAllCogs()
            base.camControls.demand('Flashlight')
            base.camControls.demand('Off')
            cog.setH(180)
            cog.danceAndGameOver()
            return
            
        delay = random.random() * 2.5
        taskMgr.doMethodLater(delay, lambda: cog.walkToPoint(self.getNextPoint()), cog.taskName('nextPoint'), extraArgs=[])
        
    @classmethod
    def fromTypeStart(cls, type):
        if type == "A": return cls(14)
        elif type == "B": return cls(18)
        elif type == "C": return cls(15)

CogBehaviours = {
'A': {
      1: {
          'awake': 3,
          'walkDelay': .35,
         },
      2: {
          'awake': 2,
          'walkDelay': .1,
         },
      3: {
          'awake': 1,
          'walkDelay': 0,
         },
      4: {
          'awake': 0,
          'walkDelay': 0,
         },
      5: {
          'awake': 0,
          'walkDelay': 0,
         }
    },
'B': {
      1: {
          'awake': 'onCamera-0',
          'walkDelay': 0,
         },
      2: {
          'awake': 'onCamera-3',
          'walkDelay': .3,
         },
      3: {
          'awake': 'onCamera-2',
          'walkDelay': .15,
         },
      4: {
          'awake': 'onCamera-1',
          'walkDelay': 0,
         },
      5: {
          'awake': 'onCamera-1',
          'walkDelay': 0,
         }
    },
'C': {
      1: {
          'awake': 0,
          'walkDelay': 0,
         },
      2: {
          'awake': 'onCamera-0',
          'walkDelay': 0,
         },
      3: {
          'awake': 'onCamera-0',
          'walkDelay': .05,
         },
      4: {
          'awake': 'onCamera-3',
          'walkDelay': 0,
         },
      5: {
          'awake': 'onCamera-2',
          'walkDelay': 0,
         }
    }
}

class Cog(Actor):
    anims = ("victory", "walk", "neutral")
    speedMap = {'A': 10, 'B': 15, 'C': 12}
    
    def __init__(self, type):
        model = self.locateModelFile(type)
        animMap = {}
        
        for anim in Cog.anims:
            animMap[anim] = self.locateAnimFile(anim, type)
            
        Actor.__init__(self, model, animMap)
        self.type = type
        self.walkPath = None
        self.speed = Cog.speedMap[self.type]
        
    def locateModelFile(self, type):
        if not base.withinTTH:
            return "data/suit%s.bam" % type
            
        return "phase_5/models/char/cog%s_robot-zero" % type
        
    def locateAnimFile(self, animName, type):
        if not base.withinTTH:
            return "data/suit%s-%s.bam" % (type, animName)
            
        phase = 4
        if type == "C":
            if animName in ('walk', 'neutral'):
                phase = 3.5
                
        return "phase_%s/models/char/suit%s-%s" % (phase, type, animName)
        
    def initialiseAIBehaviours(self, night, quadrant=None):
        self.awake = False
        
        self.behaviours = CogBehaviours[self.type][night]
        awakeTime = self.behaviours['awake']
        if isinstance(awakeTime, str):
            _, awakeTime = awakeTime.split('-')
            awakeTime = int(awakeTime)
            self.acceptOnce("cameraSeeing%s" % quadrant, self.__doAwake)
            
        self.__awakeTime = awakeTime
            
        self.accept("enterHour", self.__doAwake)
        
    def __doAwake(self, hour=None):
        if hour is not None:
            if hour != self.__awakeTime:
                return
                
        self.awake = True
        delay = self.behaviours['walkDelay'] * Timer.secondsPerHour
        taskMgr.doMethodLater(delay, self.__startWalking, self.taskName('startWalking'))
        
    def __startWalking(self, task=None):
        self.point = CogPoint.fromTypeStart(self.type)
        self.walkToPoint(self.point.getNextPoint())
        
        if task:
            return task.done
            
    def walkToPoint(self, point):
        def complete():
            self.loop('neutral')
            self.setP(0)
            self.setR(0)
            point.reached(self)
            
        here = self.getPos()
        target = point.getPos()
        
        dist = (here - target).length()
        time = dist / self.speed
        
        self.loop('walk')
        self.lookAt(Point3(target))
        self.walkPath = Sequence(self.posInterval(time, target, here), Func(complete))
        self.walkPath.start()
        
    def stopAIBehaviours(self):
        self.awake = False
        self.ignoreAll()
        self.loop('neutral')
        taskMgr.remove(self.taskName("startWalking"))
        taskMgr.remove(self.taskName("nextPoint"))
        if self.walkPath:
            self.walkPath.pause()
            self.walkPath = None
            
    def danceAndGameOver(self):
        Sequence(ActorInterval(self, 'victory'), EventInterval('gameFailed')).start()
        
    def taskName(self, string):
        return "Cog-%s-%d" % (string, id(self))
        
    def resetPos(self):
        self.setPos(CogPoint.fromTypeStart(self.type).getPos())
        
        if self.type == "A": self.setH(220)
        elif self.type == "B": self.setH(40)
        elif self.type == "C": self.setH(155)
        