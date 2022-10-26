import argparse
import csv
import os
import traceback

import classla
from lemmagen3 import Lemmatizer


classla.download("sl", logging_level="WARNING")
classla_nlp_pipeline = classla.Pipeline(
    lang="sl",
    processors="tokenize,pos,lemma,depparse",
    tokenize_pretokenized=True,
    logging_level="WARNING",
)


def _resolve_lemmagen_model_loc(model_name):
    basedir = os.path.dirname(__file__)
    return os.path.join(basedir, "lemmagen_models", model_name)


_canon_lemmatizer = Lemmatizer()
_canon_lemmatizer.load_model(_resolve_lemmagen_model_loc("kanon.bin"))
canon_lemma = _canon_lemmatizer.lemmatize

ADJ_LEMMATIZER_LOC_MAP = {
    ("m", "s"): _resolve_lemmagen_model_loc("kanon-adj-male.bin"),
    ("m", "p"): _resolve_lemmagen_model_loc("kanon-adj-male-plural.bin"),
    ("f", "s"): _resolve_lemmagen_model_loc("kanon-adj-female.bin"),
    ("f", "p"): _resolve_lemmagen_model_loc("kanon-adj-female-plural.bin"),
    ("n", "s"): _resolve_lemmagen_model_loc("kanon-adj-neutral.bin"),
    ("n", "p"): _resolve_lemmagen_model_loc("kanon-adj-neutral-plural.bin"),
}

_ADJ_LEMMATIZER_CACHE = {}


def lem_adj(gender, number, wrd):
    lem_key = (gender, number)
    if lem_key not in _ADJ_LEMMATIZER_CACHE:
        assert lem_key in ADJ_LEMMATIZER_LOC_MAP
        lemmatizer_model_loc = ADJ_LEMMATIZER_LOC_MAP[lem_key]
        lemmatizer = Lemmatizer()
        lemmatizer.load_model(lemmatizer_model_loc)
        _ADJ_LEMMATIZER_CACHE[lem_key] = lemmatizer
    lemmatizer = _ADJ_LEMMATIZER_CACHE[lem_key]
    return lemmatizer.lemmatize(wrd)


def get_adj_msd(head, word):
    feats = head.feats
    feats_dict = {}
    feats = feats.strip().split("|")
    for f in feats:
        f = f.strip().split("=")
        feats_dict[f[0]] = f[1]
    gender = feats_dict["Gender"]
    if gender == "Masc" and len(word.xpos) == 6:
        msd = word.xpos[:-1] + "ny"
    elif gender == "Masc" and len(word.xpos) == 7:
        msd = word.xpos[:-1] + "y"
    elif gender == "Fem":
        msd = word.xpos[:-1] + "n"
    elif gender == "Neut":
        msd = word.xpos[:-1] + "n"
    else:
        # msd = None
        msd = "qqqqqq"  # hacky but it means that adverbs are just copied over to the canonical form
    return msd


def _is_single_acronym(term):
    # (single word, all uppercase and length less than 5 characters)
    if len(term.words) == 1:
        word = term.words[0].text
        return len(word) < 5 and word.isupper()
    return False


def _join_term_words(term):
    return " ".join([w.text for w in term.words])


def _process_pre(pre, head, gender, number):
    canon = []
    for el in pre:
        msd = get_adj_msd(head, el)
        if msd[0] == "A":
            form = lem_adj(gender, number, el.text.lower())
            canon.append(form)
        else:
            canon.append(el.lemma.lower())
    return canon


def subfinder(mylist, pattern):
    matches = []
    for i in range(len(mylist)):
        if (
            mylist[i].text.lower() == pattern[0]
            and [t.text.lower() for t in mylist[i : i + len(pattern)]] == pattern
        ):
            matches.append(mylist[i : i + len(pattern)])
    return matches


def find_canon(term):
    if _is_single_acronym(term):
        return term.words[0].text

    head = None
    pre = []
    post = []
    propns = 0

    for word in term.words:
        if word.upos == "PROPN":
            propns += 1
        if word.head == 0:
            head = word
    ## special case where all words are proper nouns and each word is canonized independently
    if propns == len(term.words):
        canon_name = []
        for word in term.words:
            form = canon_lemma(word.text)
            canon_name.append(form)
        return " ".join(canon_name)

    if head is None:

        if len(term.words) == 1:
            head2 = term.words[0]
            head_form = canon_lemma(head2.text.lower())
            return head_form
        else:
            # just return the input because we do not cover such case
            return _join_term_words(term)
    elif head.upos == "VERB":  # if the term is not a noun phrase
        # just return the input because we do not cover such case
        return _join_term_words(term)
    else:
        for word in term.words:
            if word.id < head.id:
                pre.append(word)
            elif word.id > head.id:
                post.append(word)

        canon = []
        gender = head.xpos[2]
        number = head.xpos[3]
        ending = head.lemma[-1]
        if gender == "f" and number == "s" and ending in "ie":  # sani, hlače
            canon.extend(_process_pre(pre, head, "f", "p"))
            canon.append(head.lemma)
        elif gender == "m" and number == "p" and ending == "i":  # možgani
            canon.extend(_process_pre(pre, head, "m", "p"))
            canon.append(head.lemma)
        elif gender == "n" and number == "p" and ending == "a":  # vrata
            canon.extend(_process_pre(pre, head, "n", "p"))
            canon.append(head.lemma)
        elif gender == "f":
            canon.extend(_process_pre(pre, head, "f", "s"))
            head_form = canon_lemma(head.text.lower())
            canon.append(head_form)
        elif gender == "m":
            canon.extend(_process_pre(pre, head, "m", "s"))
            head_form = canon_lemma(head.text.lower())
            canon.append(head_form)
        elif gender == "n":
            canon.extend(_process_pre(pre, head, "n", "s"))
            head_form = canon_lemma(head.text.lower())
            canon.append(head_form)

        for el in post:
            canon.append(el.text)
        return " ".join(canon)


def process(forms):
    text = "\n".join(forms)
    doc = classla_nlp_pipeline(text)
    canonical_forms = []
    for term in doc.sentences:
        try:
            canonical_form = find_canon(term)
        except Exception:
            print(traceback.format_exc())
            canonical_form = _join_term_words(term)
        canonical_forms.append(canonical_form)
    return canonical_forms


def read_csv(fname, columnID=0):
    data = []
    with open(fname) as csvfile:
        try:
            dialect = csv.Sniffer().sniff(csvfile.read(2048))
        except csv.Error:
            print("Warning: cannot determine delimiter, assuming Excel CSV dialect.")
            dialect = "excel"
        csvfile.seek(0)
        reader = csv.reader(csvfile, dialect)
        for i, row in enumerate(reader):
            try:
                data.append(row[columnID])
            except:
                print("Error, line {}".format(i))
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Converter to canonical form in Slovene language"
    )
    parser.add_argument("csv_file", type=argparse.FileType("r"), help="Input csv file")
    parser.add_argument("column_id", type=int, help="CSV column number (zero indexed)")
    args = parser.parse_args()

    data = read_csv(args.csv_file.name, columnID=args.column_id)
    results = process(data)
    for canon in results:
        print("{}".format(canon))
