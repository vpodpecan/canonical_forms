import os
import classla
import csv
import argparse
from lemmagen3 import Lemmatizer

classla.download('sl', logging_level='WARNING')

BASEDIR = os.path.dirname(__file__)


def lem_adj(gender, wrd):
    lem = Lemmatizer()
    if gender == 'm':
        lem.load_model(os.path.join(BASEDIR, 'lemmagen_models/kanon-adj-male.bin'))
    elif gender == 'f':
        lem.load_model(os.path.join(BASEDIR, 'lemmagen_models/kanon-adj-female.bin'))
    elif gender == 'n':
        lem.load_model(os.path.join(BASEDIR, 'lemmagen_models/kanon-adj-neutral.bin'))

    form = lem.lemmatize(wrd)
    return form


def process_nlp_pipeline(lang, text):
    nlp = classla.Pipeline(lang=lang, processors='tokenize,pos,lemma', tokenize_pretokenized=True, logging_level='WARNING')
    doc = nlp(text)
    return doc


def get_adj_msd(head, word):
    feats = head.feats
    feats_dict = {}
    feats = feats.strip().split('|')
    for f in feats:
        f = f.strip().split('=')
        feats_dict[f[0]] = f[1]
    gender = feats_dict['Gender']
    #print(gender)
    #gender = gender.strip().split('=')[1]
    if gender == 'Masc' and len(word.xpos) == 6:
        msd = word.xpos[:-1]+'ny'
    elif gender == 'Masc' and len(word.xpos) == 7:
        msd = word.xpos[:-1]+'y'
    elif gender == 'Fem':
        msd = word.xpos[:-1]+'n'
    elif gender == 'Neut':
        msd = word.xpos[:-1]+'n'
    else:
        msd = None
    return msd


def subfinder(mylist, pattern):
    matches = []
    for i in range(len(mylist)):
        #print(mylist[i].text)
        #if mylist[i].text == pattern[0] and mylist[i:i+len(pattern)].text == pattern:
        if mylist[i].text.lower() == pattern[0] and [t.text.lower() for t in mylist[i:i+len(pattern)]] == pattern:
            matches.append(mylist[i:i+len(pattern)])
    return matches


def find_canon(term):
    head = None
    pre = []
    post = []
    for word in term.words:
        if word.upos == 'NOUN' or word.upos == 'PROPN':
            head = word
            break
    if head is None:
        if len(term.words) == 1:
            head2 = term.words[0]
            lem = Lemmatizer()
            lem.load_model(os.path.join(BASEDIR, 'lemmagen_models/kanon.bin'))
            head_form = lem.lemmatize(head2.text.lower())
            return head_form
        else:
            return ' '.join([w.text for w in term.words])  # just return the input because we do not cover such case
    else:
        for word in term.words:
            if word.id < head.id:
                pre.append(word)
            elif word.id > head.id:
                post.append(word)

    canon = []
    for el in pre:
        msd = get_adj_msd(head, el)
        if msd is None:
            canon.append(el.lemma.lower())
        else:
            if msd[0] == 'A' and msd[3] == 'm':
                form = lem_adj('m', el.text.lower())
                canon.append(form)
            elif msd[0] == 'A' and msd[3] == 'f':
                form = lem_adj('f', el.text.lower())
                canon.append(form)
            elif msd[0] == 'A' and msd[3] == 'n':
                form = lem_adj('n', el.text.lower())
                canon.append(form)

    lem = Lemmatizer()
    lem.load_model(os.path.join(BASEDIR, 'lemmagen_models/kanon.bin'))
    head_form = lem.lemmatize(head.text.lower())
    canon.append(head_form)
    for el in post:
        canon.append(el.text)
    return ' '.join(canon)


# def process(data):
#     '''data is a list of pairs (lemma, form)
#     '''
#     terms = [x[1] for x in data]
#     lemmas = [x[0] for x in data]
#     text = '\n'.join(terms)
#     doc = process_nlp_pipeline('sl', text)
#
#     result = []
#     for term, sent, lemma in zip(terms, doc.sentences, lemmas):
#         result.append((lemma, find_canon(sent)))
#     return result


def process(forms):
    text = '\n'.join(forms)
    doc = process_nlp_pipeline('sl', text)
    return [find_canon(sent) for sent in doc.sentences]


def read_csv(fname, columnID=0):
    data = []
    with open(fname) as csvfile:
        try:
            dialect = csv.Sniffer().sniff(csvfile.read(2048))
        except csv.Error:
            print('Warning: cannot determine delimiter, assuming Excel CSV dialect.')
            dialect = 'excel'
        csvfile.seek(0)
        reader = csv.reader(csvfile, dialect)
        for i, row in enumerate(reader):
            try:
                data.append(row[columnID])
            except:
                print('Error, line {}'.format(i))
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Converter to canonical form in Slovene language')
    parser.add_argument('csv_file', type=argparse.FileType('r'), help='Input csv file')
    parser.add_argument('column_id', type=int, help='CSV column number (zero indexed)')
    args = parser.parse_args()

    data = read_csv(args.csv_file.name, columnID=args.column_id)
    results = process(data)
    for canon in results:
        print('{}'.format(canon))


# if __name__ == '__main__':
#     if len(sys.argv) != 2:
#         print('Usage: python generate_cannonical.py <csv file>')
#     else:
#         data = read_csv(sys.argv[1], columnID=0, sep='\t')
#         results = process(data)
#         for canon in results:
#             print('{}'.format(canon))
