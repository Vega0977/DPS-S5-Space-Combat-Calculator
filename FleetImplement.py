import pygame
from pygame.locals import *
from math import *
import random
import sys
import re
import os

pygame.init()

FPS = 30
FramePerSec = pygame.time.Clock()

#colors
BLUE  = (0, 0, 255, 140)
RED   = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRIDYELLOW = (239, 242, 0)
INFOGRAY = (105,105,105)

#specialized functions
def pointtest(point,drawpoints):
    #drawpoints is a list containing points defining your polygon
    #point is the mouse position
    #if it doesn't work, list them in opposite order.
    #works for arbitrary convex geometry
    x = point[0]
    y = point[1]
    Lines = []
    index = 0
    for index in range(len(drawpoints)): #might need to mess with drawpoints to work with the hex system
        p0 = drawpoints[index]
        try: p1 = drawpoints[index+1]
        except: p1 = drawpoints[0]
        Lines.append([p0,p1])
    for l in Lines:
        p0 = l[0]
        p1 = l[1]
        x0 = p0[0]; y0 = p0[1]
        x1 = p1[0]; y1 = p1[1]
        test = (y - y0)*(x1 - x0) - (x - x0)*(y1 - y0)
        if test < 0: return False
    return True

def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1
    #little program to assess length of input file

def assemble_hexmap(corner, Hex1, Hex2, height, fillcolor, edgecolor, lwidth):
    #corner is a two value list (tuple?) for the *center* of the upper left hexagon
    #hex1 is the width in hexagons, hex2 is the height
    #fillcolor is the hexagon fill, edgecolor is the hexagon lines
    #lwidth is the width of the lines
    #height is the height from the center of the hexagon to the top edge
    radius = (2*height)/sqrt(3) #assuming I understand what it uses as 'radius' correctly
    n, r = 6, radius #n is general but here hardcoded to 6
    #Creates the hex grid's value table
    HexCoord = []
    x, y = corner[0], corner[1]
    incre = 0
    for i in range (0, Hex1):
        for i in range (0, Hex2):
            points = [
                (x + r * cos(2 * pi * i / n), y + r * sin(2 * pi * i / n),)
                for i in range(n)
            ]
            HexCoord.append([points, edgecolor, fillcolor, lwidth, [], 0]) #[] is the ship/station contents, 0 is terrain
            y = y+(2*height)
        incre += 1
        y = corner[1] + (height)*(-1*(incre % 2))
        x = x+(2*(height))
    return(HexCoord)

def hex_seeker(target, radius, team=0, checkhex=0, team_only=False, include_empty=False, list_ships=True, shipnames=False, checkhexmode = False):
    global shiplist
    #looks for all hexes within range that satisfy conditions. team = 0 includes all ships, any other number filters to anything but that number
    #unless you set team_only true, in which case it returns only ships of the specified team
    #shiplist says whether or not it returns a list of all hexes with valid ships or just a list of the ships straight up. Both have uses.
    radius = int(radius)
    topoffset = 1
    wideoffset = 25
    outrange = 0
    inrange = [] #list of hexes
    shipinrange = [] #list of ship objects
    if checkhexmode == True:
        inrange.append(checkhex)
        inrange = [checkpoint for checkpoint in inrange if -1+abs(target//25 - checkpoint//25)<radius and -1+abs(target%25 - checkpoint%25)<radius]
        if not inrange:
            return False
        if inrange:
            return True
    if include_empty == True:
        inrange.append(target)
        for x in range(0, radius):
            for i in range(0, len(inrange)):
                inrange.append(int(inrange[i])+topoffset)
                inrange.append(int(inrange[i])-topoffset)
                inrange.append(int(inrange[i])+wideoffset)
                inrange.append(int(inrange[i])-wideoffset)
                inrange.append(int(inrange[i])+wideoffset+((inrange[i]//mapheight)%2*-2)+1)
                inrange.append(int(inrange[i])-wideoffset+((inrange[i]//mapheight)%2*-2)+1)
                outrange += 1
    if include_empty == False:
        for ship in shiplist:
            inrange.append(ship.hex)
        if inrange.count(target):
            inrange.remove(target)
        #then i check to see if they're actually in range
        inrange = [checkpoint for checkpoint in inrange if -1+abs(target//25 - checkpoint//25)<radius and -1+abs(target%25 - checkpoint%25)<radius]
    shipinrange = [itemcheck[0] for itemcheck in [hexgrid[hexcheck][4] for hexcheck in inrange] if itemcheck != []]
    shipinrange = list(set(shipinrange))
    inrange = list(set(inrange))
    if include_empty:
        inrange = [possiblecheck for possiblecheck in inrange if not possiblecheck > len(hexgrid) and not possiblecheck < 0]
        return(inrange)
    if team != 0 and team_only==False:
        inrange = [hexcheck for hexcheck in inrange if [hexlooker for hexlooker in hexgrid[hexcheck][4] if hexlooker.team != team] != []]
        shipinrange = []
        for hexcheck in inrange:
            shipinrange.extend([hexlooker for hexlooker in hexgrid[hexcheck][4] if hexlooker.team != team])
    if team != 0 and team_only==True:
        inrange = [hexcheck for hexcheck in inrange if [hexlooker for hexlooker in hexgrid[hexcheck][4] if hexlooker.team == team] != []]
        shipinrange = []
        for hexcheck in inrange:
            shipinrange.extend([hexlooker for hexlooker in hexgrid[hexcheck][4] if hexlooker.team == team])
    if list_ships:
        shipinrange = [item for item in shipinrange if item != []]
        shipinrange = list(set(shipinrange))
        if shipnames:
            shipinrange = [item.name for item in shipinrange]
        return(shipinrange)
    if not list_ships:
        return(inrange)
    #searches for valid ships within a certain radius of a hex

def typecount(ship):
    return(len([unit for unit in hexgrid[ship.hex][4] if unit.ship_type == ship.ship_type]))

allweapons_dict = {}
def load_outfile(parsefile, classname):
    with open(parsefile, "r") as infi:
        infi.seek(0,0)
        input_len = int(file_len(parsefile))
        buffer = ''
        dict_define = {}
        beginread = False
        object_list = []
        object_number = -1
        for x in range(0, input_len):
            buffer = infi.readline()
            if str(re.match('BEGIN', buffer)) != 'None':
                beginread = True
            elif beginread:
                key = re.match('[a-zA-Z_]+', buffer)[0]
                value = re.search('\[.*\]', buffer)[0]
                dict_define[key] = list(map(float, value[1:-1].split(", ")))
                object_number += 1
                object_list.append(classname(key, dict_define))
                exec("globals()[key] = object_list[object_number]") # fucked up, plz no bulli
                if classname == Static_Weapon or classname == Evasion_Weapon or classname == Tracking_Weapon:
                    global allweapons_dict
                    allweapons_dict[key] = object_list[object_number] #changes go here
        return(dict_define) #not what may be expected lol

def load_shipfiles(shippath):
    shipfilelist = os.listdir(shippath) #just straight loads the stuff in the directory. Will need to redo if I add more things than shipfiles.
    beginread = False
    for shipfile in shipfilelist:
        load_outship(shipfile)
        #load shipfile here, and create the ship object. Ready for GUI placing.

shipdict = {}
shiplist = []
def load_outship(parsefile):
    parsefile = "ships\\" + parsefile
    global shiplist
    with open(parsefile, "r") as infi:
        infi.seek(0,0)
        input_len = int(file_len(parsefile))
        buffer = ''
        ship_attributes = []
        beginread = False
        object_number = -1
        for x in range(0, input_len):
            buffer = infi.readline()
            if str(re.match('BEGIN', buffer)) != 'None':
                beginread = True
            elif beginread:
                key = re.match('[a-zA-Z_]+', buffer)[0]
                value = re.search('\[.*\]', buffer)[0]
                ship_attributes.extend(value.split("] "))#[1:-1].split(", "))
                object_number += 1
        if beginread != True:
            return
        shipname = ship_attributes[0][1:-1]
        shipname = Ship(shipname)
        #exec("globals()[ship_attributes[0]] = shipname") # fucked up, plz no bulli
        #metastats
        #self.image involves code for checking ship type = pygame.image.load("sprites\Enemy_Destroyer.png")
        #self.surf = pygame.Surface((20, 10)) #approximate size of the icon
        shipname.hex = -1 #supposed to be inert until the initialization loop, which uses the value set in placement mode
        shipname.team = int(ship_attributes[1][1]) #might be dumb way to do this
        #turns the strings from the file into their respective objects
        ship_attributes[0] = "'NULL'"
        for attribute in ship_attributes:
            ship_attributes[ship_attributes.index(attribute)] = eval(attribute)
        #ship build specifics
        shipname.shiptype = ship_attributes[2][0]
        shipname.static_weapon = ship_attributes[3]
        shipname.tracking_weapon = ship_attributes[4]
        shipname.evasion_weapon = ship_attributes[5]
        shipname.docked_ships = ship_attributes[6]
        shipname.weapon_targets = {} #dictionary w/ weapon group as keys and the remaining unused weapons as values. For use in the attack gamemode.
        shipname.struc_utility = ship_attributes[7]
        shipname.computer = ship_attributes[8][0]
        shipname.ftl = ship_attributes[9][0]
        shipname.thruster = ship_attributes[10][0]
        shipname.auxiliary = ship_attributes[11]
        shipname.reactor = ship_attributes[12][0]
        if ship_attributes[13]: #temporary workaround until I decide on a permament fix
            shipname.network = ship_attributes[13][0]
        else:
            shipname.network = ship_attributes[13]
        shipname.sensor = ship_attributes[14][0]
        shipname.nsc = ship_attributes[15]
        shipname.rectat = 0
        shipdict[shipname.name] = shipname
        initialize(shipname)
        shiplist.append(shipname)

def create_strike_craft(component, mother):
    global shiplist
    newcraft = Ship("Strike Craft")
    if Basic_Fighter_Craft or Advanced_Fighter_Craft == component:
        newcraft.name = mother.name+"'s Fighter Craft"
        newcraft.evasion_weapon = [component]
    if Basic_Strike_Craft or Advanced_Strike_Craft == component:
        newcraft.name = mother.name+"'s Strike Craft"
        newcraft.static_weapon = [component]
    newcraft.team = mother.team
    newcraft.hex = mother.hex
    newcraft.hex_range = mother.hex_range
    newcraft.shiptype = component
    newcraft.computer = Basic_Computer
    newcraft.ftl = mother.ftl
    newcraft.thruster = mother.thruster
    newcraft.reactor = mother.reactor
    newcraft.sensor = mother.sensor
    newcraft.mother = mother
    initialize(newcraft)
    shiplist.append(newcraft)
    return(newcraft)

#drawing functions
#single hex is the function for just one hex, it takes the point information and draws it on the screen
def draw_single_hex(surface, hexmap, hexnumber, fill):
    points = hexmap[hexnumber][0]
    lx, ly = zip(*points) #selects points component of hex entry. might need to fuck with *
    min_x, min_y, max_x, max_y = min(lx), min(ly), max(lx), max(ly)
    target_rect = pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
    shape_surf = pygame.Surface(target_rect.size, pygame.SRCALPHA)
    if fill == False:
        pygame.draw.polygon(shape_surf, hexmap[hexnumber][1], [(x - min_x, y - min_y) for x, y in points], hexmap[hexnumber][3])
        surface.blit(shape_surf, target_rect)
    else:
        pygame.draw.polygon(shape_surf, hexmap[hexnumber][2], [(x - min_x, y - min_y) for x, y in points], hexmap[hexnumber][3])
        surface.blit(shape_surf, target_rect)
#drawing function needs to draw in two iterations, one with fill and one for edge. It takes
#info about the corners of the screen its drawing to, and the upperleftmost hex it starts on.
def update_grid_display(surface, hexmap, ulcorner, lrcorner, height, fill):
#^two last variables are height and width of full map
    #pygame.draw.rect(surface, GREEN, (ulcorner,lrcorner), width=2) this makes a box around it if i wanted that
    heightwise = floor((lrcorner[1]-ulcorner[1])/(2*height))
    widthwise = floor((lrcorner[0]-ulcorner[0])/(2*(height+.5))) #off because of the gap, need to figure out
    hexnumber = -1 #hopefully doesn't break anything
    hexdown = 0
    hexacross = 0
    while hexacross <= widthwise:
        while hexdown != heightwise:
            draw_single_hex(surface, hexmap, hexnumber, fill)
            for x in range(0,len(hexmap[hexnumber][4])):
                hexmap[hexnumber][4][x].draw(surface, hexmap[hexnumber][0][0][0]-((2*height)/sqrt(3)), (0)+hexmap[hexnumber][0][0][1]+0)
                    #places sprite on the right vector and adjusts to the left by the radius of the hexagon -((2*height)/sqrt(3))
            hexnumber += 1
            hexdown += 1
        hexdown = 0
        hexacross += 1
        hexnumber = (hexacross*mapheight)-1
def draw_regular_polygon(surface, color, vertex_count, radius, position, width, rotate=0):
    n, r = vertex_count, radius
    x, y = position
    rotate = int(rotate/2)
    points = [
        (x + r * cos((2 * pi * i / n) +rotate), y + r * sin((2 * pi * i / n)+ rotate),)
        for i in range(n)
    ]
    lx, ly = zip(*points)
    min_x, min_y, max_x, max_y = min(lx), min(ly), max(lx), max(ly)
    target_rect = pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
    shape_surf = pygame.Surface(target_rect.size, pygame.SRCALPHA)
    pygame.draw.polygon(shape_surf, color, [(x - min_x, y - min_y) for x, y in points], width)
    surface.blit(shape_surf, target_rect)
    return(points)

def hex_clicker(pos):
    if pos[0] < mapdrawwidth and pos[1] < mapdrawheight:
        for i in range(len(hexgrid)):
            if pointtest(pos, hexgrid[i][0]):
                return(i)

hexinfo_sprites = pygame.sprite.Group()
def update_hexinfo_display(selecthex):
    spritegroup = pygame.sprite.Group()
    #draw the rectangle
    #can't be transparent, might need to fix later  #lot of global vars here, possibly not good
    icondowngap = 40
    iconacrossgap = 40
    if selecthex == 'Blank':
        pygame.draw.rect(DisplaySurf, INFOGRAY, (mapdrawwidth, 0, hexinfowidth, hexinfoheight))
    else:
        pygame.draw.rect(DisplaySurf, INFOGRAY, (mapdrawwidth, 0, hexinfowidth, hexinfoheight))
        heightwise = floor((hexinfoheight)/(icondowngap)) #parenthesis might be fucked up here
        widthwise = floor(((hexinfowidth)/(iconacrossgap)))
        iconnumber = 0 #hopefully doesn't break anything
        icondown = 0
        iconacross = 0
        #while iconnumber != len(hexgrid[selecthex][4]):
        while iconacross <= widthwise and iconnumber != len(hexgrid[selecthex][4]):
            while icondown != heightwise and iconnumber != len(hexgrid[selecthex][4]):
                #draw_single_hex(surface, hexmap, hexnumber, fill) <-- not sure what to do with this
                #possibly add in stuff about names and ship health, also ship class i think
                hexgrid[selecthex][4][iconnumber].draw(DisplaySurf, (mapdrawwidth+30)+(iconacrossgap*iconacross), 30+(icondowngap*icondown))
                spritegroup.add(hexgrid[selecthex][4][iconnumber])
                hexgrid[selecthex][4][iconnumber].center = (mapdrawwidth+30)+(iconacrossgap*iconacross), 30+(icondowngap*icondown)
                        #probably shouldn't use iconnumber here, but instead come up with the thing to pick the biggest ship
                        #offset from upperleft corner of infobox is arbitary
                        #places sprite just within the upperleft corner of box and then moves by the spacing number and position in loop
                icondown += 1
                iconnumber += 1
                icondown = 0
                iconacross += 1
            #uses the same code as the hex-filler to dynamically fill in space icons with ships
            #then it draws all the little spaceships
    return(spritegroup) #experimental

lowermenu_rects = []
def sprite_clicker(pos):
    global game_mode
    rect1 = Rect(mapdrawwidth-70, mapdrawheight, 70, 20) #attack button rectangle
    icondown = 0
    iconacross = 0
    #code to check if any of the hexinfo sprites have been clicked and draw their contents. Loops in the main loop, might need to rework when i set up modes
    if hexinfo_sprites.sprites() != []:
        for i in range(0, len(hexinfo_sprites)):
            current_sprite = hexinfo_sprites.sprites()[i]
            sprite_rect = current_sprite.recton(current_sprite.center)
            if pygame.Rect.collidepoint(sprite_rect, pos):
                pygame.draw.rect(DisplaySurf, INFOGRAY, (0, mapdrawheight, mapdrawwidth, screenheight-mapdrawheight))
                font = pygame.font.SysFont(None, 24)
                icondowngap = 40
                #iconacrossgap = len(str(current_sprite.all_weapons).replace('[', ''))*5 #half-hearted approximation
                iconacrossgap = 2500
                heightwise = (screenheight-mapdrawheight)/icondowngap
                widthwise = (mapdrawwidth/iconacrossgap)
                iconnumber = 0
                while iconacross <= widthwise and iconnumber != len(current_sprite.tracking_weapon) + len(current_sprite.static_weapon) + len(current_sprite.evasion_weapon):
                    while icondown != heightwise and iconnumber != len(current_sprite.tracking_weapon) + len(current_sprite.static_weapon) + len(current_sprite.evasion_weapon):
                        #add in weapon color coding at some point
                        for w in current_sprite.all_weapons:
                            img = font.render(w[0].name+' x '+str(w[1]), True, BLUE)
                            lowermenu_rects.append(img)
                            DisplaySurf.blit(img, (0+(iconacrossgap*iconacross), mapdrawheight+30+(icondowngap*icondown)))
                            icondown += 1
                        iconnumber += 1
                        icondown = 0
                        iconacross += 1
        #Attack Button
                pygame.draw.rect(DisplaySurf, RED, rect1)
                font = pygame.font.SysFont(None, 24) 
                img = font.render('ATTACK', True, BLACK)
                DisplaySurf.blit(img, (mapdrawwidth-70, mapdrawheight))
            if rect1.collidepoint(pos):
                DisplaySurf.fill(BLACK)
                attack_mode_setup(current_sprite)
                targets_menu(current_sprite, current_sprite.all_weapons[0][0])

def conclude_turn_button(pos=(0,0)):
    global game_mode
    global turncounter
    global attacklist
    global attackresults
    rect1 = Rect(mapdrawwidth+70, mapdrawheight+70, 70, 20) #conclude turn button rectangle
    rect2 = Rect(mapdrawwidth-70, mapdrawheight, 70, 20) #begin new turn button rectangle
    if game_mode !=5:
        pygame.draw.rect(DisplaySurf, RED, rect1)
        font = pygame.font.SysFont(None, 24) 
        img = font.render('FINISH TURN', True, BLACK)
        DisplaySurf.blit(img, (mapdrawwidth+70, mapdrawheight+70))
        if rect1.collidepoint(pos):
            game_mode = 5
            attackresults = process_attacks(attacklist)
            for ship in shiplist: #resets weapon_targets
                for weapon in ship.all_weapons:
                    ship.weapon_targets[weapon[0]] = weapon[1]
    if game_mode == 5:
        DisplaySurf.fill(RED)
        pygame.draw.rect(DisplaySurf, RED, rect2)
        font = pygame.font.SysFont(None, 24) 
        img = font.render('BEGIN NEW TURN', True, BLACK)
        DisplaySurf.blit(img, (mapdrawwidth-70, mapdrawheight))
        eventcounter = 0
        for attack in attackresults:
            eventcounter +=1
            img = font.render(attack, True, BLACK)
            DisplaySurf.blit(img, (600, 30*eventcounter))
        if rect2.collidepoint(pos):
            DisplaySurf.fill(BLACK)
            game_mode = 2
            turncounter += 1
            attacklist = []
            attackresults = []

shiptoplace = 0 #set as nullship in setup commands, included here as a reminder that it is global
def movement_mode():
    global game_mode
    game_mode = 2
    for ship in shiplist:
        ship.hex_range_left = ship.hex_range
        if ship.gravity_well:
            ship.hex_range_left = min(ship.hex_raneg_left, 6)

docking_ship = 0
def select_movement(pos):
    global shiptoplace
    global dockoptions
    global docking_ship
    # a lot of this code is derived from the sprite_clicker function above
    rect1 = Rect(mapdrawwidth-90, mapdrawheight+90, 90, 20) #move ship button rectangle
    rect2 = Rect(mapdrawwidth-90, mapdrawheight+70, 90, 20) #deploy strike vessel setup
    rect3 = Rect(mapdrawwidth-400, mapdrawheight+90, 200, 20) #deploy strike craft
    rect4 = Rect(mapdrawwidth-400, mapdrawheight+110, 200, 20) #deploy fighter craft
    rect5 = Rect(mapdrawwidth-400, mapdrawheight+70, 200, 20) #return craft to ship
    font = pygame.font.SysFont(None, 24) 
    if hexinfo_sprites.sprites() != []:
        for i in range(0, len(hexinfo_sprites)):
            current_sprite = hexinfo_sprites.sprites()[i]
            sprite_rect = current_sprite.recton(current_sprite.center)
            if pygame.Rect.collidepoint(sprite_rect, pos): 
                pygame.draw.rect(DisplaySurf, BLUE, rect1)
                img = font.render('MOVE SHIP', True, BLACK)
                DisplaySurf.blit(img, (mapdrawwidth-90, mapdrawheight+90))
                if current_sprite.docked_ships != []:
                    pygame.draw.rect(DisplaySurf, BLUE, rect3)
                    img = font.render('DEPLOY STRIKE CRAFT', True, BLACK)
                    DisplaySurf.blit(img, (mapdrawwidth-400, mapdrawheight+90))
                    pygame.draw.rect(DisplaySurf, BLUE, rect4)
                    img = font.render('DEPLOY FIGHTER CRAFT', True, BLACK)
                    DisplaySurf.blit(img, (mapdrawwidth-400, mapdrawheight+110))
                if current_sprite.shiptype.ship_type == 14 or current_sprite.shiptype.ship_type == 15:
                    pygame.draw.rect(DisplaySurf, BLUE, rect5)
                    img = font.render('RETURN FIGHTER CRAFT', True, BLACK)
                    DisplaySurf.blit(img, (mapdrawwidth-400, mapdrawheight+70))
            if rect1.collidepoint(pos):
                shiptoplace = current_sprite
                draw_ship_range()
            if rect3.collidepoint(pos) and current_sprite.docked_ships.count(Basic_Strike_Craft or Advanced_Strike_Craft):
                relevant_strike_craft = current_sprite.docked_ships.index(Basic_Strike_Craft or Advanced_Strike_Craft)
                shiptoplace = create_strike_craft(current_sprite.docked_ships[relevant_strike_craft], current_sprite)
                draw_ship_range()
                del current_sprite.docked_ships[relevant_strike_craft]
            if rect4.collidepoint(pos) and current_sprite.docked_ships.count(Basic_Fighter_Craft or Advanced_Fighter_Craft):
                relevant_fighter_craft = current_sprite.docked_ships.index(Basic_Fighter_Craft or Advanced_Fighter_Craft)
                shiptoplace = create_strike_craft(current_sprite.docked_ships[relevant_fighter_craft], current_sprite)
                draw_ship_range()
                del current_sprite.docked_ships[relevant_fighter_craft]
            if rect5.collidepoint(pos):
                dockoptions.option_list = hex_seeker(current_sprite.hex, current_sprite.hex_range, team=current_sprite.team, team_only=True, shipnames=True)
                docking_ship = current_sprite
                
def redock_ship(shipwithdock, dockingship):
    shipwithdock.docked_ships.append(dockingship)
    dockingship.remove()
    dockoptions.option_list = []

def draw_ship_range(clear=False):
    if shiptoplace.hex_range > 8:
        return
    hexspace = hex_seeker(shiptoplace.hex, shiptoplace.hex_range_left, include_empty=True, list_ships=False)
    if not clear:
        for hextocolor in hexspace:
            hexgrid[hextocolor][1] = BLUE
    if clear:
        for hextocolor in hexspace:
            hexgrid[hextocolor][1] = GRIDYELLOW

def place_ship(pos):
    global shiptoplace
    ship = shiptoplace
    if shiptoplace == Nullship:
        return
    if ship.hex_range_left == 0:
        shiptoplace = Nullship
        return
    if ship != Nullship:
        if hex_clicker(pos):
            if hex_seeker(ship.hex, ship.hex_range_left, checkhex=hex_clicker(pos), checkhexmode=True):
                draw_ship_range(clear=True)
                if hexgrid[ship.hex][4].count(ship):
                    ship.remove()
                DisplaySurf.fill(BLACK)
                ship.add(hex_clicker(pos))
                ship.hex_range_left = 0 #at some point it'd be nice to let you move multiple times in a turn, but not today
                shiptoplace = Nullship
            else:
                if shiptoplace.mother != "Null" and shiptoplace.mother.hex == shiptoplace.hex:
                    shiptoplace.mother.docked_ships.append(shiptoplace)
                    shiptoplace = Nullship

def finish_movement(pos=(0,0)):
    global game_mode
    rect1 = Rect(mapdrawwidth-135, mapdrawheight+125, 135, 20) #finish movement button rectangle
    pygame.draw.rect(DisplaySurf, BLUE, rect1)
    font = pygame.font.SysFont(None, 24) 
    img = font.render('FINISH MOVEMENT', True, BLACK)
    DisplaySurf.blit(img, (mapdrawwidth-135, mapdrawheight+125))
    if rect1.collidepoint(pos):
        game_mode = 1
        DisplaySurf.fill(BLACK)

def attack_mode():
    pygame.draw.rect(DisplaySurf, BLACK, (0, 0, screenwidth, screenheight))
    font = pygame.font.SysFont(None, 24)
    img = font.render("Deploy Weapons", True, BLUE)
    DisplaySurf.blit(img, (590, 100)) #x controls where it starts the letters, so it can't be perfectly central. Maybe something like the sprite draw function needs to be done.
    #draws and sets up the 'attack' mode, a grouping of functionalities
    #draw whole new screen
    
def targets_menu(attack_ship, selected_weapon):
    if type(selected_weapon) == str:
        selected_weapon = allweapons_dict[selected_weapon]
    enemy_ships = hex_seeker(attack_ship.hex, selected_weapon.hex_range, team = attack_ship.team, shipnames = True)
    #enemy_ships.remove(attack_ship.name)
    if enemy_ships != []:
        targetoptions.option_list = enemy_ships
    else:
        targetoptions.option_list = []
    targetoptions.option_list.insert(0, 'No Ship Selected')

def leave_attack_button(pos=(0,0)):
    global game_mode
    rect1 = Rect(mapdrawwidth-70, mapdrawheight+20, 40, 20)
    pygame.draw.rect(DisplaySurf, BLUE, rect1)
    font = pygame.font.SysFont(None, 24) 
    img = font.render('MAP', True, BLACK)
    DisplaySurf.blit(img, (mapdrawwidth-70, mapdrawheight+20))
    if rect1.collidepoint(pos):
        game_mode = 1
        DisplaySurf.fill(BLACK)
        global persisweaponoption
        persisweaponoption = -1
    weapon_selectgrid = {}

attacklist = []
def attack_button(attacking_ship, defending_ship, weapon, pos=(0,0)):
    global attacklist
    global weapon_selectgrid
    rect1 = Rect(mapdrawwidth-70, mapdrawheight+45, 170, 20)
    pygame.draw.rect(DisplaySurf, RED, rect1)
    font = pygame.font.SysFont(None, 24) 
    img = font.render('CONCLUDE ATTACKS', True, BLACK)
    DisplaySurf.blit(img, (mapdrawwidth-70, mapdrawheight+45))
    if rect1.collidepoint(pos):
        for key in weapon_selectgrid:
            for value in weapon_selectgrid[key]:
                attacklist.append((attacking_ship.name, key, weapon_selectgrid[key][value], value))
        for value1 in weapon_selectgrid:
            for value2 in weapon_selectgrid[value1]:
                weapon_selectgrid[value1][value2] = 0
        global persisweaponoption
        persisweaponoption = -1
        
def attack_mode_setup(attacking_ship):
    global attack_ship
    attack_ship = attacking_ship
    weaponoptions.option_list = [entry[0].name for entry in attack_ship.all_weapons]
    global game_mode
    game_mode = 3

weapon_selectgrid = {}
def selectgrid_setup(defend_ship):
    global weapon_selectgrid
    #Sets up the counting button matrix
    available_weapons = weaponoptions.option_list
    available_targets = targetoptions.option_list
    weapon_subselectgrid = {}
    for weapons in available_weapons:
        weapon_subselectgrid[weapons] = 0
    if not weapon_selectgrid.get(defend_ship):
        weapon_selectgrid[defend_ship] = weapon_subselectgrid
#    for targets in available_targets:
#        weapon_selectgrid[targets] = weapon_subselectgrid#[0 for i in range(0, len(available_targets))]

def counting_buttons(x, y, attack_ship, defend_ship, weapon, pos=(0,0)):
    global weapon_selectgrid
    persisweaponoption
    maxcount = 0
    if defend_ship == "No Ship Selected" or defend_ship == Nullship or attack_ship == Nullship:
        return
    if weapon == -1:
        weaponselectcount = 0
    else:
        weapon = allweapons_dict[weapon]
        maxcount = attack_ship.weapon_targets[weapon] #[weapondata[1] for weapondata in attack_ship.all_weapons if weapon == weapondata[0]][0]
        weaponselectcount = weapon_selectgrid[defend_ship][weapon.name] #now integrated with matrix system
    font = pygame.font.SysFont(None, 50)
    draw_regular_polygon(DisplaySurf, INFOGRAY, 3, 13, (x+30, y), 0, rotate=0)
    img = font.render(str(weaponselectcount), True, INFOGRAY)
    DisplaySurf.blit(img, (x-20, y-18))
    draw_regular_polygon(DisplaySurf, INFOGRAY, 3, 13, (x-30, y), 0, rotate=90)
    rect1 = Rect(x-40, y-30, 30, 60)
    rect2 = Rect(x+20, y-30, 30, 60)
    if rect1.collidepoint(pos):
        if weaponselectcount > 0:
            attack_ship.weapon_targets[weapon] += 1
            weapon_selectgrid[defend_ship][weapon.name] -= 1
    if rect2.collidepoint(pos):
        if maxcount > 0:
            attack_ship.weapon_targets[weapon] -= 1
            weapon_selectgrid[defend_ship][weapon.name] += 1
    else:
        pass

def attack_dialogue(attack_ship):
    attack_ship.draw(DisplaySurf, 300, 350) #these coordinates are arbitrary but symmetrical
    #defend_ship.draw(DisplaySurf, 1000, 350)
    selected_weapon = 0
    selected_defender = 0

def deploy_mode():
    global game_mode
    game_mode = 4
    #should open the main screen and set up the ship deployment stuff. Might need to incorporate a read outfile in here.

def load_ships():
    global shiplist    

deployshipnum = 0
def deploy_ship_load():
    deployship = shiplist[deployshipnum]
    pygame.draw.rect(DisplaySurf, WHITE, ((mapdrawwidth/2)-400, mapdrawheight, 800, 120)) #just stuck there to put them in the middle of the lower info box arae
    font = pygame.font.SysFont(None, 24)
    img = font.render(deployship.name + ' ' + deployship.shiptype.name + ' Team: ' + str(deployship.team), True, BLUE)
    DisplaySurf.blit(img, (mapdrawwidth/2-400, mapdrawheight))
    
def deploy_ship(pos):
    global deployshipnum
    deployship = shiplist[deployshipnum]
    hexnum = hex_clicker(pos)
    deployship.add(hexnum)
    deployshipnum += 1

def initialize(ship):
    global allweapons_dict
    powercost = 0
    powerexcess = 0 #calculate at end?
    base_speed = 0
    base_evasion = 0
    evasion_mult = 1
    base_hex = 0
    weapon_range_bonus = 0
    base_hull = 0
    base_armor = 0
    base_shields = 0
    hull_mult = 1
    shield_mult = 1
    mobile_tracking_bonus = 0
    mobile_evasion_bonus = 0
    accuracy_bonus = 0
    tracking_bonus = 0
    ship_size = 0 #1 = small, 2 = medium, 3 = large
    #probably most efficient to go component by component
    #SHIP GAME SETUP
    #icon stuff
    if ship.team == 1:
        teamcolor = "friendly"
    if ship.team == 2:
        teamcolor = "enemy"
    if ship.team > 2:
        teamcolor = "neutral"
    ship.image = pygame.image.load("icons\\"+teamcolor+"\\"+ship.shiptype.name+"\\"+teamcolor+"_"+ship.shiptype.name+".png")#just the plain image, no number
    #then we plop 'er down
    ship.add(ship.hex)
    #SHIP BASE STATS
    base_hull += ship.shiptype.hull_points
    base_hex += ship.shiptype.base_hex
    base_evasion += ship.shiptype.base_evasion
    if ship.shiptype.ship_type == 1 or 2:
        ship_size = 1
    else:
        ship_size = 2
    #STRUCTURAL UTILITIES
    for i in ship.struc_utility:
        powercost += i.power
        base_armor += i.armor
        base_shields += i.shields
        base_hull += i.hullpoints
    #COMPUTER
    powercost += ship.computer.power
    evasion_mult += ship.computer.evasion_mod
    base_evasion += ship.computer.evasion_base
    base_hex += ship.computer.hex_range_base
    tracking_bonus += ship.computer.tracking
    accuracy_bonus += ship.computer.accuracy
    weapon_range_bonus += ship.computer.weapon_range
    mobile_tracking_bonus += ship.computer.mobile_tracking
    mobile_evasion_bonus += ship.computer.mobile_evasion
    #FTL
    powercost += ship.ftl.power
    #THRUSTER
    if ship.shiptype.ship_type == 1:
        base_evasion += (5*ship.thruster.tech_level)
        powercost += 5+(5*ship.thruster.tech_level)
    if ship.shiptype.ship_type == 2:
        base_hex += 3
        base_evasion += (4*ship.thruster.tech_level)
    #AUXILIARY
    for i in ship.auxiliary:
        if ship.auxiliary[i].type == 1:
            pass
        if ship.auxiliary[i].type == 2:
            pass
        if ship.auxiliary[i].type == 3:
            base_hex += 1
            evasion_mult += .05
            powercost += 10
        if ship.auxiliary[i].type == 4:
            base_hex += 1
            evasion_mult += .10
            powerexcess  += 20
        if ship.auxiliary[i].type == 5:
            powercost += 20
        if ship.auxiliary[i].type == 6:
            powerexcess += 50
        if ship.auxiliary[i].type == 7:
            powerexcess += 100
        if ship.auxiliary[i].type == 8:
            powerexcess += 150
        if ship.auxiliary[i].type == 9:
            powerexcess += 200
        if ship.auxiliary[i].type == 10:
            powerexcess += 250
        if ship.auxiliary[i].type == 11:
            powercost += 10
            accuracy_bonus += 5
        if ship.auxiliary[i].type == 12:
            powercost += 20
            shield_mult += .1
        if ship.auxiliary[i].type == 13:
            powercost += 150
            #bomabardment accuracy + 10
        if ship.auxiliary[i].type == 14:
            powercost += 200
            #bombardment accuracy +20
        if ship.auxiliary[i].type == 15:
            powercost += 250
            #bombardment accuracy
    #REACTORS
    #this doesn't actually work right, because it turns out power generation isn't linear for every ship type. 
    corvettepower = [75, 100, 130, 170, 220, 285, 350, 375, 415, 480, 545]
    destroyerpower = [140, 180, 240, 320, 430, 550, 670, 790, 910, 1030, 1150]
    cruiserpower = [280, 360, 480, 620, 800, 1030, 1260, 1490, 1720, 1950, 2180]
    if ship.shiptype.ship_type == 1:
        powerexcess += corvettepower[int(ship.reactor.tech_level-1)]
    if ship.shiptype.ship_type == 2:
        powerexcess += destroyerpower[int(ship.reactor.tech_level-1)]
    if ship.shiptype.ship_type == 3:
        powerexcess += cruiserpower[int(ship.reactor.tech_level-1)]
    #SENSORS
    tracking_bonus += ship.sensor.tracking_bonus
    powercost += ship.sensor.power
    #sensor range + something
    #NSC
    if ship.nsc != []:
        if ship.nsc.type[0] == 1: #might not work, gotta check
            #sensor range + 2
            pass
    #accurate up to the third or fourth kind of nsc
    #FINAL STATS + ASSIGNMENT
        #make sure to include the modifiers in the ship attribute's, because that's how we'll do shooting
    #evasion = powerexcess - powercost <-- this isn't the formula for it, but evasion does get a boost from powerexcess in real Stellaris.
    ship.evasion = base_evasion*evasion_mult
    ship.weapon_range_bonus = weapon_range_bonus
    ship.maxhull = base_hull*hull_mult
    ship.shiphull = base_hull*hull_mult
    ship.shiparmor = base_armor
    ship.shipshields = base_shields*shield_mult
    ship.hex_range = base_hex
    ship.hex_range_left = base_hex
    ship.general_accuracy_bonus = accuracy_bonus
    ship.general_tracking_bonus = tracking_bonus
    ship.mobile_evasion_bonus = mobile_evasion_bonus
    ship.mobile_tracking_bonus = mobile_tracking_bonus
    #ALL WEAPONS SETUP
    #ram is here and also fucky
    allweapons_dict[ship.name+"'s Ram"] = Ramming(ship)
    ship.all_weapons.append(allweapons_dict[ship.name+"'s Ram"])
    ship.all_weapons.extend(ship.static_weapon)
    ship.all_weapons.extend(ship.tracking_weapon)
    ship.all_weapons.extend(ship.evasion_weapon)
    #then we convert this list of all indidivual weapons into a list of (weapon, count)
    ship.all_weapons = [(weapon, ship.all_weapons.count(weapon)) for weapon in ship.all_weapons]
    ship.all_weapons = list(set(ship.all_weapons))
    #WEAPON TARGETS SETUP
    for weapon in ship.all_weapons: 
        ship.weapon_targets[weapon[0]] = weapon[1]

def aura_applier():
    global shiplist
    for ship in shiplist:
        #each if statement is for the different types of aura-creating components/weapons
        if ship.tracking_weapon != []:
            for weapon in ship.tracking_weapon:
                for friendly in hex_seeker(ship.hex, weapon.hex_range, team=ship.team, team_only=True):
                    friendly.tracking_aura += 1

def terrain_applier():
    global shiplist
    for ship in shiplist:
        if hexgrid[ship.hex][5] == 1: #asteroid field
            ship.asteroid_field = True
        if hexgrid[ship.hex][5] == 2: #gravity well
            ship.gravity_well = True
        else:
            ship.asteroid_field = False
            ship.gravity_well = False

attackresults = []
def process_attacks(attackdata):
    global attackresults
    attackresults = []
    #attackdata = attacklist
    #clear out empty entries
    attackdata = [entry for entry in attackdata if entry[2] != 0]
    #transform into list of lists of objects
    attackdata = [[shipdict[entry[0]], shipdict[entry[1]], entry[2], allweapons_dict[entry[3]]] for entry in attackdata]
    attackdata.sort(key=lambda x: (int(x[3].damage), x[3].shield_mult != 0, x[3].shield_mult<1, x[3].armor_mult<1, x[3].hull_mult<1)) #sorts from last to first for some reason
    attackdata.reverse() #quick workaround
    for attack in attackdata:
        for i in range(0, attack[2]):
            evtrack_bonus = 0
            didhit = False
            if attack[3].is_ram:
                if max(5, random.randint(0, 100)) <= min(5,(min(0, (attack[0].hex_range-attack[1].hex_range)*25-attack[1].evasion))):
                    didhit = True
            if attack[3].is_missile:
                evtrack_bonus = max(0, (attack[1].tracking_aura*5) - attack[3].accuracy)
            if attack[1].gravity_well:
                if max(5, random.randint(0, 100)) <= (min(95, attack[3].accuracy-15) - (min(90, attack[1].evasion) - min(95, attack[3].tracking))):
                    didhit = True
            if not attack[1].gravity_well and not attack[3].is_ram:
                if max(5, random.randint(0, 100)+evtrack_bonus) <= (min(95, attack[3].accuracy) - (min(90, attack[1].evasion) - min(95, attack[3].tracking))):
                    didhit = True
            if didhit and not attack[3].is_ram:
                attackresults.append(attack[0].name+ " hits " + attack[1].name + " with " + attack[3].name + " for " + str(attack[3].damage) + " damage") 
                ship = attack[1]
                damageleft = attack[3].damage
                if damageleft > 0 and ship.shipshields > 0 and attack[3].shield_mult > 0:
                    ship.shipshields = ship.shipshields - damageleft*attack[3].shield_mult
                    damageleft = max(0, 0 - ship.shipshields)
                    ship.shipshields = max(0, ship.shipshields)
                    if ship.shipshields == 0:
                        attackresults.append(ship.name + "\'s shields destroyed")
                if ship.shiparmor > 0 and attack[3].armor_mult > 0:
                    ship.shiparmor = ship.shiparmor - damageleft*attack[3].armor_mult
                    damageleft = max(0, 0 - ship.shiparmor)
                    ship.shiparmor = max(0, ship.shiparmor)
                    if ship.shiparmor == 0:
                        attackresults.append(ship.name +"\'s armor destroyed")
                if damageleft > 0 and ship.shiphull > 0:
                    ship.shiphull = ship.shiphull - damageleft*attack[3].hull_mult
                    damageleft = max(0, 0 - ship.shiphull)
                    ship.shiphull = max(0, ship.shiphull)
                if ship.shiphull == 0:
                    attackresults.append(ship.name + " has been destroyed")
                    ship.remove()
            if didhit and attack[3].is_ram: #Newton's 3rd law
                attackresults.append(attack[0].name+ " rams " + attack[1].name + " and deals " + str(attack[3].damage) + " damage") 
                ship = attack[1]
                damageleft = attack[3].damage
                if damageleft > 0 and ship.shipshields > 0 and attack[3].shield_mult > 0:
                    ship.shipshields = ship.shipshields - damageleft*attack[3].shield_mult
                    damageleft = max(0, 0 - ship.shipshields)
                    ship.shipshields = max(0, ship.shipshields)
                    if ship.shipshields == 0:
                        attackresults.append(ship.name + "\'s shields destroyed")
                if ship.shiparmor > 0 and attack[3].armor_mult > 0:
                    ship.shiparmor = ship.shiparmor - damageleft*attack[3].armor_mult
                    damageleft = max(0, 0 - ship.shiparmor)
                    ship.shiparmor = max(0, ship.shiparmor)
                    if ship.shiparmor == 0:
                        attackresults.append(ship.name +"\'s armor destroyed")
                if damageleft > 0 and ship.shiphull > 0:
                    ship.shiphull = ship.shiphull - damageleft*attack[3].hull_mult
                    damageleft = max(0, 0 - ship.shiphull)
                    ship.shiphull = max(0, ship.shiphull)
                if ship.shiphull == 0:
                    attackresults.append(ship.name + " has been destroyed")
                    ship.remove()
                attackresults.append(attack[0].name+ " rams " + attack[1].name + " and receives " + str(attack[3].damage) + " damage") 
                ship = attack[0]
                damageleft = attack[3].damage
                if damageleft > 0 and ship.shipshields > 0 and attack[3].shield_mult > 0:
                    ship.shipshields = ship.shipshields - damageleft*attack[3].shield_mult
                    damageleft = max(0, 0 - ship.shipshields)
                    ship.shipshields = max(0, ship.shipshields)
                    if ship.shipshields == 0:
                        attackresults.append(ship.name + "\'s shields destroyed")
                if ship.shiparmor > 0 and attack[3].armor_mult > 0:
                    ship.shiparmor = ship.shiparmor - damageleft*attack[3].armor_mult
                    damageleft = max(0, 0 - ship.shiparmor)
                    ship.shiparmor = max(0, ship.shiparmor)
                    if ship.shiparmor == 0:
                        attackresults.append(ship.name +"\'s armor destroyed")
                if damageleft > 0 and ship.shiphull > 0:
                    ship.shiphull = ship.shiphull - damageleft*attack[3].hull_mult
                    damageleft = max(0, 0 - ship.shiphull)
                    ship.shiphull = max(0, ship.shiphull)
                if ship.shiphull == 0:
                    attackresults.append(ship.name + " has been destroyed")
                    ship.remove()
            else:
                attackresults.append(attack[0].name+ " misses " + attack[1].name + " with " + attack[3].name)
            #80 Accuracy 10 Tracking weapon trying to hit 55 evasion target :				
    #Chance to hit = 80 - (55 - 10) = 35%			/r 1d100<=35	1-35 "HIT"
    for ship in shiplist:
        asteroidtohit = 0
        if ship.asteroid_field:
            stype = ship.shiptype.ship_type
            if stype == 1:
                asteroidtohit = 6
            if stype < 7:
                asteroidtohit = 3+(ship.shiptype*2)
            if stype == 7:
                asteroidtohit = 14
            if stype == 8:
                asteroidtohit = 15
            if stype == 9:
                asteroidtohit = 17
            if stype == 10:
                asteroidtohit = 19
            if stype == 11:
                asteroidtohit = 23
            if stype == 12:
                asteroidtohit = 30
            if random.randint(0, 100) > asteroidtohit:
                if stype < 8:
                    asteroidhitlist.append(ship)
                if stype > 8:
                    asteroidhitlist.append(ship)
                    if random.randint(0, 100) > asteroidtohit:
                        asteroidhitlist.append(ship)
            for ship in asteroidhitlist:
                attackresults.append("Asteroid wallops " + ship + " for 200 damage")
                damageleft = 200
                if damageleft > 0 and ship.shipshields > 0:
                    ship.shipshields = ship.shipshields - damageleft
                    damageleft = max(0, 0 - ship.shipshields)
                    ship.shipshields = max(0, ship.shipshields)
                    if ship.shipshields == 0:
                        attackresults.append(ship.name + "\'s shields destroyed")
                if ship.shiparmor > 0:
                    ship.shiparmor = ship.shiparmor - damageleft
                    damageleft = max(0, 0 - ship.shiparmor)
                    ship.shiparmor = max(0, ship.shiparmor)
                    if ship.shiparmor == 0:
                        attackresults.append(ship.name +"\'s armor destroyed")
                if damageleft > 0 and ship.shiphull > 0:
                    ship.shiphull = ship.shiphull - damageleft
                    damageleft = max(0, 0 - ship.shiphull)
                    ship.shiphull = max(0, ship.shiphull)
                if ship.shiphull == 0:
                    attackresults.append(ship.name + " has been destroyed")
                    ship.remove()
    return(attackresults)

#Classes!
class OptionBox():
    def __init__(self, x, y, w, h, color, highlight_color, font, option_list, selected = 0):
        self.color = color
        self.highlight_color = highlight_color
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.option_list = option_list
        self.selected = selected
        self.draw_menu = False
        self.menu_active = False
        self.active_option = -1
    def draw(self, surf):
        pygame.draw.rect(surf, self.highlight_color if self.menu_active else self.color, self.rect)
        pygame.draw.rect(surf, (0, 0, 0), self.rect, 2)
        msg = self.font.render(self.option_list[self.selected], 1, (0, 0, 0))
        surf.blit(msg, msg.get_rect(center = self.rect.center))
        if self.draw_menu:
            for i, text in enumerate(self.option_list):
                rect = self.rect.copy()
                rect.y += (i+1) * self.rect.height
                pygame.draw.rect(surf, self.highlight_color if i == self.active_option else self.color, rect)
                msg = self.font.render(text, 1, (0, 0, 0))
                surf.blit(msg, msg.get_rect(center = rect.center))
            outer_rect = (self.rect.x, self.rect.y + self.rect.height, self.rect.width, self.rect.height * len(self.option_list))
            pygame.draw.rect(surf, (0, 0, 0), outer_rect, 2)
    def update(self, event_list):
        mpos = pygame.mouse.get_pos()
        self.menu_active = self.rect.collidepoint(mpos)
        self.active_option = -1
        for i in range(len(self.option_list)):
            rect = self.rect.copy()
            rect.y += (i+1) * self.rect.height
            if rect.collidepoint(mpos):
                self.active_option = i
                break
        if not self.menu_active and self.active_option == -1:
            self.draw_menu = False
        for event in event_list:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.menu_active:
                    self.draw_menu = not self.draw_menu
                elif self.draw_menu and self.active_option >= 0:
                    self.selected = self.active_option
                    self.draw_menu = False
                    return self.option_list[self.active_option]
        return -1

class Ship(pygame.sprite.Sprite):
    def __init__(self, shipname):
        super().__init__()
        #metastats
        self.image = pygame.image.load("icons\\enemy\\Basic_Corvette\\Enemy_Basic_Corvette.png") #default icon
        self.surf = pygame.Surface((self.image.get_rect()[2], self.image.get_rect()[3])) #approximate size of the icon
        self.name = shipname
        self.hex = 0
        self.team = 0
        #ship build specifics
        self.shiptype = ''
        self.static_weapon = []
        self.tracking_weapon = []
        self.evasion_weapon = []
        self.docked_ships = []
        self.all_weapons = []
        self.weapon_targets = {} #dictionary w/ weapon group as keys and the remaining unused weapons as values. For use in the attack gamemode.
        self.struc_utility = ''
        self.computer = ''
        self.ftl = ''
        self.thruster = ''
        self.auxiliary = ''
        self.reactor = ''
        self.network = ''
        self.sensor = ''
        self.nsc = []
        #ship stats
        self.evasion = 0
        self.maxhull = 0
        self.shiphull = 0
        self.shiparmor = 0
        self.shipshields = 0
        self.hex_range = 0
        self.hex_range_left = 0
        self.general_accuracy_bonus = 0
        self.general_tracking_bonus = 0
        self.mobile_evasion_bonus = 0
        self.mobile_tracking_bonus = 0
        self.weapon_range_bonus = 0
        self.tracking_aura = 0
        #misc
        self.asteroid_field = False
        self.gravity_well = False
        self.mother = "Null" #only used for craft and other launched ships
        self.rectat = 0
    def recton(self, xy): #probably working right
        self.rectat = self.surf.get_rect(center = (xy))
        return(self.rectat) 
    def draw(self, surface, x, y):
        surface.blit(self.image, self.image.get_rect(center = (x, y)))
    def add(self, hexat):
        self.hex = hexat
        hexgrid[hexat][4].append(self)
    def remove(self):
        hexgrid[self.hex][4].remove(self)
    def delete(self):
        hexgrid[self.hex][4].remove(self)
        shiplist.remove(self)

class Static_Weapon:
    def __init__(self, statwepname, statweapons_dict):
        self.is_missile = False
        self.is_ram = False
        self.name = statwepname
        self.tier = statweapons_dict[statwepname][0]
        self.slot = statweapons_dict[statwepname][1]
        self.damage = statweapons_dict[statwepname][2]
        self.tracking = statweapons_dict[statwepname][3]
        self.hex_range = statweapons_dict[statwepname][4]
        self.power_cost = statweapons_dict[statwepname][5]
        self.accuracy = statweapons_dict[statwepname][6]
        self.hull_mult = statweapons_dict[statwepname][7]
        self.armor_mult = statweapons_dict[statwepname][8]
        self.shield_mult = statweapons_dict[statwepname][9]
class Evasion_Weapon:
    def __init__(self, evasionwepname, evasionwep_dict):
        self.is_missile = True
        self.is_ram = False
        self.name = evasionwepname
        self.damage = evasionwep_dict[evasionwepname][0]
        self.evasion = evasionwep_dict[evasionwepname][1]
        self.tracking = evasionwep_dict[evasionwepname][2]
        self.hex_range = evasionwep_dict[evasionwepname][3]
        self.power = evasionwep_dict[evasionwepname][4]
        self.accuracy = evasionwep_dict[evasionwepname][5]
        self.hull_mult = evasionwep_dict[evasionwepname][6]
        self.armor_mult = evasionwep_dict[evasionwepname][7]
        self.shield_mult = evasionwep_dict[evasionwepname][8]
class Tracking_Weapon:
    def __init__(self, trackwepname, trackwep_dict):
        self.is_missile = False
        self.is_ram = False
        self.name = trackwepname
        self.damage = trackwep_dict[trackwepname][0]
        self.evasion = trackwep_dict[trackwepname][1]
        self.tracking = trackwep_dict[trackwepname][2]
        self.hex_range = trackwep_dict[trackwepname][3]
        self.power = trackwep_dict[trackwepname][4]
        self.accuracy = trackwep_dict[trackwepname][5]
        self.hull_mult = trackwep_dict[trackwepname][6]
        self.armor_mult = trackwep_dict[trackwepname][7]
        self.shield_mult = trackwep_dict[trackwepname][8]
class Struc_Utility:
    def __init__(self, utilname, strucutils_dict):
        self.name = utilname
        self.slot = strucutils_dict[utilname][0]
        self.power = strucutils_dict[utilname][1]
        self.armor = strucutils_dict[utilname][2]
        self.shields = strucutils_dict[utilname][3]
        self.hullpoints = strucutils_dict[utilname][4]
class Computer:
    def __init__(self, computername, computers_dict):
        self.name = computername
        self.strat_type = computers_dict[computername][0]
        self.evasion_mod = computers_dict[computername][1]
        self.evasion_base = computers_dict[computername][2]
        self.tracking = computers_dict[computername][3]
        self.accuracy = computers_dict[computername][4]
        self.weapon_range = computers_dict[computername][5]
        self.hex_range_base = computers_dict[computername][6]
        self.mobile_tracking = computers_dict[computername][7]
        self.mobile_evasion = computers_dict[computername][8]
        self.power = computers_dict[computername][9]
class FTL:
    def __init__(self, ftlname, ftl_dict):
        self.name = ftlname
        self.tech_level = ftl_dict[ftlname][0]
        self.power = ftl_dict[ftlname][1]
class Sensor:
    def __init__(self, sensorname, sensor_dict):
        self.name = sensorname
        self.sensor_range = sensor_dict[sensorname][0]
        self.tracking_bonus = sensor_dict[sensorname][1]
        self.power = sensor_dict[sensorname][2]
class NSC:
    def __init__(self, nscname, nsc_dict):
        self.name = nscname
        self.type = nsc_dict[nscname][0]
        self.power = nsc_dict[nscname][1]
class Reactor:
    def __init__(self, reactorname, reactor_dict):
        self.name = reactorname
        self.tech_level = reactor_dict[reactorname][0]
class Auxiliary:
    def __init__(self, auxiliaryname, auxiliary_dict):
        self.name = auxiliaryname
        self.type = auxiliary_dict[auxiliaryname][0]
        self.power = auxiliary_dict[auxiliaryname][1]
class Thruster:
    def __init__(self, thrustername, thruster_dict):
        self.name = thrustername
        self.tech_level = thruster_dict[thrustername][0]
class Ship_Type:
    def __init__(self, shiptypename, shiptype_dict):
        self.name = shiptypename
        self.ship_type = shiptype_dict[shiptypename][0]
        self.fleet_size = shiptype_dict[shiptypename][1]
        self.base_hex = shiptype_dict[shiptypename][2]
        self.base_evasion = shiptype_dict[shiptypename][3]
        self.hull_points = shiptype_dict[shiptypename][4]
class Ramming:
    def __init__(self, mothership):
        self.name = mothership.name+"'s Ram"
        self.is_missile = False
        self.is_ram = True
        self.shiptype = mothership.shiptype
        self.hex_range = mothership.hex_range
        self.damage = mothership.shiphull
        self.hull_mult = 1
        self.armor_mult = 0
        self.shield_mult = 0
#Setup a pixel display with caption
DisplaySurf = pygame.display.set_mode((1300,700))
DisplaySurf.fill(BLACK)
pygame.display.set_caption("FleetSim")

#Setup Info
#hexmap stuff
mapheight = 25
mapwidth = 45
hexheight = 15
mapdrawheight = 500
mapdrawwidth = 1100
#screen stuff
screenwidth = 1300
screenheight = 700
#hexinfo stuff
hexinfoheight = screenheight
hexinfowidth = screenwidth-mapdrawwidth
hexinfocolor = INFOGRAY
#setup commands
DisplaySurf = pygame.display.set_mode((1300,700))
DisplaySurf.fill(BLACK)
pygame.display.set_caption("FleetSim")

hexgrid = assemble_hexmap((30,30), mapwidth, mapheight, hexheight, WHITE, GRIDYELLOW, 1)
update_grid_display(DisplaySurf, hexgrid, (0,0), (mapdrawwidth,mapdrawheight), hexheight, False)
update_hexinfo_display('Blank')

targetoptions = OptionBox(950, 40, 300, 40, INFOGRAY, GRIDYELLOW, pygame.font.SysFont(None, 30), ["Ship 1", "Ship 2", "Ship 3"])
weaponoptions = OptionBox(140, 40, 200, 40, INFOGRAY, GRIDYELLOW, pygame.font.SysFont(None, 30), ["Weapon 1", "Weapon 2", "Weapon 3"])
dockoptions = OptionBox(950, 40, 300, 40, INFOGRAY, GRIDYELLOW, pygame.font.SysFont(None, 30), [])

statweapons_file = r"static_weapon.txt" #should be replaced with a more general system for loading outfiles
strucutils_file = r"structural_utility.txt"
computers_file = r"computer.txt"
ftl_file = r"ftl.txt"
thrusters_file = r"thrusters.txt"
evasionweps_file = r"evasion_weapon.txt"
trackweps_file = r"tracking_weapon.txt"
nsc_file = r"nsc.txt"
sensors_file = r"sensors.txt"
reactors_file = r"reactor.txt"
auxiliary_file = r"auxiliary.txt"
ship_file = r"ship_type.txt"

load_outfile(statweapons_file, Static_Weapon)
load_outfile(strucutils_file, Struc_Utility)
load_outfile(computers_file, Computer)
load_outfile(ftl_file, FTL)
load_outfile(thrusters_file, Thruster)
load_outfile(evasionweps_file, Evasion_Weapon)
load_outfile(trackweps_file, Tracking_Weapon)
load_outfile(nsc_file, NSC)
load_outfile(sensors_file, Sensor)
load_outfile(reactors_file, Reactor)
load_outfile(auxiliary_file, Auxiliary)
load_outfile(ship_file, Ship_Type)

#assorted additional setup commands
Nullship = Ship("Null")
shipfiletoload = r"ships"
load_shipfiles(shipfiletoload)

turncounter = 0
attack_ship = Nullship
defend_ship = Nullship
shiptoplace = Nullship
targets_menu(attack_ship, Small_Blue_Laser)
#Beginning Game Loop
weaponselectcount = 0 #total number of weapons selected in attack mode. Probably not the best way to do this honestly.
recolor = 0
event_list = []
persisweaponoption = -1
persistargetoption = -1 #results from the menu option dropdowns in attack mode.
current_team = 0
game_mode = 4#1 = examine, 2 = movement, 3 = attack, 4 = deployment, 5 = between-turns

#pseudoish commands
#deploy_ship_load()
current_team = 2

run = True

while run:
    event_list = pygame.event.get()
    if game_mode == 1:
        update_grid_display(DisplaySurf, hexgrid, (0,0), (mapdrawwidth,mapdrawheight), hexheight, False)
        conclude_turn_button()
    if game_mode == 2:
        update_grid_display(DisplaySurf, hexgrid, (0,0), (mapdrawwidth,mapdrawheight), hexheight, False)
        if dockoptions.option_list:
            dockoption = dockoptions.update(event_list)
            dockoptions.draw(DisplaySurf)
            if dockoption != -1:
                redock_ship(shipdict[dockoption], docking_ship)
                DisplaySurf.fill(BLACK)
        finish_movement()
    if game_mode == 3:
        #game mode three needs to specify attack ship, defend ship, and i guess stuff about what's selected in the menus
        weaponoption = weaponoptions.update(event_list)
        targetoption = targetoptions.update(event_list)
        if weaponoption != -1:
            persisweaponoption = weaponoption
            targets_menu(attack_ship, persisweaponoption)
            targetoptions.selected = 0
            defend_ship = "No Ship Selected"
        if targetoption != -1:
            persistargetoption = targetoption
            defend_ship = persistargetoption #was tinkering with this
            selectgrid_setup(defend_ship)
        attack_mode()
        attack_dialogue(attack_ship)
        targetoptions.draw(DisplaySurf)
        weaponoptions.draw(DisplaySurf)
        counting_buttons(650, 500, attack_ship, defend_ship, persisweaponoption)
        attack_button(attack_ship, defend_ship, persisweaponoption)
        leave_attack_button()
    if game_mode == 4:
        update_grid_display(DisplaySurf, hexgrid, (0,0), (mapdrawwidth,mapdrawheight), hexheight, False)
    if game_mode == 5:
        conclude_turn_button()
    for event in event_list:
        pos = pygame.mouse.get_pos()
        if event.type == QUIT:
            run = False
        if game_mode == 1:
            if event.type == pygame.MOUSEBUTTONUP:
                sprite_clicker(pos)
                conclude_turn_button(pos)
                if pygame.Rect((0,0, mapdrawwidth, mapdrawheight)).collidepoint(pos):
                    hexgrid[recolor][1] = GRIDYELLOW
                    if hex_clicker(pos):
                        DisplaySurf.fill(BLACK)
                        recolor = hex_clicker(pos)
                        hexgrid[recolor][1] = RED
                        hexinfo_sprites = update_hexinfo_display(recolor)
                else:
                    hexgrid[recolor][1] = GRIDYELLOW
        elif game_mode == 2:
            if event.type == pygame.MOUSEBUTTONUP:
                select_movement(pos)
                place_ship(pos)
                finish_movement(pos)
                if pygame.Rect((0,0, mapdrawwidth, mapdrawheight)).collidepoint(pos) and shiptoplace == Nullship:
                    hexgrid[recolor][1] = GRIDYELLOW
                    if hex_clicker(pos):
                        DisplaySurf.fill(BLACK)
                        recolor = hex_clicker(pos)
                        hexgrid[recolor][1] = RED
                        hexinfo_sprites = update_hexinfo_display(recolor)
                else:
                    hexgrid[recolor][1] = GRIDYELLOW
        elif game_mode == 3:
            if event.type == pygame.MOUSEBUTTONUP:
                counting_buttons(650, 500, attack_ship, defend_ship, persisweaponoption, pos)
                attack_button(attack_ship, defend_ship, persisweaponoption, pos)
                leave_attack_button(pos)
        elif game_mode == 4:
            if event.type == pygame.MOUSEBUTTONUP:
                if pygame.Rect((0,0, mapdrawwidth, mapdrawheight)).collidepoint(pos):
                    deploy_ship(pos)
                    if deployshipnum == len(shiplist):
                        game_mode = 1
                        DisplaySurf.fill(BLACK)
                    else:
                        deploy_ship_load()
        elif game_mode == 5:
            if event.type == pygame.MOUSEBUTTONUP:
                conclude_turn_button(pos)
    pygame.display.update()
    FramePerSec.tick(FPS)
pygame.quit()
