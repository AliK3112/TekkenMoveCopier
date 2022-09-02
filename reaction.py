from copy import deepcopy
import json

# "reaction_list": [
#     {
#         "pushback_indexes": [0, 0, 0, 0, 0, 0, 0], len = 7
#         "u1list": [0, 0, 0, 0, 0, 0], len = 6
#         "vertical_pushback": 0,
#         "standing": 0,
#         "ch": 0,
#         "crouch": 0,
#         "crouch_ch": 0,
#         "left_side": 0,
#         "left_side_crouch": 0,
#         "right_side": 0,
#         "right_side_crouch": 0,
#         "back": 0,
#         "back_crouch": 0,
#         "block": 0,
#         "crouch_block": 0,
#         "wallslump": 0,
#         "downed": 0
#     },
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
# "pushbacks": [
#     {
#         "val1": 0,
#         "val2": 0,
#         "val3": 1,
#         "pushbackextra_idx": 0
#     }, ]
#  "pushback_extras": [0, 0, ... ]

pushback_aliases = {
    27: 21,
    77: 76
}

movesToAdd = []


def search(pat, txt):
    M = len(pat)
    N = len(txt)
    for i in range(N - M + 1):
        j = 0
        while(j < M):
            if (txt[i + j] != pat[j]):
                break
            j += 1
        if (j == M):
            return i
    return -1


def prettyPrint(d, indent=0):
    for key, value in d.items():
        if key == 'pushbacks':
            print('%-20s:' % key)
            for pushback in value:
                print('\t', end='')
                print('Duration: %-5d' % pushback['val1'], end=' ')
                print('Displacement: %-5d' % pushback['val2'], end=' ')
                print('Num of Extra: %-5d' % pushback['val3'], end=' ')
                print('Extras:', pushback['pushbackextra'])
            print()
        elif key == 'u1list':
            print('%-20s:' % key, end=' ')
            for i in value:
                print('%d' % i, end=' ')
            print()
        else:
            print('%-20s: %s' % (key, value))
    return


# Should return a dictionary with ALL data about a reaction list
# 'standing', 'ch' etc.. should store name of the move
def getReactionListAllData(moveset, idx: int):
    reaction_list = moveset['reaction_list']
    if idx >= len(reaction_list):
        return None

    # Getting specific reaction list
    reaction_list = deepcopy(reaction_list[idx])

    pushbacks = moveset['pushbacks']
    pushback_extras = moveset['pushback_extras']

    reaction_list['pushback_list'] = []

    # Iterating through pushbacks of reaction lists and assigining them
    for i, index in enumerate(reaction_list['pushback_indexes']):
        pushback = deepcopy(pushbacks[index])

        # Assigning 'pushbackextra_idx' value to it
        extra_idx = pushback['pushbackextra_idx']
        val3 = pushback['val3']
        pushback['pushbackextra'] = pushback_extras[extra_idx: extra_idx+val3]
        # del pushback['pushbackextra_idx']

        reaction_list['pushback_list'].append(pushback)

    # Renaming 'pushback_indexes' to 'pushbacks'
    # reaction_list['pushbacks'] = reaction_list['pushback_indexes']
    # del reaction_list['pushback_indexes']

    # Assigning move-names instead of indexes
    for i in keys:
        index = reaction_list[i]
        reaction_list[i] = getMoveName(moveset, index)

    return reaction_list


def pushbackMatches1(obj1, obj2):
    return obj1['val1'] == obj2['val1'] and obj1['val2'] == obj2['val2'] and obj1['val3'] == obj2['val3']


def matchPushbacks(moveset, srcReactionList, idx):
    pushback_keys = ['front', 'back', 'left',
                     'right', 'front_ch', 'downed', 'block']
    toFindPushbacks = srcReactionList['pushbacks']
    for i, pushback in enumerate(moveset['pushbacks']):
        # Val 1, 2 and 3 match. Now we need to match pushback extra idx
        if pushbackMatches1(pushback, toFindPushbacks[idx]):
            pbid = pushback['pushbackextra_idx']
            t7_list = moveset['pushback_extras'][pbid:pbid+pushback['val3']]

            if toFindPushbacks[idx]['pushbackextra'] == t7_list:
                print('\tPushback-%-10s:%d -> idx:%d' %
                      (pushback_keys[idx], i, pbid), end=' -> ')
                print(t7_list)
                return i
    return -1


# Takes TTT2 reaction list and displays T7 equivalent
def findSimilarReactionList(moveset, srcReactionList):
    reactions_list = moveset['reaction_list']
    pushbacks = moveset['pushbacks']
    pushback_extras = moveset['pushback_extras']
    moves = moveset['moves']
    print("%-20s: %d" % ('vertical_pushback',
          srcReactionList['vertical_pushback']))
    for key in keys:
        print("%-20s: " % key, end='')
        id = getMoveID(moveset, srcReactionList[key])
        if id == -1:
            id = srcReactionList[key]
            if id not in movesToAdd:
                movesToAdd.append(id)  # moveToAdd is global
        print(id)

    pushback_keys = ['front', 'back', 'left',
                     'right', 'front_ch', 'downed', 'block']
    for i, pb in enumerate(srcReactionList['pushbacks']):
        matchPushbacks(moveset, srcReactionList, i)
        list = pb['pushbackextra']
        pushback_extra_idx = search(list, pushback_extras)
        print('\tPushback-%-10s:' % pushback_keys[i], end=' ')
        print(pushback_extra_idx)
    return


def getMoveName(moveset: dict, move_idx: int):
    if move_idx >= 0x8000:
        move_idx = moveset['aliases'][move_idx-0x8000]
    return moveset['moves'][move_idx]['name']


def getMoveID(moveset, movename):
    for i, move in enumerate(moveset['moves']):
        if move['name'] == movename:
            return i
    return -1


def reverseBitOrder(number):
    res = 0
    for i in range(7):  # skip last bit
        bitVal = (number & (1 << i)) != 0
        res |= (bitVal << (7 - i))
    return res


def convertU15(number):
    return (number >> 7) | ((reverseBitOrder(number)) << 24)


def loadJson(filename):
    try:
        with open(filename) as f:
            data = json.load(f)
    except FileNotFoundError:
        data = None
    return data


def SaveJson(filename, movesetData):
    with open(filename, "w") as f:
        json.dump(movesetData, f, indent=4)
    return


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


def copyVoicelist(tag2_jin, t7_jin, voiceclip_idx):
    new_list = getVoiceclips(tag2_jin, voiceclip_idx)
    voiceclip_idx = len(t7_jin['voiceclips'])
    for value in new_list:
        t7_jin['voiceclips'].append(value)
    return voiceclip_idx


def main():
    t7_moveset = loadJson('t7_JIN.json')
    tag2_moveset = loadJson('tag2_JIN.json')
    if tag2_moveset == None:
        return
    tag2_list = getReactionListAllData(tag2_moveset, 90)
    # prettyPrint(tag2_list)
    print(tag2_list)
    SaveJson('temp_new.json', tag2_list)
    # findSimilarReactionList(t7_moveset, tag2_list)

    # checkReactionlists = [116, 9, 107, 212, 117, 213]
    # for i in checkReactionlists:
    #     tag2_list = getReactionListAllData(tag2_moveset, i)
    #     findSimilarReactionList(t7_moveset, tag2_list)
    return


if __name__ == "__main__":
    main()
