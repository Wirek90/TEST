'''Flask stuff (server, routes, request handling, session, etc.)
This layer should only consist of logic that is hardly related to Flask.'''

from flask import Flask, render_template, request, redirect, url_for
import persistence
import logic
import util
from flask_bootstrap import Bootstrap

app = Flask(__name__)
bootstrap = Bootstrap(app)


@app.route('/')
@app.route('/list')
def list_questions():
    questions = persistence.get_all_items('question')
    questions = logic.sort_list_of_dicts_by_time(questions)
    labels = logic.get_list_of_headers(questions)
    return render_template('list_questions.html', questions=questions, labels=labels, search=False)


@app.route('/new-question')
def new_question():
    return render_template('ask_question.html')


@app.route('/new-question', methods=["POST"])
def submit_question():
    dict = logic.question_dict(request.form["title"], request.form["question"])
    persistence.add_row_to_db(dict, "question")
    return redirect('/list')


@app.route('/question/<int:question_id>/new-comment', methods=["GET", "POST"])
def new_question_comment(question_id=None):
    if request.method == "GET":
        question = persistence.get_item_by_id("question", question_id)
        return render_template('add_comment.html', question=question, question_id=question_id)
    if request.method == "POST":
        dict = logic.comment_dict(request.form["comment"], question_id=question_id)
        persistence.add_row_to_db(dict, "comment")
        return redirect('/question/' + str(question_id))


@app.route('/question/<int:question_id>/answer/<int:answer_id>/new-comment', methods=["GET", "POST"])
def new_answer_comment(question_id=None, answer_id=None):
    if request.method == "GET":
        answer = persistence.get_item_by_id("answer", answer_id)
        return render_template('add_comment.html', answer=answer, answer_id=answer_id, question_id=question_id)
    if request.method == "POST":
        dict = logic.comment_dict(request.form["comment"], answer_id=answer_id, question_id=question_id)
        persistence.add_row_to_db(dict, "comment")
        return redirect('/question/' + str(question_id))


@app.route('/comments/<comment_id>/edit', methods=["GET", "POST"])
def edit_comment(comment_id=None):
    question_comment = persistence.get_item_by_id("comment", comment_id)
    question_id = question_comment[0]['question_id']
    question = persistence.get_item_by_id("question", question_id)
    if request.method == "GET":
        return render_template('add_comment.html',
                               question_comment=question_comment,
                               question=question,
                               question_id=question_id)
    if request.method == "POST":
        question_comment[0]['message'] = request.form["comment"]
        persistence.edit_comment(question_comment)
        return redirect('/question/' + str(question_id))


@app.route('/question/<int:question_id>/answer/<int:answer_id>/accept', methods=["POST"])
def accept_answer(question_id=None, answer_id=None):
    persistence.accept_answer(answer_id)
    return redirect('/question/' + str(question_id))


@app.route('/question/<int:question_id>/new-answer')
def write_answer(question_id=None):
    questions = persistence.get_item_by_id("question", question_id)
    user_list = logic.show_the_users()
    return render_template('post_answer.html', questions=questions,
                           question_id=question_id, user_list=user_list)


@app.route('/question/<int:question_id>/new-answer', methods=['POST'])
def submit_answer(question_id):
    dict = logic.answer_dict(question_id, request.form['answer'])
    persistence.add_row_to_db(dict, "answer")
    return redirect('/question/' + str(question_id))


@app.route('/question/<int:question_id>/delete')
def delete_question(question_id=None):
    persistence.delete_item('question', question_id)
    return redirect('/')


@app.route('/comments/<int:comment_id>/delete')
def delete_comment(comment_id=None):
    question_id = persistence.get_item_by_id('comment', comment_id)[0]["question_id"]
    persistence.delete_item('comment', comment_id)
    return redirect('/question/' + str(question_id))


@app.route('/question/<question_id>')
def view_question(question_id=None):
    question = persistence.get_item_by_id("question", question_id)
    questions_answer = persistence.get_item_by_foreign_key('answer', question_id, "question_id")
    question_comment = persistence.get_item_by_foreign_key('comment', question_id, "question_id")
    answer_ids = logic.get_answer_ids(questions_answer)
    answer_comment = logic.get_answer_comments(answer_ids)
    labels = logic.get_list_of_headers(question)
    labels_answer = logic.get_list_of_headers(questions_answer)
    labels_question_comment = logic.get_list_of_headers(question_comment)
    labels_answer_comment = logic.get_list_of_headers(answer_comment)
    return render_template('display_question.html',
                           question=question,
                           questions_answer=questions_answer,
                           labels=labels,
                           question_id=question_id,
                           labels_answer=labels_answer,
                           question_comment=question_comment,
                           answer_comment=answer_comment,
                           labels_question_comment=labels_question_comment,
                           labels_answer_comment=labels_answer_comment)


@app.route('/question/<int:question_id>/vote-up')
def vote_question_up(question_id=None):
    logic.vote_question(question_id, True)
    return redirect('/question/' + str(question_id))


@app.route('/question/<int:question_id>/vote-down')
def vote_question_down(question_id=None):
    logic.vote_question(question_id, False)
    return redirect('/question/' + str(question_id))


@app.route('/question/<int:question_id>/<int:answer_id>/vote-up')
def vote_answer_up(question_id=None, answer_id=None):
    logic.vote_answer(answer_id, True)
    return redirect('/question/' + str(question_id))


@app.route('/question/<int:question_id>/<int:answer_id>/vote-down')
def vote_answer_down(question_id=None, answer_id=None):
    logic.vote_answer(answer_id, False)
    return redirect('/question/' + str(question_id))


@app.route('/search', methods=["POST", "GET"])
def search():
    questions = persistence.search(query=request.form)
    if questions:
        questions = logic.sort_list_of_dicts_by_time(questions)
        labels = logic.get_list_of_headers(questions)
        return render_template('list_questions.html', questions=questions, labels=labels, search=True)
    else:
        return render_template('search_failed.html', term=request.form['query'])


@app.route('/registration', methods=["POST", "GET"])
def user_registration():
    if request.method == "GET":
        return render_template("registration.html")
    if request.method == "POST":
        name = request.form['username']
        logic.register_user(name)
        return redirect('/')


@app.route('/view_users')
def view_users():
    labels=util.US_FIELDS
    users = persistence.view_users()
    return render_template('list_users.html', labels=labels, users=users)





if __name__ == '__main__':
    app.secret_key = 'some_key'
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=True,
    )
