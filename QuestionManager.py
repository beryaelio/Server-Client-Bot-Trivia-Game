import os
import random
import importlib.util


class QuestionManager:
    """
    A class that manages the connection between the Questions and the game server.
    """
    def __init__(self, questions_filename='questions.py'):
        # Dynamically set the path to the questions file
        dir_path = os.path.dirname(os.path.realpath(__file__))  # Gets the directory where this script is located
        self.question_file = os.path.join(dir_path, questions_filename)
        self.questions = []
        self.load_questions()
        self.current_question = None

    def load_questions(self):
        """Loads the questions from the Question.py file"""
        try:
            spec = importlib.util.spec_from_file_location("questions_module", self.question_file)
            questions_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(questions_module)
            self.questions = questions_module.questions  # Make sure this line correctly assigns the questions
        except Exception as e:
            print(f"Error loading questions: {e}")

    def get_random_question(self):
        """Returns a random question from the questions"""
        if self.questions:
            self.current_question = random.choice(self.questions)
            return self.current_question['question']
        else:
            return "No questions available."

    def get_correct_answer(self):
        """returns the correct answer for the current question"""
        if self.current_question:
            return self.current_question['answer']
        else:
            return "No question has been asked."
