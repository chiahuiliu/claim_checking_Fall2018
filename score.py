#Adapted from https://github.com/FakeNewsChallenge/fnc-1/blob/master/scorer.py
#Original credit - @bgalbraith
from sklearn.metrics import f1_score

def score_submission(gold_labels, test_labels, article_stance):
    score = 0.0
    if article_stance:
        LABELS = ['observing', 'for', 'against', 'ignoring']
        cm = [[0, 0, 0, 0],
              [0, 0, 0, 0],
              [0, 0, 0, 0],
              [0, 0, 0, 0]]
        for i, (g, t) in enumerate(zip(gold_labels, test_labels)):
            g_stance, t_stance = g, t
            if g_stance == t_stance:
                score += 0.25
            cm[LABELS.index(g_stance)][LABELS.index(t_stance)] += 1
    else:
        LABELS = ['unknown', 'false', 'true']
        RELATED = LABELS[0:3]
        cm = [[0, 0, 0],
              [0, 0, 0],
              [0, 0, 0]]
        for i, (g, t) in enumerate(zip(gold_labels, test_labels)):
            g_stance, t_stance = g, t
            if g_stance == t_stance:
                score += 0.25
            cm[LABELS.index(g_stance)][LABELS.index(t_stance)] += 1
            #cm[g_stance][t_stance] += 1

    return score, cm


def print_confusion_matrix(cm, article_stance):
    lines = []
    if article_stance:
        LABELS = ['observing', 'for', 'against', 'ignoring']
        header = "|{:^11}|{:^11}|{:^11}|{:^11}|".format('', *LABELS)
        line_len = len(header)
        lines.append("-"*line_len)
        lines.append(header)
        lines.append("-"*line_len)

        hit = 0
        total = 0
        for i, row in enumerate(cm):
            hit += row[i]
            total += sum(row)
            lines.append("|{:^11}|{:^11}|{:^11}|{:^11}|".format(LABELS[i],
                                                                       *row))
            lines.append("-"*line_len)
        print('\n'.join(lines))
    else:
        LABELS = ['unknown', 'false', 'true']
        header = "|{:^11}|{:^11}|{:^11}|{:^11}|".format('', *LABELS)
        line_len = len(header)
        lines.append("-"*line_len)
        lines.append(header)
        lines.append("-"*line_len)

        hit = 0
        total = 0
        for i, row in enumerate(cm):
            hit += row[i]
            total += sum(row)
            lines.append("|{:^11}|{:^11}|{:^11}|{:^11}|".format(LABELS[i],
                                                                       *row))
            lines.append("-"*line_len)
        print('\n'.join(lines))


def report_score(actual,predicted, article_stance):
    score,cm = score_submission(actual,predicted, article_stance)
    best_score, _ = score_submission(actual,actual, article_stance)
    print("Confusion Matrix")
    print_confusion_matrix(cm, article_stance)
    print("official score")
    print("Score: " +str(score) + " out of " + str(best_score) + "\t("+str(score*100/best_score) + "%)")
    return score*100/best_score


 #   Copyright 2017 Cisco Systems, Inc.
 #
 #   Licensed under the Apache License, Version 2.0 (the "License");
 #   you may not use this file except in compliance with the License.
 #   You may obtain a copy of the License at
 #
 #     http://www.apache.org/licenses/LICENSE-2.0
 #
 #   Unless required by applicable law or agreed to in writing, software
 #   distributed under the License is distributed on an "AS IS" BASIS,
 #   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 #   See the License for the specific language governing permissions and
 #   limitations under the License.
