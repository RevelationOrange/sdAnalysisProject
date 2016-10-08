import json


'''
get an end of day packet from the game by having your network monitor open (f12 in firefox and I think chrome too) while
you finish a day and save it in a file names EOD.txt in the same folder as this program
the end of day packet is a client_action that's about 240 kb
also, it's probly best to put this stuff in its own folder, just for organization
'''

def main():
    def getGrade(perc):
        if perc > 50.0:
            grade = 'A++'
        elif perc > 40.0:
            grade = 'A+'
        elif perc > 30.0:
            grade = 'A'
        elif perc > 20.0:
            grade = 'B'
        elif perc > 15.0:
            grade = 'C'
        elif perc > 10.0:
            grade = 'D'
        elif perc > 5.0:
            grade = 'E'
        else:
            grade = 'F'
        return grade
    inFilename = 'EOD.txt'
    outFilename0 = 'cityGrades.txt'
    outFilename1 = 'detailedStats.txt'
    with open(inFilename) as inFile:
        for line in inFile:
            p = line[:-1]
    packet = json.loads(p)
    detailedHeaders = ['name', 'total_item_gold_value_contributions', 'total_gold_contributions',
                       'total_special_for_gold_contributions', 'total_sales', 'total_special_for_item_contributions']
    mdhlen = max([len(i) for i in detailedHeaders])
    outReplStr = '{:<17} {:<%d,} {:<%d,} {:<%d,} {:<%d,} {}\n' % (mdhlen, mdhlen, mdhlen, mdhlen)
    outReplStr0 = '{:<17} {:<%d} {:<%d} {:<%d} {:<%d} {}\n' % (mdhlen, mdhlen, mdhlen, mdhlen)
    for e in (packet['result']['events']):
        if 'city' in e:
            with open(outFilename0, 'w') as outFile, open(outFilename1, 'w') as detailedOutFile:
                detailedOutFile.write(outReplStr0.format(*detailedHeaders))
                for m in (e['city']['members']):
                    if 'name' in m:
                        itemVal = m['total_item_gold_value_contributions']# + m['total_special_for_item_contributions']
                        goldVal = m['total_gold_contributions'] + m['total_special_for_gold_contributions']
                        totalSales = m['total_sales']
                        name = m['name']
                        donationPer = 100.*(itemVal*1.5 + goldVal)/float(totalSales)
                        print('{:<17} {:<19} {}'.format(name, donationPer, getGrade(donationPer)))
                        outFile.write('{:<17} {:<19} {}\n'.format(name, donationPer, getGrade(donationPer)))
                        detailedOutFile.write(outReplStr.format(*[m[i] for i in detailedHeaders]))

if __name__ == '__main__':
    main()
