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

## Pre-requisites
Make sure the moveset doesn't have duplicate names.
If it does, remember to rename duplicate names like "SameMove", "SameMove2", "SaveMove3"... 
