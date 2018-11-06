import sys
from collections import Counter


def read_data(fname):
    data = []
    for line in open(fname,"r"):
        data.append(line)
    return data


def _add_value_to_dict(d , key, value):
    try:
        d[key].update( [value] )
    except KeyError:
        d[key] = Counter()
        d[key].update([value])


def update_Emle_with_line(emission,value):
    words = value.strip().split(" ")
    for word in words:
        try:
            w, pos = word.split("/")
            _add_value_to_dict(emission, w, pos)
        except ValueError:
            all_parts = word.split("/")
            pos = all_parts[-1]
            for i in range(len(all_parts)-1):
                _add_value_to_dict(emission,all_parts[i],pos)

    # pattern = re.compile("\/([^\s]+)")
    # result = re.findall(pattern, value)



def extract_pos(value):
    pos = []
    words = value.split(" ")
    for word in words:
        all_parts = word.split("/")
        p = all_parts[-1]
        p = p.strip()
        pos.append(p)

    return pos


def update_Qmle_with_line(line):
    pos = extract_pos(line)
    pos.insert(0,"START")
    pos.insert(0,"START")
    for i in range(2, len(pos)):
        trigram_list = pos[i - 2:i + 1]
        trigram_tuple = tuple(trigram_list)
        bigram_tuple = tuple(trigram_list[:-1])
        # print trigram_list
        unigram.update(trigram_list)
        trigram.update([trigram_tuple])
        bigram.update([bigram_tuple])


def write_E_mle_to_flie(e_mle_filename):
    f = open(e_mle_filename,"w")
    for word in emission:
        for pos in emission[word]:
            str_to_flie = str(word) + " " + str(pos) + "\t" + str(emission[word][pos])+ "\n"
            f.write(str_to_flie)



def write_Q_mle_to_flie(q_mle_file_name):
    f = open(q_mle_file_name, "w")
    number_of_element = 4
    for counter_type in [trigram,bigram,unigram]:
        number_of_element -= 1
        for key in counter_type.most_common():
            value = counter_type[key[0]]
            str_key = ""
            for i in range(number_of_element):
                # if len(key)!= number_of_element:
                #     print key
                #     exit()
                if number_of_element > 1:
                    str_key   += str(key[0][i])
                else:
                    str_key += str(key[i])
                if i != number_of_element-1:
                    str_key+= " "
                else:
                    str_key+= "\t"

            write_to_file = str_key + str(value) +"\n"
            f.write(write_to_file)



trigram = Counter()
bigram  = Counter()
unigram  = Counter()
emission = {}  # each word is a list


def main():
    input_file_name  = sys.argv[1] if len(sys.argv) > 1 else "ass1-tagger-train"
    q_mle_filename   = sys.argv[2] if len(sys.argv) > 2 else "q.mle"
    e_mle_filename   = sys.argv[3] if len(sys.argv) > 3 else "e.mle"
    print (e_mle_filename)
    with open(input_file_name) as f:
        for text_line in f:
            update_Qmle_with_line(text_line)
            update_Emle_with_line(emission,text_line)

    write_Q_mle_to_flie(q_mle_filename)
    write_E_mle_to_flie(e_mle_filename)


if __name__ == '__main__':
    main()


