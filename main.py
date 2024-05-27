import random
from math import fabs
from functools import partial
import sys
import pygame
from pygame.locals import RESIZABLE, VIDEORESIZE, QUIT
import json

# back end



with open("data.json") as dataFile:
    data = json.load(dataFile)
    names = data["names"]
    items = data["items"]

with open("settings.json") as settingsFile:
    settings = json.load(settingsFile)

# This class is used by all rooms and entities that can hold/contain items
class Inventory():

    def __init__(self):

        # This dictionary contains the name of each item held as a key and the number of each item as the value
        self.__inventory = {}

    # This prints every item in the dictionary
    def seeInventory(self):
        if not self.isEmpty():

            # save current sideList
            save = sideList.get()

            items = []
            for i in self.__inventory.items():
                if i[1]>1:
                    items.append(listLabel(f"{i[0]} ({i[1]})"))
                else:
                    items.append(listLabel(str(i[0])))
            items.append(noneListButton("exit",(partial(sideList.update,save),)))
            sideList.update(items)
        else:
            textBox.say("Your inventory is empty")

    # This checks whether an item is in the dictionary
    def has(self, item):
        return item in self.__inventory

    # This removes a used item from the inventory
    def use(self, item):
        if self.__inventory[item] == 1:
            del self.__inventory[item]
        else:
            self.__inventory[item] -= 1

    # This adds an item to the dictionary
    def get(self, item):
        if self.has(item):
            self.__inventory[item] += 1
        else:
            self.__inventory[item] = 1

    # This returns the raw dictionary
    def getInventory(self):
        return self.__inventory

    def isEmpty(self):
        if self.__inventory == {}:
            return True
        else:
            return False


# Used to manage all the different rooms
class Map():

    def __init__(self):

        # contains each room instance in the order they were generated
        # (though an order based on location would allow for a binary search through the array so implementation should be considered)
        self.__rooms = []
        self.makeRoom([0, 0])
        self.__rooms[0].enter(player)
        textBox.say(f"You spawned in a {self.__rooms[0].getRoomDescription()}")

    # generates a new room
    def makeRoom(self, location):

        # randomly selects the type of room and adds it to the rooms array
        self.kindsOfRooms = [Kitchen,
                             TreasureRoom,
                             QuarterMastersRoom,
                             Dungeon,
                             Room
                            ]
        self.__rooms.append(random.choice(self.kindsOfRooms)(location[::]))

    # checks if a room has already been generated
    def roomExists(self, location):

        # linear search through rooms
        for i in self.__rooms:
            if location == i.getLocation():
                return True
        return False

    # returns the room instance at a certain location
    def findRoom(self, location):

        # by a linear search
        for i in self.__rooms:
            if location == i.getLocation():
                return i


# these are things that move around the rooms, like the player
class Entity():
    def __init__(self, location):
        self._location = location[::]
        self.__moved = True

    def setLocalLocation(self, location):
        self._localLocation = location
        self.__moved = False

    def getImage(self):
        if hasattr(self, "_image"):
            return self._image
        else:
            return False

    def getLocation(self):
        return self._location

    def update(self):
        pass

    def getMoved(self):
        return self.__moved

    def getLocalLocation(self):
        return self._localLocation

class Being(Entity):
    def __init__(self,location):
        super().__init__(location)
        self._name = random.choice(names)
        self._holding = Inventory()
        self._health = settings["defaultHP"]
        self._attack = settings["defaultAttack"]
        self._species = "no species (error)"
    def takeDamage(self, health):
        self._health -= health
        if self._health <= 0:
            if player.getLocation() == self._location:
                textBox.say(f"{self._name} the {self._species} died")
            gameMap.findRoom(self._location).leave(self)
            entities.remove(self)
    def regenerate(self, health):
        self._health += health

    def attack(self, entity):
        if self._location == player._location:
            textBox.say(
                f"{self._name} the {self._species} attacked {entity.getName()} the {entity.getSpecies()} and did {self._attack} damage")
        entity.takeDamage(self._attack)

    def move(self, vector):
        gameMap.findRoom(self._location).leave(self)
        self._location[0] += vector[0]
        self._location[1] += vector[1]
        self.__moved = True
        if not gameMap.roomExists(self._location):
            gameMap.makeRoom(self._location)
        gameMap.findRoom(self._location).enter(self)

    def goTo(self, entity):
        if self._location != entity.getLocation():
            if fabs(entity.getLocation()[0] - self._location[0]) > fabs(entity.getLocation()[1] - self._location[1]):
                if entity.getLocation()[0] - self._location[0] > 0:
                    self.move([1, 0])
                else:
                    self.move([-1, 0])
            else:
                if entity.getLocation()[1] - self._location[1] > 0:
                    self.move([0, 1])
                else:
                    self.move([0, -1])
    def pickUp(self, item):

        # removes item from room and adds it to the entity
        gameMap.findRoom(self._location).getRoomItems().remove(item)
        self._holding.get(item.getType())

    def getInventory(self):
        return self._holding

    def getActions(self):
        actions.append(listButton(f"attack {self._name} the {self._species}", (partial(player.attack, self),)))

    def getSpecies(self):
        return self._species

    def getName(self):
        return self._name

    def getHP(self):
        return self._health

    def getAttack(self):
        return self._attack

    def give(self, entity, item):
        self._holding.use(item)
        entity.getInventory().get(item)

class Player(Being):
    def __init__(self, username):
        super().__init__([0, 0])
        self._species = "player"
        self._name = username
        self._image = pygame.image.load("sprites/humanAccurateProportions.png").convert_alpha()
        header.updateHP(self._health)
        header.updateAttack(self._attack)

    def look(self, where):
        room = gameMap.findRoom([self._location[0] + where[0], self._location[1] + where[1]])

        seen = []

        seen.append(f"There's {room.getRoomDescription()}")
        if room.getRoomItems():
            seen.append("The items in the room are:")
            for i in room.getRoomItems():
                seen.append(i.getType())

        if room.beingsInside:
            seen.append("The beings in this room are:")
            for i in room.beingsInside:
                seen.append(f"{i.getName()} the {i.getSpecies()}")
        return seen

    def regenerate(self, health):
        super().regenerate(health)
        header.updateHP(self._health)

    def update(self):
        for i in range(-settings["renderDistance"], settings["renderDistance"]+1):
            for j in range(-settings["renderDistance"], settings["renderDistance"]+1):
                place = [self._location[0] + i, self._location[1] + j]
                if not gameMap.roomExists(place):
                    gameMap.makeRoom(place)

    def takeDamage(self, health):
        super().takeDamage(health)
        header.updateHP(self._health)
        if self._health <= 0:
            cutScene(["you died"])
            pygame.quit()
            sys.exit()


class Troll(Being):
    def __init__(self, location):
        super().__init__(location)
        self._species = "troll"
        self._image = pygame.image.load("sprites/troll.png").convert_alpha()

    def update(self):
        moves = [[0, 1], [1, 0], [-1, 0], [0, -1]]
        if random.random() < settings["trollMovementChance"]:
            self.move(random.choice(moves))

        for i in gameMap.findRoom(self._location).beingsInside:
            if random.random() < settings["trollAttackChance"] and i != self:
                self.attack(i)


class Prisoner(Being):
    def __init__(self, location, freer):
        super().__init__(location)
        self._species = "prisoner"
        self.__freer = freer
        self._image = pygame.image.load("sprites/humanAccurateProportions.png").convert_alpha()

    def update(self):
        self.goTo(self.__freer)
        if self._location == self.__freer.getLocation():
            for i in gameMap.findRoom(self._location).beingsInside:
                if i.getSpecies() == "troll":
                    self.attack(i)
                    break


'''
class Goblin(Entity):
    def __init__(self,location):
        super().__init__(location)
        self._species = "goblin"

    def update(self):
        for i in range(-1,1):
            for j in range(-1,1):
                if gameMap.roomExists([self._location[0]+i,self._location[1]+j]) and any(i.getSpecies() == "player" for i in gameMap.findRoom([self._location[0]+i,self._location[1]+j]).inside):
                    #the following code will not work in multiplayer games so will have to be modified if I want to add that functionality:
                    self.goTo(player)
'''


# immovable regions in which entities can move between
class Room():
    def __init__(self, location):
        self._location = location
        self._roomDescription = "an empty room"
        self._contains = []

        # stores entities in the room
        self.inside = []
        self.beingsInside = []

        # randomly decides whether the room houses a troll
        if random.random() < settings["trollSpawnChance"]:
            newTroll = Troll(self._location[::])
            self.enter(newTroll)
            entities.append(newTroll)

        '''
        if random.random() > 0:
            newGoblin = Goblin(self.__location[::])
            self.inside.append(newGoblin)
            entities.append(newGoblin)
        '''

        if random.random() < settings["itemSpawnChance"]:
            self._contains.append(Item(random.choice(list(items.keys()))))

    def leave(self, entity):
        self.beingsInside.remove(entity)
        self.inside.remove(entity)

    def enter(self, entity):
        self.beingsInside.append(entity)
        self.inside.append(entity)

    def getLocation(self):
        return self._location

    def getRoomDescription(self):
        return self._roomDescription

    def getRoomItems(self):
        return self._contains

    def getActions(self):

        # allows an entity in the room to pick up an item in the room
        for i in self.getRoomItems():
            actions.append(listButton(f"pick up {i.getType()}", (partial(player.pickUp, i),)))

        for i in self.inside:
            i.getActions()

    def seeRoomEntities(self):
        for i in self.beingsInside:
            print(f"{i.getName()} the {i.getSpecies()}")


class Kitchen(Room):
    def __init__(self, location):
        super().__init__(location)
        self._roomDescription = "a dusty abandoned kitchen"
        foods = ["grape", "porridge", "potato"]
        for _ in range(random.randint(0, 5)):
            self._contains.append(Item(random.choice(foods)))


class QuarterMastersRoom(Room):
    def __init__(self, location):
        super().__init__(location)
        self._roomDescription = "a decrepit abandoned quarter master's room"
        for _ in range(random.randint(0, 5)):
            if random.random() > 0.5:
                if random.random() > 0.5:
                    self._contains.append(Item("bronzeKey"))
                else:
                    if random.random() > 0.25:
                        self._contains.append(Item("silverKey"))
                    else:
                        self._contains.append(Item("goldKey"))
            else:
                self._contains.append(Item("dungeonKey"))

class treasureChest(Entity):
    def __init__(self,location):
        super().__init__(location)
        self._chestOpened = False
    def getActions(self):
        actions.append(listButton(f"open treasure chest", (self.openTreasure,)))

class gold(treasureChest):
    def __init__(self,location):
        super().__init__(location)
        self._image = pygame.image.load("sprites/goldChest.png").convert_alpha()
    def openTreasure(self):
        if not self._chestOpened:
            if player.getInventory().has("goldKey"):
                self._chestOpened = True
                self._image = pygame.image.load("sprites/openGoldChest.png").convert_alpha()
                player.getInventory().use("goldKey")
                cutScene(["you got the gold treasure and won the game"])

                pygame.quit()
                sys.exit()

            else:
                textBox.say("you wasted a turn trying to open a locked gold treasure chest without a gold key")
        else:
            textBox.say("You wasted a turn opening an already opened treasure chest")

class silver(treasureChest):
    def __init__(self,location):
        super().__init__(location)
        self._image = pygame.image.load("sprites/silverChest.png").convert_alpha()
    def openTreasure(self):
        if not self._chestOpened:
            if player.getInventory().has("silverKey"):
                self._chestOpened = True
                self._image = pygame.image.load("sprites/openSilverChest.png").convert_alpha()

                lines = []

                lines.append("you looted:")
                silverLoot = ["porridge", "potato", "silverKey", "goldKey", "dungeonKey"]
                player.getInventory().use("silverKey")
                for i in range(random.randint(4, 7)):
                    item = random.choice(silverLoot)
                    lines.append(f"a {item}")
                    player.getInventory().get(item)

                cutScene(lines)

            else:
                textBox.say("you wasted a turn trying to open a locked silver treasure chest without a silver key")
        else:
            textBox.say("You wasted a turn opening an already opened treasure chest")

class bronze(treasureChest):
    def __init__(self,location):
        super().__init__(location)
        self._image = pygame.image.load("sprites/bronzeChest.png").convert_alpha()
    def openTreasure(self):
        if not self._chestOpened:
            if player.getInventory().has("bronzeKey"):
                self._chestOpened = True
                self._image = pygame.image.load("sprites/openBronzeChest.png").convert_alpha()

                lines = []

                lines.append("you looted:")
                bronzeLoot = ["grape", "porridge", "potato", "bronzeKey", "silverKey", "dungeonKey"]
                player.getInventory().use("bronzeKey")
                for i in range(random.randint(2, 5)):
                    item = random.choice(bronzeLoot)
                    lines.append(f"a {item}")
                    player.getInventory().get(item)

                cutScene(lines)

            else:
                textBox.say("you wasted a turn trying to open a locked bronze treasure chest without a bronze key")
        else:
            textBox.say("You wasted a turn opening an already opened treasure chest")

class wood(treasureChest):
    def __init__(self,location):
        super().__init__(location)
        self._image = pygame.image.load("sprites/woodChest.png").convert_alpha()

    def openTreasure(self):
        if not self._chestOpened:
            self._chestOpened = True
            self._image = pygame.image.load("sprites/openWoodChest.png").convert_alpha()

            lines = []

            lines.append("you looted:")
            woodLoot = ["grape", "porridge", "bronzeKey", "dungeonKey"]
            for i in range(random.randint(1, 3)):
                item = random.choice(woodLoot)
                lines.append(f"a {item}")
                player.getInventory().get(item)

            cutScene(lines)
        else:
            textBox.say("You wasted a turn opening an already opened treasure chest")

class TreasureRoom(Room):
    def __init__(self, location):
        super().__init__(location)
        self.__tier = random.choice(["gold","silver","bronze","wood"])
        self._roomDescription = f"a room with a {self.__tier} treasure chest"
        self._chestOpened = False

        self.inside.append(eval(self.__tier+"("+str(self._location)+")"))

class cell(Entity):
    def __init__(self,location):
        super().__init__(location)
        self.__dungeonOpened = False
        self.__began = pygame.time.get_ticks()

    def getActions(self):
        actions.append(listButton(f"open dungeon", (self.openDungeon,)))

    def openDungeon(self):
        if not self.__dungeonOpened:
            if player.getInventory().has("dungeonKey"):
                player.getInventory().use("dungeonKey")
                self.__dungeonOpened = True
                newPrisoner = Prisoner(self.getLocation()[::], player)
                gameMap.findRoom(self.getLocation()).enter(newPrisoner)
                entities.append(newPrisoner)

            else:
                textBox.say("You wasted a turn trying to open a locked dungeon without a dungeonKey")
        else:
            textBox.say("You wasted a turn opening an already opened dungeon")

    def getImage(self):
        if self.__dungeonOpened:
            return pygame.image.load("sprites/emptyCell.png").convert_alpha()
        else:
            return getAnimation(self.__began,80,"animations/inCell")

class Dungeon(Room):
    def __init__(self, location):
        super().__init__(location)
        self._roomDescription = "a locked dungeon with a despondent prisoner"
        self.inside.append(cell(self._location))

class Item():
    def __init__(self,type):
        self.__type = type
        self.__image = pygame.image.load("sprites/"+items[type]).convert_alpha()
        self.__image = pygame.transform.rotate(self.__image, random.random() * 360)
        self.__localLocation = (random.random(),random.random())

    def getType(self):
        return self.__type

    def getImage(self):
        return self.__image

    def getLocalLocation(self):
        return self.__localLocation


# front end
pygame.init()

# default values on startup though game window is resizable
width = settings["defaultWidth"]
height = settings["defaultHeight"]
screen = pygame.display.set_mode((width, height), RESIZABLE)
pygame.display.set_caption("game")
pygame.display.set_icon(pygame.image.load("icons/largePixelatedSword.png").convert_alpha())

with open("dialogue.json") as dialogueFile:
    dialogue = json.load(dialogueFile)


def cutScene(lines, speed=settings["cutSceneSpeed"]):
    global width
    global height
    global screen

    defaultFont = pygame.font.Font("font.ttf", min(int(defaultFontSize * height), int(defaultFontSize * width)))

    nextLineTimer = pygame.USEREVENT + 1
    pygame.time.set_timer(nextLineTimer, speed)

    for line in lines:
        nextLine = False

        line = eval("f\"" + line + "\"")
        cutSceneLabel = defaultFont.render(line, False, "white")
        while not nextLine:

            for event in pygame.event.get():

                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()

                elif event.type == VIDEORESIZE:
                    width, height = event.size
                    screen = pygame.display.set_mode((width, height), RESIZABLE)

                    # font is resized
                    defaultFont = pygame.font.Font("font.ttf",
                                                   min(int(defaultFontSize * height), int(defaultFontSize * width)))
                    cutSceneLabel = defaultFont.render(line, False, "white")

                elif event.type == nextLineTimer:
                    nextLine = True

                elif event.type == pygame.KEYDOWN and event.key == 13:
                    nextLine = True
                    pygame.time.set_timer(nextLineTimer, speed)

            screen.fill("black")
            screen.blit(cutSceneLabel,
                        (width / 2 - cutSceneLabel.get_width() / 2, height / 2 - cutSceneLabel.get_height() / 2))

            pygame.display.update()

def getAnimation(begin, max_frames, path):
    time_per_frame = 1000 // 24  # Calculate time in milliseconds for each frame at 24 FPS
    elapsed_time = pygame.time.get_ticks() - begin
    frame = (elapsed_time // time_per_frame) % max_frames + 1
    frame_str = f"{frame:04d}"  # Format frame number with leading zeros

    image_path = f"{path}/{frame_str}.png"
    return pygame.image.load(image_path).convert_alpha()

# contains hp and attack
class Header():

    def __init__(self, size, spacingFactor):
        self.__size = size
        self.__spacingFactor = spacingFactor
        self.__spacing = height * self.__size / self.__spacingFactor

        self.__heart = pygame.image.load("icons/heart.png").convert_alpha()
        self.__heart = pygame.transform.scale(self.__heart, (height * self.__size, height * self.__size))
        self.__sword = pygame.image.load("icons/sword.png").convert_alpha()
        self.__sword = pygame.transform.scale(self.__sword, (height * self.__size, height * self.__size))
        self.__font = pygame.font.Font("font.ttf", int(height * self.__size * 2))
        self.__hpValue = str(settings["defaultHP"])
        self.__attackValue = str(settings["defaultAttack"])
        self.__hp = self.__font.render(self.__hpValue, False, "white")
        self.__attack = self.__font.render(self.__attackValue, False, "white")

    def resize(self, width, height):
        self.__spacing = height * self.__size / self.__spacingFactor
        self.__heart = pygame.image.load("icons/heart.png").convert_alpha()
        self.__heart = pygame.transform.scale(self.__heart, (height * self.__size, height * self.__size))
        self.__sword = pygame.image.load("icons/sword.png").convert_alpha()
        self.__sword = pygame.transform.scale(self.__sword, (height * self.__size, height * self.__size))
        self.__font = pygame.font.Font("font.ttf", int(height * self.__size * 2))
        self.__hp = self.__font.render(self.__hpValue, False, "white")
        self.__attack = self.__font.render(self.__attackValue, False, "white")

    def updateHP(self, newHP):
        self.__hpValue = str(newHP)
        self.__hp = self.__font.render(self.__hpValue, False, "white")

    def updateAttack(self, newAttack):
        self.__attackValue = str(newAttack)
        self.__attack = self.__font.render(self.__attackValue, False, "white")

    def render(self):
        place = self.__spacing
        screen.blit(self.__heart, (place, 0))
        place = place + self.__heart.get_width() + self.__spacing
        screen.blit(self.__hp, (place, 0))
        place = place + self.__hp.get_width() + self.__spacing
        screen.blit(self.__sword, (place, 0))
        place = place + self.__sword.get_width() + self.__spacing
        screen.blit(self.__attack, (place, 0))


class RoomRenderer():
    def __init__(self, wallHeight, doorWidth, topLeft, width, height):
        self.__wallHeight = wallHeight
        self.__doorWidth = doorWidth

        self.resize(topLeft, width, height)

    def resize(self, topLeft, width, height):
        self.__topLeft = topLeft
        self.__width = width
        self.__height = height

        self.__rectWidth = self.__wallHeight * min(self.__height, self.__width) / 2

        self.__absoluteDoorWidth = self.__doorWidth * min(self.__height, self.__width)
        self.__rectLengthVertical = (self.__height - self.__absoluteDoorWidth) / 2
        self.__rectLengthHorizontal = (self.__width - self.__absoluteDoorWidth) / 2

        self.__topLeftTop = pygame.rect.Rect(self.__topLeft[0], self.__topLeft[1], self.__rectLengthHorizontal,
                                             self.__rectWidth)
        self.__topLeftBottom = pygame.rect.Rect(self.__topLeft[0], self.__topLeft[1], self.__rectWidth,
                                                self.__rectLengthVertical)
        self.__topRightTop = pygame.rect.Rect(self.__topLeft[0] + self.__width - self.__rectLengthHorizontal,
                                              self.__topLeft[1], self.__rectLengthHorizontal, self.__rectWidth)
        self.__topRightBottom = pygame.rect.Rect(self.__topLeft[0] + self.__width - self.__rectWidth, self.__topLeft[1],
                                                 self.__rectWidth, self.__rectLengthVertical)
        self.__bottomLeftTop = pygame.rect.Rect(self.__topLeft[0],
                                                self.__topLeft[1] + self.__height - self.__rectLengthVertical,
                                                self.__rectWidth, self.__rectLengthVertical)
        self.__bottomLeftBottom = pygame.rect.Rect(self.__topLeft[0],
                                                   self.__topLeft[1] + self.__height - self.__rectWidth,
                                                   self.__rectLengthHorizontal, self.__rectWidth)
        self.__bottomRightTop = pygame.rect.Rect(self.__topLeft[0] + self.__width - self.__rectWidth,
                                                 self.__topLeft[1] + self.__height - self.__rectLengthVertical,
                                                 self.__rectWidth, self.__rectLengthVertical)
        self.__bottomRightBottom = pygame.rect.Rect(self.__topLeft[0] + self.__width - self.__rectLengthHorizontal,
                                                    self.__topLeft[1] + self.__height - self.__rectWidth,
                                                    self.__rectLengthHorizontal, self.__rectWidth)

    def updateRoom(self):
        self.__renderedEntities = []
        for entity in currentRoom.inside:
            if entity.getImage():
                if entity.getMoved():
                    entity.setLocalLocation((random.random(), random.random()))
                self.__renderedEntities.append(entity)

        self.__renderedItems = []
        for item in currentRoom.getRoomItems():
            self.__renderedItems.append(item)

        self.__renderedThings = sorted(self.__renderedItems+self.__renderedEntities,key=lambda x:x.getLocalLocation()[1])
    def render(self):
        pygame.draw.rect(screen, "white", self.__topLeftTop)
        pygame.draw.rect(screen, "white", self.__topLeftBottom)
        pygame.draw.rect(screen, "white", self.__topRightTop)
        pygame.draw.rect(screen, "white", self.__topRightBottom)
        pygame.draw.rect(screen, "white", self.__bottomLeftTop)
        pygame.draw.rect(screen, "white", self.__bottomLeftBottom)
        pygame.draw.rect(screen, "white", self.__bottomRightTop)
        pygame.draw.rect(screen, "white", self.__bottomRightBottom)

        for thing in self.__renderedThings:
            screen.blit(thing.getImage(),(int(self.__rectWidth+self.__topLeft[0]+thing.getLocalLocation()[0]*(self.__width-2*self.__rectWidth-50)),int(self.__rectWidth+self.__topLeft[1]+thing.getLocalLocation()[1]*(self.__height-2*self.__rectWidth-90))))

class TextBox():
    def __init__(self, size):
        self.__size = size
        self.__texts = []

    def resize(self, width, height):
        if self.__texts:
            self.__fontSize = min(int(self.__size * height * 2 / len(self.__texts)),int(width*3/len(max(self.__texts,key=lambda x: len(x[0]))[0])))
            self.__font = pygame.font.Font("font.ttf", self.__fontSize)

    def say(self, text, time=settings["textBoxSpeed"]):
        self.__texts.append((text, pygame.time.get_ticks(), time))
        self.__fontSize = min(int(self.__size * height * 2/len(self.__texts)),int(width*3/len(max(self.__texts, key=lambda x: len(x[0]))[0])))
        self.__font = pygame.font.Font("font.ttf", self.__fontSize)

    def render(self):
        # pygame.draw.line(screen, "white", (0, (1 - self.__size) * height), (width, (1 - self.__size) * height))
        for i, text in enumerate(self.__texts):
            screen.blit(self.__font.render(text[0], False, "white"),
                        (0, (1 - self.__size) * height + i * self.__fontSize / 2))

        if self.__texts and pygame.time.get_ticks() - self.__texts[0][1] >= self.__texts[0][2]:
            self.__texts.pop(0)
            self.resize(width,height)

class listLabel():
    def __init__(self,text):
        self.__text = text
    def getText(self):
        return self.__text
    def getHoverColour(self):
        return "black"
    def command(self):
        pass

class listButton():
    def __init__(self,text,commands):
        self.__text = text
        self._commands = commands
    def getText(self):
        return self.__text
    def getHoverColour(self):
        return "gray"
    def command(self):
        global nextScene

        if not nextScene:
            for command in self._commands:
                command()
            nextScene = True

class noneListButton(listButton):
    def __init__(self,text,commands):
        super().__init__(text,commands)
    def command(self):

        if not nextScene:
            for command in self._commands:
                command()

class SideList():
    def __init__(self,size=settings["sideListSize"]):
        self.__items = []
        self.__size = size
        self.resize(width,height)

    def get(self):
        return self.__items

    def update(self,items):
        self.__items = items
        self.resize(width,height)

    def removeItem(self,item):
        self.__items.remove(item)
        self.resize(width,height)

    def addItem(self,item):
        self.__items.append(item)
        self.resize(width,height)

    def resize(self,width,height):
        if self.__items:
            self.__rectHeight = height*(1-settings["headerSize"]-settings["textBoxSize"]) / len(self.__items)
            self.__rectWidth = width * self.__size
            self.__fontSize = min(int(self.__rectHeight * 2),
                                  int(self.__rectWidth * 2.5 / len(max(self.__items, key=lambda x: len(x.getText())).getText())))
            self.__font = pygame.font.Font("font.ttf", self.__fontSize)

    def onClick(self):
        if pygame.mouse.get_pos()[0]>width*(1-self.__size):
            # admittedly, this is a linear search, sue me
            for i,item in enumerate(self.__items):
                if pygame.mouse.get_pos()[1]>height*settings["headerSize"]+i*self.__rectHeight and pygame.mouse.get_pos()[1]<height*settings["headerSize"]+(i+1)*self.__rectHeight:
                        item.command()
    def render(self):
        if pygame.mouse.get_pos()[0]>width*(1-self.__size):
            for i,item in enumerate(self.__items):
                if pygame.mouse.get_pos()[1]>height*settings["headerSize"]+i*self.__rectHeight and pygame.mouse.get_pos()[1]<height*settings["headerSize"]+(i+1)*self.__rectHeight:
                    screen.blit(self.__font.render(item.getText(), False, "white", item.getHoverColour()),(width*(1-self.__size),height*settings["headerSize"]+i*self.__rectHeight))
                else:
                    screen.blit(self.__font.render(item.getText(), False, "white"),
                                (width * (1-self.__size),height*settings["headerSize"]+i*self.__rectHeight))
        else:
            for i, item in enumerate(self.__items):
                screen.blit(self.__font.render(item.getText(), False, "white"),
                            (width * (1-self.__size),height*settings["headerSize"]+i*self.__rectHeight))

class directionButton():
    def __init__(self,size,direction,topLeft):
        self.__size = size
        self.__topLeft = topLeft
        self.__direction = direction

        self.resize(width,height)
    def resize(self,width,height):
        self.__width = max(width,height)*self.__size
        self.__verticalLength = height-settings["headerSize"]*height-settings["textBoxSize"]*height-2*self.__width
        self.__horizontalLength = width-2*settings["directionButtonSize"]*max(width,height)

        match self.__direction:

            case "left":
                self.__topLeft = (0,settings["headerSize"]*height + self.__width)
                self.__image = pygame.image.load("icons/arrowIcon.png").convert_alpha()
                self.__hoverImage = pygame.image.load("icons/arrowIconGrey.png").convert_alpha()
                self.__place = (self.__topLeft[0],self.__verticalLength/2-self.__width/2+self.__topLeft[1])
            case "up":
                self.__topLeft = (self.__width,settings["headerSize"]*height)
                self.__image = pygame.transform.rotate(pygame.image.load("icons/arrowIcon.png").convert_alpha(),270)
                self.__hoverImage = pygame.transform.rotate(pygame.image.load("icons/arrowIconGrey.png").convert_alpha(), 270)
                self.__place = (self.__horizontalLength/2-self.__width/2+self.__topLeft[0],self.__topLeft[1])
            case "right":
                self.__topLeft = (width-self.__width,settings["headerSize"]*height+self.__width)
                self.__image = pygame.transform.rotate(pygame.image.load("icons/arrowIcon.png").convert_alpha(), 180)
                self.__hoverImage = pygame.transform.rotate(pygame.image.load("icons/arrowIconGrey.png").convert_alpha(), 180)
                self.__place = (self.__topLeft[0], self.__verticalLength / 2 - self.__width/2 + self.__topLeft[1])
            case "down":
                self.__topLeft = (self.__width,height-settings["textBoxSize"]*height-self.__width)
                self.__image = pygame.transform.rotate(pygame.image.load("icons/arrowIcon.png").convert_alpha(), 90)
                self.__hoverImage = pygame.transform.rotate(pygame.image.load("icons/arrowIconGrey.png").convert_alpha(), 90)
                self.__place = (self.__horizontalLength / 2 - self.__width/2 + self.__topLeft[0], self.__topLeft[1])

        self.__image = pygame.transform.scale_by(self.__image,self.__width/10)
        self.__hoverImage = pygame.transform.scale_by(self.__hoverImage,self.__width/10)

    def onClick(self):
        global nextScene

        if pygame.mouse.get_pos()[0] > self.__place[0] and pygame.mouse.get_pos()[1] > self.__place[1] and pygame.mouse.get_pos()[0] < self.__place[0] + self.__width and pygame.mouse.get_pos()[1] < self.__place[1] + self.__width:

            match self.__direction:

                case "up":
                    player.move([0, 1])
                    textBox.say(f"You entered {gameMap.findRoom(player.getLocation()).getRoomDescription()}")
                case "down":
                    player.move([0, -1])
                    textBox.say(f"You entered {gameMap.findRoom(player.getLocation()).getRoomDescription()}")
                case "left":
                    player.move([-1, 0])
                    textBox.say(f"You entered {gameMap.findRoom(player.getLocation()).getRoomDescription()}")
                case "right":
                    player.move([1, 0])
                    textBox.say(f"You entered {gameMap.findRoom(player.getLocation()).getRoomDescription()}")

            nextScene = True

    def render(self):
        if pygame.mouse.get_pos()[0] > self.__place[0] and pygame.mouse.get_pos()[1] > self.__place[1] and pygame.mouse.get_pos()[0] < self.__place[0] + self.__width and pygame.mouse.get_pos()[1] < self.__place[1] + self.__width:
            screen.blit(self.__hoverImage,self.__place)
        else:
            screen.blit(self.__image,self.__place)

# proportion of screen taken up by font
defaultFontSize = settings["defaultFontSize"]

defaultFont = pygame.font.Font("font.ttf", min(int(defaultFontSize * height), int(defaultFontSize * width)))
usernameLabel = defaultFont.render("Username: ", False, "white")
username = ""
inputBox = defaultFont.render(username, False, "white")


# intro
nextScene = False

while not nextScene:

    for event in pygame.event.get():

        if event.type == QUIT:
            pygame.quit()
            sys.exit()

        elif event.type == VIDEORESIZE:
            width, height = event.size
            screen = pygame.display.set_mode((width, height), RESIZABLE)

            # font is resized
            defaultFont = pygame.font.Font("font.ttf", min(int(defaultFontSize * height), int(defaultFontSize * width)))
            usernameLabel = defaultFont.render("Username: ", False, "white")
            inputBox = defaultFont.render(username, False, "white")

        elif event.type == pygame.KEYDOWN:

            # if letter and lower case
            if event.key >= 97 and event.key <= 133:

                # first key is capitalised
                if username == "":
                    username += chr(event.key - 32)
                else:
                    username += chr(event.key)

            # backspace
            elif event.key == 8:
                username = username[:-1]

            # enter
            elif event.key == 13:
                nextScene = True

            # rerender input box as has been modified
            inputBox = defaultFont.render(username, False, "white")

    screen.fill("black")
    screen.blit(usernameLabel, (width / 2 - usernameLabel.get_width(), height / 2 - usernameLabel.get_height() / 2))
    screen.blit(inputBox, (width / 2, height / 2 - usernameLabel.get_height() / 2))

    pygame.display.update()


header = Header(settings["headerSize"], settings["headerSpacingFactor"])
textBox = TextBox(settings["textBoxSize"])
roomRenderer = RoomRenderer(settings["wallHeight"], settings["doorWidth"], (0, settings["headerSize"] * height), width*(1-settings["sideListSize"]), height * (1-settings["headerSize"]-settings["textBoxSize"]))
sideList = SideList()
left = directionButton(settings["directionButtonSize"],"left",(0,(settings["headerSize"]+settings["directionButtonSize"])*height))
right = directionButton(settings["directionButtonSize"],"right",((1-settings["directionButtonSize"])*width,settings["headerSize"]*height+settings["directionButtonSize"]*height))
up = directionButton(settings["directionButtonSize"],"up",(settings["directionButtonSize"]*width,settings["headerSize"]*height))
down = directionButton(settings["directionButtonSize"],"down",(settings["directionButtonSize"]*width,(1-settings["textBoxSize"]-settings["directionButtonSize"])*height))

player = Player(username)
cutScene(dialogue["defaultIntro"])

def gameLoop1(actions=[]):
    global width
    global height
    global screen
    global nextScene

    header.resize(width, height)
    textBox.resize(width, height)
    roomRenderer.resize((0, settings["headerSize"] * height), width*(1-settings["sideListSize"]), height * (1-settings["headerSize"]-settings["textBoxSize"]))
    roomRenderer.updateRoom()
    sideList.update(actions)
    sideList.resize(width,height)

    nextScene = False
    while not nextScene:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == VIDEORESIZE:
                width, height = event.size
                screen = pygame.display.set_mode((width, height), RESIZABLE)

                header.resize(width, height)
                textBox.resize(width, height)
                roomRenderer.resize((0, settings["headerSize"] * height), width*(1-settings["sideListSize"]),
                                    height * (1 - settings["headerSize"] - settings["textBoxSize"]))
                sideList.resize(width,height)
            elif event.type == pygame.MOUSEBUTTONUP:
                sideList.onClick()

        screen.fill("black")
        header.render()
        textBox.render()
        roomRenderer.render()
        sideList.render()

        pygame.display.update()

def gameLoop2():
    global width
    global height
    global screen
    global nextScene

    header.resize(width, height)
    textBox.resize(width, height)
    roomRenderer.resize((settings["directionButtonSize"]*max(width,height), settings["headerSize"] * height+settings["directionButtonSize"]*max(width,height)), max(width,height) * (1-2*settings["directionButtonSize"]),
                        height - settings["headerSize"]*height - settings["textBoxSize"]*height-2*settings["directionButtonSize"]*max(width,height))
    roomRenderer.updateRoom()
    left.resize(width,height)
    right.resize(width, height)
    up.resize(width, height)
    down.resize(width, height)

    nextScene = False
    while not nextScene:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == VIDEORESIZE:
                width, height = event.size
                screen = pygame.display.set_mode((width, height), RESIZABLE)

                header.resize(width, height)
                textBox.resize(width, height)
                roomRenderer.resize((0, settings["headerSize"] * height), width * (1 - settings["sideListSize"]),
                                    height * (1 - settings["headerSize"] - settings["textBoxSize"]))
                sideList.resize(width, height)
                left.resize(width,height)
                right.resize(width,height)
                up.resize(width,height)
                down.resize(width,height)

            elif event.type == pygame.MOUSEBUTTONUP:
                left.onClick()
                right.onClick()
                up.onClick()
                down.onClick()

        screen.fill("black")
        header.render()
        textBox.render()
        roomRenderer.render()
        left.render()
        right.render()
        up.render()
        down.render()

        pygame.display.update()

entities = []
entities.append(player)
gameMap = Map()

# no functionality for now:
moveNumber = 0

while True:
    moveNumber += 1

    for i in entities:
        i.update()

    currentRoom = gameMap.findRoom(player.getLocation())

    # stores available actions. Each action takes the tuple form (description,(functions),((function parameter),(function parameter)...))
    actions = [listButton("look around", (partial(cutScene,["you looked north"]+player.look([0, 1])+["you looked south"]+player.look([0, -1])+["you looked east"]+player.look([1, 0])+["you looked west"]+player.look([-1, 0])),))]

    currentRoom.getActions()

    if player.getInventory().has("grape"):
        actions.append(
            listButton("eat grape (+2HP)", (partial(player.regenerate, 2), partial(player.getInventory().use, "grape"))))
    if player.getInventory().has("porridge"):
        actions.append(listButton("eat porridge (+5HP)",
                        (partial(player.regenerate, 5), partial(player.getInventory().use, "porridge"))))
    if player.getInventory().has("potato"):
        actions.append(
            listButton("eat potato (+10HP)", (partial(player.regenerate, 10), partial(player.getInventory().use, "potato"))))

    # stores available actions that do not take up a turn.
    actions += [
        noneListButton("check inventory", (player.getInventory().seeInventory,))]

    gameLoop1(actions)
    gameLoop2()
