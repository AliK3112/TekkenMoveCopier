from copy import deepcopy
import sys
import json
from moveDependencies import MoveDependencies

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


def getMoveID(moveset, movename, start=0):
    n = len(moveset['moves'])
    start = 0 if (start >= n or start < 0) else start
    for i in range(start, n):
        if moveset['moves'][i]['name'] == movename:
            return i
    return -1


def getVoiceclipList(moveset, idx):
    list = []
    i = idx
    while True:
        voiceclip = moveset['voiceclips'][i]
        list.append(voiceclip)
        if voiceclip == 4294967295:
            break
        i += 1
    return list


def isLast(prop):
    return 0 == prop['id'] and 0 == prop['type'] and 0 == prop['value']


def getExtrapropsList(moveset, idx):
    list = []
    while True:
        prop = moveset['extra_move_properties'][idx]
        list.append(prop)
        if isLast(prop):
            break
        idx += 1
    return list


class MoveCopier:
    def __init__(self, sourceMvst, dstMvst, dependency_name_id, dependency_id_name):
        if sourceMvst == None:
            raise BaseException('Source Moveset Empty')
        if dstMvst == None:
            raise BaseException('Destination Moveset Empty')
        if isSame(sourceMvst, dstMvst):
            raise BaseException('Source & Destination movesets are the same')

        self.__srcMvst = sourceMvst
        self.__dstMvst = dstMvst
        self.__dependency_name_id = dependency_name_id
        self.__dependent_id_name = dependency_id_name

    def CopyAllDependentMoves(self):
        indexesOfAddedMoves = []

        # Iterate the dictionary
        for _, src_move_id in enumerate(self.__dependent_id_name):
            # Create the move and get the ID
            new_move_id = self.softCopyMove(src_move_id)

            # Storing index of this newly created move
            indexesOfAddedMoves.append(new_move_id)
            print('Move Added: %-20s. Index = %d' %
                  (self.__dependent_id_name[id], indexesOfAddedMoves[-1]))

            # Creating extraprops list
            self.createExtramovePropertiesList(src_move_id, new_move_id)

        # Update transition
        for i, src_move_id in enumerate(self.__dependent_id_name):
            self.updateTransition(src_move_id, indexesOfAddedMoves[i])

        # Copying tag 2 cancels to put into T7
        # for _, src_move_id in enumerate(self.__dependent_id_name):
        #     copyCancels(src_move_id)

        return

    # Updates the transition attribute, this value may refer to a move that doesn't exist yet, so better to call this function after importing moves
    def updateTransition(self, src_move_id, new_move_id):
        new_move = self.__dstMvst['moves'][new_move_id]
        if new_move['transition'] >= 0x8000:
            return
        new_move['transition'] = getMoveID(
            self.__dstMvst, getMoveName(self.__srcMvst, new_move['transition']))
        return

    def softCopyMove(self, move_id):
        src_move = self.__srcMvst['moves'][move_id]

        # Creating a deep copy of Tag 2 move
        new_move = deepcopy(src_move)

        # Assigning attributes to this new move
        new_move['hit_condition_idx'] = 0
        new_move['extra_properties_idx'] = -1
        new_move['u8'] = len(self.__dstMvst['moves']) - 8
        new_move['u8_2'] = 9

        # Assigning idx
        new_move['cancel_idx'] = len(self.__dstMvst['cancels'])

        # Adding new move to end of the moves list
        self.__dstMvst['moves'].append(new_move)

        # Fixing u15
        # new_move['u15'] = convertU15(new_move['u15'])

        # Copying voice-clip
        voiceclip_idx = new_move['voiceclip_idx']
        new_move['voiceclip_idx'] = self.createNewVoiceclipList(voiceclip_idx)

        return len(self.__dstMvst['moves'])-1

    def createNewVoiceclipList(self, voiceclip_idx):
        if voiceclip_idx == -1:
            return -1
        new_list = getVoiceclipList(self.__srcMvst, voiceclip_idx)
        voiceclip_idx = len(self.__dstMvst['voiceclips'])
        for value in new_list:
            self.__dstMvst['voiceclips'].append(value)
        return voiceclip_idx

    def createExtramovePropertiesList(self, src_move_id, new_move_id):
        # Get moves
        new_move = self.__dstMvst['moves'][new_move_id]
        src_move = self.__srcMvst['moves'][src_move_id]

        # Read list of extraproperties and store them
        src_props_idx = src_move['extra_properties_idx']
        if src_props_idx == -1:
            return
        src_props_list = getExtrapropsList(self.__srcMvst, src_props_idx)

        # Create T7 equivalent of it
        new_props_list = []
        for prop in src_props_list:
            id, type, value = prop['id'], prop['type'], prop['value']
            # type, id, value = getMoveExtrapropAlias(type, id, value)
            # if id == None:
            #     break
            new_props_list.append({'id': id, 'type': type, 'value': value})

        # Assigning index
        new_index = len(self.__dstMvs['extra_move_properties'])
        new_move['extra_properties_idx'] = new_index
        for i in new_props_list:
            self.__dstMvs['extra_move_properties'].append(i)


def copyMovesAcrossMovesets(sourceMvst, destMvst, targetMoveName):
    moveDependency_name_id, moveDependency_id_name = MoveDependencies(
        sourceMvst, destMvst, targetMoveName).getDependencies()
    copierObj = MoveCopier(sourceMvst, destMvst,
                           moveDependency_name_id, moveDependency_id_name)


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

    srcMvst = sys.argv[1]
    dstMvst = sys.argv[2]
    movName = sys.argv[3]

    copyMovesAcrossMovesets(srcMvst, dstMvst, movName)


def test():
    srcMvst = loadJson('./tag2_JIN.json')
    dstMvst = loadJson('./t7_JIN.json')
    movName = 'JIN_up03'
    copyMovesAcrossMovesets(srcMvst, dstMvst, movName)


if __name__ == '__main__':
    # main()
    test()
