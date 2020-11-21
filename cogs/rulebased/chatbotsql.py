import jellyfish
import sqlite3
import functools
import operator

similarity_treshold = 0.2

welcome = "Hi! I'm Arthur, the customer support chatbot. How can I help you?"

questions = (
    "The app if freezing after I click run button",
    "I don't know how to proceed with the invoice",
    "I get an error when I try to install the app",
    "It crash after I have updated it",
    "I cannot login in to the app",
    "I'm not able to download it"
            )

answers = (
        "You need to clean up the cache. Please go to ...",
        "Please go to Setting, next Subscriptions and there is the Billing section",
        "Could you plese send the log files placed in ... to ...",
        "Please restart your PC",
        "Use the forgot password button to setup a new password",
        "Probably you have an ad blocker plugin installed and it blocks the popup with the download link"
            )

default_answer = "The issues has been saved. We will contact you soon."

def initialize_database(db):
    conn = sqlite3.connect(db)
    conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS data USING fts5(question, answer);")
    cur = conn.cursor()

    for index, question in enumerate(questions):
        cur.execute("INSERT INTO data(question, answer) VALUES(?, ?);", (question, answers[index]))

    query = cur.execute("SELECT question,answer FROM data;")
    
    return cur

def get_highest_similarity(customer_question, cur):
    sql = "SELECT answer FROM data WHERE question LIKE ? LIMIT 1"
    cur.execute(sql, ["%"+customer_question+"%"])
    answer = cur.fetchall()

    if len(answer) > 0:
        return functools.reduce(operator.iconcat, answer)
    else:
        return default_answer

def run_chatbot(cur):
    print(welcome)
    question = ""
    while question != "thank you":
        question = input()
        answer = get_highest_similarity(question, cur)
        print(answer)

cur = initialize_database("chatbot.sqlite")
run_chatbot(cur)