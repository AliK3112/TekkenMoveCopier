import collections
import json
import sys

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


def getMoveID(moveset, movename: str):
    for i, move in enumerate(moveset['moves']):
        if move['name'] == movename:
            return i
    return -1


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

        self.__srcMvst = sourceMvst
        self.__dstMvst = dstMvst
        self.__moveName = targetMoveName
        self.__srcMoveId = getMoveID(self.__srcMvst, self.__moveName)

        self.__dependency_name_id = {}  # KEY: moveName VALUE: moveID
        self.__dependent_id_name = {}  # KEY: moveID VALUE: moveName

        self.__dependency_name_id[targetMoveName] = self.__srcMoveId
        self.__dependent_id_name[self.__srcMoveId] = targetMoveName

    def __checkDependencies(self):
        moveID = int(-1)
        stack = [self.__srcMoveId]
        while stack:
            moveID = stack.pop(0)
            if (moveID == 1631):
                name = self.__dependent_id_name[moveID]
                del self.__dependent_id_name[moveID]
                del self.__dependency_name_id[name]
                continue
            self.__getTransitionDependencies(moveID, stack)
            self.__getCancelDependencies(moveID, stack)
            self.__getReactionListDependencies(moveID, stack)

    def getDependencies(self):
        # self.__dependency_name_id = collections.OrderedDict(
        #     sorted(self.__dependency_name_id.items()))
        # self.__dependent_id_name = collections.OrderedDict(
        #     sorted(self.__dependent_id_name.items()))
        self.__checkDependencies()
        return self.__dependency_name_id, self.__dependent_id_name

    def getMoveName(self):
        return self.__moveName

    def getMove(self):
        return self.__srcMvst['moves'][self.__srcMoveId]

    def __get881ReqIdx(self) -> int:
        return self.__srcMvst['hit_conditions'][1]['requirement_idx']
        # end = [{"req": 881, "param": 0}, {"req": 881, "param": 0}]
        # return search(end, self.__srcMvst['requirements'])

    def __getTransitionDependencies(self, moveID: int, stack: list):
        transition = self.__srcMvst['moves'][moveID]['transition']
        if transition >= 0x8000:
            return
        nextMoveName = getMoveName(self.__srcMvst, transition)
        nextMoveId = getMoveID(self.__dstMvst, nextMoveName)

        # if transitioned value doesn't exist, add it to list of dependencies
        if nextMoveId == -1:
            # if not, add it's name within dependencies
            if nextMoveName not in self.__dependency_name_id:
                self.__dependency_name_id[nextMoveName] = transition
                self.__dependent_id_name[transition] = nextMoveName

                # recursive re-call for the move we just found
                # self.__checkDependencies(nextMoveId)
                stack.append(nextMoveId)
        return

    def __getCancelDependencies(self, moveID: int, stack: list):
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
                if nextMoveName not in self.__dependency_name_id:
                    self.__dependency_name_id[nextMoveName] = nextMoveId
                    self.__dependent_id_name[nextMoveId] = nextMoveName

                    # recursive re-call for the move we just found
                    # self.__checkDependencies(nextMoveId)
                    stack.append(nextMoveId)

            if cancel['command'] == 0x8000:
                break

            cancel_idx += 1
        return

    def __getReactionListDependencies(self, moveID: int, stack: list):
        hit_cond_idx = self.__srcMvst['moves'][moveID]['hit_condition_idx']
        if hit_cond_idx == 0:
            return

        endListReq = self.__get881ReqIdx()

        while True:
            # Getting requirement of the hit condition
            reqIdx = self.__srcMvst['hit_conditions'][hit_cond_idx]['requirement_idx']

            # Getting the reaction list index
            reactionListIdx = self.__srcMvst['hit_conditions'][hit_cond_idx]['reaction_list_idx']

            # Getting reaction list
            reactionList = self.__srcMvst['reaction_list'][reactionListIdx]

            # Iterating reaction list
            for key in reaction_keys:
                # Getting name of the move within source movelist
                nextMoveName = getMoveName(self.__srcMvst, reactionList[key])
                nextMoveId = getMoveID(self.__dstMvst, nextMoveName)

                # Checking if that move exists within destination movelist
                if nextMoveId == -1:
                    # Storing ID of the reaction list key into 'nextMoveId'
                    nextMoveId = reactionList[key]
                    # if not, add it's name within dependencies
                    if nextMoveName not in self.__dependency_name_id:
                        self.__dependent_id_name[reactionList[key]
                                                 ] = nextMoveName
                        self.__dependency_name_id[nextMoveName] = reactionList[key]

                        # recursive re-call for the move we just found
                        # self.__checkDependencies(nextMoveId)

                        # add into stack
                        stack.append(nextMoveId)

            if reqIdx == endListReq:
                break

            hit_cond_idx += 1
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
    srcMvst = loadJson('./t7_DEVIL_JIN.json')
    dstMvst = loadJson('./t7_JIN.json')
    movName = 'Dj_lusako'
    printDependencies(srcMvst, dstMvst, movName)


if __name__ == '__main__':
    main()
