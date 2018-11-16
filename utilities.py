

def check_if_number(s):
    return s.replace('.','',1).replace(',','').isdigit()

def check_if_number_word(s):
    if "-" in s:
        parts = s.replace('.','',1).replace(',','').split("-",1)
        if check_if_number(parts[0]):
            return True

    return False


def find_convetion_type(word):
    feature = []
    if check_if_number(word):
        feature.append("NUMBER")
    if check_if_number_word(word):
        feature.append("NUMBER-WORD")
    if word[0].isupper() and word[1:].islower():
        feature.append("^Aa")
    elif word.isupper():
        feature.append("CAPITALS")
    if word.endswith("ed"):
        feature.append(".*ed")
    elif word.endswith("ing"):
        feature.append(".*ing")
    elif word.endswith("s"):
        feature.append(".*s")
    elif word[-1] == ".":
        feature.append(".*.")
    elif len(word.split("-")) == 2:
        feature.append("WORD-WORD")

    return '-'.join(feature)