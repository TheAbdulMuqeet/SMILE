import os
from re import compile
from glob import glob
from aiml import Kernel
from dotenv import load_dotenv
from py2neo import Graph
from seek import Neo4jHandler
from extractor import RelationExtractor
from memories import Memories, getsid
from transformers import pipeline

class Chatbot:
    def __init__(self):
        """__init__ performs following tasks:\n1. Load all environment variables\n2. Setups Neo4j\n3. Learns from AIML\n4. Setups additional data members"""
        print("================================")


        load_dotenv()
        self.name = os.environ['BOT']
        print(f"Initializing {self.name}")

        print("Load environment variables...", end=" ")
        user = os.environ['GRAPH_USER']
        passw = os.environ['GRAPH_PASSWORD']
        url = os.environ['GRAPH_URL']
        self.uname = None
        print("Success")

        print("Setting up Memories and Neo4j...", end=" ")
        try:
            self.graph = Graph(url, auth=(user, passw))  # Graph object
            self.neo4j_handler = Neo4jHandler(self.graph) # Injector
            self.memory = Memories(self.graph) # Neo4j Memories class
            self.memory.handle_social(path=os.environ['KB_DIR']) # Social network
            print("Success")
        except Exception as e:
            print("Some error occurred")
            print("ERR:", e)

        print("Setting up Input Parser and Sentiment Analysis model...", end=" ")
        try:
            self.extractor = RelationExtractor()
            self.model = pipeline("text-classification", model="finiteautomata/bertweet-base-sentiment-analysis")
            print("Success")
        except Exception as e:
            print("Some error occurred")
            print("ERR:", e)

        print("Fetch history backup...", end=" ")
        self.docs_path = os.path.join(os.getcwd(), os.environ['DOCS'])
        print("Success\nLearning from AIML data...", end=" ")

        try:
            self.myBot = Kernel()

            for filename in os.listdir('files'):
                if filename.endswith('.aiml'):
                    self.myBot.learn("./files/" + filename)
            print("Success")
        except Exception as e:
            print("Some error occurred")
            print("ERR:", e)

        print("================================")

        self.gPredicates = {}
        self.chat_counter = 0
    
    def set_sid(self, sid):
        if sid:
            self.memory.id = sid
        else:
            self.memory.id = getsid()
        print(self.memory.id)

    def clear_predicates(self):
        """Clears AIML predicates as due to the possibility of reading old data"""
        self.myBot.setPredicate("rel", "")
        self.myBot.setPredicate("obj1", "")
        self.myBot.setPredicate("obj2", "")
        self.myBot.setPredicate("operation", "")

    def response(self, message):
        """The brain of the bot which replies to the message."""
        predicates = {}
        self.chat_counter += 1
        try:
            if message.lower() == "bye" or message.lower() == "good bye":
                reply = "Bye"
            else:
                
                self.extractor.process(message)  # Extract user social network from input
                print(f"--- INFO: Relations extracted. Message: {message}")

                reply = self.myBot.respond(message)

                self.memory.handle_semantic(message) # Use wordnet to create semantics
                print(f"--- INFO: Semantics handled. Message: {message}")

                # chat session and user-bot interaction || Same thing as saving the chat
                self.memory.handle_episodic(
                    uname=self.uname.capitalize(),
                    user=message.strip(), bot=reply.strip(), sequence=self.chat_counter
                )
                print(f"--- INFO: Chat saved. \n\t--- Message: {message}\n\t--- Reply: {reply}")

                predicates["obj1"] = self.myBot.getPredicate("obj1")
                predicates["rel"] = self.myBot.getPredicate("rel")
                predicates["obj2"] = self.myBot.getPredicate("obj2")
                predicates["operation"] = self.myBot.getPredicate("operation")

                if not None in predicates.values():
                    if predicates["operation"] == "current_user":
                        self.neo4j_handler.add_person(self.uname)
                        self.clear_predicates()
                    elif predicates["operation"] == "add_rel":
                        self.neo4j_handler.add_relationship(
                            self.gPredicates["user"], predicates["rel"], predicates["obj1"])
                        self.clear_predicates()
                    elif predicates["operation"] == "find_rel_user":
                        relatives = self.neo4j_handler.find_relation(
                            self.gPredicates["user"], predicates["rel"])
                        if relatives:
                            reply = reply % (', '.join(relatives))
                        else:
                            reply = f"Sorry, I don't have information about your {predicates['rel']}."
                        self.clear_predicates()

                    elif predicates["operation"] == "find_person":
                        person_to_find = predicates["obj1"].capitalize()
                        person_data = self.neo4j_handler.find_person(
                            person_to_find)
                        if person_data:
                            reply = reply % (person_data)
                        else:
                            reply = f"Sorry, I don't have information about {person_to_find}."
                        self.clear_predicates()
                self.save(message, reply)
            emotion = self.model(message)[0]["label"]
            return {"response": reply, "emotion": emotion}
        except Exception as e:
            print(f"An error occurred: {e}")
            return "Sorry, something went wrong while processing your message."

        
    def save(self, message, reply):
        """Saves the chat"""
        with open(os.path.join(self.docs_path, "history.txt"), "a") as file:
            file.write(f"User said: {message}\n")

        with open(os.path.join(self.docs_path, "history.txt"), "a") as file:
            file.write(f"Bot responded: {reply}\n")