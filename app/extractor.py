from spacy import load as spacy_load
from spacy.language import Language

@Language.factory("merge_pos")
def merge_pos(nlp, name):
    def merge_pos_component(doc):
        with doc.retokenize() as retokenizer:
            for token in doc:
                if token.dep_ in ["amod", "compound"] and token.head.pos_ == "NOUN":
                    start = token.i
                    end = token.head.i + 1
                    retokenizer.merge(doc[start:end])
        return doc
    return merge_pos_component

class RelationExtractor:
    def __init__(self, model="en_core_web_sm"):
        self.nlp = spacy_load(model)
        self.nlp.add_pipe("merge_entities")
        self.nlp.add_pipe("merge_pos")

    def lemmatize(self, token):
        if token.lemma_ in ["be", "have", "do"]:
            return token.text 
        else:
            return token.lemma_

    def process(self, text):
        doc = self.nlp(text)
        root = None
        nsubj = None
        dobj = None
        parent = None
        child = None
        grandchild = None

        for token in doc:
            if token.dep_ == "ROOT" and (token.pos_ in {"VERB", "AUX"}):
                root = token
            elif token.dep_ == "nsubj" and (token.pos_ in {"PROPN", "NOUN"}):
                nsubj = token
            elif token.dep_ in {"dobj", "attr"} and (token.pos_ in {"PROPN", "NOUN"}):
                dobj = token
            elif token.dep_ == "prep" and (token.head.pos_ in {"NOUN", "PROPN"}):
                parent = token.head
                child = token
                for child_token in token.children:
                    if child_token.dep_ == "pobj":
                        grandchild = child_token
                        break

        output = {}

        if all([root, nsubj, dobj]):
            output = {
                "primary": nsubj.text,
                "relation_1": self.lemmatize(root),
                "secondary": dobj.text
            }
            if parent and child and grandchild:
                output["relation_2"] = child.text
                output["tertiary"] = grandchild.text

        return None if output == {} else output 
