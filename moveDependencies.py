import json
import os
import sys

KEY1 = 'SrcMoveId'
KEY2 = 'name'

keys = [
    "standing",
    "ch",
    "crouch",
    "crouch_ch",
    "left_side",
    "left_side_crouch",
    "right_side",
    "right_side_crouch",
    "back",
    "back_crouch",
    "block",
    "crouch_block",
    "wallslump",
    "downed"
]


def loadJson(filename):
    try:
        with open(filename) as f:
            data = json.load(f)
    except FileNotFoundError:
        data = None
    return data


def isSame(moveset1, moveset2):
    return moveset1['version'] == moveset2['version'] \
        and moveset1['tekken_character_name'] == moveset2['tekken_character_name'] \
        and moveset1['character_name'] == moveset2['character_name'] \
        and moveset1['creator_name'] == moveset2['creator_name']


def isSameInDifferentGame(moveset1, moveset2):
    return moveset1['tekken_character_name'] == moveset2['tekken_character_name'] \
        and moveset1['creator_name'] == moveset2['creator_name']


def getMoveName(moveset, move_id: int):
    if move_id >= 0x8000:
        move_id = moveset['aliases'][move_id-0x8000]
    return moveset['moves'][move_id]['name']


def getMoveID(moveset, movename):
    for i, move in enumerate(moveset['moves']):
        if move['name'] == movename:
            return i
    return -1


class MoveDependencies:
    def __init__(self, sourceMvst, dstMvst, targetMoveName):
        if sourceMvst == None:
            raise BaseException('Source Moveset Empty')
        if dstMvst == None:
            raise BaseException('Destination Moveset Empty')
        if targetMoveName == None:
            raise BaseException('targetMoveName Empty')
        if isSame(sourceMvst, dstMvst):
            raise BaseException('Source & Destination movesets are the same')

        self.__srcMvst = sourceMvst
        self.__dstMvst = dstMvst
        self.__moveName = targetMoveName
        self.__srcMoveId = getMoveID(self.__srcMvst, self.__moveName)
        self.__dependentMoves = []
        self.__checkDependencies(self.__srcMoveId)
        self.__dependentMoves.sort(key=lambda d: list(d.values())[0])

    def __checkDependencies(self, moveID: int):
        self.__getTransitionDependencies(moveID)
        self.__getCancelDependencies(moveID)
        self.__getReactionListDependencies(moveID)

    def getDependencies(self):
        return self.__dependentMoves

    def getMoveName(self):
        return self.__moveName

    def getMove(self):
        return self.__srcMvst['moves'][self.__srcMoveId]

    def __get881ReqIdx(self) -> int:
        return self.__srcMvst['hit_conditions'][1]['requirement_idx']

    def __getTransitionDependencies(self, moveID: int):
        transition = self.__srcMvst['moves'][moveID]['transition']
        if transition >= 0x8000:
            return
        nextMoveName = getMoveName(self.__srcMvst, transition)
        nextMoveId = getMoveID(self.__dstMvst, nextMoveName)

        # if transitioned value doesn't exist, add it to list of dependencies
        if nextMoveId == -1:
            # if not, add it's name within dependencies
            if nextMoveName not in [value for elem in self.__dependentMoves
                                    for value in elem.values()]:
                self.__dependentMoves.append(
                    {KEY1: transition, KEY2: nextMoveName})

                # recursive re-call for the move we just found
                self.__checkDependencies(nextMoveId)
        return

    def __getCancelDependencies(self, moveID: int):
        cancel_idx = self.__srcMvst['moves'][moveID]['cancel_idx']
        while True:
            # Storing cancel
            cancel = self.__srcMvst['cancels'][cancel_idx]

            # If group cancel, skip
            if cancel['command'] == 0x800b:
                cancel_idx += 1
                continue

            # Storing move id of the cancel
            nextMoveId = cancel['move_id']

            # If alias, skip
            if nextMoveId >= 0x8000:
                if cancel['command'] == 0x8000:  # if also last cancel
                    break
                cancel_idx += 1
                continue

            # Get move name within source moveset
            nextMoveName = getMoveName(self.__srcMvst, nextMoveId)

            # See if the move exists within destination moveset
            if getMoveID(self.__dstMvst, nextMoveName) == -1:

                # if not, add it's name within dependencies
                if nextMoveName not in [value for elem in self.__dependentMoves
                                        for value in elem.values()]:
                    self.__dependentMoves.append(
                        {KEY1: nextMoveId, KEY2: nextMoveName})

                    # recursive re-call for the move we just found
                    self.__checkDependencies(nextMoveId)

            if cancel['command'] == 0x8000:
                break

            cancel_idx += 1
        return

    def __getReactionListDependencies(self, moveID: int):
        hit_cond_idx = self.__srcMvst['moves'][moveID]['hit_condition_idx']
        if hit_cond_idx == 0:
            return

        endListReq = self.__get881ReqIdx()

        while True:
            # Getting reaction of the hit condition
            reqIdx = self.__srcMvst['hit_conditions'][hit_cond_idx]['requirement_idx']

            # Getting the reaction list index
            reactionListIdx = self.__srcMvst['hit_conditions'][hit_cond_idx]['reaction_list_idx']

            # Getting reaction list
            reactionList = self.__srcMvst['reaction_list'][reactionListIdx]

            # Iterating reaction list
            for key in keys:
                # Getting name of the move within source movelist
                nextMoveName = getMoveName(self.__srcMvst, reactionList[key])
                nextMoveId = getMoveID(self.__dstMvst, nextMoveName)

                # Checking if that move exists within destination movelist
                if nextMoveId == -1:
                    nextMoveId = reactionList[key]
                    # if not, add it's name within dependencies
                    if nextMoveName not in [value for elem in self.__dependentMoves
                                            for value in elem.values()]:
                        self.__dependentMoves.append({
                            KEY1: reactionList[key], KEY2: nextMoveName})

                        # recursive re-call for the move we just found
                        self.__checkDependencies(nextMoveId)

            if reqIdx == endListReq:
                break

            hit_cond_idx += 1
        return


def getMoveDependencies(sourceMvst, destMvst, targetMoveName):
    moveDependencies = MoveDependencies(
        sourceMvst, destMvst, targetMoveName).getDependencies()
    print(
        "%s -> %s : Copying move \"%s\"" % (sourceMvst['character_name'], destMvst['character_name'], targetMoveName))
    for dep in moveDependencies:
        print("ID in source moveset: %4d\tName: %s" % (dep[KEY1], dep[KEY2]))


def main():
    if len(sys.argv) < 4:
        print('Parameters:')
        print('1 = Source Moveset')
        print('2 = Desination Moveset')
        print('3 = Name of Move to Import')
        return
    srcMvst = sys.argv[1]
    dstMvst = sys.argv[2]
    movName = sys.argv[3]

    if srcMvst == None:
        print('Source moveset not passed')
        return

    if dstMvst == None:
        print('Destination moveset not passed')
        return

    if movName == None:
        print('Target move not passed')
        return
    getMoveDependencies(srcMvst, dstMvst, movName)


def test():
    srcMvst = loadJson('./tag2_JIN.json')
    dstMvst = loadJson('./t7_JIN.json')
    movName = 'Jz_sKAM01_'
    getMoveDependencies(srcMvst, dstMvst, movName)


if __name__ == '__main__':
    # main()
    test()
