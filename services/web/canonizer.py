import os
import classla
import csv
import argparse
from lemmagen3 import Lemmatizer

classla.download('sl', logging_level='WARNING')

BASEDIR = os.path.dirname(__file__)


def lem_adj(gender, number, wrd):
    lem = Lemmatizer()
    if gender == 'm' and number == 's':
        lem.load_model(os.path.join(BASEDIR, 'lemmagen_models/kanon-adj-male.bin'))
    elif gender == 'm' and number == 'p':
        lem.load_model(os.path.join(BASEDIR, 'lemmagen_models/kanon-adj-male-plural.bin'))
    elif gender == 'f' and number == 's':
        lem.load_model(os.path.join(BASEDIR, 'lemmagen_models/kanon-adj-female.bin'))
    elif gender == 'f' and number == 'p':
        lem.load_model(os.path.join(BASEDIR, 'lemmagen_models/kanon-adj-female-plural.bin'))
    elif gender == 'n' and number == 's':
        lem.load_model(os.path.join(BASEDIR, 'lemmagen_models/kanon-adj-neutral.bin'))
    elif gender == 'n' and number == 'p':
        lem.load_model(os.path.join(BASEDIR, 'lemmagen_models/kanon-adj-neutral-plural.bin'))

    form = lem.lemmatize(wrd)
    return form


def process_nlp_pipeline(lang, text):
    nlp = classla.Pipeline(lang=lang, processors='tokenize,pos,lemma, depparse', tokenize_pretokenized=True, logging_level='WARNING')
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

    try:
        if len(term.words) == 1 and term.words[0].text.isupper() and len( term.words[0].text) < 5: # if acronym (single word, all uppercase and length les than 5 characters)
            return  term.words[0].text

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
                lem = Lemmatizer()
                lem.load_model(os.path.join(BASEDIR, 'lemmagen_models/kanon.bin'))
                form = lem.lemmatize(word.text)
                canon_name.append(form)
            return ' '.join(canon_name)



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
            if head.xpos[3] == 'p' and head.xpos[2] == 'f' and head.lemma[-1] == 'i': #sani
                for el in pre:
                    msd = get_adj_msd(head, el)
                    if msd[0] == 'A':
                        form = lem_adj('f', 'p', el.text.lower())
                        canon.append(form)
                    else:
                        canon.append(el.lemma.lower())
                canon.append(head.lemma)
            elif head.xpos[3] == 'p' and head.xpos[2] == 'f' and head.lemma[-1] == 'e': #hlače
                for el in pre:
                    msd = get_adj_msd(head, el)
                    if msd[0] == 'A':
                        form = lem_adj('f', 'p', el.text.lower())
                        canon.append(form)
                    else:
                        canon.append(el.lemma.lower())
                canon.append(head.lemma)
            elif head.xpos[3] == 'p' and head.xpos[2] == 'm' and head.lemma[-1] == 'i': #možgani
                for el in pre:
                    msd = get_adj_msd(head, el)
                    if msd[0] == 'A':
                        form = lem_adj('m', 'p', el.text.lower())
                        canon.append(form)
                    else:
                        canon.append(el.lemma.lower())
                canon.append(head.lemma)
            elif head.xpos[3] == 'p' and head.xpos[2] == 'n' and head.lemma[-1] == 'a': #vrata
                for el in pre:
                    msd = get_adj_msd(head, el)
                    if msd[0] == 'A':
                        form = lem_adj('n', 'p', el.text.lower())
                        canon.append(form)
                    else:
                        canon.append(el.lemma.lower())
                canon.append(head.lemma)
            elif head.xpos[2] == 'f':
                for el in pre:
                    msd = get_adj_msd(head, el)
                    if msd[0] == 'A':
                        form = lem_adj('f', 's', el.text.lower())
                        canon.append(form)
                    else:
                        canon.append(el.lemma.lower())
                lem = Lemmatizer()
                lem.load_model(os.path.join(BASEDIR, 'lemmagen_models/kanon.bin'))
                head_form = lem.lemmatize(head.text.lower())
                canon.append(head_form)
            elif head.xpos[2] == 'm':
                for el in pre:
                    msd = get_adj_msd(head, el)
                    if msd[0] == 'A':
                        form = lem_adj('m', 's', el.text.lower())
                        canon.append(form)
                    else:
                        canon.append(el.lemma.lower())
                lem = Lemmatizer()
                lem.load_model(os.path.join(BASEDIR, 'lemmagen_models/kanon.bin'))
                head_form = lem.lemmatize(head.text.lower())
                canon.append(head_form)
            elif head.xpos[2] == 'n':
                for el in pre:
                    msd = get_adj_msd(head, el)
                    if msd[0] == 'A':
                        form = lem_adj('n', 's', el.text.lower())
                        canon.append(form)
                    else:
                        canon.append(el.lemma.lower())
                lem = Lemmatizer()
                lem.load_model(os.path.join(BASEDIR, 'lemmagen_models/kanon.bin'))
                head_form = lem.lemmatize(head.text.lower())
                canon.append(head_form)

            for el in post:
                canon.append(el.text)
            return ' '.join(canon)
    except:
        return ' '.join([w.text for w in term.words])


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
