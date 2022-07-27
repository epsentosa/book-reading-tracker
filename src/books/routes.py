from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import url_for
from flask import request
from flask import flash
from flask import session
from books import bcrypt
from books import mysql
from books.forms import RegistrationForm
from books.forms import LoginForm
from books.forms import SearchForm
from books.forms import AddBook
from books.forms import AddNote
from functools import wraps
from math import ceil


def is_logged_in(fn):
    @wraps(fn)
    def wrapper(*args,**kwargs):
        if "user" in session:
            return fn(*args,**kwargs)
        flash("Please login first")
        return redirect(url_for('site.login_page'))
    return wrapper


site = Blueprint('site',__name__,static_folder="static")

@site.route('/')
@site.route('/home',methods = ['POST','GET'])
@is_logged_in
def home_page():
    msg = f"Succesfully Login for user {session['user']}"
    return render_template("home.html",msg=msg)

@site.route('/register',methods = ['POST','GET'])
def register_page():
    if "user" in session:
        return redirect(url_for('site.home_page'))

    form = RegistrationForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data
        psswd_hash = bcrypt.generate_password_hash(password)
        with mysql.connection.cursor() as cursor:
            email_check = "SELECT email FROM members WHERE email = %s;"
            insert_query = "INSERT INTO members (full_name,email,password) VALUES (%s,%s,%s);"
            cursor.execute(email_check,(email,))
            is_registered = cursor.fetchone()
            if is_registered:
                flash("Email already registered.")
                return render_template("register.html",form=form)
            else:
                cursor.execute(insert_query,(name,email,psswd_hash))
                mysql.connection.commit()

        flash("Registation Successful, please login.",category='success')
        return redirect(url_for('site.login_page'))
    
    if form.errors: 
        for error in form.errors.values():
            flash(error[0])

    return render_template("register.html",form=form)

@site.route('/login',methods = ['POST','GET'])
def login_page():
    if "user" in session:
        return redirect(url_for('site.home_page'))

    form = LoginForm()
    if request.method == "POST":
        email = form.email.data
        password = form.password.data
        with mysql.connection.cursor() as cursor:
            email_check = "SELECT email FROM members WHERE email = %s;"
            password_check = "SELECT password FROM members WHERE email = %s;"
            name = "SELECT member_id,full_name FROM members WHERE email = %s;"
            cursor.execute(email_check,(email,))
            is_email = cursor.fetchone()
            if is_email:
                cursor.execute(password_check,(email,))
                password_check = cursor.fetchone()[0]
                is_password = bcrypt.check_password_hash(password_check,password)
                if is_password:
                    cursor.execute(name,(email,))
                    user = cursor.fetchone()
                    member_id = user[0]
                    name = user[1]
                    session['user'] = name
                    session['id'] = member_id
                    return redirect(url_for('site.home_page'))
                flash("Wrong Password, try again")

            else:
                flash("Email Not Found, please register")
                
    return render_template("login.html",form=form)

@site.route('/logout')
def logout():
    session.pop('user',None)
    return redirect(url_for('site.home_page'))

@site.route('/search',methods = ['POST','GET'])
@site.route('/search/<keyword>/page/<int:index>',methods = ['POST','GET'])
@is_logged_in
def search(index = 1, keyword = None):

    def create_result(title,start_page,result_per_page):
        with mysql.connection.cursor() as cursor:
            search_query = """SELECT b.book_id,b.title,b.num_pages,b.publication_date,
                              b.isbn,p.name,a.name,m.full_name
                              FROM books b LEFT JOIN publishers p ON b.publisher_id = p.publisher_id 
                              LEFT JOIN authors a ON b.author_id = a.author_id 
                              LEFT JOIN members m ON b.added_by = m.member_id
                              WHERE b.title LIKE '%%%s%%'""" % title
            cursor.execute(search_query + "LIMIT %s,%s" % (start_page,result_per_page))
            result = cursor.fetchall()
            return result

    search_form = SearchForm()
    add_book = AddBook()
    start_page = (index * 10) - 10
    result_per_page = 10

    if keyword:
        title = keyword
        
        total_query_result = session["total_query"]
        total_pages = session["total_pages"]
            
        result = create_result(title,start_page,result_per_page)

        return render_template('search.html',form=search_form,form_book=add_book,result=result, \
                keyword = title,total_query=total_query_result,total_pages=total_pages, \
                start_page=start_page,current_page=index)

    session.pop('total_query',None)
    session.pop('total_pages',None)
    # below session for passing when add book byself and automatically add to collection,
    # to show difference flashed in collection
    session['add_book_byself'] = False
    return render_template('search.html',form=search_form,form_book=add_book)

@site.route('/searching',methods = ['POST'])
@is_logged_in
def searching():
    title = request.form.get('search')
    index = request.form.get('page',1)
    result_per_page = 10
    
    if title:
        # below to check if there is some input with single quotation or percent, to prevent SQL SYNTAX error 
        title = title.replace("\'","\\'")
        title = title.replace("%","\%")
        # best solution i found so far
        with mysql.connection.cursor() as cursor:
            search_query = "SELECT * FROM books WHERE title LIKE '%%%s%%'" % title
            cursor.execute(search_query)
            total_query_result = cursor.rowcount
            total_pages = ceil(total_query_result/result_per_page)
            if total_query_result == 0:
                flash("No Data Found")
    
        session['search'] = title
        session["total_query"] = total_query_result
        session["total_pages"] = total_pages

    else:
        total_pages = session['total_pages']
        if int(index) > total_pages:
            flash("Out of range pages",category="out_range")
        title = session['search']

    return redirect(url_for('site.search',keyword = title, index = index))

@site.route('/add_book',methods = ["POST"])
def add_book():

    def query_check_or_add(name,table):
        if table == "publishers":
            query_check = "SELECT publisher_id FROM publishers WHERE name = %s;"
            query_add = "INSERT INTO publishers (name) VALUES (%s);"
        else:
            query_check = "SELECT author_id FROM authors WHERE name = %s;"
            query_add = "INSERT INTO authors (name) VALUES (%s);"

        cursor.execute(query_check,(name,))
        id = cursor.fetchone()
        if id:
            return id

        cursor.execute(query_add,(name,))
        mysql.connection.commit()
        cursor.execute(query_check,(name,))
        id = cursor.fetchone()
        return id

    member_id = session['id']
    form = AddBook()
    if form.validate_on_submit():
        title = form.title.data
        num_pages = form.num_pages.data
        publication_date = form.publication_date.data
        isbn = form.isbn.data
        publisher = form.publisher.data
        author = form.author.data

        with mysql.connection.cursor() as cursor:
            title_check = "SELECT book_id FROM books WHERE title = %s;"
            insert_query = """INSERT INTO books (title,num_pages,publication_date,
                            isbn,publisher_id,author_id,added_by) 
                            VALUES (%s,%s,%s,%s,%s,%s,%s);"""
            cursor.execute(title_check,(title,))
            is_registered = cursor.fetchone()
            if is_registered:
                flash("Book already in Database.")
                return redirect(url_for('site.search'))

            publisher_id = query_check_or_add(publisher,'publishers')
            author_id = query_check_or_add(author,'authors')
            cursor.execute(insert_query,(title,num_pages,publication_date,isbn,publisher_id,author_id, \
                           member_id))
            mysql.connection.commit()

            # this run the query again to take book_id and passing to add_collection
            cursor.execute(title_check,(title,))
            is_registered = cursor.fetchone()

        session['add_book_byself'] = True
        return redirect(url_for('site.add_collection',book_id = is_registered ))
    
    if form.errors: 
        for error in form.errors.values():
            flash(error[0])

    return redirect(url_for('site.search'))

@site.route('/add_collection/<int:book_id>',methods = ['GET','POST'])
def add_collection(book_id):

    member_id = session['id']
    with mysql.connection.cursor() as cursor:
        book_id_check = "SELECT book_id FROM collections WHERE member_id = %s and book_id = %s;"
        insert_query = "INSERT INTO collections (member_id,book_id) VALUES (%s,%s);"
        cursor.execute(book_id_check,(member_id,book_id))
        is_registered = cursor.fetchone()
        if is_registered:
            flash("Book already in Your Collections.")
            return redirect(url_for('site.collection'))

        cursor.execute(insert_query,(member_id,book_id))
        mysql.connection.commit()

    add_book_byself = session['add_book_byself']
    if add_book_byself:
        flash("Book Registration Successful, added automatically to your Collection",category='success')
    else:
        flash("New book added to Collections",category='success')
    return redirect(url_for('site.collection'))

"""
function for collection use
"""
def count_collection(member_id,title,result_per_page):
    with mysql.connection.cursor() as cursor:
        collection_query = """ SELECT b.title,b.num_pages FROM books b
                        INNER JOIN collections c ON c.book_id = b.book_id
                        INNER JOIN members m ON c.member_id = m.member_id
                        where c.member_id = %s and b.title LIKE '%%%s%%' """ % (member_id,title)
        cursor.execute(collection_query)
        total_collection = cursor.rowcount
        total_pages = ceil(total_collection/result_per_page)
        return (total_collection,total_pages)
    
@site.route('/collection',methods = ['GET','POST'])
@site.route('/collection/page/<int:index>',methods = ['GET','POST'])
@site.route('/collection/search/<keyword>/page/<int:index>',methods = ['GET','POST'])
@is_logged_in
def collection(index = 1,keyword = None):

    search_form = SearchForm()
    start_page = (index * 10) - 10
    result_per_page = 10

    def create_result(member_id,start_page,result_per_page,title):
        with mysql.connection.cursor() as cursor:
            search_query = """ SELECT b.book_id,b.title,b.num_pages,b.publication_date,b.isbn, 
                            p.name,a.name,m_add.full_name,COUNT(n.book_id) FROM books b
                            LEFT JOIN publishers p ON b.publisher_id = p.publisher_id 
                            LEFT JOIN authors a ON b.author_id = a.author_id 
                            LEFT JOIN members m_add ON b.added_by = m_add.member_id
                            INNER JOIN collections c ON c.book_id = b.book_id
                            INNER JOIN members m ON c.member_id = m.member_id
                            LEFT JOIN notes n ON m.member_id = n.member_id AND b.book_id = n.book_id
                            where c.member_id = %s and b.title LIKE '%%%s%%' 
                            GROUP BY book_id """ % (member_id,title)
            cursor.execute(search_query + "LIMIT %s,%s" % (start_page,result_per_page))
            result = cursor.fetchall()
            return result

    member_id = session["id"]
    title = ''

    if keyword:
        title = keyword
        total_collection = session["total_query"]
        total_pages = session["total_pages"]
        on_search = session["on_search"]

        global_total_collection = session["global_total_query"]
        result = create_result(member_id,start_page,result_per_page,title)
        return render_template('collection.html',form=search_form,result=result,total_pages=total_pages, \
                start_page=start_page,total_query=total_collection,current_page=index,keyword = title, \
                global_total_query=global_total_collection,on_search=on_search)


    total_collection = count_collection(member_id,title,result_per_page)[0]
    global_total_collection = total_collection
    total_pages = count_collection(member_id,title,result_per_page)[1]
    on_search = False

    result = create_result(member_id,start_page,result_per_page,title)

    session["search"] = title
    session["total_query"] = total_collection
    session["total_pages"] = total_pages
    session["on_search"] = on_search 
    session["global_total_query"] = global_total_collection

    return render_template('collection.html',form=search_form,result=result,total_pages=total_pages, \
            start_page=start_page,total_query=total_collection,current_page=index,keyword = title, \
            global_total_query=global_total_collection,on_search=on_search)

@site.route('/collection_searching',methods = ['POST'])
def collection_searching():
    member_id = session["id"]
    title = request.form.get('search')
    index = request.form.get('page',1)
    result_per_page = 10
    on_search = session['on_search']

    if title or on_search:
        on_search = True
        if title:
            # below to check if there is some input with single quotation or percent,
            # to prevent SQL SYNTAX error 
            title = title.replace("\'","\\'")
            title = title.replace("%","\%")
            # best solution i found so far
        else:
            title = session['search']
        total_collection = count_collection(member_id,title,result_per_page)[0]
        total_pages = count_collection(member_id,title,result_per_page)[1]
        if total_collection == 0:
            flash("No Data Found")

        session["search"] = title
        session["total_query"] = total_collection
        session["total_pages"] = total_pages
        session["on_search"] = on_search 

        return redirect(url_for('site.collection', keyword = title, index = index))
    else:
        return redirect(url_for('site.collection', index = index))

@site.route('/collection/delete/<int:book_id>',methods = ['POST'])
def delete_collection(book_id):

    member_id = session['id']
    if request.method == "POST":

        with mysql.connection.cursor() as cursor:
            title_query = "SELECT title FROM books WHERE book_id = %s;"
            delete_collection_query = "DELETE FROM collections WHERE member_id = %s and book_id = %s;"
            delete_note_query = "DELETE FROM notes WHERE member_id = %s and book_id = %s;"
            cursor.execute(title_query,(book_id,))
            book_title = cursor.fetchone()
            cursor.execute(delete_collection_query,(member_id,book_id))
            cursor.execute(delete_note_query,(member_id,book_id))
            mysql.connection.commit()

        flash(f"-->{book_title[0]}<-- has deleted from your Collections",category='success')
        return redirect(url_for('site.collection'))

@site.route('/note',methods = ['GET','POST'])
@is_logged_in
def note_page():
    member_id = session['id']

    with mysql.connection.cursor() as cursor:
        notes_query = """SELECT n.note_id,b.title,n.num_page,n.title,n.description FROM notes n
                        LEFT JOIN books b ON n.book_id = b.book_id WHERE n.member_id = %s
                        ORDER BY note_id DESC;"""
        cursor.execute(notes_query,(member_id,))
        total_note = cursor.rowcount
        result = cursor.fetchall()

    return render_template('notes.html',total_note=total_note,result=result)


@site.route('/note/add/<int:book_id>',methods = ['GET','POST'])
@is_logged_in
def add_note(book_id):
    add_note = AddNote()

    with mysql.connection.cursor() as cursor:
        title_query = "SELECT title,num_pages FROM books WHERE book_id = %s;"
        cursor.execute(title_query,(book_id,))
        result = cursor.fetchone()
        book_title = result[0]
        num_pages = result[1]

    if add_note.validate_on_submit():
        member_id = session['id']
        num_page = add_note.num_page.data
        title = add_note.title.data
        description = add_note.description.data
        with mysql.connection.cursor() as cursor:
            addNote_query = """INSERT INTO notes VALUES (DEFAULT,%s,%s,%s,%s,%s);"""
            cursor.execute(addNote_query,(member_id,book_id,num_page,title,description))
            mysql.connection.commit()

        flash("New note added",category='success')
        return redirect(url_for('site.note_page'))

    return render_template('add_note.html',form = add_note, book_title = book_title, \
            num_pages = num_pages)

@site.route('/note/delete/<int:note_id>',methods = ['POST'])
def delete_note(note_id):

    member_id = session['id']
    if request.method == "POST":

        with mysql.connection.cursor() as cursor:
            check_query = "SELECT title FROM notes WHERE note_id = %s;"
            delete_query = "DELETE FROM notes WHERE member_id = %s and note_id = %s;"
            cursor.execute(check_query,(note_id,))
            note_title = cursor.fetchone()
            cursor.execute(delete_query,(member_id,note_id))
            mysql.connection.commit()

        flash(f"-->{note_title[0]}<-- has deleted from your Notes",category='success')
        return redirect(url_for('site.note_page'))

@site.route('/collection/<int:book_id>',methods = ['POST','GET'])
@is_logged_in
def detail_book(book_id):
    book_id = book_id
    member_id = session['id']
    path_to_back = request.referrer

    with mysql.connection.cursor() as cursor:
        book_query = """ SELECT b.book_id,b.title,b.num_pages,b.publication_date,b.isbn, 
                        p.name,a.name,m_add.full_name,COUNT(n.book_id) FROM books b
                        LEFT JOIN publishers p ON b.publisher_id = p.publisher_id 
                        LEFT JOIN authors a ON b.author_id = a.author_id 
                        LEFT JOIN members m_add ON b.added_by = m_add.member_id
                        INNER JOIN collections c ON c.book_id = b.book_id
                        INNER JOIN members m ON c.member_id = m.member_id
                        LEFT JOIN notes n ON m.member_id = n.member_id AND b.book_id = n.book_id
                        where c.member_id = %s and b.book_id = %s
                        GROUP BY book_id; """
        notes_query = """SELECT n.note_id,b.title,n.num_page,n.title,n.description FROM notes n
                        LEFT JOIN books b ON n.book_id = b.book_id WHERE n.member_id = %s
                        and n.book_id = %s ORDER BY note_id DESC;"""

        cursor.execute(book_query,(member_id,book_id))
        book_result = cursor.fetchall()

        cursor.execute(notes_query,(member_id,book_id))
        total_note = cursor.rowcount
        note_result = cursor.fetchall()
        return render_template('detail_book.html',book_result = book_result, note_result = note_result, \
                total_note = total_note, path = path_to_back)

    #TODO
    # continue mockup of note_page, change footer style
    # make constrain in show description notes
    # make notes editable
    # make some real note on books!!
