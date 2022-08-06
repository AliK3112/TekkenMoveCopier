from copy import deepcopy
import json

#####################################################################################
#                              STOLEN FROM KILO                                     #
#####################################################################################
from Tag2Aliases import tag2_requirements, tag2_extra_move_properties


def getMoveExtrapropAlias(type, id, value):
    alias = tag2_extra_move_properties.get(id, None)
    if alias != None:
        id = alias['t7_id']
        if 'force_value' in alias:
            value = alias['value']
    return type, id, value


def getRequirementAlias(req, param):
    alias = tag2_requirements.get(req, None)
    if alias != None:
        req = alias['t7_id']
        if 'param_alias' in alias:
            param = alias['param_alias'].get(param, param)
    return req, param


def fillDict(dictionnary):
    keylist = sorted(dictionnary)
    generatedKeys = 0

    if 0xFFFF in dictionnary:
        return dictionnary

    for i in range(len(keylist) - 1):
        key = keylist[i]
        nextkey = keylist[i + 1]
        key_diff = nextkey - (key + 1)

        if 'nofill' in dictionnary[key] or 'nofill' in dictionnary[nextkey]:
            continue

        alias_offset = dictionnary[key]['t7_id'] - key
        alias_offset2 = dictionnary[nextkey]['t7_id'] - nextkey

        if alias_offset == alias_offset2 and key_diff > 0:
            for i in range(1, key_diff + 1):
                dictionnary[key + i] = {
                    't7_id': dictionnary[key]['t7_id'] + i,
                    'desc': '%d:FILLED' % (key + i)
                }
                generatedKeys += 1

    dictionnary[0xFFFF] = 'FILLED_DICT'
    print("Generated %d keys" % (generatedKeys))
    return dictionnary


def fillAliasesDictonnaries():
    fillDict(tag2_requirements)
    fillDict(tag2_extra_move_properties)

######################################################################################


# This table was created manually for Tag2 -> T7 Jin Omen Stance
requirement_aliases = {
    31: 28,
    33: 30,
    1005: 1179,
    1012: 1186,
    1019: 1193,
    1257: 1644,
    1302: 1688,
    1304: 1690,
    1306: 1692,
    1323: 2625,
    1438: 1282,
    1461: 1321,
    1978: 1943,
    1988: 1953,
    1998: 1963,
    2018: 1983,
    2028: 1993,
    2048: 2013,
    2143: 1294,
    2151: 215,
    2156: 2337,
    2204: 2557,
    2218: 1282,
}


# Aliases for group cancels that I found, this table was created manually for Tag2 -> T7 Jin Omen Stance
group_cancel_aliases = [
    {
        'move_id': 0,
        'starting_frame': 101,
        'alias': {
            'move_id': 0,
            'starting_frame': 113,
        },
    },
    {
        'move_id': 288,
        'starting_frame': 51,
        'alias': {
            'move_id': 320,
            'starting_frame': 52,
        },
    },
    {
        'move_id': 558,
        'starting_frame': 92,
        'alias': {
            'move_id': 595,
            'starting_frame': 93,
        },
    },
    {
        'move_id': 791,
        'starting_frame': 19,
        'alias': {
            'move_id': 825,
            'starting_frame': 19,
        },
    },
    {
        'move_id': 864,
        'starting_frame': 20,
        'alias': {
            'move_id': 898,
            'starting_frame': 20,
        },
    },
    {
        'move_id': 971,
        'starting_frame': 51,
        'alias': {
            'move_id': 1005,
            'starting_frame': 51,
        },
    },
    {
        'move_id': 952,
        'starting_frame': 18,
        'alias': {
            'move_id': 986,
            'starting_frame': 18,
        },
    },
    {
        'move_id': 1218,
        'starting_frame': 8,
        'alias': {
            'move_id': 1254,
            'starting_frame': 8,
        },
    },
    {
        'move_id': 1256,
        'starting_frame': 15,
        'alias': {
            'move_id': 1288,
            'starting_frame': 13,
        },
    },
    {
        'move_id': 1302,
        'starting_frame': 6,
        'alias': {
            'move_id': 1332,
            'starting_frame': 6,
        },
    },
    {
        'move_id': 1309,
        'starting_frame': 8,
        'alias': {
            'move_id': 1339,
            'starting_frame': 8,
        },
    },
    {
        'move_id': 1336,
        'starting_frame': 10,
        'alias': {
            'move_id': 1366,
            'starting_frame': 8,
        },
    },
    {
        'move_id': 1493,
        'starting_frame': 3,
        'alias': {
            'move_id': 1519,
            'starting_frame': 3,
        },
    },
    {
        'move_id': 1497,
        'starting_frame': 122,
        'alias': {
            'move_id': 1546,
            'starting_frame': 143,
        },
    },
    {
        'move_id': 1620,
        'starting_frame': 19,
        'skip': 'yes',
    },
]


def saveJson(filename, movesetData):
    with open(filename, "w") as f:
        json.dump(movesetData, f, indent=4)
    return


def loadJson(filename):
    try:
        with open(filename) as f:
            data = json.load(f)
    except FileNotFoundError:
        data = None
    return data


def reverseBitOrder(number):
    res = 0
    for i in range(7):  # skip last bit
        bitVal = (number & (1 << i)) != 0
        res |= (bitVal << (7 - i))
    return res


def convertU15(number):
    return (number >> 7) | ((reverseBitOrder(number)) << 24)


def getMoveName(moveset, move_id):
    if move_id >= 0x8000:
        move_id = moveset['aliases'][move_id-0x8000]
    return moveset['moves'][move_id]['name']


def getMoveID(moveset, movename):
    for i, move in enumerate(moveset['moves']):
        if move['name'] == movename:
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


def createExtramovePropertiesList(tag2_moveset, t7_moveset, tag2_moveid, t7_moveid):
    # Get T7 move
    t7_move = t7_moveset['moves'][t7_moveid]

    # Get TTT2 move
    tag2_move = tag2_moveset['moves'][tag2_moveid]

    # Read list of extraproperties and store them
    tag2_props_idx = tag2_move['extra_properties_idx']
    if tag2_props_idx == -1:
        return
    tag2_move_props = getExtrapropsList(tag2_moveset, tag2_props_idx)

    # Create T7 equivalent of it
    t7_move_props = []
    for prop in tag2_move_props:
        id, type, value = prop['id'], prop['type'], prop['value']
        type, id, value = getMoveExtrapropAlias(type, id, value)
        if id == None:
            break
        t7_move_props.append({'id': id, 'type': type, 'value': value})

    # Assigning index
    new_index = len(t7_moveset['extra_move_properties'])
    t7_move['extra_properties_idx'] = new_index
    for i in t7_move_props:
        t7_moveset['extra_move_properties'].append(i)
    print('New props list created for move %s at index %d' %
          (t7_move['name'], new_index))
    return


# Find idx of the cancel extradata. Take tag2 extradata value and find it's index in T7 moveset
def findExtradataIndex(extradata_value, moveset):
    for i, j in enumerate(moveset['cancel_extradata']):
        if j == extradata_value:
            return i
    return 0


# This was supposed to be a function that would take both movesets, and do a 'pattern matching' to find index of the same input sequence
def findEquivalentInputSequence(idx):
    newValue = {
        27: 27,
        47: 48,
        116: 243,
    }.get(idx, idx)
    return newValue + 0x800d


# Finds the T7 equivalent of TTT2 move ID, remember that I store moves with their names in these structures
def updateMoveIDs(t7_cancel, tag2_moveset, t7_moveset):
    if (t7_cancel['command'] == 0x800b):
        return

    if t7_cancel['move_id'] >= 0x8000:
        return

    t7_cancel['move_id'] = getMoveID(
        t7_moveset, getMoveName(tag2_moveset, t7_cancel['move_id']))
    return


# This was supposed to be a pattern search function or a new requirement list builder function
def updateRequirementIdx(idx):
    return requirement_aliases.get(idx, idx)


# Checks and applies group cancel alias
def specialCommandAlias(t7_cancel):
    # Get command alias
    command = t7_cancel['command']
    if command == 0x800b:
        for i, item in enumerate(group_cancel_aliases):
            if item['move_id'] == t7_cancel['move_id'] and item['starting_frame'] == t7_cancel['starting_frame']:
                try:  # Skip 'Tag out' group cancel
                    if item['skip'] == 'yes':
                        return False
                except:
                    pass
                t7_cancel['move_id'] = item['alias']['move_id']
                t7_cancel['starting_frame'] = item['alias']['starting_frame']
                break
    elif 0x800d <= command <= 0x81ff:
        t7_cancel['command'] = findEquivalentInputSequence(command - 0x800d)
    return True


def copyCancelList(tag2_moveset, t7_moveset, tag2_cancel_idx, t7_cancel_idx):
    count = 0
    while True:
        tag2_cancel = tag2_moveset['cancels'][tag2_cancel_idx]
        t7_cancel = deepcopy(tag2_cancel)
        if not specialCommandAlias(t7_cancel):
            tag2_cancel_idx += 1
            continue

        extradata_value = tag2_moveset['cancel_extradata'][t7_cancel['extradata_idx']]
        t7_cancel['extradata_idx'] = findExtradataIndex(
            extradata_value, t7_moveset)

        updateMoveIDs(t7_cancel, tag2_moveset, t7_moveset)

        t7_cancel['requirement_idx'] = updateRequirementIdx(
            t7_cancel['requirement_idx'])

        t7_moveset['cancels'].append(t7_cancel)

        # updating iterator & count
        tag2_cancel_idx += 1
        count += 1

        if t7_cancel['command'] == 0x8000:
            break
    return count, t7_cancel_idx + count


def createNewVoiceclipList(tag2_moveset, t7_moveset, voiceclip_idx):
    new_list = getVoiceclipList(tag2_moveset, voiceclip_idx)
    voiceclip_idx = len(t7_moveset['voiceclips'])
    for value in new_list:
        t7_moveset['voiceclips'].append(value)
    return voiceclip_idx


# Updates the transition attribute, this value may refer to a move that doesn't exist yet, so better to call this function after importing moves
def updateTransition(tag2_moveset, t7_moveset, move_id):
    t7_move = t7_moveset['moves'][move_id]
    if t7_move['transition'] >= 0x8000:
        return
    t7_move['transition'] = getMoveID(
        t7_moveset, getMoveName(tag2_moveset, t7_move['transition']))
    return


def copyCancels(t7_moveset, tag2_moveset, movename):
    # Get Tekken 7 move
    t7_move_id = getMoveID(t7_moveset, movename)
    if (t7_move_id == -1):
        print('Move %s not found in Tekken 7 moveset' % movename)
        return
    t7_move = t7_moveset['moves'][t7_move_id]

    # Get Tag 2 Move ID to get Tag 2 move
    tag2_move_id = getMoveID(tag2_moveset, t7_move['name'])
    if (tag2_move_id == -1):
        print('Move %s not found in Tag 2 moveset' % t7_move['name'])
        return
    tag2_move = tag2_moveset['moves'][tag2_move_id]

    # if their names aren't equal, break
    if tag2_move['name'] != t7_move['name']:
        print('move Name not equal\nTag 2: %s\n T7: %s' %
              (tag2_move['name'], t7_move['name']))
        return

    # Get cancel_idx of tag 2 move
    tag2_move_cancel_idx = tag2_move['cancel_idx']

    # Set t7 index to last cancel
    t7_move_cancel_idx = len(t7_moveset['cancels'])

    size_of_new_cancel_list, newIdx = copyCancelList(
        tag2_moveset, t7_moveset, tag2_move_cancel_idx, t7_move_cancel_idx)

    # Assigning index to move whose cancel list was just created
    t7_moveset['moves'][t7_move_id]['cancel_idx'] = t7_move_cancel_idx

    # Adjusting rest of the cancels
    for j in range(t7_move_id+1, len(t7_moveset['moves'])):
        t7_moveset['moves'][j]['cancel_idx'] += size_of_new_cancel_list

    return


def softCopyMove(tag2_moveset, t7_moveset, move_id):
    tag2_move = tag2_moveset['moves'][move_id]

    # Creating a deep copy of Tag 2 move
    t7_move = deepcopy(tag2_move)

    # Assigning attributes to this new move
    t7_move['hit_condition_idx'] = 0
    t7_move['extra_properties_idx'] = -1
    t7_move['u8'] = len(t7_moveset['moves']) - 8
    t7_move['u8_2'] = 9

    # Create empty cancel
    cancel = {
        "command": 0x8000,
        "extradata_idx": 0,
        "requirement_idx": 0,
        "frame_window_start": 0,
        "frame_window_end": 0,
        "starting_frame": 0,
        "move_id": 32769,
        "cancel_option": 336
    }

    # Assigning idx
    t7_move['cancel_idx'] = len(t7_moveset['cancels'])

    # Adding new cancel to end of cancels list
    # t7_jin['cancels'].append(cancel)

    # Adding new move to end of the moves list
    t7_moveset['moves'].append(t7_move)

    # Fixing u15
    t7_move['u15'] = convertU15(t7_move['u15'])

    # Copying voice-clip
    voiceclip_idx = t7_move['voiceclip_idx']
    if voiceclip_idx != -1:
        t7_move['voiceclip_idx'] = createNewVoiceclipList(
            tag2_moveset, t7_moveset, voiceclip_idx)

    return len(t7_moveset['moves'])-1


def copyMoves(tag2_moveset, t7_moveset, newMovesToAdd):
    indexesOfAddedMoves = []

    # Let's copy moves first
    for movename in newMovesToAdd:
        # Get ID of tag 2 move
        tag2_move_id = getMoveID(tag2_moveset, movename)

        # Create the move and get the ID
        t7_move_id = softCopyMove(tag2_moveset, t7_moveset, tag2_move_id)

        # Storing index of this newly created move
        indexesOfAddedMoves.append(t7_move_id)
        print('Move Added: %-20s. Index = %d' %
              (movename, indexesOfAddedMoves[-1]))

        # Creating extraprops list
        createExtramovePropertiesList(
            tag2_moveset, t7_moveset, tag2_move_id, t7_move_id)

    # Update transition
    for i in indexesOfAddedMoves:
        updateTransition(tag2_moveset, t7_moveset, i)

    # Copying tag 2 cancels to put into T7
    for move in newMovesToAdd:
        copyCancels(t7_moveset, tag2_moveset, move)

    return


if __name__ == "__main__":
    # Filling kilo's alias dictionary
    fillAliasesDictonnaries()
    t7_jin = loadJson('./t7_JIN.json')
    tag2_jin = loadJson('./tag2_JIN.json')

    newMovesToAdd = ['sGrd_RE11', 'sDm_HAR00MG', 'cDm_KAO00MG', 'sDm_HARL0MG', 'cDm_KAOL0MG',
                     'sDm_HARR0MG', 'cDm_KAOR0MG', 'sDm_KAO0027', 'sDm_KAOL27M', 'sDm_KAOR27M']

    copyMoves(tag2_jin, t7_jin, newMovesToAdd)

    # Save to JSON
    path = r"ADD PATH TO JSON HERE"
    saveJson('%s/%s.json' % (path, t7_jin['character_name']), t7_jin)
