import json


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


def loadJson(filename):
    try:
        with open(filename) as f:
            data = json.load(f)
    except FileNotFoundError:
        data = None
    return data


def main():
    data = loadJson('t7_JIN.json')
    if data == None:
        return

    far = []  # flat array of requirements
    for requirement in data['requirements']:
        far.append(requirement['req'])
        far.append(requirement['param'])

    # toFind = [44, 0, 0x8003, 0, 0x84c6, 0x7000010,
    #           0x84c6, 0x9000000, 0x802e, 9, 881, 0]
    # toFind = [44, 0, 32769, 0, 881, 0]
    toFind = [
        {'req': 44, 'param': 0},
        {'req': 32769, 'param': 0},
        {'req': 881, 'param': 0},
    ]
    idx = search(toFind, data['requirements'])
    print("Requirement list found at index ", idx)
    return


if __name__ == "__main__":
    main()
