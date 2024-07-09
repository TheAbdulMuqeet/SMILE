from py2neo import Node, Relationship

class Neo4jHandler:
    def __init__(self, graph):
        self.graph = graph
    
    def add_person(self, person):
        self._create_and_return_person(person)

    def add_relationship(self, person1, relationship, person2):
        self._create_and_return_relationship(person1, relationship, person2)

    def find_relation(self, person, relation):
        result = self._find_relation(person, relation)
        return result

    def find_person(self, person):
        result = self._find_person(person)
        return result

    def _create_and_return_person(self, person):
        person_node = Node("Person", name=person)
        self.graph.merge(person_node, "Person", "name")
        return person_node

    def _create_and_return_relationship(self, person1, relationship, person2):
        person1_node = self.graph.nodes.match("Person", name=person1).first()
        if not person1_node:
            person1_node = Node("Person", name=person1)
            self.graph.create(person1_node)
        
        person2_node = self.graph.nodes.match("Person", name=person2).first()
        if not person2_node:
            person2_node = Node("Person", name=person2)
            self.graph.create(person2_node)
        
        rel = Relationship(person1_node, relationship.upper(), person2_node)
        self.graph.merge(rel)
        return rel

    def _find_relation(self, person, relation):
        query = (
            "MATCH (a:Person {name: $person})-[:%s]->(b) "
            "RETURN b.name AS name" % relation.upper()
        )
        result = self.graph.run(query, person=person)
        return [record["name"] for record in result]

    def _find_person(self, person):
        person_node = self.graph.nodes.match("Person", name=person).first()
        return dict(person_node) if person_node else None
    
