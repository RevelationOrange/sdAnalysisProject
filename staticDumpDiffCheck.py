import json
import snp2lib
import os
from os import sep
import codecs


'''
this program (currently) will find differences between two static dump files. place the files (which must be .json
files) in the same folder as staticDumpDiffCheck.py (and make sure oldFileName and newFileName are those of the files
you want to check), and it will write the file changes.txt in the same folder, which contains where each difference is
found, and whether something was added, removed, or changed.
'''

# spacer is the delineator between depth levels of the dict, so output shows up with different spacing
spacer = '  '
'''
this block explains the logic of the recursive function findTheDiffs and how it determines where differences are found
and what type (add, rem, change, or mismatch if types don't agree)
note that any indices given (which is any location that's just a number) may not be accurate since lists get sorted
note that all output is to the file given
cases:
  type mismatch:
    output that a mismatch was found, add the location and items to the difference list
  dict:
    dict1 == dict2: nothing, just return at the end
    else:
      state that a difference was found, output the keys trail
      difference in keys:
        go through keys and output which keys are new and which were removed
      go through each key that exists in both dicts:
        add key to keys trail, case: dict1[key], dict2[key]
  list:
    list1 == list2: nothing, just return at end
    else:
      state that a difference was found, output the keys trail
      if length diff:
        for one list, check 'if in' the other, record added, removed
        for added, append to diffList: keysTrail, 'add', thing
        for removed, append to diffList: keysTrail, 'rem', thing
        check diffList for any 'dummy' entries. if found, set 'changes to true
        if changes: this means the things in addList and remList aren't additions or removals, but each is a change in another
          output the number of things changed, which is the length of remList, since addList includes the dummy
        else:
          if anything is added or removed, output how many (for both lists)
      else: same length but some changes
        if these are lists of dicts:
          append a dummy entry to newThing and send the two lists back into findTheDiffs, so it'll be treated as an add
          or removal
          this functionality was added because otherwise, the dicts would be delved into and possibly hundreds or
          thousands of differences would be found, and every tiny change would be added to diffList, which isn't at all
          practical
          AFTER that, add a dummy key to the keys trail, since something is going to get removed
        else:
          sort both lists to ensure ordering
          go through each thing, for i in the length of the lists:
            add i to keys trail
            case: list1[i], list2[i], i
  else (str, int, empty, whatever):
    if thing1 == thing2: nothing, just return at end
    else:
      output that data was changed and where, state the old and new things
      find the last entry in keysTrail that's not an index
      add keysTrail[-1], 'change', thing1, thing2 to diffList
  del keysTrail[-1]
  return
'''
def findTheDiffs(oldThing, newThing, keysTrail, theFile, ntabs=1):
    # full logic found above, but this function goes through the given static dump files to find differences

    # diffList holds each recorded change (except differences in keys, output to theFile) using the format:
    # [location (a key), change type, object (usually a list or dict)]
    # if the change type is a mismatch or a change, both objects are appended after change type
    diffList = []
    if type(oldThing) != type(newThing):
        theFile.write( spacer*ntabs + "uh, their types are different. that's not right.\n" )
        diffList.append([keysTrail, 'mismatch', oldThing, newThing])
    elif type(oldThing) is dict:
        if oldThing == newThing:
            pass
        else:
            theFile.write( spacer*ntabs + 'difference found in ' + ', '.join([ str(x) for x in keysTrail]) + '\n' )
            # grab the keys from each thing now, so as not to keep calling .keys()
            # boy, how silly would it be to keep doing that? >.>
            oldKeys = oldThing.keys()
            newKeys = newThing.keys()
            if sorted(oldKeys) != sorted(newKeys):
                theFile.write( spacer*ntabs + 'difference in keys found in ' + ', '.join([ str(x) for x in keysTrail]) + '\n')
                addKeys = []
                remKeys = []
                for key in oldKeys:
                    if key not in newKeys:
                        remKeys.append(key)
                for key in newKeys:
                    if key not in oldKeys:
                        addKeys.append(key)
                if len(addKeys) > 0:
                    theFile.write( spacer*(ntabs+1) + 'new key(s): ' + ', '.join(addKeys) + '\n' )
                if len(remKeys) > 0:
                    theFile.write( spacer*(ntabs+1) + 'removed key(s): ' + ', '.join(remKeys) + '\n' )
            # using sets here easily gets the keys that exist in both dicts
            for key in list(set(oldKeys)&set(newKeys)):
                keysTrail.append(key)
                diffList += findTheDiffs(oldThing[key], newThing[key], keysTrail, theFile, ntabs+1)
    elif type(oldThing) is list:
        if oldThing == newThing:
            pass
        else:
            theFile.write( spacer*ntabs + 'difference found in ' + ', '.join([ str(x) for x in keysTrail]) + '\n' )
            if len(oldThing) != len(newThing):
                # case: 2 lists of differing lengths where an extra entry is the same as another entry in that list
                # since 'thing' in each loop will always be found in the other list, this means nothing will be added
                # to the add or rem lists
                # hopefully this only shows up in one place ('customer_levels') so I can just be lazy and not accout
                # for it in general, because ugghhh.
                # well, it did show up in build times for a workstation. dammit.
                addLists = []
                remLists = []
                for thing in oldThing:
                    if thing not in newThing:
                        remLists.append(thing)
                for thing in newThing:
                    if thing not in oldThing:
                        addLists.append(thing)
                for thing in addLists:
                    diffList.append([keysTrail[-1], 'add', thing])
                for thing in remLists:
                    diffList.append([keysTrail[-1], 'rem', thing])
                changes = False
                # in this loop, changes only gets set to true when a dummy is found, which only happens when the two
                # lists are the same length but a difference is found
                for x in diffList:
                    if type(x[2]) is dict:
                        if 'dummy' in x[2]:
                            changes = True
                            newThing.remove({'dummy':'dummy'})
                            diffList.remove(x)
                # if there are changes, say how many, if there are only additions/removals, state how many of each
                if changes:
                    theFile.write( spacer*(ntabs+1) + str(len(remLists)) + ' ' + keysTrail[-1] + ' changed\n' )
                else:
                    if len(addLists) > 0:
                        theFile.write( spacer*(ntabs+1) + str(len(addLists)) + ' ' + keysTrail[-1] + ' added\n' )
                    if len(remLists) > 0:
                        theFile.write( spacer*(ntabs+1) + str(len(remLists)) + ' ' + keysTrail[-1] + ' removed\n' )
            else:
                if type(oldThing[0]) is dict and type(newThing[0]) is dict:
                    # if the next level down is dictionaries, we don't want to dig deeper and deeper and end up
                    # recording every tiny little difference, so toss a dummy entry on to newThing and throw it back
                    # into findTheDiff, only don't increase the indentations
                    # also add a dummy key, which won't be used anywhere but to be removed, to preserve the keys trail
                    newThing.append({'dummy':'dummy'})
                    diffList += findTheDiffs(oldThing, newThing, keysTrail, theFile, ntabs)
                    keysTrail.append('dummy')
                else:
                    sOld = sorted(oldThing)
                    sNew = sorted(newThing)
                    for index in range(len(sOld)):
                        keysTrail.append(index)
                        diffList += findTheDiffs(sOld[index], sNew[index], keysTrail, theFile, ntabs+1)
    else:
        if oldThing == newThing:
            pass
        else:
            theFile.write( spacer*ntabs + 'data changed in {}: old: {}, new: {}\n'.format(str(keysTrail[-1]), oldThing, newThing) )
            j = -1
            while type(keysTrail[j]) is int:
                j -= 1
            diffList.append([keysTrail[j], 'change', oldThing, newThing])
    del keysTrail[-1]
    return diffList

def placeholder():
    # this just makes the code easier to navigate for my particular ide
    pass

# here, set the filenames for the static dumps you want to use and the output file where the change locations will be
# recorded
sdFileNums = ['17238', '17873', '17874', '17921']
oldFileName = 'sd' + sdFileNums[-2] + '.json'
newFileName = 'sd' + sdFileNums[-1] + '.json'
updFolder = 'updates'
outputFileName = updFolder + sep + 'changes.txt'

# this determines whether or not each thing in diffs (defined later) will be printed
# if you want to see a bunch of stuff in your terminal, set it to True
showDiffs = 1

# open each file and store in oldSD and newSD
# res is used to bypass the 'result' key, which isn't particularly interesting
with open(oldFileName, 'r') as sdFile:
    res = json.load(sdFile)
oldSD = res['result']

with open(newFileName, 'r') as sdFile:
    res = json.load(sdFile)
newSD = res['result']

# print the new and old version numbers. for posterity.
print('old version:', oldSD['sv_version'], '\nnew version:', newSD['sv_version'], '\n')

# diffs will hold the entry for each change: [location, type, object(, other object)]
diffs = []
# then open the output file, creating the directory if necessary
# if not(os.path.exists(updFolder) and os.path.isdir(updFolder)):
os.makedirs(updFolder, exist_ok=True)
with open(outputFileName, 'w') as outFile:
    # check that any differences exist,
    if oldSD != newSD:
        # if so, say so and starting digging into the dictionaries
        print('some differences')
        outFile.write('differences between versions {} and {}:\n'.format(oldSD['sv_version'], newSD['sv_version']))
        diffs += findTheDiffs(oldSD, newSD, ['result'], outFile)
        outFile.write('\n')
        print('info written to', outputFileName)
    else:
        # if not, output so and we're done
        print('no differences found')

# finally, if you set showDiffs to True, you'll see every changed entry
#print len(diffs)

# [u'customers', u'sv_version', u'assets', u'items', u'recipes', u'modules', u'cl_version', u'customer_level_values',
# u'SELL_MINIMUM_PERCENT', u'recipe_unlocks', u'improvements', u'fame_levels', u'hunts']
# dict with changeTypes for keys
diffDict = {}
for thing in diffs:
    if thing[0] in diffDict:
        diffDict[thing[0]]['stuff'] += [thing[1:]]
    else:
        diffDict[thing[0]] = {'stuff':[thing[1:]], 'adds':0, 'removals':0, 'changes':0}

# create a 'clean' diff dict, one that finds and combines changes instead of storing them as separate adds and removals
cleanDiffDict = {}
for key in diffDict:
    for thing in diffDict[key]['stuff']:
        thingMatch = False
        for otherThing in diffDict[key]['stuff']:
            if type(thing[1]) is dict:
                if thing[1]['id'] == otherThing[1]['id']:
                    if thing != otherThing:
                        thingMatch = True
                        if key in cleanDiffDict:
                            if ['change', otherThing[1], thing[1]] not in cleanDiffDict[key]['stuff']:
                                cleanDiffDict[key]['stuff'] += [['change', thing[1], otherThing[1]]]
                        else:
                            cleanDiffDict[key] = {'stuff':[['change', thing[1], otherThing[1]]], 'adds':0, 'removals':0, 'changes':0}
        if not thingMatch:
            if key in cleanDiffDict:
                cleanDiffDict[key]['stuff'] += [thing]
            else:
                cleanDiffDict[key] = {'stuff':[thing], 'adds':0, 'removals':0, 'changes':0}

# sum up totals for cleanDiffDict
for key in cleanDiffDict:
    for thing in cleanDiffDict[key]['stuff']:
        if thing[0] == 'add': cleanDiffDict[key]['adds'] += 1
        elif thing[0] == 'rem': cleanDiffDict[key]['removals'] += 1
        elif thing[0] == 'change': cleanDiffDict[key]['changes'] += 1
        else: print('derp!')

allNewIDs = []
itemCheckSections = {'items':['id'], 'recipes':['id', 'components'], 'improvements':['requirements'],
                     'recipe_unlocks':['crafted_item_id', 'recipe_id'], 'quests':['party_items']}
for section in itemCheckSections:
    print(section)
    if section in cleanDiffDict:
        for thing in cleanDiffDict[section]['stuff']:
            for key in itemCheckSections[section]:
                if type(thing[1][key]) is list:
                    for subThing in thing[1][key]:
                        allNewIDs.append(subThing['item_id'])
                else:
                    allNewIDs.append(thing[1][key])
uqIDs = list(set(allNewIDs))
if 0 in uqIDs: uqIDs.remove(0)

cleanDiffDict['fullItems'] = {'stuff':[['new version', x] for x in uqIDs]}

if showDiffs:
    checkList = snp2lib.getInfo()
    for key in cleanDiffDict:
        if key in checkList:
            with codecs.open('updates'+sep+key+'.txt', 'w', 'utf-8') as updateFile:
                print(key)
                if key == 'fame_levels':
                    for change in ['add', 'rem', 'change']:
                        niceThing = snp2lib.getInfo([key, change, [ x[1] for x in cleanDiffDict['fame_levels']['stuff']
                                                                    if x[0] == change]], newSD)
                        if len(niceThing[1]) > 0:
                            snp2lib.prInfo([key]+niceThing, updateFile)
                else:
                    for thing in cleanDiffDict[key]['stuff']:
                        if thing[0] == 'change':
                            newChange = thing[1]
                            oldChange = thing[2]
                            niceNew = snp2lib.getInfo([key, thing[0], newChange], newSD)
                            niceOld = snp2lib.getInfo([key, thing[0], oldChange], newSD)
                            if niceNew == niceOld:
                                niceThing = niceNew
                                niceThing[0] = 'minor change'
                            else:
                                niceThing = [thing[0], {}]
                                for ckey in niceNew[1]:
                                    niceThing[1]['new'+ckey] = niceNew[1][ckey]
                                for ckey in niceOld[1]:
                                    niceThing[1]['old'+ckey] = niceOld[1][ckey]
                        else:
                            change = thing[1]
                            niceThing = snp2lib.getInfo([key, thing[0], change], newSD)
                        #print key, niceThing
                        for x in niceThing[1]:
                            print(x + ':', niceThing[1][x])
                        snp2lib.prInfo([key]+niceThing, updateFile)
                        print('')
                print('info written to', 'updates'+sep+key+'.txt')
        else:
            print(key + ':', cleanDiffDict[key], '\n')
