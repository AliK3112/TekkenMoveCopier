from copy import deepcopy
import json

# with open(jsonPath, "w") as f:
#     movesetData = self.dict()
#     movesetData['original_hash'] = self.calculateHash(movesetData)
#     movesetData['last_calculated_hash'] = movesetData['original_hash']
#     movesetData['mota_type'] = (1 << 2)  # allow hand mota by default
#     json.dump(movesetData, f, indent=4)

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


def SaveJson(filename, movesetData):
    with open(filename, "w") as f:
        json.dump(movesetData, f, indent=4)
    return


def LoadJson(filename):
    try:
        with open(filename) as f:
            data = json.load(f)
    except FileNotFoundError:
        data = None
    return data


def getMoveName(moveset, move_idx):
    if move_idx >= 0x8000:
        move_idx = moveset['aliases'][move_idx-0x8000]
    return moveset['moves'][move_idx]['name']


def getMoveID(moveset, movename):
    for i, move in enumerate(moveset['moves']):
        if move['name'] == movename:
            return i
    return -1


def getVoiceclips(moveset, idx):
    list = []
    i = idx
    while True:
        voiceclip = moveset['voiceclips'][i]
        list.append(voiceclip)
        if voiceclip == 4294967295:
            break
        i += 1
    return list


def extradata(tag2_val, t7_jin):
    for i, j in enumerate(t7_jin['cancel_extradata']):
        if j == tag2_val:
            return i
    return 0


def checkInputSequence(idx):
    newValue = {
        27: 27,
        47: 48,
        116: 243,
    }.get(idx, idx)
    return newValue + 0x800d


def updateMoveIDs(t7_cancel, tag2_jin, t7_jin):
    if (t7_cancel['command'] == 0x800b):
        return

    if t7_cancel['move_id'] >= 0x8000:
        return

    t7_cancel['move_id'] = getMoveID(
        t7_jin, getMoveName(tag2_jin, t7_cancel['move_id']))
    return


def updateRequirementIdx(idx):
    return requirement_aliases.get(idx, idx)


def specialCommandAlias(t7_cancel):
    # Get command alias
    command = t7_cancel['command']
    if command == 0x800b:
        for i, item in enumerate(group_cancel_aliases):
            if item['move_id'] == t7_cancel['move_id'] and item['starting_frame'] == t7_cancel['starting_frame']:
                try:
                    if item['skip'] == 'yes':
                        return False
                except:
                    pass
                t7_cancel['move_id'] = item['alias']['move_id']
                t7_cancel['starting_frame'] = item['alias']['starting_frame']
                break
    elif 0x800d <= command <= 0x81ff:
        t7_cancel['command'] = checkInputSequence(command - 0x800d)
    return True


def copyCancelLists(tag2_jin, t7_jin, tag2_cancel_idx, t7_cancel_idx):
    count = 0
    while True:
        tag2_cancel = tag2_jin['cancels'][tag2_cancel_idx]
        t7_cancel = deepcopy(tag2_cancel)
        if not specialCommandAlias(t7_cancel):
            tag2_cancel_idx += 1
            continue

        extradata_value = tag2_jin['cancel_extradata'][t7_cancel['extradata_idx']]
        t7_cancel['extradata_idx'] = extradata(
            extradata_value, t7_jin)

        updateMoveIDs(t7_cancel, tag2_jin, t7_jin)

        t7_cancel['requirement_idx'] = updateRequirementIdx(
            t7_cancel['requirement_idx'])
        # t7_jin['cancels'].insert(t7_cancel_idx + count, t7_cancel)
        t7_jin['cancels'].append(t7_cancel)

        # updating iterator & count
        tag2_cancel_idx += 1
        count += 1

        if t7_cancel['command'] == 0x8000:
            # t7_jin['cancels'][t7_cancel_idx+count] = t7_cancel
            break
    return count, t7_cancel_idx + count


def copyVoicelist(tag2_jin, t7_jin, voiceclip_idx):
    new_list = getVoiceclips(tag2_jin, voiceclip_idx)
    voiceclip_idx = len(t7_jin['voiceclips'])
    for value in new_list:
        t7_jin['voiceclips'].append(value)
    return voiceclip_idx


def reverseBitOrder(number):
    res = 0
    for i in range(7):  # skip last bit
        bitVal = (number & (1 << i)) != 0
        res |= (bitVal << (7 - i))
    return res


def convertU15(number):
    return (number >> 7) | ((reverseBitOrder(number)) << 24)


def softCopyMove(tag2_jin, t7_jin, move_idx):
    tag2_move = tag2_jin['moves'][move_idx]
    t7_move = deepcopy(tag2_move)
    t7_move['hit_condition_idx'] = 0
    t7_move['extra_properties_idx'] = -1
    t7_move['u8'] = len(t7_jin['moves']) - 8
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

    # Adding idx
    t7_move['cancel_idx'] = len(t7_jin['cancels'])

    # Adding new cancel to end of cancels list
    # t7_jin['cancels'].append(cancel)

    # Adding new move to end of the moves list
    t7_jin['moves'].append(t7_move)

    # Fixing u15
    t7_move['u15'] = convertU15(t7_move['u15'])

    # Copying voice-clip
    voiceclip_idx = t7_move['voiceclip_idx']
    if voiceclip_idx != -1:
        t7_move['voiceclip_idx'] = copyVoicelist(
            tag2_jin, t7_jin, voiceclip_idx)

    return len(t7_jin['moves'])-1


def updateTransition(tag2_jin, t7_jin, move_idx):
    t7_move = t7_jin['moves'][move_idx]
    if t7_move['transition'] >= 0x8000:
        return
    t7_move['transition'] = getMoveID(
        t7_jin, getMoveName(tag2_jin, t7_move['transition']))
    return


def func(tag2_jin, t7_jin):
    new_idx = []
    newMovesToAdd = ['sGrd_RE11', 'sDm_HAR00MG', 'cDm_KAO00MG', 'sDm_HARL0MG', 'cDm_KAOL0MG',
                     'sDm_HARR0MG', 'cDm_KAOR0MG', 'sDm_KAO0027', 'sDm_KAOL27M', 'sDm_KAOR27M']

    # Let's copy moves first
    for movename in newMovesToAdd:
        tag2_index = getMoveID(tag2_jin, movename)
        new_idx.append(softCopyMove(tag2_jin, t7_jin, tag2_index))
        print('Move Added: %-20s. Index = %d' % (movename, new_idx[-1]))

    # # Let's copy moves first
    # start_idx = 1729
    # end_idx = 1740
    # for i in range(start_idx, end_idx):
    #     new_idx.append(softCopyMove(tag2_jin, t7_jin, i))

    # print(new_idx)
    # Update transition
    for i in range(new_idx[0], new_idx[-1]):
        updateTransition(tag2_jin, t7_jin, i)

    for move in newMovesToAdd:
        copyCancels(t7_jin, tag2_jin, move)

    path = r"C:\Users\alikh\Documents\TekkenMovesetExtractor\extracted_chars\t7_JIN_BOSS"
    SaveJson('%s/%s.json' % (path, t7_jin['character_name']), t7_jin)
    return


def layCancels(moveset, move_idx):
    cancel_idx = moveset['moves'][move_idx]['cancel_idx']
    print("%d %s -> " % (move_idx, moveset['moves'][move_idx]['name']), end='')
    while True:
        cancel = moveset['cancels'][cancel_idx]
        print(cancel['move_id'], end='')
        if cancel['command'] == 0x8000:
            print()
            break
        else:
            print(', ', end='')
        cancel_idx += 1
    return


def fixingCancelIdx(tag2_jin, t7_jin):
    moveID = 2234
    c_idx = t7_jin['moves'][moveID]['cancel_idx']
    for i in range(moveID, len(t7_jin['moves'])-1):
        prev = t7_jin['moves'][i]['cancel_idx']
        prev += 1
        t7_jin['moves'][i+1]['cancel_idx'] = prev
    return


def main():
    t7_jin = LoadJson('./t7_JIN_12.json')
    tag2_jin = LoadJson('./tag2_JIN.json')
    func(tag2_jin, t7_jin)
    return
    # for i in range(1730, 1741):
    # layCancels(tag2_jin, i)
    fromMoveIdx = 1828
    toMoveIdx = 2241
    fromIdx = 6722
    toIdx = 11002
    # times = toIdx - fromIdx
    # fixingCancelIdx(tag2_jin, t7_jin)
    nCancels = len(t7_jin['cancels'])
    print('length t7_jin[\'cancels\']: ', nCancels)
    # return
    # # Deleting all cancels from the end
    # while len(t7_jin['cancels']) != 11002:
    #     t7_jin['cancels'].pop()

    # times = copyCancelLists(tag2_jin, t7_jin, fromIdx, toIdx)
    # for i in range(0, times-1):
    #     cancel = t7_jin['cancels'][fromIdx + i]
    #     new_cancel = deepcopy(cancel)
    #     t7_jin['cancels'].insert(toIdx + i, new_cancel)

    # n = len(t7_jin['moves'])


def copyCancels(t7_jin, tag2_jin, movename):
    start = 2254
    end = 2274
    # for i in range(start, end+1):
    # Get Tekken 7 move
    t7_move_id = getMoveID(t7_jin, movename)
    if (t7_move_id == -1):
        print('Move %s not found in Tekken 7 moveset' % movename)
        return
    t7_move = t7_jin['moves'][t7_move_id]

    # Get Tag 2 Move ID to get Tag 2 move
    tag2_move_id = getMoveID(tag2_jin, t7_move['name'])
    if (tag2_move_id == -1):
        print('Move %s not found in Tag 2 moveset' % t7_move['name'])
        return
    tag2_move = tag2_jin['moves'][tag2_move_id]

    # if their names isn't equal, break
    if tag2_move['name'] != t7_move['name']:
        print('move Name not equal\nTag 2: %s\n T7: %s' %
              (tag2_move['name'], t7_move['name']))
        return

    # Get cancel_idx of tag 2 move
    tag2_move_cancel_idx = tag2_move['cancel_idx']

    # Set toIdx to last cancel idx
    t7_move_cancel_idx = len(t7_jin['cancels'])

    # toIdx = t7_jin['moves'][i]['cancel_idx']
    times, newIdx = copyCancelLists(
        tag2_jin, t7_jin, tag2_move_cancel_idx, t7_move_cancel_idx)

    # Assigning index to move whose cancel list was just created
    t7_jin['moves'][t7_move_id]['cancel_idx'] = t7_move_cancel_idx
    # print('Cancel_idx for next move should be:', newIdx)
    # t7_jin['moves'][t7_move_id+1]['cancel_idx'] += times
    # fromMoveIdx += 1
    for j in range(t7_move_id+1, len(t7_jin['moves'])):
        t7_jin['moves'][j]['cancel_idx'] += times

    # for i in range(last, len(t7_jin['moves'])-1):
    #     t7_jin['moves'][i+1]['cancel_idx'] += times
    # print('After everything length of cancels: ', len(t7_jin['cancels']))
    # path = r"C:\Users\alikh\Documents\TekkenMovesetExtractor\extracted_chars\t7_JIN_BOSS"
    # SaveJson('%s/%s.json' % (path, t7_jin['character_name']), t7_jin)
    return


if __name__ == "__main__":
    # main()
    t7_jin = LoadJson('./t7_JIN.json')
    print(getMoveID(t7_jin, 'JIN_up03'))
