from random import getrandbits
from random import randint
from model.CellType import CellType
from model.ActionType import ActionType
from model.Direction import Direction
from model.Game import Game
import math
from model.TrooperType import TrooperType
from model.Move import Move
from model.Trooper import Trooper
from model.TrooperStance import TrooperStance
from model.World import World


class MyStrategy:

    def __init__(self):
        self.grid = []
        self.WALL = -1
        self.BLANK = -2
        self.world = 0

    def move(self, me: Trooper, world: object, game: Game, move: Move):

        if me.action_points >= game.standing_move_cost:
            self.world = world

            W = world.width
            H = world.height

            self.grid.clear()

            for counterX in range(W):
                self.grid.append([])
                for counterY in range(H):
                    cell = world.cells[counterX][counterY]
                    if cell == CellType.FREE:
                        found = False

                        troopers = world.troopers
                        for trooper in troopers:
                            if trooper.teammate and (trooper.x == counterX and trooper.y == counterY):
                                self.grid[counterX].append(int(self.WALL))
                                found = True
                                break

                        if not found:
                            self.grid[counterX].append(int(self.BLANK))
                    elif cell == CellType.LOW_COVER:
                        #ищем по бонусам
                        found = False
                        for bonus in world.bonuses:
                            if bonus.x == counterX and bonus.y == counterY:
                                self.grid[counterX].append(int(self.BLANK))
                                found = True
                                break

                        if not found:
                            self.grid[counterX].append(int(self.WALL))
                    else:
                        self.grid[counterX].append(int(self.WALL))

            troopers = world.troopers

            if me.type == TrooperType.COMMANDER:
                for trooper in troopers:
                    isCanThrowGrenade = world.is_visible(game.grenade_throw_range, me.x, me.y, me.stance, trooper.x, trooper.y, trooper.stance) and me.action_points >= game.grenade_throw_cost and me.holding_grenade
                    if isCanThrowGrenade and not trooper.teammate:
                        self.throwGrenade(trooper, move)
                        return

                    if not trooper.teammate and me.action_points >= me.shoot_cost:
                        self.shoot(trooper, move, game, me)
                        return
            elif me.type == TrooperType.FIELD_MEDIC:
                for trooper in troopers:
                    if trooper.teammate:
                        isCanHeal = world.is_visible(1, me.x, me.y, me.stance, trooper.x, trooper.y, trooper.stance) and me.holding_medikit and trooper.hitpoints < trooper.maximal_hitpoints and me.action_points >= game.field_medic_heal_cost

                        if isCanHeal:
                            self.heal(trooper, move)
                            return

                for trooper in troopers:
                    isCanThrowGrenade = world.is_visible(game.grenade_throw_range, me.x, me.y, me.stance, trooper.x, trooper.y, trooper.stance) and me.action_points >= game.grenade_throw_cost and me.holding_grenade
                    if isCanThrowGrenade and not trooper.teammate:
                        self.throwGrenade(trooper, move)
                        return

                for trooper in troopers:
                    if not trooper.teammate and me.action_points >= me.shoot_cost:
                        self.shoot(trooper, move, game, me)
                        return
            else:
                for trooper in troopers:
                    isCanThrowGrenade = world.is_visible(game.grenade_throw_range, me.x, me.y, me.stance, trooper.x, trooper.y, trooper.stance) and me.action_points >= game.grenade_throw_cost and me.holding_grenade
                    if isCanThrowGrenade and not trooper.teammate:
                        self.throwGrenade(trooper, move)
                        return

                    if not trooper.teammate and me.action_points >= me.shoot_cost:
                        self.shoot(trooper, move, game, me)
                        return

            if me.action_points >= game.standing_move_cost:
                self.go(me, world, game, move)
            else:
                print('Не осталось очков на ходьбу')

            return

    def increaseStance(self, move : Move, game : Game, me : Trooper):
        move.action = ActionType.RAISE_STANCE
        move.direction = Direction.CURRENT_POINT

    def decreaseStance(self, move : Move, game : Game, me : Trooper):
        move.action = ActionType.LOWER_STANCE
        move.direction = Direction.CURRENT_POINT

    def shoot(self, trooper : Trooper, move : Move, game : Game, me : Trooper):
        if self.world.is_visible(me.shooting_range, me.x, me.y, TrooperStance.PRONE, trooper.x, trooper.y, trooper.stance):
            if me.stance != TrooperStance.PRONE:
                self.decreaseStance(move, game, me)
            else:
                self.shootTrooper(trooper, move, game, me)
        elif self.world.is_visible(me.shooting_range, me.x, me.y, TrooperStance.KNEELING, trooper.x, trooper.y, trooper.stance):
            if me.stance != TrooperStance.KNEELING:
                if me.stance == TrooperStance.STANDING:
                    self.decreaseStance(move, game, me)
                elif me.stance == TrooperStance.PRONE:
                    self.increaseStance(move, game, me)
            else:
                self.shootTrooper(trooper, move, game, me)
        elif self.world.is_visible(me.shooting_range, me.x, me.y, TrooperStance.STANDING, trooper.x, trooper.y, trooper.stance):
            if me.stance != TrooperStance.STANDING:
                self.increaseStance(move, game, me)
            else:
                self.shootTrooper(trooper, move, game, me)
        else:
            self.go(me, self.world, game, move)

    def distanceBetweenPoints(self, x1, x2, y1, y2):
        return math.hypot(x2 - x1, y2 - y1)

    def shootTrooper(self, trooper : Trooper, move : Move, game : Game, me : Trooper):
        move.action = ActionType.SHOOT
        move.x = trooper.x
        move.y = trooper.y

    def heal(self, trooper : Trooper, move : Move):
        move.action = ActionType.HEAL
        move.x = trooper.x
        move.y = trooper.y
        print('Солдат полечил')

    def throwGrenade(self, trooper : Trooper, move : Move):
        move.action = ActionType.THROW_GRENADE
        move.x = trooper.x
        move.y = trooper.y


    def moveToCenter(self, me: Trooper, world: object, game: Game, move: Move):
        targetX = world.width / 2
        targetY = world.height / 2

        farrestDistance = 0

        if me.type == TrooperType.COMMANDER:
            for trooper in world.troopers:
                if self.distanceBetweenPoints(me.x, trooper.x, me.y, trooper.y) > farrestDistance:
                    farrestDistance = self.distanceBetweenPoints(me.x, trooper.x, me.y, trooper.y)

            if farrestDistance > 4:
                return

        self.moveToPoint(targetX, targetY, me, world, game, move)


    def moveToNonMedic(self, me: Trooper, world: object, game: Game, move: Move):
        troopers = world.troopers

        for trooper in troopers:
            if trooper.type != TrooperType.FIELD_MEDIC and trooper.teammate:
                targetX = 0
                targetY = 0
                move.action = ActionType.MOVE

                if me.type == TrooperType.FIELD_MEDIC and trooper.hitpoints < trooper.maximal_hitpoints:
                    targetX = trooper.x
                    targetY = trooper.y
                else:
                    targetX = trooper.x + randint(0, 9) % 3
                    targetY = trooper.y + randint(0, 9) % 3

                self.moveToPoint(targetX, targetY, me, world, game, move)

    def moveToCommander(self, me: Trooper, world: object, game: Game, move: Move):
        troopers = world.troopers
        for trooper in troopers:
            if trooper.type == TrooperType.COMMANDER and trooper.teammate:
                targetX = 0
                targetY = 0
                move.action = ActionType.MOVE

                if me.type == TrooperType.FIELD_MEDIC:
                    if trooper.hitpoints < trooper.maximal_hitpoints:
                        targetX = trooper.x
                        targetY = trooper.y
                    else:
                        targetX = trooper.x + randint(0, 9) % 3
                        targetY = trooper.y + randint(0, 9) % 3
                else:
                    targetX = trooper.x + randint(0, 9) % 3
                    targetY = trooper.y + randint(0, 9) % 3

                self.moveToPoint(targetX, targetY, me, world, game, move)


    def moveToPoint(self, targetX, targetY, me: Trooper, world: object, game: Game, move: Move):
        cells = world.cells

        offsetX = 0

        if me.x > targetX:
            offsetX = -1
        elif me.x < targetX:
            offsetX = 1
        else:
            offsetX = 0

        offsetY = 0

        if me.y > targetY:
            offsetY = -1
        elif me.y < targetY:
            offsetY = 1
        else:
            offsetY = 0

        x = -1
        y = -1
        canMoveToPoint = False

        if offsetX != 0:
            x = me.x + offsetX
            y = me.y
        elif offsetY != 0:
            x = me.x
            y = me.y + offsetY

        for bonus in world.bonuses:
            if bonus.x == x and bonus.y == y:
                canMoveToPoint = True

        canMoveX = offsetX != 0 and cells[me.x + offsetX][me.y] == CellType.FREE
        canMoveY = offsetY != 0 and cells[me.x][me.y + offsetY] == CellType.FREE

        canMoveX = canMoveX or canMoveToPoint
        canMoveY = canMoveY or canMoveToPoint

        if canMoveX or canMoveY:
            move.action = ActionType.MOVE

            if canMoveX and canMoveY:
                if randint(0, 9) % 2 == 0:
                    move.x = me.x + offsetX
                    move.y = me.y
                else:
                    move.x = me.x
                    move.y = me.y + offsetY
            elif canMoveX:
                move.x = me.x + offsetX
                move.y = me.y
            else:
                move.x = me.x
                move.y = me.y + offsetY
        else:
            print('Recalculate direction')

            quarter = 0

            if me.x > targetX and me.y < targetY:
                quarter = 1
            elif me.x > targetX and me.y > targetY:
                quarter = 2
            elif me.x < targetX and me.y > targetY:
                quarter = 3
            elif me.x < targetX and me.y < targetY:
                quarter = 4

            if quarter == 1:
                offsetX = 1
                offsetY = -1
            elif quarter == 2:
                offsetX = 1
                offsetY = 1
            elif quarter == 3:
                offsetX = -1
                offsetY = 1
            elif quarter == 4:
                offsetX = -1
                offsetY = -1

            if offsetX != 0:
                x = me.x + offsetX
                y = me.y
            elif offsetY != 0:
                x = me.x
                y = me.y + offsetY

            canMoveX = offsetX != 0 and cells[me.x + offsetX][me.y] == CellType.FREE
            canMoveY = offsetY != 0 and cells[me.x][me.y + offsetY] == CellType.FREE

            #if not canMoveX and not canMoveY:
                #self.moveToPoint(targetX + randint(0, 9) % 2, targetY + randint(0, 9) % 2, me, world, game, move)
                #return

            if canMoveX or canMoveY:
                print('Can move new direction')
                move.action = ActionType.MOVE

                if canMoveX and canMoveY:
                    if randint(0, 9) % 2 == 0:
                        move.x = me.x + offsetX
                        move.y = me.y
                    else:
                        move.x = me.x
                        move.y = me.y + offsetY
                elif canMoveX:
                    move.x = me.x + offsetX
                    move.y = me.y
                else:
                    move.x = me.x
                    move.y = me.y + offsetY

    def go(self, me: Trooper, world: object, game: Game, move: Move):
        print('Солдат пошёл')

        if me.action_points >= game.stance_change_cost and me.stance != TrooperStance.STANDING:
            self.increaseStance(move, game, me)
            return

        troopers = world.troopers

        isCommanderAlive = False
        isNonMedicAlive = False

        for trooper in troopers:
            if trooper.type == TrooperType.COMMANDER and trooper.teammate and trooper.hitpoints > 0:
                isCommanderAlive = True
                break

        for trooper in troopers:
            if trooper.type != TrooperType.FIELD_MEDIC and trooper.teammate and trooper.hitpoints > 0:
                isNonMedicAlive = True
                break

        if me.type == TrooperType.FIELD_MEDIC:
            if isCommanderAlive:
                self.moveToCommander(me, world, game, move)
            elif isNonMedicAlive:
                self.moveToNonMedic(me, world, game, move)
            else:
                self.moveToCenter(me, world, game, move)
        elif me.type == TrooperType.COMMANDER:
            self.moveToCenter(me, world, game, move)
        else:
            if not isCommanderAlive:
                self.moveToCenter(me, world, game, move)
            else:
                self.moveToCommander(me, world, game, move)