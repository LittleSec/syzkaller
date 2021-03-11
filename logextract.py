from datetime import datetime
import re
import sys
import os

# 2021/02/21 23:48:55 VMs 4, executed 11301937, corpus cover 77745, corpus signal 135438, max signal 205594, crashes 254, repro 0
timeRe = r"\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}"
execRe = r"executed \d+"
corpusCovRe = r"corpus cover \d+"
corpusSigRe = r'corpus signal \d+'
maxSigRe = r"max signal \d+"
crashesRe = r"crashes \d+"
logRe = r"{0} +VMs \d+, +{1}.*{2}.*{3}.*{4}.*{5}".format(timeRe, execRe, corpusCovRe, corpusSigRe, maxSigRe, crashesRe)
# 2021/02/21 23:46:55 vm-0: crash: no output from test machine
crashLogPrefixRe = r"{0} vm-\d+: +crash: +".format(timeRe)
crashLogRe = r"{0}.*".format(crashLogPrefixRe)


timePat = re.compile(timeRe)
execPat = re.compile(execRe)
corpusCovPat = re.compile(corpusCovRe)
corpusSigPat = re.compile(corpusSigRe)
maxSigPat = re.compile(maxSigRe)
crashesPat = re.compile(crashesRe)
logPat = re.compile(logRe)
crashLogPrefixPat = re.compile(crashLogPrefixRe)
crashLogPat = re.compile(crashLogRe)


header = ["Time", "executed", "corpus_cov", "corpus_sig", "max_sig", "crashes"]
starttime = None
is1stline = True


def extract1line(line):
    global starttime
    if (logPat.match(line)):
        record = []
        dtstr = timePat.search(line).group()
        if starttime is None:
            starttime = datetime.strptime(dtstr, "%Y/%m/%d %H:%M:%S")
            record.append("0")
        else:
            nowdt = datetime.strptime(dtstr, "%Y/%m/%d %H:%M:%S")
            diffdt = nowdt - starttime
            timeValInSecond = diffdt.total_seconds()
            record.append("{}".format(int(timeValInSecond)))
        for pattern in [execPat, corpusCovPat, corpusSigPat, maxSigPat, crashesPat]:
            matchstr = pattern.search(line).group().strip()
            matchval = matchstr.split(' ')[-1]
            record.append(matchval)
        return record 
    else:
        return None


GenCSV = False
GenCrashInfo = True
IgnLostConnect = True
IgnNoOutput = True
IgnWarning = True
IsRedundant = True


def isCrashLines(line):
    if (crashLogPat.match(line)):
        crashinfo = crashLogPrefixPat.sub("", line).strip()
        if IgnLostConnect and "lost connection to test machine" in crashinfo:
            return None
        if IgnNoOutput and "no output from test machine" in crashinfo:
            return None
        if IgnWarning and crashinfo.startswith("WARNING"):
            return None
        return crashinfo
    else:
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Useage: python3 {0} path/to/log [num]".format(sys.argv[0]))
        exit(1)
    else:
        if len(sys.argv) == 3:
            lineCnt = int(sys.argv[2])
        else:
            lineCnt = -1
        logfilename = sys.argv[1]
        if not os.path.exists(logfilename):
            print("Not such file: {0}".format(logfilename))
            exit(1)
        table = [header]
        crashesinfo = []
        with open(logfilename, mode='r') as fr:
            cnt = 0
            for line in fr.readlines():
                line = line.strip()
                if line == "":
                    continue
                cnt += 1
                if lineCnt > 0 and cnt > lineCnt:
                    continue
                if GenCrashInfo:
                    record = isCrashLines(line)
                    if record is not None:
                        crashesinfo.append(record)
                if GenCSV:
                    record = extract1line(line)
                    if record is not None:
                        table.append(record)
        if GenCrashInfo:
            crashinfofilename = logfilename + ".crashes"
            with open(crashinfofilename, mode='w') as fw:
                if IsRedundant:
                    crashesinfo = set(crashesinfo)
                for record in crashesinfo:
                    fw.write(record + '\n')
        if GenCSV:
            csvfilename = logfilename + ".csv"
            with open(csvfilename, mode='w') as fw:
                for record in table:
                    fw.write(",".join(record) + '\n')