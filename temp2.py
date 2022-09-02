import json

from moveCopier import search
from reaction import prettyPrint
from moveDependencies import getMoveID, reaction_keys


reactionlist = {
    "pushback_indexes": [
        91,
        91,
        91,
        91,
        91,
        77,
        91
    ],
    "u1list": [
        0,
        0,
        0,
        0,
        0,
        0
    ],
    "vertical_pushback": 0,
    "standing": "sDm_KAOR18G",
    "ch": "sDm_KAO00R",
    "crouch": "sDm_KAOR18G",
    "crouch_ch": "sDm_KAO00R",
    "left_side": "sDm_KAOL0MG",
    "left_side_crouch": "sDm_KAOL0MG",
    "right_side": "sDm_KAOR0MG",
    "right_side_crouch": "sDm_KAOR0MG",
    "back": "sDm_KAO30M",
    "back_crouch": "sDm_KAO30M",
    "block": "sGrd_hM00",
    "crouch_block": "cGrd_lR00",
    "wallslump": "dDw_OUC00_",
    "downed": "dDwrOUC00_",
    "pushback_list": [
        {
            "val1": 0,
            "val2": 0,
            "val3": 8,
            "pushbackextra_idx": 698,
            "pushbackextra": [
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0
            ]
        },
        {
            "val1": 0,
            "val2": 0,
            "val3": 8,
            "pushbackextra_idx": 698,
            "pushbackextra": [
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0
            ]
        },
        {
            "val1": 0,
            "val2": 0,
            "val3": 8,
            "pushbackextra_idx": 698,
            "pushbackextra": [
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0
            ]
        },
        {
            "val1": 0,
            "val2": 0,
            "val3": 8,
            "pushbackextra_idx": 698,
            "pushbackextra": [
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0
            ]
        },
        {
            "val1": 0,
            "val2": 0,
            "val3": 8,
            "pushbackextra_idx": 698,
            "pushbackextra": [
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0
            ]
        },
        {
            "val1": 32,
            "val2": 50,
            "val3": 8,
            "pushbackextra_idx": 586,
            "pushbackextra": [
                300,
                200,
                100,
                50,
                0,
                0,
                0,
                0
            ]
        },
        {
            "val1": 0,
            "val2": 0,
            "val3": 8,
            "pushbackextra_idx": 698,
            "pushbackextra": [
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0
            ]
        }
    ]
}

pushback_aliases = {}

def subfinder(mylist, pattern):
    matches = []
    for i in range(len(mylist)):
        if mylist[i] == pattern[0] and mylist[i:i+len(pattern)] == pattern:
            matches.append(i)
    return matches

def loadJson(filepath: str):
    try:
        with open(filepath) as f:
            data = json.load(f)
    except FileNotFoundError:
        data = None
    return data

def reactionlistFn(dstMvst):
	# Find pushback extradata indexes in destination movelist
	pushback_list = reactionlist['pushback_list']
	print(len(dstMvst['pushback_extras']))
	for i, pushback in enumerate(pushback_list):
		# print(pushback)
		pushback_extra_idx = pushback['pushbackextra_idx']
		pushback_extra_idx = search(pushback['pushbackextra'], dstMvst['pushback_extras'], pushback_extra_idx-10)
		print("old: ", pushback['pushbackextra_idx'], 'new: ', pushback_extra_idx)
		pushback['pushbackextra_idx'] = pushback_extra_idx
		del pushback['pushbackextra']

	# Find pushback indexes in destination movelist
	print('#######################')
	pushbacks = dstMvst['pushbacks']
	for pushback in pushback_list:
		new_idx = search([pushback], pushbacks)
		print(new_idx)
	print('#######################')
	return

def test2(dstMvst):
    # Replace move names with move IDs
	for key in reaction_keys:
		moveID = getMoveID(dstMvst, reactionlist[key])
		reactionlist[key] = moveID if moveID != -1 else reactionlist[key]

	pushbacks = dstMvst['pushbacks']
	pushback_list = reactionlist['pushback_list']
	for i, pushback in enumerate(pushback_list):
		old_idx = reactionlist['pushback_indexes'][i]
		pushback_extra_idx = pushback['pushbackextra_idx']
		new_list = subfinder(dstMvst['pushback_extras'], pushback['pushbackextra'])
		del pushback['pushbackextra']
		print('old index: ', old_idx, end=' -> ')
		# print('new indexes:')
		# print(new_list)
		if old_idx in pushback_aliases:
			reactionlist['pushback_indexes'][i] = pushback_aliases[old_idx]
			print('new index (aliased): ', new_idx)
			continue
		for idx in new_list:
			pushback['pushbackextra_idx'] = idx
			new_idx = search([pushback], pushbacks)
			if new_idx != -1:
				# print(pushback, '->', new_idx)
				pushback_aliases[old_idx] = new_idx
				print('new index: ', new_idx)
				reactionlist['pushback_indexes'][i] = new_idx
				break
		# break
		# TODO: Create new pushback
	del reactionlist['pushback_list']
	print('\n#######################')
	prettyPrint(reactionlist)
	print('\n#######################')
	prettyPrint(pushback_aliases)
	return

def main():
	dstMvst = loadJson('t7_JIN.json')
	test2(dstMvst)


def test3():
	try:
		with open('copy_aliases1.txt', 'r') as f:
			# lines = f.read()
			lines = f.read().replace('\n', '')
			# print(lines)
			group_cancel_aliases = json.loads(lines)
			group_cancel_aliases = group_cancel_aliases['group_cancel_aliases']
			for item in group_cancel_aliases:
				if (item['alias'] == {}): continue
				print("Move ID: %-4d -> %-4d" % (item['move_id'], item['alias']['move_id']), end=' ')
				print("| Starting Frame: %-4d -> %-4d" % (item['starting_frame'], item['alias']['starting_frame']))
	except:
		print('File not found')
		pass

def test4():
	dstMvst = loadJson('t7_JIN.json')
	end = [{"req": 881, "param": 0}, {"req": 881, "param": 0}]
	idx = search(end, dstMvst['requirements'])
	print(idx)

if __name__ == '__main__':
	# main()
	test3()