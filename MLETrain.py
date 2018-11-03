import re

def read_data(fname):
    data = []
    for line in file(fname):
        data.append(line)
    return data

def extract_pos():
    pass


def between(value):
    # Find and validate before-part.
    pos_b = pos_a = 0
    pos = []
    pos.append("START")
    pos.append("START")
    ended_line = False
    while (not ended_line):
        value = value[pos_b:]
        pos_a = value.find("/")
        if pos_a == -1:
            print "error 1"
            exit()
        # Find and validate after part.
        pos_b = value.find(" ")
        if pos_b == -1:
            pos_b = value.find("\n")
            ended_line = True
        # Return middle part.
        pos_name = value[pos_a+1:pos_b]
        if "/" in pos_name:
            pos_a = pos_name.rfind("/")
            pos_name = pos_name[pos_a+1:]
            # print pos_name
        pos_b+=1
        pos.append(pos_name)

    return pos



from collections import Counter
trigram = Counter()
bigram  = Counter()
unigram  = Counter()

for line in file("ass1-tagger-train"):

    pos = between(line)
    for i in range(2,len(pos)):
        trigram_list  = pos[i-2:i+1]
        trigram_tuple = tuple(trigram_list)
        bigram_tuple  = tuple(trigram_list[:-1])
        # print trigram_list
        unigram.update(trigram_list)
        trigram.update([trigram_tuple])
        bigram.update([bigram_tuple])


f = open("q.mle", "w")
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

        # print str_key

        # str_key   = str_key[0]
        # str_key   = str_key.replace("'","")
        # str_key   = str_key.replace("(","")
        # str_key   = str_key.replace(")","")
        # str_key   = str_key.replace(",","")
        print str_key
        write_to_file = str_key + str(value) +"\n"
        f.write(write_to_file)


print "TRIGRAM"
print trigram
print "BIGRAM"
print bigram
print "UNIGRAM"
print unigram