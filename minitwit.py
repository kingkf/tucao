# -*- coding: utf-8 -*-
"""
    MiniTwit
    ~~~~~~~~

    A microblogging application written with Flask and sqlite3.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import time
from sqlite3 import dbapi2 as sqlite3
from datetime import datetime
from flask import Flask, request, session, url_for, redirect, \
     render_template, abort, g, flash, _app_ctx_stack, jsonify
import os


# configuration
path = os.path.dirname(os.path.abspath(__file__))
DATABASE = path + '/miniTwit.db'
PER_PAGE = 30
DEBUG = True
SECRET_KEY = 'development key'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('MINITWIT_SETTINGS', silent=True)


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    top = _app_ctx_stack.top
    if not hasattr(top, 'sqlite_db'):
        top.sqlite_db = sqlite3.connect(app.config['DATABASE'])
        top.sqlite_db.row_factory = sqlite3.Row
    return top.sqlite_db


@app.teardown_appcontext
def close_database(exception):
    """Closes the database again at the end of the request."""
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()


def init_db():
    """Creates the database tables."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def query_db(query, args=(), one=False):
    """Queries the database and returns a list of dictionaries."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv


def get_company_id(company_name):
    """Convenience method to look up the id for a username."""
    rv = query_db('select company_id from company where company_name= ?',
                  [company_name], one=True)
    return rv[0] if rv else None


def format_datetime(timestamp):
    """Format a timestamp for display."""
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d @ %H:%M')



    g.user = None
    if 'user_id' in session:
        g.user = query_db('select * from user where user_id = ?',
                          [session['user_id']], one=True)


@app.route('/')
def timeline():
    """Shows a users timeline or if no user is logged in it will
    redirect to the public timeline.  This timeline shows the user's
    messages as well as all the messages of followed users.
    """
    return redirect(url_for('public_timeline'))

@app.route('/public')
def public_timeline():
    """Displays the latest messages of all users."""
    return render_template('timeline.html', messages=query_db('''
        select message.*, company.* from message, company
        where message.company_id = company.company_id
        order by message.pub_date desc limit ?''', [PER_PAGE]), companys=query_db('''
        select company_name from company''')

        )


@app.route('/<company_name>')
def company_timeline(company_name):
    """Display's a company bullshit."""
    profile_company = query_db('select * from company where company_name= ?',
                            [company_name], one=True)
    if profile_company is None:
        abort(404)
    return render_template('timeline.html', messages=query_db('''
            select message.*, company.* from message, company where
            company.company_id= message.company_id and company.company_id= ?
            order by message.pub_date desc limit ?''',
            [profile_company['company_id'], PER_PAGE]),
            profile_company=profile_company,
            companys=query_db('''select company_name from company'''))


@app.route('/add_message/<company_id>', methods=['POST'])
def add_message(company_id):
    """post a new message for the company."""
    if request.form['text']:
        db = get_db()
        db.execute('''insert into message (company_id, text, pub_date)
          values (?, ?, ?)''', (company_id, request.form['text'],
                                int(time.time())))
        db.commit()
        flash('add success')
    return redirect(url_for('timeline'))



@app.route('/add_company', methods=['GET', 'POST'])
def add_company():
    """add the company"""
    error = None
    if request.method == 'POST':
        if not request.form['company_name']:
            error = 'You have to enter a company name'
        elif get_company_id(request.form['company_name']) is not None:
            error = 'The company name is already taken'
        else:
            db = get_db()
            db.execute('''insert into company(
              company_name) values (?)''',
              [request.form['company_name']])
            db.commit()
            flash('add success')
            return redirect(url_for('company_timeline', company_name=request.form['company_name']))
    return render_template('register.html', error=error)

@app.route('/show/comments/<message_id>/')
def show_comment(message_id):
    comments = query_db('''
    select * from comments where comments.message_id=?''', [message_id])
    print type(comments)
    commentdict={}
    for i in range(len(comments)):
        temp={}
        temp['text']=comments[i]['comment_text']
        temp['date']=comments[i]['pub_date']
        commentdict[str(i)]=temp
    return jsonify(**commentdict)

@app.route('/add/comment/<message_id>/', methods=['POST'])
def add_comment(message_id):
    message_id = int(message_id)
    if request.method == 'POST':
        text = request.form['text']
        db = get_db()
        db.execute('''insert into comments (comment_text, message_id, pub_date)
                      values (?,?,?)''', (text, message_id, int(time.time())))
        db.commit()
        return "success"



@app.route("/xxoo")
def xxoo():
    print 'xxx'
    return jsonify(a=1)

# add some filters to jinja
app.jinja_env.filters['datetimeformat'] = format_datetime


if __name__ == '__main__':
    init_db()
    app.run()
