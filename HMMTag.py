import numpy as np
import sys
lambda_interpolation = [0.8,0.15,0.05]
all_states = set()
special_tags = set([".","$","``",'(',')',"''",',',':','#','``'])
tags_to_go_over = all_states - special_tags
# word_to_state_probability = {}

from collections import Counter
unigram = {}
bigram = {}
trigram = {}
emission = {}
deno = 'denominator'


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
    if not trigram.has_key((prev_prev_tag,prev_tag)):
        return 1e-16
    try:
        tri = float(trigram[(prev_prev_tag,prev_tag)][tag] / float(trigram[(prev_prev_tag,prev_tag)][deno]))
    except KeyError:
        tri = 1.0/trigram[(prev_prev_tag,prev_tag)][deno]
    if not bigram.has_key(prev_tag):
        return 1e-16
    try:
        bi  = float(bigram[prev_tag][tag] / float(bigram[prev_tag][deno]))
    except KeyError:
        bi  = 1.0/bigram[prev_tag][deno]
    try:
        uni = float(unigram[tag]/ float(unigram[deno]))
    except KeyError:
        uni = 1e-16
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


def find_backwars_tags(trellis):
    last_line = trellis[-1]
    for i,key in enumerate(last_line.keys()):
        if i==0:
            max_prob = last_line[key][1]
            max_tag = key
        elif last_line[key][1] > max_prob:
            max_prob = last_line[key][1]
            max_tag = key

    tags_list = []
    tags_list.insert(0,max_tag)

    for back in range(len(trellis)-1):
        tags_list.insert(0, trellis[len(trellis)-1-back][tags_list[0]][0])

    return tags_list


def synthesize_sentence(words,tags_list):
    result_sentence = ""
    for i,word in enumerate(words):
        result_sentence += word + "/" + str(tags_list[i]) + " "
    result_sentence = result_sentence[:-1]
    result_sentence += "\n"

    return result_sentence


def is_special_case(trellis,word,i,words, prev_tag,prev_prev_tag):
    two_backwords_is_known = False
    if word == "." and i == len(words)-1:
        probability, prev_tag_at_state = max([(trellis[-2][prev_tag][1] , prev_tag) for prev_tag in all_states])
        trellis[-1][word] = (prev_tag_at_state,0)
        return True
    if word in special_tags or word.replace('.','',1).replace(',',' ').isdigit():
        if word.replace('.','',1).replace(',',' ').isdigit():
            word = "CD"
        if len(trellis) == 1:    # only first word is like that
            sure_prev_tag = prev_tag
            trellis[-1][word] = (prev_tag, 0)
            return True
        if len(trellis[-2].keys()) > 1:
            probability, prev_tag_at_state = max([(trellis[-2][prev_tag][1], prev_tag) for prev_tag in tags_to_go_over])
            trellis[-1][word] = (prev_tag_at_state, 0)
            return True
        else:
            sure_prev_tag = trellis[-2].keys()[0]
            probability, prev_tag_at_state = (trellis[-2][sure_prev_tag][1], sure_prev_tag)
            trellis[-1][word] = (prev_tag_at_state, 0)
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
        if is_special_case(trellis,words[0],0,words,prev_tag,prev_prev_tag):
            knwon_one_backwords = True
        else:
            for tag in all_states:
                prob = getScore(words[0], tag, prev_tag, prev_prev_tag)
                trellis[0][tag] = (prev_tag,prob)

    if len(words) == 1:
        return trellis

    for i,word in enumerate(words[1:]):
        trellis.append({})
        special_case = is_special_case(trellis,word,i, words, prev_tag,prev_prev_tag)
        #print "i is %0d word is %s"%(i,word)
        if special_case:
            knwon_one_backwords = True
            continue
        if (not knwon_one_backwords):
            for tag in tags_to_go_over:
                option = []
                for j,prev_tag in enumerate(tags_to_go_over):
                    if j == 0:
                        prev_set = prev_tag
                        prev_set_score = (trellis[-2][prev_tag][1] + getScore(word, tag, prev_tag, trellis[-2][prev_tag][0]))
                    elif (trellis[-2][prev_tag][1] + getScore(word, tag, prev_tag, trellis[-2][prev_tag][0]) >  prev_set_score):
                        prev_set = prev_tag
                        prev_set_score = (trellis[-2][prev_tag][1] + getScore(word, tag, prev_tag, trellis[-2][prev_tag][0]))

                probability, prev_tag_at_state = prev_set_score, prev_set
                trellis[-1][tag] = (prev_tag_at_state,probability)
        else:
            handle_one_backward_is_known(trellis,word)
            knwon_one_backwords = False

    return trellis



def find_answer(input_file_name,output_file_name):
    text = []
    f = open(input_file_name)
    for i,line in enumerate(f):
        #print "line number %0d"%i
        if i%50 == 1:
            print "line number %0d"%i
        words = line.strip().split(" ")
        prev_prev_tag = "START"
        prev_tag = "START"
        trellis = viterbi_decoder(words,prev_prev_tag,prev_tag)
        tags_list = find_backwars_tags(trellis)
        text.append(synthesize_sentence(words, tags_list))

    text[-1] = text[-1][:-1]
    write_to_output_file(output_file_name, text)

def evaulate_result(output_file_name):
    text = []
    for i, line in enumerate(open(output_file_name)):
        text.append(line.strip())
    good = 0.0
    bad  = 0.0
    wrong_tags= []
    true_tags = []

    from MLETrain import extract_pos
    for i,correct_line in enumerate(open("ass1-tagger-test")):
        correct = extract_pos(correct_line)
        my_pos  = extract_pos(text[i])
        assert len(my_pos)== len(correct)
        how_many_corrct = 0.0
        for j in range(len(my_pos)):
            if (correct[j] == my_pos[j] ):
                how_many_corrct += 1
            else:
                if (correct[j] == ")" or correct[j] == "("):
                    print
                wrong_tags.append(my_pos[j])
                true_tags.append(correct[j])
        good += how_many_corrct
        bad += len(my_pos) - how_many_corrct

    print ("good")
    print (good)
    print ("bad")
    print (bad)

    print ("good/(bad+good)")
    print (good/(bad+good))

    print (zip(true_tags,wrong_tags))


def main():
# input_file_name q_mle_filename e_mle_filename output_file_name extra_file_name
    input_file_name  = sys.argv[1] if len(sys.argv) > 1 else "ass1-tagger-test-input"
    q_mle_filename   = sys.argv[2] if len(sys.argv) > 2 else "q.mle"
    e_mle_filename   = sys.argv[3] if len(sys.argv) > 3 else "e.mle"
    output_file_name = sys.argv[4] if len(sys.argv) > 4 else "outpot.txt"
    extra_file_name  = sys.argv[5] if len(sys.argv) > 5 else "extra.txt"

    # create_transition(q_mle_filename)
    # create_emission(e_mle_filename)
    # create_denominator()
    # find_answer(input_file_name,output_file_name)
    print ("Evaluate")
    evaulate_result(output_file_name)


if __name__ == '__main__':
    main()


