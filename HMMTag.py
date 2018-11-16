import numpy as np
import sys
import time
from utilities import *
lambda_interpolation = [0.8,0.15,0.05]
all_states = set()
special_tags = set([".","$","``",'(',')',"''",',',':','#','``'])
tags_to_go_over = all_states - special_tags
# word_to_state_probability = {}
end_early = -900
skip_start = 600
from collections import Counter
unigram = {}
bigram = {}
trigram = {}
emission = {}
rare_words_emission = {}
deno = 'denominator'
should_be_trusted = 7

def create_emission_for_rare_words():
    for e in emission:
        number_of_appearnces  = sum(emission[e].values())
        if number_of_appearnces < 5 and not check_if_number(e):
            for t in emission[e].keys():
                if not rare_words_emission.has_key(t):
                    rare_words_emission[t] = 0

                rare_words_emission[t] += 1

    print rare_words_emission

def create_denominator():
    global tags_to_go_over
    tags_to_go_over = all_states - special_tags
    for d in [trigram,bigram,emission]:
        for couple in d:
            all_value = d[couple].values()
            sum_all = sum(all_value)
            d[couple][deno] = sum_all

    all_value = unigram.values()
    sum_all = sum(all_value)
    unigram[deno] = sum_all
    all_value = rare_words_emission.values()
    rare_words_emission[deno] = sum(all_value)

def add_to_emission(all_parts):
    w = all_parts[0]
    if not w in emission:
        emission[w] = {}

    emission[w][all_parts[1]] = int(all_parts[2])

    all_states.add(all_parts[1])

def create_emission(e_file):
    for line in open(e_file):
        all_parts = line.strip().replace("\t", " ").split(" ")
        if len(all_parts) < 3:
            print
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


def handle_no_tag_per_word(word,tag):
    if emission[word][deno] > 4:
        return 1e-36
    else:
        return 1e-5

def probability_by_feature(feature,tag):
    d = (emission[feature][deno])
    if not emission[feature].has_key(tag):
        return 0.01 / d
    n = float(emission[feature][tag])
    return n / d


def handle_unknown_word(word,tag,feature):
    if word.isupper():
        lower_word = word.lower()
        if (emission.has_key(lower_word) and emission[lower_word][deno] > 5):
            if not tag in emission[lower_word]:
                lower_prob = (handle_no_tag_per_word(lower_word, tag))
            else:
                lower_prob = float(emission[lower_word][tag]) / emission[lower_word][deno]

            return lower_prob

    if not rare_words_emission.has_key(tag):
        rare_prob = 1e-10
    else:
        rare_prob = float(rare_words_emission[tag]) / rare_words_emission[deno]

    if feature =="":
        return rare_prob
    else:
        return probability_by_feature(feature,tag)/2 + rare_prob/2


def emision_probability(word,tag):
    feature = find_convetion_type(word)
    if not word in emission:
        return (handle_unknown_word(word,tag,feature),False)

    count = emission[word][deno]

    if not tag in emission[word]:
        return (handle_no_tag_per_word(word,tag), count > should_be_trusted)

    if feature == "":
        return (float(emission[word][tag] / float(emission[word][deno])) , count > should_be_trusted)
    else:
        e_prob = float(emission[word][tag]) / count
        if count < 15:
            f_prob = probability_by_feature(feature,tag)
            return 0.5 * f_prob + 0.5 * e_prob, count > should_be_trusted

        return e_prob, count > should_be_trusted


def get_three_bi_uni_gram(tag, prev_tag, prev_prev_tag):
    if not trigram.has_key((prev_prev_tag,prev_tag)):
        return 1e-5
    try:
        tri = float(trigram[(prev_prev_tag,prev_tag)][tag] / float(trigram[(prev_prev_tag,prev_tag)][deno]))
    except KeyError:
        tri = 1.0/trigram[(prev_prev_tag,prev_tag)][deno]
    if not bigram.has_key(prev_tag):
        return 1e-5
    try:
        bi  = float(bigram[prev_tag][tag] / float(bigram[prev_tag][deno]))
    except KeyError:
        bi  = 1.0/bigram[prev_tag][deno]
    try:
        uni = float(unigram[tag]/ float(unigram[deno]))
    except KeyError:
        uni = 1e-5
    return [tri,bi,uni]


def getScore(word, tag, prev_tag, prev_prev_tag):
    e_proba, trust = emision_probability(word,tag)
    e_proba = np.log(e_proba)
    q_proba = get_three_bi_uni_gram(tag, prev_tag, prev_prev_tag)
    q_proba = np.sum(np.array(q_proba) * np.array(lambda_interpolation))
    q_proba = np.log(q_proba)
    if trust:
        return 0.5 * e_proba + 0.5 * q_proba
    else:
        return 0.2 * e_proba + 0.8 * q_proba


def write_to_output_file(output_file_name,text):
    f = open(output_file_name, "w")
    for sen in text:
        f.write(sen)


def find_max_in_trellis_word(d):
    for i,key in enumerate(d.keys()):
        if i==0:
            max_prob = d[key][1]
            max_tag = key
        elif d[key][1] > max_prob:
            max_prob = d[key][1]
            max_tag = key
    return max_tag


def find_backwars_tags(trellis):
    last_line = trellis[-1]
    tags_list = []
    current_tuple = find_max_in_trellis_word(last_line)
    for back in range(len(trellis)):
        tags_list.insert(0, current_tuple[1])
        prev_prev = trellis[-(1+back)][current_tuple][0]
        current_tuple = (prev_prev, current_tuple[0])


    return tags_list


def synthesize_sentence(words,tags_list):
    result_sentence = ""
    for i,word in enumerate(words):
        result_sentence += word + "/" + str(tags_list[i]) + " "
    result_sentence = result_sentence[:-1]
    result_sentence += "\n"

    return result_sentence


def check_low_emission_number(s):
    if (emission.has_key(s) and len(emission[s]) == 2 and emission[s].values()[0] > 10):
        keys = emission[s].keys()
        for k in keys:
            if k != deno:
                return (True , k)
    return False, None


def insert_into_trellis(trellis, word, tag, prev_tag, prev_prev_tag):
        if len(trellis) <= 1:    # only first word is like that
            trellis[-1][(prev_tag,tag)] = (prev_prev_tag, getScore(word, tag, prev_tag, prev_prev_tag))
            return
        if len(trellis[-2]) == 1:
            prev_tag = trellis[-2].keys()[0][1]
            prev_prev_tag = trellis[-2].keys()[0][0]
            prev_set_score = (trellis[-2][(prev_prev_tag, prev_tag)][1] + getScore(word, tag, prev_tag, prev_prev_tag))
            trellis[-1][(prev_tag, tag)] = (prev_prev_tag, prev_set_score)
            return
        if len(trellis[-2]) <= len(tags_to_go_over):
            prev_tag = trellis[-2].keys()[0][1]
            another_prev_tag = trellis[-2].keys()[-1][1]
            if (prev_tag == another_prev_tag): #pre_tag_is_known
                for j,prev_prev_tag in enumerate(tags_to_go_over):
                    if j == 0:
                        prev_prev_set = prev_prev_tag
                        tup = (prev_prev_tag, prev_tag )
                        pre_score = trellis[-2][tup][1]
                        prev_set_score = ( pre_score + getScore(word, tag, prev_tag, prev_prev_tag))
                    elif ( (trellis[-2][(prev_prev_tag, trellis[-2].keys()[0][1])][1] + getScore(word, tag, prev_tag, prev_prev_tag)) > prev_set_score):
                        prev_prev_set = prev_prev_tag
                        tup = (prev_prev_tag, trellis[-2].keys()[0][1])
                        prev_set_score = (trellis[-2][tup][1] + getScore(word, tag, prev_tag, prev_prev_tag))

                    trellis[-1][(prev_tag, tag)] = (prev_prev_set, prev_set_score)
                return
            else: #prev_prev_tag is known
                prev_prev_tag = trellis[-2].keys()[0][0]
                for prev_tag in tags_to_go_over:
                    prev_set_score = ( trellis[-2][(prev_prev_tag, prev_tag)][1] + getScore(word, tag, prev_tag, prev_prev_tag))
                    trellis[-1][(prev_tag, tag)] = (prev_prev_tag, prev_set_score)
                return
        else:
            for prev_tag in tags_to_go_over:
                for j, prev_prev_tag in enumerate(tags_to_go_over):
                    if j == 0:
                        prev_prev_set = prev_prev_tag
                        prev_set_score = (trellis[-2][(prev_prev_tag, prev_tag)][1] + getScore(word, tag, prev_tag, prev_prev_tag))
                    elif ((trellis[-2][(prev_prev_tag, prev_tag)][1] + getScore(word, tag, prev_tag, prev_prev_tag)) > prev_set_score):
                        prev_prev_set = prev_prev_tag
                        prev_set_score = (trellis[-2][(prev_prev_tag, prev_tag)][1] + getScore(word, tag, prev_tag, prev_prev_tag))

                trellis[-1][(prev_tag, tag)] = (prev_prev_set, prev_set_score)


def is_special_case(trellis,word,i,words, prev_tag,prev_prev_tag):
    case_of_emission, emission_tag = check_low_emission_number(word)
    if case_of_emission:
        insert_into_trellis(trellis, word, emission_tag, prev_tag, prev_prev_tag)
        return True

    if check_if_number(word):
        insert_into_trellis(trellis, word, "CD", prev_tag, prev_prev_tag)
        return True

    if word in special_tags or check_if_number(word):
        correct_tag = word
        insert_into_trellis(trellis,word,correct_tag,prev_tag,prev_prev_tag)
        return True


    return False


def handle_one_backward_is_known(trellis,word):
    key_pre_word = trellis[-2].keys()
    assert len(key_pre_word) == 1
    prev_tag = key_pre_word[0]
    for j,tag in enumerate(tags_to_go_over):
        prev_set_score = ( trellis[-2][prev_tag][1] + getScore(word, tag, prev_tag, trellis[-2][prev_tag][0]))
        trellis[-1][tag] = (prev_tag, prev_set_score)


def viterbi_decoder(words,prev_prev_tag,prev_tag):
    trellis = [{}]
    knwon_one_backwords = False
    if len(words) > 0:
        if not is_special_case(trellis,words[0],0,words,prev_tag,prev_prev_tag):
            for tag in tags_to_go_over:
                insert_into_trellis(trellis,words[0],tag,prev_tag,prev_prev_tag)

    if len(words) > 1:
        trellis.append({})
        if not is_special_case(trellis,words[1],1,words,prev_tag,prev_prev_tag):
            for tag in tags_to_go_over:
                insert_into_trellis(trellis, words[1], tag, prev_tag, prev_prev_tag)

    if len(words) == 2:
        return trellis

    for i,word in enumerate(words[2:]):
        trellis.append({})
        special_case = is_special_case(trellis,word,i+2, words, prev_tag,prev_prev_tag)
        #print "i is %0d word is %s"%(i,word)
        if special_case:
            continue
        else:
            for tag in tags_to_go_over:
                insert_into_trellis(trellis, word, tag, prev_tag, prev_prev_tag)

    return trellis



def find_answer(input_file_name,output_file_name,extra_file_name):
    text = []
    f = open(input_file_name)
    for i,line in enumerate(f):
        #print "line number %0d"%i
        if i < skip_start: continue
        if i%1 == 0:
            print "line number %0d"%i
        words = line.strip().split(" ")
        prev_prev_tag = "START"
        prev_tag = "START"
        trellis = viterbi_decoder(words,prev_prev_tag,prev_tag)
        # t = []
        # for i in trellis:
        #     t.append(str(i)+"\n")
        # write_to_output_file(extra_file_name,t)
        tags_list = find_backwars_tags(trellis)
        text.append(synthesize_sentence(words, tags_list))
        if (end_early + skip_start == i ):
            break
    text[-1] = text[-1][:-1]
    write_to_output_file(output_file_name, text)

def evaulate_result(output_file_name,extra_file_name):
    text = []
    for i, line in enumerate(open(output_file_name)):
        text.append(line.strip())
        print line
    good = 0.0
    bad  = 0.0
    wrong_tags= []
    true_tags = []
    wrong_lines = []
    wrong_words = []
    from MLETrain import extract_pos
    for i,correct_line in enumerate(file("ass1-tagger-test")):
        if i < skip_start: continue
        correct = extract_pos(correct_line)
        my_pos  = extract_pos(text[i-skip_start])
        assert len(my_pos)== len(correct)
        how_many_corrct = 0.0
        for j in range(len(my_pos)):
            if (correct[j] == my_pos[j] ):
                how_many_corrct += 1
            else:
                wrong_tags.append(my_pos[j])
                true_tags.append(correct[j])
                wrong_words.append(text[i-skip_start].split(" ")[j])
        good += how_many_corrct
        bad += len(my_pos) - how_many_corrct
        if len(my_pos) - how_many_corrct > 0:
            wrong_lines.append(text[i-skip_start] + "\n")

        if i  == skip_start + end_early:
            break
    print ("good")
    print (good)
    print ("bad")
    print (bad)

    print ("good/(bad+good)")
    print (good/(bad+good))
    wrong = Counter()
    right = Counter()
    wrong.update(wrong_tags)
    right.update(true_tags)
    uni = Counter()
    uni.update(zip(true_tags,wrong_tags))
    print (zip(true_tags,wrong_tags))
    print ("wrong")
    # print (wrong)
    # print uni.most_common()
    print wrong_words
    write_to_output_file(extra_file_name,wrong_lines)

def main():
# input_file_name q_mle_filename e_mle_filename output_file_name extra_file_name
    input_file_name  = sys.argv[1] if len(sys.argv) > 1 else "ass1-tagger-test-input"
    q_mle_filename   = sys.argv[2] if len(sys.argv) > 2 else "q.mle"
    e_mle_filename   = sys.argv[3] if len(sys.argv) > 3 else "e.mle"
    output_file_name = sys.argv[4] if len(sys.argv) > 4 else "outpot.txt"
    extra_file_name  = sys.argv[5] if len(sys.argv) > 5 else "extra.txt"

    create_transition(q_mle_filename)
    create_emission(e_mle_filename)
    create_emission_for_rare_words()
    create_denominator()
    find_answer(input_file_name,output_file_name,extra_file_name)

    # trellis = []
    # import ast
    # for k,i in enumerate(file(extra_file_name)):
    #     print i
    #     print k
    #     trellis.append(ast.literal_eval(i))
    #     if k == 4: break
    # tags_list = find_backwars_tags(trellis)

    print ("Evaluate")
    evaulate_result(output_file_name,extra_file_name)


if __name__ == '__main__':
    start = time.time()
    main()
    end = time.time()
    print"time is %f"%(end - start)


