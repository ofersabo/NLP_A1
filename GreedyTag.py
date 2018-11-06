import numpy as np
import sys
# input_file =
# output_file =
# Q_file =
# E_file =
lambda_interpolation = [0.8,0.15,0.05]
all_states = set()
# word_to_state_probability = {}

from collections import Counter
unigram = {}
bigram = {}
trigram = {}
emission = {}
deno = 'denominator'


def create_denominator():
    for d in [trigram,bigram,emission]:
        for couple in d:
            all_value = d[couple].values()
            sum_all = sum(all_value)
            d[couple][deno] = sum_all

    all_value = unigram.values()
    sum_all = sum(all_value)
    unigram[deno] = sum_all


def add_to_emission(all_parts):
    w = all_parts[0]
    if not w in emission:
        emission[w] = {}

    emission[w][all_parts[1]] = int(all_parts[2])

    all_states.add(all_parts[1])

def create_emission(e_file):
    for line in open(e_file):
        all_parts = line.strip().replace("\t", " ").split(" ")
        add_to_emission(all_parts)



def add_to_trigram(all_parts):
    pre_tuple = (all_parts[0],all_parts[1])
    if not  pre_tuple in trigram:
        trigram[pre_tuple] = {}

    trigram[pre_tuple][all_parts[2]] = int(all_parts[3])


def add_to_bigram(all_parts):
    pre_single = all_parts[0]
    if not pre_single in bigram:
        bigram[pre_single] = {}

    bigram[pre_single][all_parts[1]] = int(all_parts[2])

def add_to_unigram(all_parts):
    unigram[all_parts[0]] = int(all_parts[1])


def create_transition(q_file):
    for line in open(q_file):
        all_parts = line.strip().replace("\t", " ").split(" ")

        if len(all_parts) == 4:
            add_to_trigram(all_parts)
        elif len(all_parts) == 3:
            add_to_bigram(all_parts)
        elif len(all_parts) == 2:
            add_to_unigram(all_parts)
        else:
            print ("ERROR")
            exit()


def handle_no_tag_per_word():
    return 1e-5


def handle_unknown_word():
    return 1


def emision_probability(word,tag):
    if not word in emission:
        return handle_unknown_word()
    elif not tag in emission[word]:
        return handle_no_tag_per_word()

    return float(emission[word][tag] / float(emission[word][deno]))


def get_three_bi_uni_gram(tag, prev_tag, prev_prev_tag):
    try:
        tri = float(trigram[(prev_prev_tag,prev_tag)][tag] / float(trigram[(prev_prev_tag,prev_tag)][deno]))
    except KeyError:
        tri = 1e-5
    try:
        bi  = float(bigram[prev_tag][tag] / float(bigram[prev_tag][deno]))
    except KeyError:
        bi  = 1e-5
    try:
        uni = float(unigram[tag]/ float(unigram[deno]))
    except KeyError:
        uni = 1e-5
    return [tri,bi,uni]


def getScore(word, tag, prev_tag, prev_prev_tag):
    e_proba = np.log(emision_probability(word,tag))
    q_proba = get_three_bi_uni_gram(tag, prev_tag, prev_prev_tag)
    q_proba = np.sum(np.array(q_proba) * np.array(lambda_interpolation))
    q_proba = np.log(q_proba)
    return e_proba + q_proba


def write_to_output_file(output_file_name,text):
    f = open(output_file_name, "w")
    for sen in text:
        f.write(sen)


def find_answer(input_file_name,output_file_name):
    text = []
    f = open(input_file_name)
    for line in f:

        result_line = ""
        words = line.strip().split(" ")
        prev_prev_tag = "START"
        prev_tag = "START"
        for i,word in enumerate(words):
            max_probability = 1
            for tag in all_states:
                prob = getScore(word, tag, prev_tag, prev_prev_tag)
                if ( prob > max_probability or max_probability  == 1):
                    max_probability = prob
                    state = tag

            prev_prev_tag = prev_tag
            prev_tag = state
            result_line+= word + "/" + str(state) + " "
        result_line += "\n"
        text.append(result_line)
    text[-1] = text[-1][:-1]
    write_to_output_file(output_file_name,text)

def evaulate_result(output_file_name):
    text = []
    for i, line in enumerate(open(output_file_name)):
        text.append(line.strip())
    good = 0.0
    bad  = 0.0
    from MLETrain import extract_pos
    for i,correct_line in enumerate(open("ass1-tagger-test")):
        correct = extract_pos(correct_line)
        my_pos  = extract_pos(text[i])
        assert len(my_pos)== len(correct)
        how_many_corrct = 0.0
        for j in range(len(my_pos)):
            if (correct[j] == my_pos[j] ):
                how_many_corrct += 1
        good += how_many_corrct
        bad += len(my_pos) - how_many_corrct

    print ("good")
    print (good)
    print ("bad")
    print (bad)

    print ("good/(bad+good)")
    print (good/(bad+good))



def main():
# input_file_name q_mle_filename e_mle_filename output_file_name extra_file_name
    input_file_name  = sys.argv[1] if len(sys.argv) > 1 else "ass1-tagger-test-input"
    q_mle_filename   = sys.argv[2] if len(sys.argv) > 2 else "q.mle"
    e_mle_filename   = sys.argv[3] if len(sys.argv) > 3 else "e.mle"
    output_file_name = sys.argv[4] if len(sys.argv) > 4 else "outpot.txt"
    extra_file_name  = sys.argv[5] if len(sys.argv) > 5 else "extra.txt"

    create_transition(q_mle_filename)
    create_emission(e_mle_filename)
    create_denominator()
    find_answer(input_file_name,output_file_name)
    print ("Evaluate")
    evaulate_result(output_file_name)


if __name__ == '__main__':
    main()


