from os import makedirs, listdir, getcwd
from os.path import join
from random import randint
from re import findall, MULTILINE, sub
from pytholog import KnowledgeBase, Expr
from spacy import load as spacy_load
from spacy_wordnet.wordnet_annotator import WordnetAnnotator
from re import sub


def getsid():
    """Generates a unique id for each session using numpy.random.randit() \nCompares the new id with all of the past ids (stores in a text file)"""
    id = 0
    past_sessions = []

    with open("./docs/past_sessions.txt", "r") as past:
        past_sessions = past.read().split('\n')
    while str(id) in past_sessions:
        for i in range(5):
            id += randint(1000, 9999)

    with open("./docs/past_sessions.txt", "a") as past:
        past.write(f"{str(id)}\n")
    return id


def parse_rules_social(rules, paths):
    """Parses the rules of prolog file, converts them into facts and returns a list of nodes\nNode Structure: [Relation, [Node1 , Node2]]"""
    for path in paths:
        handler = KnowledgeBase("prolog")
        handler.from_file(file=path)
        nodes = []

        for rule in rules:
            ask = rule.split(":-")[0]  # rule(X, Y):- fact(X, Y). -> rule(X, Y)
            result = handler.query(Expr(ask))
            if not 'No' in result:  # If rule has no related facts
                for sample in result:
                    relation = ask.split("(")[0]
                    objects = [obj.capitalize() for obj in sample.values()]
                    nodes.append([relation.upper(), objects])
    return nodes


def parse_facts_social(facts):
    """Converts facts into neo4j nodes \nNode Structure: [Relation, [Node1 , Node2]]\nInput: <class 'List'>\nOutput:<class 'List'>"""
    regex = r"(.+)\((.+)\)"
    _1_object = []
    _2_objects = []
    for fact in facts:
        matches = findall(regex, fact, MULTILINE)
        if matches:
            relation = matches[0][0].upper()
            objects = [obj.capitalize() for obj in matches[0][1].split(', ')]
            data = [relation, objects]
            _2_objects.append(data) if len(
                objects) == 2 else _1_object.append(data)
    return _2_objects


def extract_hypernym(token):
    """Extracts the hypernym (parent category) for a given token."""
    synsets = token._.wordnet.synsets()
    if not synsets:
        return None
    # Take the first synonym and get its hypernyms
    hypernyms = synsets[0].hypernyms()
    if not hypernyms:
        return None
    # Return the first lemma name of the hypernym
    return hypernyms[0].lemmas()[0].name()


def get_hypernyms(input, nlp):
    """Gets up to 4 levels of hypernyms for each noun token in the input using nlp."""
    doc = nlp(input)
    hypernyms = []

    for token in doc:
        if token.pos_ == "NOUN":  # Check if the token is a noun
            sequence = [token.text.capitalize()]  # Save the base token
            for _ in range(4):
                hypernym_name = extract_hypernym(token)
                if hypernym_name:
                    hypernym_name = sub(
                        r'[^a-zA-Z]', ' ', hypernym_name).capitalize()
                    # Save the hypernym for a token
                    sequence.append(hypernym_name)
                    # Get the token for current hypernym
                    token = nlp(hypernym_name)[0]
                else:
                    break
            hypernyms.append(sequence)

    return hypernyms


class Memories:
    def __init__(self, graph):
        self.graph = graph
        self.id = None
        self.init()

    def init(self):
        """- Initiates the Neo4j Memory Nodes (uses Merge keyword)\n- Gets the unique id for current session\n- Downloads wordnet"""
        query = (
            "MERGE (bot:Main:Bot {name: 'Bot'})"
            "MERGE (m1:Memory:EpisodicMemory {name: 'Episodic'})"
            "MERGE (m2:Memory:SocialMemory {name: 'Social'})"
            "MERGE (m3:Memory:SemanticMemory {name: 'Semantic'})"
            "MERGE (bot)-[:HAS]->(m1)"
            "MERGE (bot)-[:HAS]->(m2)"
            "MERGE (bot)-[:HAS]->(m3)"
        )
        self.graph.run(query)

        # Load SpaCy model and add WordNet annotator
        self.nlp = spacy_load("en_core_web_sm")
        self.nlp.add_pipe("spacy_wordnet", after='tagger')

    def handle_episodic(self, uname, user, bot, sequence):
        """Creates nodes (a user, his session, and chat) and relations between them \n(user)-[:HAS]->(session) \n(session)-[:SEQUENCE]->(chat)"""
        query = (
            "MERGE (memory:Memory:EpisodicMemory {name: 'Episodic'})"
            "MERGE (user:EpisodicMemory:Person {name: $name}) "
            "MERGE (session:EpisodicMemory:Episode {name: 'Conversation', sid: $sid})"
            "CREATE (chat:EpisodicMemory:Chat {name: $seq, _1_user: $input, _2_bot: $output})"
            "MERGE (memory)-[:OF]->(user)"
            "MERGE (user)-[:HAS]->(session)"
            "CREATE (session)-[:SEQUENCE]->(chat)"
        )
        self.graph.run(query, name=uname, sid=self.id,
                       input=user, output=bot, seq=sequence)

    def load_social(self, path):
        """Loads facts & rules from given prolog file and parse them into facts\n1. Separates facts and rules from each knowledge base in a directory\n2. Acquires facts from all the rules \n3. Converts facts in the Neo4J node format -> [Relation, [Node1 , Node2]]"""
        rules = {}
        facts = {}
        self.facts = {}

        path = getcwd() + path
        makedirs(path, exist_ok=True)
        kbs = [join(path, kb) for kb in listdir(path)]

        #  Filtering rules and facts
        for kb in kbs:
            with open(kb, "r") as f:
                content = f.read().split(".")
                content = [
                    f"{phrase.strip()}." for phrase in content if not phrase == "\n"]
                t_rules = filter(
                    lambda item: True if ":-" in item else False, content)
                t_facts = filter(
                    lambda item: False if ":-" in item else True, content)
            # D:\\UMT\...\\family.pl -> Family
            kb_name = kb.split("\\")[-1].split(".")[0].capitalize()
            facts[kb_name] = (list(t_facts))
            rules[kb_name] = (list(t_rules))

        for key, values in facts.items():
            self.facts[key] = parse_facts_social(values)

        for key, values in rules.items():
            self.facts[key].extend(parse_rules_social(values, kbs))

    def handle_social(self, path):
        """Creates nodes (a user, his session, and chat) and relations between them 
        (user)-[:HAS]->(session) 
        (session)-[:SEQUENCE]->(chat)"""

        self.load_social(path)

        for key, facts in self.facts.items():
            for fact in facts:
                if fact:  # Ensure fact is not an empty string
                    relation, objects = fact[0], fact[1]

                    # Construct the query with the dynamic relationship
                    query = (
                        "MERGE (memory:Memory:SocialMemory {name: 'Social'}) "
                        "MERGE (kb:Memory:SocialMemory:KnowledgeBase {name: $kb}) "
                        "MERGE (person1:SocialMemory:Person {name: $person1}) "
                        "MERGE (person2:SocialMemory:Person {name: $person2}) "
                        "MERGE (memory)-[:OF]->(kb) "
                        "MERGE (kb)-[:HAS]->(person1) "
                        "MERGE (kb)-[:HAS]->(person2) "
                        f"MERGE (person1)-[:{relation}]->(person2)"
                    )

                    # Execute the query
                    self.graph.run(
                        query, kb=key, person1=objects[0], person2=objects[1])

    def handle_semantic(self, input):
        """Extract the semantics from inputs and add them to the Semantic Memory"""
        semantics = get_hypernyms(input, self.nlp)
        root_query = (
            "MERGE (memory:Memory:SemanticMemory {name: 'Semantic'}) "
            "MERGE (root:SemanticMemory:Meaning {name: $root}) "
            "MERGE (memory)-[:OF]->(root) "
        )

        query = (
            "MERGE (root:SemanticMemory {name: $root}) "
            "MERGE (meaning:SemanticMemory:Meaning {name: $child}) "
            "MERGE (root)-[:IS]->(meaning) "
        )

        for semantic in semantics:
            self.graph.run(root_query, root=semantic[0])
            root = semantic[0]
            for meaning in semantic[1:]:
                self.graph.run(query, root=root, child=meaning)
                root = meaning


if __name__ == '__main__':
    link = "bolt://localhost:7687"
    db = "neo4j"
    passw = "12345678"
    username = input("Enter your name: ")

    # graph = Graph(link, auth=(db, passw))
    graph = ""
    memory = Memories(graph)
    memory.handle_social(path="/docs/kb")

    for i in range(3):
        user_said = input("User: ")
        bot_said = input("Bot: ")
        memory.handle_semantic(user_said)
        memory.handle_episodic(
            uname=username.capitalize(),
            user=user_said.strip(), bot=bot_said.strip(), sequence=i+1
        )

