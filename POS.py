from collections import defaultdict, Counter
#import numpy as np
import sys
#import re

class solution(object):
    def __init__(self):
        self.word = set() # word set
        self.states = set() # tag set
        self.initial_prob = Counter() # length = tag list
        self.trans_prob = defaultdict(Counter) # length = tag_list * tag_list
        self.emit_prob = defaultdict(Counter) # length = tag_list * {}
        self.frequency = defaultdict(Counter) # word: tag: frequency
        self.res = []
        self.total_tag_count = 0
        self.punctuations = ['.', ',', '?', '!', '``', "''"]

    def viterbi(self, obs):
        # for add one smooth:
        # initial_prob: P(tag) = 1 / self.tag_count
        # trans_prob: P(tag1 | tag2) = 1 / self.tag_count
        # emit_prob: P(word | tag) = 1 / self.word_count
        ini_p = 1.0 / self.tag_count
        tra_p = 1.0 / self.tag_count
        emi_p = 1.0 / self.word_count
        V = [{}]
        for st in self.states:
            V[0][st] = {"prob": self.initial_prob.get(st, ini_p) * self.emit_prob[st].get(obs[0], emi_p), "prev": None}

        for t in range(1, len(obs)):
            V.append({})
            for st in self.states:
                max_tr_prob = max(V[t - 1][prev_st]["prob"] * self.trans_prob.get(prev_st, {st: tra_p}).get(st, tra_p) for prev_st in self.states)
                for prev_st in self.states:
                    if V[t - 1][prev_st]["prob"] * self.trans_prob[prev_st].get(st, tra_p) == max_tr_prob:
                        max_prob = max_tr_prob * self.emit_prob[st].get(obs[t], emi_p)
                        V[t][st] = {"prob": max_prob, "prev": prev_st}
                        break
        opt = []
        previous = "BOS"
        #if obs[-1] in self.punctuations:
            #opt.append(obs[-1])
        #else:
        max_prob = max(value["prob"] for value in V[-1].values())
        for st, data in V[-1].items():
            if data["prob"] == max_prob:
                opt.append(st)
                previous = st
                break
        for t in range(len(V) - 2, -1, -1):
            #if obs[t] in self.punctuations:
                #opt.insert(0, obs[t])
            #else:
            opt.insert(0, V[t + 1][previous]["prev"])
            previous = V[t + 1][previous]["prev"]
        self.res += opt
        return opt

    def test(self, fileName):
        golden = []
        most_freq = []
        with open(fileName, 'r') as testFile:
            for line in testFile.readlines():
                line = line.strip().split(" ")
                obs = []
                #obs.append("BOS")
                result = []
                for entry in line:
                    entry = entry.replace("\/", "")
                    entry = entry.replace("*", "")
                    if entry.find('/') == -1:
                        word = entry[:-2]
                        tag = entry[-2:]
                    elif entry.count("/") == 2:
                        if "-" in entry:
                            e1, entry = entry.split("-")
                        elif "&" in entry:
                            e1, entry = entry.split("&")
                        else:
                            continue
                        w, t = e1.split("/")
                        obs.append(w)
                        result.append(t)
                        word, tag = entry.split("/")
                    else:
                        word, tag = entry.split("/")
                    obs.append(word)
                    result.append(tag)
                    if word in self.frequency:
                        most_freq.append(self.frequency[word].most_common(1)[0][0])
                    else:
                        most_freq.append(self.initial_prob.most_common(1)[0][0])
                opt = self.viterbi(obs)
                golden += result
                #print "***********************************************"
                #print obs
                #print result
                #print opt
        wrong_viterbi_pair = Counter()
        count_viterbi = 0
        count_freq = 0
        for i in range(len(self.res)):
            if self.res[i] == golden[i]:
                count_viterbi += 1
            else:
                wrong_viterbi_pair[(self.res[i], golden[i])] += 1
            if most_freq[i] == golden[i]:
                count_freq += 1
        #print "golden result: ", golden
        #print "viterb result: ", self.res
        #print "freque result: ", most_freq
        #print (wrong_viterbi_pair)
        print ("Accuracy of viterbi algorithm is ", count_viterbi * 1.0 / len(self.res))
        print ("Accuracy of baseline frequency is ", count_freq * 1.0 / len(self.res))


    def count(self, fileName, smooth_method):
        self.word.add("BOS")
        self.states.add("BOS")
        with open(fileName, 'r') as inputFile:
            for line in inputFile.readlines():
                line = line.strip().split(",")
                pre_tag = "BOS"
                for entry in line:
                    entry = entry.replace("\/", "")
                    entry = entry.replace("*","")
                    if entry.find('/') == -1:
                        word = entry[:-2]
                        tag = entry[-2:]
                    elif entry.count("/") == 2:
                        if "-" in entry:
                            e1, entry = entry.split("-")
                        elif "&" in entry:
                            e1, entry = entry.split("&")
                        else:
                            continue
                        w, t = e1.split("/")
                        self.word.add(w)
                        self.states.add(t)
                        self.initial_prob[t] += 1
                        self.trans_prob[pre_tag][t] += 1
                        self.emit_prob[t][w] += 1
                        self.frequency[w][t] += 1
                        pre_tag = t
                        self.total_tag_count += 1
                        word, tag = entry.split("/")
                    else:
                        word, tag = entry.split("/")
                    self.word.add(word)
                    self.states.add(tag)
                    self.initial_prob[tag] += 1
                    self.trans_prob[pre_tag][tag] += 1
                    self.emit_prob[tag][word] += 1
                    self.frequency[word][tag] += 1
                    pre_tag = tag
                    self.total_tag_count += 1

        self.tag_count = len(self.states)
        self.word_count = len(self.word)

        for k in self.initial_prob.keys():
            if smooth_method == "add_one":
                self.initial_prob[k] = (self.initial_prob[k] + 1) * 1.0 /  (self.total_tag_count + self.tag_count)
            else:
                self.initial_prob[k] /= self.total_tag_count * 1.0

        for k in self.trans_prob.keys():
            di = self.trans_prob[k]
            s = sum(di.values())
            for key in di.keys():
                if smooth_method == "add_one":
                    di[key] = (di[key] + 1) * 1.0 / (s + len(di))
                else:
                    di[key] /= s * 1.0
            self.trans_prob[k] = di

        for k in self.emit_prob.keys():
            di = self.emit_prob[k]
            s = sum(di.values())
            for key in di.keys():
                if smooth_method == "add_one":
                    di[key] = (di[key] + 1) * 1.0 / (s + len(di))
                else:
                    di[key] /= s * 1.0
            self.emit_prob[k] = di
        #print self.emit_prob
        self.emit_prob["BOS"] = {"BOS": 1.0}
if __name__ == "__main__":
    trainFile = sys.argv[POS.train.large]
    testFile = sys.argv[POS.test]
    s = solution()
    print ("start train...")
    s.count(trainFile, "add_one")
    print ("start test...")
    s.test(testFile)
