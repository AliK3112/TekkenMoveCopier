import collections
import json
from operator import itemgetter
import sys

from Aliases import fillAliasesDictonnaries, getMoveExtrapropAlias, getRequirementAlias

reaction_keys = [
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

reqListEndval = {
    'Tekken7': 881,
    'Tag2': 690,
    'Revolution': 697,
    'Tekken6': 397,
    'Tekken5DR': 327,
    'Tekken5': 321,
    'Tekken4': 263,
}

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


def getMoveName(moveset, move_id: int) -> str:
    if move_id >= 0x8000:
        move_id = moveset['aliases'][move_id-0x8000]
    try:
        return moveset['moves'][move_id]['name']
    except:
        return ""


def getMoveID(moveset, movename: str):
    for i, move in enumerate(moveset['moves']):
        if move['name'] == movename:
            return i
    return -1

paramProps = [0x81d4, 0x81d5, 0x81dc, 0x83c3]
forbiddenMoves = ["Kz_rsakoT", "Kz_rsakoDA"]

def isTagMove (movename: str):
    return movename.find("Chg") != -1

class MoveDependencies:
    def __init__(self, sourceMvst: dict, dstMvst: dict, targetMoveName: str):
        if sourceMvst == None:
            raise BaseException('Source Moveset Empty')
        if dstMvst == None:
            raise BaseException('Destination Moveset Empty')
        if targetMoveName == None:
            raise BaseException('targetMoveName Empty')
        if isSame(sourceMvst, dstMvst):
            raise BaseException('Source & Destination movesets are the same')
        if getMoveID(dstMvst, targetMoveName) != -1:
            raise BaseException(
                'The move \"%s\" already exists within destination moveset' % targetMoveName)
        self.aliases = loadJson('copy_aliases.json')
        if self.aliases == None:
            print(
                '[DEPENDENCY CHECKER] No aliases loaded from "copy_aliases.json"')

        self.__srcMvst = sourceMvst
        self.__dstMvst = dstMvst
        self.__moveName = targetMoveName
        self.__srcMoveId = getMoveID(self.__srcMvst, self.__moveName)

        self.__dependency_name_id = {}  # KEY: moveName VALUE: moveID
        self.__dependent_id_name = {}  # KEY: moveID VALUE: moveName

        self.__dependency_name_id[targetMoveName] = self.__srcMoveId
        self.__dependent_id_name[self.__srcMoveId] = targetMoveName

    def __checkDependencies(self):
        fillAliasesDictonnaries(self.__srcMvst['version'])
        moveID = int(-1)
        stack = [self.__srcMoveId]
        while stack:
            moveID = stack.pop(0)
            move = self.__srcMvst['moves'][moveID]
            moveName = move['name']
            if moveName in forbiddenMoves or isTagMove(moveName):
                del self.__dependent_id_name[moveID]
                del self.__dependency_name_id[moveName]
                continue
            self.__getTransitionDependencies(move, stack)
            self.__getCancelDependencies(move, stack)
            self.__getExtrapropDependencies(move, stack)
            self.__getReactionListDependencies(move, stack)

    def getDependencies(self):
        self.__checkDependencies()
        return self.__dependency_name_id, self.__dependent_id_name

    def getMoveName(self):
        return self.__moveName

    def getMove(self):
        return self.__srcMvst['moves'][self.__srcMoveId]

    def __getEndListReqIdx(self) -> int:
        return self.__srcMvst['hit_conditions'][1]['requirement_idx']

    def __getTransitionDependencies(self, move: dict, stack: list):
        transition = move['transition']
        if transition >= 0x8000:
            return
        self.__appendMoveToStackIfNotPresent(transition, stack)
        return

    def __getCancelDependencies(self, move: dict, stack: list):
        idx = move['cancel_idx']
        if idx >= len(self.__srcMvst['cancels']): return
        while True:
            # Storing cancel
            cancel = self.__srcMvst['cancels'][idx]

            # If group cancel, skip
            if cancel['command'] == 0x800b:
                idx += 1
                continue

            # Storing move id of the cancel
            nextMoveId = cancel['move_id']

            # If alias, skip
            if nextMoveId >= 0x8000:
                if cancel['command'] == 0x8000:  # if also last cancel
                    break
                idx += 1
                continue

            # Check dependencies in requirements list
            self.__getRequirementListDependencies(cancel['requirement_idx'], stack)

            self.__appendMoveToStackIfNotPresent(nextMoveId, stack)

            if cancel['command'] == 0x8000:
                break

            idx += 1
        return
    
    def __getRequirementListDependencies(self, idx: int, stack: list):
        if idx == 0: return
        if idx >= len(self.__srcMvst['requirements']): return
        while True:
            # Storing requirement
            req, param = itemgetter("req", "param")(self.__srcMvst['requirements'][idx])
            if req < 0x8000:
                if req == reqListEndval[self.__srcMvst['version']]:
                    break
                idx += 1
                continue

            req, param = getRequirementAlias(self.__srcMvst['version'], req, param)

            if req in paramProps:
                paramMoveId = param
                self.__appendMoveToStackIfNotPresent(paramMoveId, stack)

            if req == reqListEndval[self.__srcMvst['version']]:
                break

            idx += 1
        return
    
    def __getExtrapropDependencies(self, move: dict, stack: list):
        idx = move['extra_properties_idx']
        if idx == -1: return
        if idx >= len(self.__srcMvst['extra_move_properties']): return
        # 0x83c4 + 0x20
        while True:
            id, type, value = itemgetter("id", "type", "value")(self.__srcMvst['extra_move_properties'][idx])
            type, id, value = getMoveExtrapropAlias(self.__srcMvst['version'], type, id, value)

            if id in paramProps:
                paramMoveId = value
                self.__appendMoveToStackIfNotPresent(paramMoveId, stack)

            if id == 0 and type == 0 and value == 0:
                break

            idx += 1
        return

    def __getReactionListDependencies(self, move: dict, stack: list):
        idx = move['hit_condition_idx']
        if idx == 0: return
        if idx >= len(self.__srcMvst['hit_conditions']): return

        endListReq = self.__getEndListReqIdx()

        while True:
            # Getting requirement of the hit condition
            reqIdx = self.__srcMvst['hit_conditions'][idx]['requirement_idx']

            # Getting the reaction list index
            reactionListIdx = self.__srcMvst['hit_conditions'][idx]['reaction_list_idx']

            # Getting reaction list
            reactionList = self.__srcMvst['reaction_list'][reactionListIdx]

            # Iterating reaction list
            for key in reaction_keys:
                nextMoveId = reactionList[key]
                self.__appendMoveToStackIfNotPresent(nextMoveId, stack)

            if reqIdx == endListReq:
                break

            idx += 1
        return
    
    def __appendMoveToStackIfNotPresent(self, moveId: int, stack: list):
        # Get move name within source moveset
        moveName = getMoveName(self.__srcMvst, moveId)

        # See if the move exists within destination moveset
        if getMoveID(self.__dstMvst, moveName) == -1:
            # if not, add it's name within dependencies
            if moveName not in self.__dependency_name_id:
                self.__dependency_name_id[moveName] = moveId
                self.__dependent_id_name[moveId] = moveName

                # Adding it to stack of moves
                stack.append(moveId)
        return


def printDependencies(sourceMvst, destMvst, targetMoveName):
    moveDependency_name_id, moveDependency_id_name = MoveDependencies(
        sourceMvst, destMvst, targetMoveName).getDependencies()

    for _, id in enumerate(moveDependency_id_name):
        print(id, moveDependency_id_name[id])

    print('Moves:', len(moveDependency_id_name))


def main():
    if len(sys.argv) < 4:
        print('Parameters:')
        print('1 = Source Moveset')
        print('2 = Desination Moveset')
        print('3 = Name of Move to Import')
        return

    if sys.argv[1] == None:
        print('Source moveset not passed')
        return

    if sys.argv[2] == None:
        print('Destination moveset not passed')
        return

    if sys.argv[3] == None:
        print('Target move not passed')
        return

    srcMvst = loadJson(sys.argv[1])
    if srcMvst == None:
        print('Error reading Source moveset')
        return

    dstMvst = loadJson(sys.argv[2])
    if dstMvst == None:
        print('Error reading Destination moveset')
        return

    movName = sys.argv[3]

    printDependencies(srcMvst, dstMvst, movName)


def test():
    srcMvst = loadJson('./tag2_KAZUYA.json')
    dstMvst = loadJson('./t7_KAZUYA.json')
    # movName = 'Dj_lusako'
    movName = 'Kz_rsako'
    printDependencies(srcMvst, dstMvst, movName)


if __name__ == '__main__':
    main()
