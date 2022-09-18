# TekkenMoveCopier
Python scripts to safely copy moves from across Tekken games (7 & Tag 2 for now)

# How to use?
```
python moveCopier.py <sourceMovesetJsonPath> <TargetMovesetJsonPath> <moveName>
```
## If you want to only print the dependencies, run this command instead
```
python moveDependencies.py <sourceMovesetJsonPath> <TargetMovesetJsonPath> <moveName>
```
## Example
```
python moveCopier.py ./t7_JIN.json ./tag2_JIN.json JIN_up03
```

## How to forbid some moves from being copied-over?
Pretty simple. The tool supports a "copy_aliases.json" file which contains info about group cancels, forbidden moves & requirement indices.
![copy_aliases.json Format](https://user-images.githubusercontent.com/83224003/190888148-033ae5d6-0c8c-4a7a-9ac5-54fb8789931d.png)


## Pre-requisites
Make sure the moveset doesn't have duplicate names.
If it does, remember to rename duplicate names like "SameMove", "SameMove2", "SaveMove3"... 
