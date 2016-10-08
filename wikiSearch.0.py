import snp2lib
from os import sep
import json
import argparse
import sys


'''
wikiSearch.py is meant to return information that would normally be found on the edgebee wiki, using flexible searches,
like price ranges for items, or item types that customers will buy
'''

class addWithOpt(argparse.Action):
    def __call__(self, parser, namespace, values, *args, **kwargs):
        a = getattr(namespace, self.dest)
        if a is None:
            a = []
        a.append([args[0][1:]]+values)
        setattr(namespace, self.dest, a)

class dummyFile():
    # this is just a way to avoid making a file when using snp2lib.getInfo()
    def __init__(self):
        self.output = ''
    def write(self, derp):
        self.output += derp
    def unleash(self):
        print(self.output)

# sdp = snp2lib.getPlainSD()
wsFolder = 'wikiSearchData'

def eq(x,y):
    return x == y

def ne(x,y):
    return x != y

def lt(x,y):
    return x < y

def le(x,y):
    return x <= y

def gt(x,y):
    return x > y

def ge(x,y):
    return x >= y

def within(x,y):
    return x >= y[0] and x <= y[1]

def nothing(x):
    return x

def canIntConvert(x):
    # just a convenience, so a string can be checked if it's an int without crashing
    try:
        int(x)
        return True
    except:
        return False

def listTest(key, val, chktype):
    defRet = True if chktype == '==' else False
    def tst(theDict):
        for i in theDict[key]:
            if type(i) is str:
                if val in i.lower():
                    return defRet
        return not defRet
    return [tst, [key, val, chktype]]

def list2Test(key, val, chktype):
    # gotta check key, if it's a list then check it against the whole list or whatever
    defRet = True if chktype == '==' else False
    def tst(theDict):
        if (type(theDict[key])) is list:
            if type(val) is list:
                for thing in theDict[key]:
                    doubleMatch = True
                    for _ in range(len(val)):
                        if type(val[_]) is str:
                            if val[_] not in thing[_].lower():
                                doubleMatch =False
                        else:
                            if val[_] != thing[_]:
                                doubleMatch = False
                    if doubleMatch:
                        return defRet
                return not defRet
            else:
                for thing in theDict[key]:
                    for i in thing:
                        if type(i) is list:
                            if val in i:
                                return defRet
                        elif str(val) in str(i).lower():
                            return defRet
                return not defRet
        else:
            return not defRet
    return [tst, [key, val, chktype]]

def numTest(key, val, chktype, meta=''):
    chkFxns = {'len': len, 'len2': len, 'len3': len, '': nothing}
    if meta == 'len3':
        a = [['a', 2], ['b', 7]]
        def tst(x):
            for y in x[key]:
                for z in y:
                    if type(z) is str:
                        if testDict[chktype](chkFxns[meta](z), val):
                            return True
            return False
    elif meta == 'len2':
        def tst(x):
            # print(x[key])
            for y in x[key]:
                if type(y) is not int:
                    if testDict[chktype](chkFxns[meta](y), val):
                        return True
            return False
    else:
        def tst(x):
            return testDict[chktype](chkFxns[meta](x[key]), val)
    return [tst, [key, val, chktype, meta]]

def textTest(key, txt, chktype):
    # this function adds a test for text values
    # key is the dict key to use, txts contains the values to match
    defRet = True if chktype == '==' else False
    def tst(x):
        if txt in x[key].lower():
            return defRet
        else:
            return not defRet
    return [tst, [key, txt, chktype]]

def getItemKeys():
    # the item searching function
    # argKeys converts text keys entered by the user into the dict keys to actually use
    # numTypes designates which keys need to use valueSearch() rather than textSearch()
    argAssocs = {'madeOn': ['made on', 'station', 'workstation'], 'sellXP': ['sell xp', 'sale xp'],
                 'nfRecs': ['used in', 'pre for'], 'craftXP': ['craft xp'], 'madeBy': ['worker', 'crafter', 'made by'],
                 'nextItem': ['unlocks', 'next item', 'next'], 'repairCost': ['repair cost'],
                 'craftTime': ['speed', 'craft speed', 'craft time', 'time'], 'ingredients': ['uses', 'needs'],
                 'nfQuests': ['quests', 'used in quests', 'needed for quests'], 'value': ['price', 'cost'],
                 'prevItem': ['prev item', 'previous item', 'unlocked by', 'prev'],
                 'craftTimeNum': ['speed num', 'speed number', 'time num', 'ntime', 'nspeed'],
                 'nfBuilds': ['used in building', 'building'], 'type': ['category'], 'rare': ['israre', 'is rare'],
                 'rrare': ['really rare', 'actually rare', 'prerare', 'any rare']}
    baseKeys = ['madeOn', 'sellXP', 'nfRecs', 'craftXP', 'madeBy', 'id', 'picLink', 'nextItem', 'repairCost', 'name',
                'level', 'craftTime', 'ingredients', 'nfQuests', 'value', 'prevItem', 'craftTimeNum', 'nfBuilds',
                'type', 'rare', 'rrare']
    numTypes = ['sellXP', 'craftXP', 'id', 'repairCost', 'level', 'value', 'craftTimeNum']
    listTypes = ['madeOn', 'nfQuests', 'prevItem', 'nfRecs']
    list2Types = ['ingredients', 'nfBuilds', 'nextItem']
    strTypes = list(set(numTypes+listTypes+list2Types)^set(baseKeys))
    argKeys = {}
    # add the base keys to the converter rather than typing them into the dict manually
    for x in baseKeys:
        argKeys[x] = x
    for k in argAssocs:
        for assoc in argAssocs[k]:
            argKeys[assoc] = k
    return strTypes,numTypes,listTypes,list2Types,argKeys

def getCustomerKeys():
    argAssocs = {'color': ['hex code'], 'lvlReq': ['level required', 'shop level'], 'equips': ['can use', 'equip', 'klash'],
                 'startLvl': ['start level', 'starts at'], 'appealReq': ['appeal required', 'appeal', 'appeal needed'],
                 'iTypes': ['types', 'can buy', 'buy list', 'will buy', 'type list', 'item list', 'items', 'buys'],
                 'unlockedBy': ['prereq', 'building', 'unlocked by'], 'maxLvl': ['max level']}
    baseKeys = ['color', 'id', 'lvlReq', 'name', 'startLvl', 'iTypes', 'maxLvl', 'class', 'unlockedBy', 'appealReq',
                'equips']
    numTypes = ['id', 'lvlReq', 'startLvl', 'maxLvl', 'appealReq']
    listTypes = ['iTypes', 'unlockedBy', 'equips']
    list2Types = []
    strTypes = list(set(numTypes + listTypes + list2Types) ^ set(baseKeys))
    argKeys = {}
    for x in baseKeys:
        argKeys[x] = x
    for k in argAssocs:
        for assoc in argAssocs[k]:
            argKeys[assoc] = k
    return strTypes,numTypes,listTypes,list2Types,argKeys

def getModuleKeys():
    argAssocs = {'bonuses': ['bonus', 'gives bonus'], 'hammerCost': ['hammers', 'hammer cost'],
                 'maxBuyable': ['max buyable', 'max with gold'], 'unlockedBy': ['prereq', 'unlocked by'],
                 'appeals': ['appeal', 'appeal bonus'], 'goldCosts': ['price', 'cost', 'gold cost'],
                 'times': ['upgrade time', 'upgrade times', 'time'], 'levelReq': ['level', 'shop level',
                                                                                  'level required']}
    baseKeys = ['picLink', 'name', 'bonuses', 'id', 'hammerCost', 'maxBuyable', 'unlockedBy', 'tier', 'appeals',
               'goldCosts', 'times', 'levelReq']
    numTypes = ['tier', 'levelReq', 'hammerCost', 'id', 'maxBuyable', 'hammerCost']
    listTypes = ['times', 'goldCosts', 'appeals']
    list2Types = ['bonuses']
    strTypes = list(set(numTypes + listTypes + list2Types) ^ set(baseKeys))
    argKeys = {}
    for x in baseKeys:
        argKeys[x] = x
    for k in argAssocs:
        for assoc in argAssocs[k]:
            argKeys[assoc] = k
    return strTypes,numTypes,listTypes,list2Types,argKeys

def getImprovementKeys():
    argAssocs = {'buildUnlocks': ['unlocks building', 'unlocks buildings', 'buildings unlocked', 'unlocks',
                                  'next building'],
                 'upgradeCost': ['upgrade cost', 'cost', 'requires'],
                 'custUnlocks': ['customers', 'unlocks customer', 'unlocks customers'],
                 'level': ['unlocked at'], 'bonus': ['bonus given', 'bonus provided', 'gives bonus'],
                 'unlockedBy': ['unlocked by', 'previous building', 'prereq'],
                 'time': ['upgrade time', 'upgrade duration'], 'description': ['descr', 'text']}
    baseKeys = ['name', 'buildUnlocks', 'upgradeCost', 'id', 'custUnlocks', 'level', 'picLink', 'bonus', 'unlockedBy',
                'time', 'description']
    numTypes = ['id', 'level', 'time']
    listTypes = ['upgradeCost', 'bonus', 'unlockedBy']
    list2Types = ['custUnlocks', 'buildUnlocks']
    strTypes = list(set(numTypes + listTypes + list2Types) ^ set(baseKeys))
    argKeys = {}
    for x in baseKeys:
        argKeys[x] = x
    for k in argAssocs:
        for assoc in argAssocs[k]:
            argKeys[assoc] = k
    return strTypes,numTypes,listTypes,list2Types,argKeys

def getQuestKeys():
    argAssocs = {'xp': ['xp reward', 'exp', 'exp reward'], 'unlockedBy': ['unlocked by', 'previous quest'],
                 'custsNeeded': ['customers', 'custs', 'customers needed', 'customers required', 'custs needed',
                                 'custs requierd', 'required custs', 'required customers', 'needed custs',
                                 'needed customers'],
                 'itemsNeeded': ['items', 'items required', 'required items', 'items needed', 'needed items'],
                 'shopLevelReq': ['shop level required', 'shop level', 'level required', 'level', 'unlocked at'],
                 'introText': ['intro'], 'outroText': ['outro'], 'time': ['duration']}
    baseKeys = ['id', 'name', 'xp', 'picLink', 'reward', 'unlockedBy', 'custsNeeded', 'itemsNeeded', 'shopLevelReq',
                'introText', 'time', 'outroText']
    numTypes = ['id', 'xp', 'shopLevelReq', 'time']
    listTypes = ['reward', 'custsNeeded', 'itemsNeeded']
    list2Types = []
    strTypes = list(set(numTypes + listTypes + list2Types) ^ set(baseKeys))
    argKeys = {}
    for x in baseKeys:
        argKeys[x] = x
    for k in argAssocs:
        for assoc in argAssocs[k]:
            argKeys[assoc] = k
    return argKeys, numTypes, listTypes, list2Types,argKeys

def getHuntKeys():
    argAssocs = {'comValue': ['common loot', 'common loot req', 'common loot requirement', 'common'],
                 'minLvl': ['min level', 'minimum level', 'meaningless', 'super useless', 'why even'],
                 'description': ['descr', 'text'], 'maxLvl': ['max level', 'xp cutoff', 'xp cutoff level'],
                 'time': ['duration'], 'loots': ['rewards'], 'xpPerLoot': ['xp', 'xp reward', 'xp per loot'],
                 'shopLvlReq': ['level', 'shop level', 'shop level req', 'shop level required']}
    baseKeys = ['comValue', 'minLvl', 'description', 'maxLvl', 'time', 'name', 'loots', 'id', 'picLink', 'xpPerLoot',
                'shopLvlReq']
    numTypes = ['comValue', 'minLvl', 'maxLvl', 'time', 'id', 'xpPerLoot', 'shopeLvlReq']
    listTypes = []
    list2Types = ['loots']
    strTypes = list(set(numTypes + listTypes + list2Types) ^ set(baseKeys))
    argKeys = {}
    for x in baseKeys:
        argKeys[x] = x
    for k in argAssocs:
        for assoc in argAssocs[k]:
            argKeys[assoc] = k
    return argKeys, numTypes, listTypes, list2Types,argKeys

def getWorkerKeys():
    argAssocs = {'couponCost': ['coupons', 'coupons to hire'], 'goldCost': ['gold', 'cost', 'price', 'gold to hire'],
                 'shopLevelReq': ['shop level', 'level', 'level req', 'level requirement', 'shop level requirement']}
    baseKeys = ['couponCost', 'name', 'id', 'goldCost', 'shopLevelReq']
    numTypes = ['couponCost', 'id', 'goldCost', 'shopLevelReq']
    listTypes = []
    list2Types = []
    strTypes = list(set(numTypes + listTypes + list2Types) ^ set(baseKeys))
    argKeys = {}
    for x in baseKeys:
        argKeys[x] = x
    for k in argAssocs:
        for assoc in argAssocs[k]:
            argKeys[assoc] = k
    return argKeys, numTypes, listTypes, list2Types,argKeys

def getAchievementKeys():
    argAssocs = {'requirement': ['criteria', 'req']}
    baseKeys = ['name', 'requirement', 'requrement', 'reward']
    numTypes = []
    listTypes = ['reward']
    list2Types = []
    strTypes = list(set(numTypes + listTypes + list2Types) ^ set(baseKeys))
    argKeys = {}
    for x in baseKeys:
        argKeys[x] = x
    for k in argAssocs:
        for assoc in argAssocs[k]:
            argKeys[assoc] = k
    return argKeys, numTypes, listTypes, list2Types,argKeys

def getClassKeys():
    argAssocs = {'klashItems': ['can use', 'can equip', 'equipable', 'klash'], 'description': ['descr', 'text']}
    baseKeys = ['klashItems', 'name', 'id', 'fullPic', 'description', 'icon']
    numTypes = ['id']
    listTypes = ['klashItems']
    list2Types = []
    strTypes = list(set(numTypes + listTypes + list2Types) ^ set(baseKeys))
    argKeys = {}
    for x in baseKeys:
        argKeys[x] = x
    for k in argAssocs:
        for assoc in argAssocs[k]:
            argKeys[assoc] = k
    return argKeys, numTypes, listTypes, list2Types,argKeys

def finder(testList, section, searchMode, searchData):
    foundStuff = []
    for i in searchData:
        ors = False
        ands = True
        for chk in testList:
            test = chk[0]
            if test(i):
                ors = True
            else:
                if searchMode == 'and':
                    ands = False
        if ors and ands:
            foundStuff.append(i)
    return foundStuff

def qParser(q, keys, pref='-'):
    cmpDict = {'eq': '==', 'not': '!=', 'over': '>', 'above': '>', 'greater': '>',
               'under': '<', 'below': '<', 'less': '<', 'least': '>=', 'most': '<=', 'between': 'range'}
    ignoredTerms = {'at', 'between', 'than', 'and'}
    criteria = []
    print(q, 'q')
    for x in (' '.join(q).split(', ')):
        print(x, 'x')
        y = x.split(': ')
        key = y.pop(0)
        print(y, 'y')
        y = y[0].split(' ')
        if key in keys:
            key = keys[key]
        criteria.append('-'+key)
        a = 'items -search nfBuilds buildings +level > 5'
        chkType = 0
        if key == 'search':
            chkType = key
            criteria.append(y.pop(0))
            criteria.append(y.pop(0))
        for i in range(len(y)):
            if y[i] in cmpDict or y[i] in cmpDict.values():
                chkType = y[i]
            if y[i] in cmpDict:
                criteria.append(cmpDict[y[i]])
            elif y[i] not in ignoredTerms:
                if not chkType and ('*' not in y[i]):
                    criteria.append('==')
                    chkType = '=='
                criteria.append(y[i])
    print(criteria, 'criteria')
    return criteria

def wikiSearchV2(qs, show=True, outFile=dummyFile()):
    fxnDict = {'items': getItemKeys, 'customers': getCustomerKeys, 'improvements': getImprovementKeys,
               'modules': getModuleKeys, 'workers': getWorkerKeys, 'achievements': getAchievementKeys,
               'character_classes': getClassKeys, 'hunts': getHuntKeys, 'quests': getQuestKeys}
    sectionDict = {'quests': 'hunts', 'dungeon quests': 'hunts', 'event quests': 'quests', 'buildings': 'improvements',
                   'recipe unlocks': 'recipe_unlocks', 'class': 'character_classes', 'classes': 'character_classes',
                   'item': 'items', 'customer': 'customers', 'shop stuff': 'modules', 'shop': 'modules'}
    baseSections = snp2lib.prInfo()
    for val in baseSections:
        sectionDict[val] = val

    parseNeeded = False
    if type(qs) is str:
        if ',' in qs:
            parseNeeded = True
        qs = qs.split(' ')
    smode = 'or' if 'or' in qs else 'and'
    while 'or' in qs: qs.remove('or')
    # print('\'searches\'', searches)
    section = qs.pop(0)
    if ',' in section:
        section = ''.join([x for x in section if x != ','])

    if section not in sectionDict:
        print('not a valid section:', section)
        return
    actualSection = sectionDict[section]
    searchData = []
    with open(sep.join([wsFolder, actualSection])) as searchDataFile:
        for line in searchDataFile:
            searchData.append(json.loads(line))

    keys = fxnDict[actualSection]()
    strTypes,numTypes,listTypes,list2Types,keyAssocs = keys
    if parseNeeded:
        criteria = qParser(qs, keyAssocs)
    else:
        criteria = qs
    critParser = argparse.ArgumentParser(description='parse search terms')
    for val in strTypes:
        critParser.add_argument('-'+val, dest='strCrits', nargs='+', action=addWithOpt)
    for val in numTypes:
        critParser.add_argument('-'+val, dest='numCrits', nargs='+', action=addWithOpt)
    for val in listTypes:
        critParser.add_argument('-'+val, dest='lCrits', nargs='+', action=addWithOpt)
    for val in list2Types:
        critParser.add_argument('-'+val, dest='l2Crits', nargs='+', action=addWithOpt)
    critParser.add_argument('-search', dest='searches', nargs='+', action='append')
    s2s = critParser.parse_args(criteria)
    # print('crits', s2s)

    tests = []
    metaParser = argparse.ArgumentParser(description='parse meta criteria')
    metaParser.add_argument('-eq', '-==', nargs='+', action=addWithOpt)
    metaParser.add_argument('-not', '-!=', nargs='+', action=addWithOpt)
    metaParser.add_argument('-over', '->', nargs='+', action=addWithOpt)
    metaParser.add_argument('->=', dest='ge', nargs='+', action=addWithOpt)
    metaParser.add_argument('-under', '-<', nargs='+', action=addWithOpt)
    metaParser.add_argument('-<=', dest='le', nargs='+', action=addWithOpt)
    metaParser.add_argument('-range', nargs='+', action=addWithOpt)
    numParser = metaParser
    metaOptionsText = [x[1:] for x in vars(metaParser)['_option_string_actions'] if x not in ['--help', '-h']]

    if s2s.searches:
        for crit in s2s.searches:
            resultKey = crit.pop(0)
            print(resultKey)
            for i in range(len(crit)):
                if crit[i][0] == '+':
                    crit[i] = '-'+crit[i][1:]
            print(crit)
            subSearchResults = wikiSearchV2(crit)
            names = set([x['name'] for x in subSearchResults])
            print(section, resultKey, names)
            newq = '{} -{} == {} or'.format(section, resultKey, ' '.join(names))
            print(newq)
            searchData = wikiSearchV2(newq)

    if s2s.strCrits:
        for crit in s2s.strCrits:
            # go through each search criteria
            key = crit[0]
            values = crit[1:]

            # list of the argument sets
            strArgs = []
            # ignoreNums is used to skip terms that have been combined when a full name is found, or meta terms
            ignoreNums = []
            for i in range(len(values)):
                if i not in ignoreNums:
                    # val is the term to be checked, in tests such as: if 'dagger' in x[name]
                    # can also be a meta indicator, such as *len
                    val = values[i].lower()

                    # check what val is
                    # if it starts with a *, it's a meta search term, such as len or search (probly, later)
                    if val[0] == '*':
                        # make a list for the meta criteria, since it's used in a different function call
                        metaArgs = []
                        metaCrits = values[i:]
                        # the first argument is the type of check (minus the *)
                        metaType = metaCrits.pop(0)[1:]

                        # with this loop, pop the end of the argument list until it's a number, since in this section
                        # numbers must be for meta arguments, and only numbers are used (so far- ugh, that's gonna be a
                        # pain for searches)
                        while not canIntConvert(metaCrits[-1]):
                            metaCrits.pop()

                        # for any term in the arguments that isn't a number, it's a check type, so put a - in front of
                        # it for the metaParser
                        # oh lord, that's gonna be a pain once I get search working
                        mcwOptions = [y if canIntConvert(y) else '-'+y for y in metaCrits]

                        metaVals = metaParser.parse_args(mcwOptions)

                        # go through each thing in the margs namespace
                        mvs = vars(metaVals)
                        for k in mvs:
                            # for each key
                            if mvs[k]:
                                # if anything was entered in it
                                for s in mvs[k]:
                                    # then for each search type, get the check type from the first item in the list
                                    chkType = s.pop(0)
                                    # if it's not a range check
                                    if chkType != 'range':
                                        # go through each value and get a test function to append to the metaArgs list
                                        for v in s:
                                            metaArgs.append([int(v), chkType, metaType])
                                    else:
                                        # for a range check, the first argument needs to be two numbers, so append it
                                        # like that
                                        s = [int(x) for x in s]
                                        metaArgs.append([[min(s), max(s)], chkType, metaType])
                        # go through each of the test arguments and add a function to tests
                        for arg in metaArgs:
                            tests.append(numTest(key, *arg))
                        # update the ignored numbers to include the meta arguments
                        ignoreNums += range(i, i+len(metaCrits)+1)
                    elif val in ['==', '!=']:
                        # if the val is a check type, set chkType to it
                        # chkType tells the functions what to return if the text is found
                        chkType = val
                    else:
                        # this deals with the actual text values to match
                        # first off, all the possible values will be searched in order to find exact matches, so found
                        # defaults to False
                        found = False
                        for t in searchData:
                            # for each thing in the data that will be searched
                            if not found:
                                # if an exact match hasn't already been found
                                # get the lowercase of the full text
                                chk = t[key].lower()
                                if chk[:len(val)] == val:
                                    # if the value being checked matches the beginning of the text
                                    # wlen = number of words in the text
                                    wlen = len(chk.split())
                                    if wlen-1+i < len(values):
                                        # if the full text is within the length of all the search terms
                                        # meaning it's possible that the next terms could match the full text found
                                        # i.e. if the text is 'fine lance of the wold', that can't match if there's only
                                        # 2 terms left, so don't search (else out of bounds list error)
                                        # get the rest of the search terms that could match, lowercase 'em, and check if
                                        # they match the full text
                                        restOfNames = [y.lower() for y in values[i:i+wlen]]
                                        if chk == ' '.join(restOfNames):
                                            # if there is a full test match, mark found (so you don't keep searching and
                                            # end up with a list that has 'worker' in 20 times), update the ignored
                                            # numbers, and add the name and check type to the string arguments for later
                                            found = True
                                            ignoreNums += range(i, i+wlen)
                                            strArgs.append([' '.join(restOfNames), chkType])
                        if not found:
                            # if a full text match isn't found, add the text as a single word to the string arguments
                            strArgs.append([val, chkType])
            # here, add the calls to get test functions and append them to tests
            for strTest in strArgs:
                tests.append(textTest(key, *strTest))

    if s2s.numCrits:
        for crit in s2s.numCrits:
            # go through each search criteria
            key = crit[0]
            values = crit[1:]
            numArgs = []
            numVals = numParser.parse_args([x if canIntConvert(x) else '-'+x for x in values])
            # print(numVals)
            nvs = vars(numVals)
            for k in nvs:
                if nvs[k]:
                    for s in nvs[k]:
                        chkType = s.pop(0)
                        if chkType != 'range':
                            for v in s:
                                numArgs.append([int(v), chkType])
                        else:
                            s = [int(x) for x in s]
                            numArgs.append([[min(s), max(s)], chkType])
            for numTst in numArgs:
                tests.append(numTest(key, *numTst))

    if s2s.lCrits:
        for crit in s2s.lCrits:
            # go through each search criteria
            key = crit[0]
            values = crit[1:]
            listArgs = []
            ignoreNums = []
            for i in range(len(values)):
                if i not in ignoreNums:
                    val = values[i].lower()
                    if val[0] == '*':
                        metaArgs = []
                        metaCrits = values[i:]
                        metaType = metaCrits.pop(0)[1:]
                        while not canIntConvert(metaCrits[-1]):
                            metaCrits.pop()
                        mcwOptions = [y if canIntConvert(y) else '-'+y for y in metaCrits]
                        metaVals = metaParser.parse_args(mcwOptions)
                        mvs = vars(metaVals)
                        for k in mvs:
                            if mvs[k]:
                                for s in mvs[k]:
                                    chkType = s.pop(0)
                                    if chkType != 'range':
                                        for v in s:
                                            metaArgs.append([int(v), chkType, metaType])
                                    else:
                                        s = [int(x) for x in s]
                                        metaArgs.append([[min(s), max(s)], chkType, metaType])
                        for arg in metaArgs:
                            tests.append(numTest(key, *arg))
                        ignoreNums += range(i, i+len(metaCrits)+1)
                    elif val in ['==', '!=']:
                        chkType = val
                    else:
                        found = False
                        for t in searchData:
                            if not found:
                                chkLst = t[key]
                                if type(chkLst) is list:
                                    for chk in chkLst:
                                        if type(chk) == type(val):
                                            chk = chk.lower()
                                            if chk[:len(val)] == val:
                                                wlen = len(chk.split())
                                                if wlen-1+i < len(values):
                                                    restOfNames = [y.lower() for y in values[i:i+wlen]]
                                                    if chk == ' '.join(restOfNames):
                                                        found = True
                                                        ignoreNums += range(i, i+wlen)
                                                        listArgs.append([' '.join(restOfNames), chkType])
                        if not found:
                            listArgs.append([val, chkType])
            for lTest in listArgs:
                tests.append(listTest(key, *lTest))

    if s2s.l2Crits:
        for crit in s2s.l2Crits:
            # go through each search criteria
            key = crit[0]
            values = crit[1:]
            list2Args = []
            ignoreNums = []
            for i in range(len(values)):
                if i not in ignoreNums:
                    val = values[i].lower()
                    if val[0] == '*':
                        metaArgs = []
                        metaCrits = values[i:]
                        metaType = metaCrits.pop(0)[1:]
                        metaLen = 0
                        for x in metaCrits:
                            if x in metaOptionsText or canIntConvert(x):
                                metaLen += 1
                            else:
                                break
                        metaCrits = metaCrits[:metaLen]
                        print(metaCrits[:metaLen])
                        while not canIntConvert(metaCrits[-1]):
                            metaCrits.pop()
                        print(metaCrits, 'mc final')
                        mcwOptions = [y if canIntConvert(y) else '-'+y for y in metaCrits]
                        metaVals = metaParser.parse_args(mcwOptions)
                        mvs = vars(metaVals)
                        for k in mvs:
                            if mvs[k]:
                                for s in mvs[k]:
                                    chkType = s.pop(0)
                                    if chkType != 'range':
                                        for v in s:
                                            metaArgs.append([int(v), chkType, metaType])
                                    else:
                                        s = [int(x) for x in s]
                                        metaArgs.append([[min(s), max(s)], chkType, metaType])
                        for arg in metaArgs:
                            tests.append(numTest(key, *arg))
                        ignoreNums += range(i, i+len(metaCrits)+1)
                    elif val in ['==', '!=']:
                        chkType = val
                    else:
                        found = False
                        for t in searchData:
                            if not found:
                                chkLst = t[key]
                                if type(chkLst) is list:
                                    for chkLst2 in chkLst:
                                        if type(chkLst2) is list:
                                            for chk in chkLst2:
                                                if canIntConvert(val):
                                                    val = int(val)
                                                if type(chk) == type(val):
                                                    if type(val) == str:
                                                        chk = chk.lower()
                                                        if val.lower() == 'iron':
                                                            print('{}, {}, {}, {}'.format(val, chk, values[i:], 'derp'))
                                                        if chk[:len(val)] == val:
                                                            wlen = len(chk.split())
                                                            if wlen-1+i < len(values):
                                                                restOfNames = [y.lower() for y in values[i:i+wlen]]
                                                                if chk == ' '.join(restOfNames):
                                                                    found = True
                                                                    ignoreNums += range(i, i+wlen)
                                                                    list2Args.append([' '.join(restOfNames), chkType])
                                                    elif i+1 < len(values):
                                                        for c in chkLst2:
                                                            if type(c) is str:
                                                                if values[i+1].lower() in c.lower():
                                                                    found = True
                                                                    ignoreNums += range(i, i+2)
                                                                    list2Args.append([[val, values[i+1]], chkType])
                        if not found:
                            list2Args.append([val, chkType])
            for l2test in list2Args:
                tests.append(list2Test(key, *l2test))

    for x in tests: print(x)
    if len(tests):
        foundStuff = []
        for i in searchData:
            ors = False
            ands = True
            for chk in tests:
                test = chk[0]
                if test(i):
                    ors = True
                else:
                    if smode == 'and':
                        ands = False
            if ors and ands:
                foundStuff.append(i)
        return foundStuff
    else:
        return searchData

testDict = {'==':eq, '!=':ne, '<':lt, '<=':le, '>':gt, '>=':ge, 'range':within, 'noth':nothing}

if __name__ == '__main__':
    # q = 'items, worker: armorer, price: between 50000 and 600000, level: over 10, ingredients: *len over 3'
    # q = 'items, nfBuilds: *search , level: over 15'
    # q = 'items, worker: armorer, uses: mithril, rrare: no, uses: not crystal'
    # q = 'customers, buys: bows, max level: over 16'
    # q = 'customers, klash: shields, max level: at least 18'
    # a = wikiSearch(q)
    # print(q)
    # print(sys.argv)
    # sys.argv += ['4', '23', '--sum']
    # print(sys.argv)
    # q = 'items -level between 2 and 5 -nfBuilds +derp over 2 +herp seven -value over 5000 -ingredients herp derp -name enraging blade'
    # q = 'items -madeBy leatherworker'

    # q = 'items -name *len != 3 range 7 2 < 8 != great == fine Lance of the wolf white != knife -level over 2 -madeBy derp *len > 5'
    # q = 'items -name != great knife dagger robe hat blade rage bow *len == 5 or 7'
    # q = 'items -name == great or dagger'
    # q = 'items -level range 7 6 -value range 1000 100'
    # q = 'items -name *len range 5 15 -level range 7 6 -value range 8000 400 -craftTime == very short'
    # q = 'items -level range 7 6 -value range 8000 400 range 299 800 > 233'
    # q = 'items -nfQuests == phantom shield derp -madeOn == table anvil luxurious'
    # q = 'items -ingredients *len range 3 5 != mithril lumps == gems death 2 iron 3 leather'
    # q = 'items -ingredients *len3 > 15'
    # q = 'items -level > 0 -search nfBuilds buildings +level > 5 -nfBuilds > 5'
    # q = 'items -search nfBuilds buildings +level > 5'
    # q = 'items -ingredients == 3'
    # q = 'items -level > 0 -search ingredients items +level > 15'
    # q = 'items -level == 21 -type == armor'
    # q = 'items, level: 21, type: armor'
    # q = 'items, level: over 0'
    # q = 'items, uses: *len between 3 and 5 not mithril lumps death eq gems'
    q = 'items, uses: not gems crystal eq 3 mithril, worker: jeweler, rrare: no'
    # q1 = 'items, uses: *len between 3 and 5 not mithril lumps eq gems'
    # q = 'classes -name knight'
    print(q)
    a = wikiSearchV2(q)
    # b = wikiSearchV2(q1)
    # for x in a: print(x['name'], (x))
    anames = (([x['name'] for x in a]))
    # bnames = (([x['name'] for x in b]))
    # print(set(anames)^set(bnames))
    for x in a:
        print(x['name'], x['ingredients'])
    print(len(a))
