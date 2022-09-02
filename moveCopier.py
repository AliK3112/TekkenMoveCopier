from copy import deepcopy
import sys
import json
from Aliases import fillAliasesDictonnaries, getMoveExtrapropAlias, getRequirementAlias
from moveDependencies import MoveDependencies, reaction_keys


def loadJson(filepath: str):
    try:
        with open(filepath) as f:
            data = json.load(f)
    except FileNotFoundError:
        data = None
    return data


def saveJson(filename, movesetData):
    with open(filename, "w") as f:
        json.dump(movesetData, f, indent=4)
    return


def search(pat, txt, start=0):
    M = len(pat)
    N = len(txt)
    for i in range(start, N - M + 1):
        j = 0
        while(j < M):
            if (txt[i + j] != pat[j]):
                break
            j += 1
        if (j == M):
            return i
    return -1

def subfinder(mylist, pattern):
    matches = []
    for i in range(len(mylist)):
        if mylist[i] == pattern[0] and mylist[i:i+len(pattern)] == pattern:
            matches.append(i)
    return matches


def isSame(moveset1, moveset2):
    return moveset1['version'] == moveset2['version'] \
        and moveset1['tekken_character_name'] == moveset2['tekken_character_name'] \
        and moveset1['character_name'] == moveset2['character_name'] \
        and moveset1['creator_name'] == moveset2['creator_name']


def isSameInDifferentGame(moveset1, moveset2):
    return moveset1['tekken_character_name'] == moveset2['tekken_character_name'] \
        and moveset1['creator_name'] == moveset2['creator_name']


def getMoveName(moveset, idx: int) -> str:
    if idx >= len(moveset['moves']):
        raise BaseException('Invalid move index passed: %d' % idx)

    if idx >= 0x8000:
        idx = moveset['aliases'][idx-0x8000]
    return moveset['moves'][idx]['name']


def getMoveID(moveset: dict, movename: str, start=0):
    n = len(moveset['moves'])
    start = 0 if (start >= n or start < 0) else start
    for i in range(start, n):
        if moveset['moves'][i]['name'] == movename:
            return i
    return -1


def getVoiceclipList(moveset, idx: int) -> list:
    if idx >= len(moveset['voiceclips']):
        raise BaseException('Invalid voiceclip index passed: %d' % idx)

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


def getExtrapropsList(moveset, idx: int) -> list:
    if idx >= len(moveset['extra_move_properties']):
        raise BaseException('Invalid extra move properties index passed: %d' % idx)

    list = []
    while True:
        prop = moveset['extra_move_properties'][idx]
        list.append(prop)
        if isLast(prop):
            break
        idx += 1
    return list


def getInputSequence(moveset, idx: int) -> list:
    if idx >= len(moveset['input_sequences']):
        raise BaseException('Invalid input sequence index passed: %d' % idx)

    sequence = deepcopy(moveset['input_sequences'][idx])
    start = sequence['extradata_idx']
    end = start + sequence['u2']
    list = moveset['input_extradata'][start: end]
    sequence['inputs'] = list
    return sequence


def getReqList(moveset, idx: int) -> list:
    if idx >= len(moveset['requirements']):
        raise BaseException('Invalid requirements list index passed: %d' % idx)

    list = []
    while True:
        requirement = deepcopy(moveset['requirements'][idx])
        req, param = getRequirementAlias(moveset['version'], requirement['req'], requirement['param'])
        requirement['req'] = req
        requirement['param'] = param
        list.append(requirement)
        if (requirement['req'] == 881):  # TODO: Replace 881 with game end req val
            break
        idx += 1
    return list

def getReactionList(moveset, idx: int) -> dict:
    if idx >= len(moveset['reaction_list']):
        raise BaseException('Invalid reaction list index passed: %d' % idx)

    # Getting specific reaction list
    reaction_list = deepcopy(moveset['reaction_list'][idx])

    reaction_list['pushback_list'] = []

    # Iterating through pushbacks of reaction lists and assigining them
    for i, index in enumerate(reaction_list['pushback_indexes']):
        pushback = deepcopy(moveset['pushbacks'][index])

        # Assigning 'pushbackextra_idx' value to it
        extra_idx = pushback['pushbackextra_idx']
        val3 = pushback['val3']
        pushback['pushbackextra'] = moveset['pushback_extras'][extra_idx: extra_idx+val3]

        reaction_list['pushback_list'].append(pushback)

    # Assigning move-names instead of indexes
    for i in reaction_keys:
        index = reaction_list[i]
        reaction_list[i] = getMoveName(moveset, index)

    return reaction_list


# Find idx of the cancel extradata. Take source extradata value and find it's index in destination moveset
def findExtradataIndex(extradata_value: int, moveset: dict):
    for i, j in enumerate(moveset['cancel_extradata']):
        if j == extradata_value:
            return i

    # Add if it doesn't exist, add it
    moveset['cancel_extradata'].append(extradata_value)
    return len(moveset['cancel_extradata'])


class MoveCopier:
    def __init__(self, sourceMvst: dict, dstMvst: dict, dependency_name_id: dict, dependency_id_name: dict):
        if sourceMvst == None:
            raise BaseException('Source Moveset Empty')
        if dstMvst == None:
            raise BaseException('Destination Moveset Empty')
        if isSame(sourceMvst, dstMvst):
            raise BaseException('Source & Destination movesets are the same')
        if dstMvst['version'] != 'Tekken7':
            raise BaseException(
                'Destination Moveset is Not a Tekken 7 moveset. version =', dstMvst['version'])

        self.__srcMvst = sourceMvst
        self.__dstMvst = dstMvst
        self.__dependency_name_id = dependency_name_id
        self.__dependent_id_name = dependency_id_name
        self.pushback_aliases = {}
        self.group_cancel_aliases = {}

        with open('copy_aliases.txt', 'r') as f:
            try:
                lines = f.read().replace('\n', '')
                obj = json.loads(lines)
                self.group_cancel_aliases = obj['group_cancel_aliases']
            except:
                self.group_cancel_aliases = {}

    def __get881ReqIdx(self) -> int:
        end = [{"req": 881, "param": 0}, {"req": 881, "param": 0}]
        return search(end, self.__dstMvst['requirements'])
        # return self.__srcMvst['hit_conditions'][1]['requirement_idx']

    def CopyAllDependentMoves(self):
        keys = ['requirements', 'extra_move_properties', 'voiceclips', 'hit_conditions', 
        'pushbacks', 'pushback_extras', 'reaction_list', 'cancels', 'moves', 'input_sequences',
        'input_extradata', 'cancel_extradata']
        before = {}
        for i in keys:
            before[i] = len(self.__dstMvst[i])

        fillAliasesDictonnaries(self.__srcMvst['version'])
        indexesOfAddedMoves = []

        # Iterate the dictionary
        for _, src_move_id in enumerate(self.__dependent_id_name):
            # Create the move and get the ID
            new_move_id = self.softCopyMove(src_move_id)

            # Storing index of this newly created move
            indexesOfAddedMoves.append(new_move_id)
            print('Move Added: %s. Index = %d' % (self.__dependent_id_name[src_move_id], indexesOfAddedMoves[-1]))

        print('\n')

        # Creating secondary properties. (cancels, reactions)
        for i, src_move_id in enumerate(self.__dependent_id_name):
            # Update transition
            self.updateTransition(src_move_id, indexesOfAddedMoves[i])

            # Creating extraprops list
            print('Creating Extraprop list at idx: %d for move %d - %s' % (len(self.__dstMvst['extra_move_properties']), indexesOfAddedMoves[i], self.__dependent_id_name[src_move_id]))
            self.createExtramovePropertiesList(src_move_id, new_move_id)

            # Get source move
            src_move = self.__srcMvst['moves'][src_move_id]

            # Get new move
            new_move_id = indexesOfAddedMoves[i]
            new_move = self.__dstMvst['moves'][new_move_id]

            # if their names aren't equal, break
            if src_move['name'] != new_move['name']:
                raise BaseException('move Name not equal\nSource: %s\nNew: %s' % (src_move['name'], new_move['name']))

            # Get cancel index of src move
            src_move_cancel_idx = src_move['cancel_idx']

            # Set index to last cancel
            new_move_cancel_idx = len(self.__dstMvst['cancels'])

            # Copy Cancels
            print('Creating cancel list at idx: %d for move %d - %s' % (new_move['cancel_idx'], new_move_id, new_move['name']))
            size_of_new_cancel_list = self.copyCancelList(src_move_cancel_idx)

            # Assigning index to move whose cancel list was just created
            self.__dstMvst['moves'][new_move_id]['cancel_idx'] = new_move_cancel_idx

            # Adjusting rest of the cancels
            for j in range(new_move_id+1, len(self.__dstMvst['moves'])):
                self.__dstMvst['moves'][j]['cancel_idx'] += size_of_new_cancel_list

            # Creating hit conditions & reaction lists
            print('Creating Hit Condition list at idx: %d for move %d - %s' % (len(self.__dstMvst['hit_conditions']), new_move_id, new_move['name']))
            new_move['hit_condition_idx'] = self.createHitCondition(src_move['hit_condition_idx'])
            print('\n')
        
        after = {}
        for i in keys:
            after[i] = len(self.__dstMvst[i])

        for i in keys:
            print('New %s created: %d' % (i, after[i] - before[i]))
        return

    # Updates the transition attribute, this value may refer to a move that doesn't exist yet, so better to call this function after importing moves
    def updateTransition(self, src_move_id: int, new_move_id: int):
        new_move = self.__dstMvst['moves'][new_move_id]
        if new_move['transition'] >= 0x8000:
            return
        new_move['transition'] = getMoveID(self.__dstMvst, getMoveName(self.__srcMvst, new_move['transition']))
        return

    def softCopyMove(self, move_id: int):
        src_move = self.__srcMvst['moves'][move_id]

        # Creating a deep copy of Source move
        new_move = deepcopy(src_move)

        # Assigning attributes to this new move
        new_move['hit_condition_idx'] = 0
        new_move['extra_properties_idx'] = -1
        new_move['u8_2'] = self.__dstMvst['aliases'][-1]
        new_move['u8'] = len(self.__dstMvst['moves']) - new_move['u8_2'] + 2

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
            type, id, value = getMoveExtrapropAlias(
                self.__srcMvst['version'], type, id, value)
            if id == None:
                break
            new_props_list.append({'id': id, 'type': type, 'value': value})

        # Assigning index
        new_index = len(self.__dstMvst['extra_move_properties'])
        new_move['extra_properties_idx'] = new_index
        self.__dstMvst['extra_move_properties'] += new_props_list

        return new_index

    def createRequirementsList(self, reqList):
        idx = search(reqList, self.__dstMvst['requirements'])
        if idx == -1:
            idx = len(self.__dstMvst['requirements'])
            for req in reqList:
                self.__dstMvst['requirements'].append(req)
        return idx

    def createHitCondition(self, src_hit_idx: int) -> int:
        if src_hit_idx == 0:
            return 0
        req881 = self.__get881ReqIdx()
        new_idx = len(self.__dstMvst['hit_conditions'])
        while True:
            hit_cond = deepcopy(self.__srcMvst['hit_conditions'][src_hit_idx])
            reqList = getReqList(self.__srcMvst, hit_cond['requirement_idx'])
            if (reqList == [{'req': 881, 'param': 0}]):
                req_idx = req881
            else:
                req_idx = self.createRequirementsList(reqList)
            hit_cond['requirement_idx'] = req_idx
            print('[REACTION] Requirement list created at idx: %d' % req_idx)

            # Get new reaction list idx
            reactionList = getReactionList(self.__srcMvst, hit_cond['reaction_list_idx'])
            hit_cond['reaction_list_idx'] = self.createReactionList(reactionList)
            print('Reaction list created at idx: %d' % hit_cond['reaction_list_idx'])
            
            # Append new hit condition
            self.__dstMvst['hit_conditions'].append(hit_cond)

            # Loop break
            if req_idx == req881:
                break

            src_hit_idx += 1

        return new_idx

    def createReactionList(self, reactionlist: dict) -> int:
        # Replace move names with move IDs
        for key in reaction_keys:
            moveID = getMoveID(self.__dstMvst, reactionlist[key])
            if moveID == -1:
                raise Exception('move "%s" not found while creating reaction list' % reactionlist[key])
            reactionlist[key] = moveID

        searchFlag = True

        # Find pushback indexes in destination movelist
        pushback_list = reactionlist['pushback_list']
        del reactionlist['pushback_list']
        for i, pushback_data in enumerate(pushback_list):
            pushback_idx = reactionlist['pushback_indexes'][i] # Old pushback_index
            pushback_idx, flag = self.getPushbackIdx(pushback_data, pushback_idx, i)
            if not flag:
                searchFlag = False
            reactionlist['pushback_indexes'][i] = pushback_idx # Assigning new pushback index

        if searchFlag:
            new_idx = search([reactionlist], self.__dstMvst['reaction_list'])
            if new_idx != -1:
                return new_idx

        # Appending new reaction-list into moveset
        new_idx = len(self.__dstMvst['reaction_list'])
        self.__dstMvst['reaction_list'].append(reactionlist)
        return new_idx

    # Returns also a Flag to decide whether we should search for this reaction
    # list in destination or not, once correct pushbacks have been applied
    def getPushbackIdx(self, pushback_dict: dict, pushback_idx: int, idx: int):
        # Getting all pushback indexes
        pushback_extra = pushback_dict['pushbackextra']
        del pushback_dict['pushbackextra']
        indexes = subfinder(self.__dstMvst['pushback_extras'], pushback_extra)

        # If no pushback_extras were found
        if len(indexes) <= 0:
            # Create new extras list
            new_pushback_idx = len(self.__dstMvst['pushback_extras'])
            self.__dstMvst['pushback_extras'] += pushback_extra
            pushback_dict['pushbackextra_idx'] = new_pushback_idx

            # This also means to create new pushback
            new_idx = len(self.__dstMvst['pushbacks'])
            self.__dstMvst['pushbacks'].append(pushback_dict)
            return new_idx, False

        if pushback_idx in self.pushback_aliases:
            new_idx = self.pushback_aliases[pushback_idx]
            return new_idx, True
        for idx in indexes:
            pushback_dict['pushbackextra_idx'] = idx
            new_idx = search([pushback_dict], self.__dstMvst['pushbacks'])
            if new_idx != -1:
                self.pushback_aliases[pushback_idx] = new_idx
                return new_idx, True

        # If after complete search, the pushback_idx is still -1, then add new
        new_idx = len(self.__dstMvst['pushbacks'])
        self.__dstMvst['pushbacks'] += pushback_extra
        return new_idx, False

    def updateMoveID(self, new_cancel):
        if (new_cancel['command'] == 0x800b):
            return

        if new_cancel['move_id'] >= 0x8000:
            return

        new_cancel['move_id'] = getMoveID(
            self.__dstMvst, getMoveName(self.__srcMvst, new_cancel['move_id']))
        return

    def checkCommand(self, cancel):
        command = cancel['command']
        # Group Cancel
        if command == 0x800b:
            for item in self.group_cancel_aliases:
                if item['move_id'] == cancel['move_id'] and item['starting_frame'] == cancel['starting_frame']:
                    if not item['alias']:
                        continue
                    cancel['move_id'] = item['alias']['move_id']
                    cancel['starting_frame'] = item['alias']['starting_frame']
                    break
            return True

        # Input sequence
        if 0x800d <= command <= len(self.__srcMvst['input_sequences']):
            inputSeq = getInputSequence(self.__srcMvst, command - 0x800d)
            self.createInputSequence(inputSeq)
        return False

    def createInputSequence(self, inputSeq):
        inputExtras = self.__dstMvst['input_extradata']
        last = inputExtras.pop()
        idx = len(inputExtras)
        self.__dstMvst['input_extradata'] += inputSeq['inputs']
        self.__dstMvst['input_extradata'].append(last)
        del inputSeq['inputs']
        inputSeq['extradata_idx'] = idx
        self.__dstMvst['input_sequences'].append(inputSeq)
        return

    def copyCancelList(self, src_cancel_idx: int):
        count = 0
        while True:
            try:
                src_cancel = self.__srcMvst['cancels'][src_cancel_idx]
            except:
                n = len(self.__srcMvst['cancels'])
                print('Total cancels = %d | idx = %d' % (n, src_cancel_idx))
                raise Exception
            new_cancel = deepcopy(src_cancel)

            # Check if it is an input sequence or group cancel
            if self.checkCommand(new_cancel):
                src_cancel_idx += 1
                continue

            # Update extradata
            extradata_value = self.__srcMvst['cancel_extradata'][src_cancel['extradata_idx']]
            new_cancel['extradata_idx'] = findExtradataIndex(extradata_value, self.__dstMvst)

            # Update move ID
            self.updateMoveID(new_cancel)

            # Update requirement_idx
            reqList = getReqList(self.__srcMvst, src_cancel['requirement_idx'])
            new_cancel['requirement_idx'] = self.createRequirementsList(reqList)
            print('Requirement list created at idx: %d' % new_cancel['requirement_idx'])

            # Update the new cancel into 'cancels' list
            self.__dstMvst['cancels'].append(new_cancel)

            # Update iterator
            src_cancel_idx += 1
            count += 1

            if new_cancel['command'] == 0x8000:
                break
        return count


def copyMovesAcrossMovesets(sourceMvst, destMvst, targetMoveName):
    moveDependency_name_id, moveDependency_id_name = MoveDependencies(
        sourceMvst, destMvst, targetMoveName).getDependencies()
    copierObj = MoveCopier(sourceMvst, destMvst,
                           moveDependency_name_id, moveDependency_id_name)
    copierObj.CopyAllDependentMoves()
    # for _, id in enumerate(moveDependency_id_name):
    #     print(id, moveDependency_id_name[id])
    print("Done copying %s and all of it's dependencies" % targetMoveName)
    # path = r"C:\Users\alikh\Documents\TekkenMovesetExtractor\extracted_chars\t7_JIN_TEST"
    path = r"./"
    # saveJson('%s/%s_new.json' % (path, destMvst['character_name']), destMvst)


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
    # print('STILL Work in Progress')
