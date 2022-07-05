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
                    user_id = user[0]
                    name = user[1]
                    session['user'] = name
                    session['id'] = user_id
                    return redirect(url_for('site.home_page'))
                flash("Wrong Password, try again")

            else:
                flash("Email Not Found, please register")
                
    return render_template("login.html",form=form)

@site.route('/logout')
def logout():
    session.pop('user',None)
    return redirect(url_for('site.home_page'))

@site.route('/search_result',methods = ['POST'])
@is_logged_in
def search_result():
    if request.method == "POST":
        title = request.form.get('search')
        index = request.form.get('page',1)
        result_per_page = 10
        
        if title:
            # below to check if there is some input with single quotation or percent, to prevent SQL SYNTAX error 
            title = title.replace("\'","\\'")
            title = title.replace("%","\%")
            # best solution i found so far
            with mysql.connection.cursor() as cursor:
                search_query = "SELECT * FROM books WHERE tittle LIKE '%%%s%%'" % title
                cursor.execute(search_query)
                total_query_result = cursor.rowcount
                total_pages = ceil(total_query_result/result_per_page)
                if total_query_result == 0:
                    flash("No Data Found")
        
            session['search'] = title
            session["total_query"] = total_query_result
            session["total_pages"] = total_pages

        else:
            title = session['search']

        return redirect(url_for('site.search',keyword = title, i = index))

@site.route('/search',methods = ['POST','GET'])
@site.route('/search/<keyword>/page/<int:i>',methods = ['POST','GET'])
@is_logged_in
def search(i = 1, keyword = None):
    search_form = SearchForm()
    add_book = AddBook()
    start_page = (i * 10) - 10
    result_per_page = 10
    print(i, keyword)

    def create_result(title,start_page,result_per_page):
        with mysql.connection.cursor() as cursor:
            search_query = """ SELECT b.book_id,b.tittle,b.num_pages,b.publication_date,b.isbn,p.name,a.name,m.full_name
                                FROM books b LEFT JOIN publishers p ON b.publisher_id = p.publisher_id 
                                LEFT JOIN authors a ON b.author_id = a.author_id 
                                LEFT JOIN members m ON b.added_by = m.member_id
                                WHERE b.tittle LIKE '%%%s%%'""" % title
            cursor.execute(search_query + "LIMIT %s,%s" % (start_page,result_per_page))
            result = cursor.fetchall()
            return result

    if keyword:
        title = keyword
        
        total_query_result = session["total_query"]
        total_pages = session["total_pages"]
            
        result = create_result(title,start_page,result_per_page)

        return render_template('search.html',form=search_form,form_book=add_book,result=result, \
                total_query=total_query_result,total_pages=total_pages,start_page=start_page,current_page=i)

    session.pop('total_query',None)
    session.pop('total_pages',None)
    return render_template('search.html',form=search_form,form_book=add_book)

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
        tittle = form.tittle.data
        num_pages = form.num_pages.data
        publication_date = form.publication_date.data
        isbn = form.isbn.data
        publisher = form.publisher.data
        author = form.author.data

        with mysql.connection.cursor() as cursor:
            tittle_check = "SELECT tittle FROM books WHERE tittle = %s;"
            insert_query = """INSERT INTO books (tittle,num_pages,publication_date,
                            isbn,publisher_id,author_id,added_by) 
                            VALUES (%s,%s,%s,%s,%s,%s,%s);"""
            cursor.execute(tittle_check,(tittle,))
            is_registered = cursor.fetchone()
            if is_registered:
                flash("Book already in Database.")
                return redirect(url_for('site.search'))

            publisher_id = query_check_or_add(publisher,'publishers')
            author_id = query_check_or_add(author,'authors')
            cursor.execute(insert_query,(tittle,num_pages,publication_date,isbn,publisher_id,author_id,member_id))
            mysql.connection.commit()

        flash("Book Registration Successful",category='success')
        # return redirect(url_for('site.collections'))
        return redirect(url_for('site.search'))
    
    if form.errors: 
        for error in form.errors.values():
            flash(error[0])

    return redirect(url_for('site.search'))

@site.route('/add_collection/<int:book_id>',methods = ['POST'])
def add_collection(book_id):

    member_id = session['id']
    if request.method == "POST":

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

        flash("New book added to Collections",category='success')
        return redirect(url_for('site.collection'))
    
@site.route('/collections',methods = ['GET','POST'])
@site.route('/collections/page/<int:i>',methods = ['GET','POST'])
@is_logged_in
def collection(i = 1):

    search_form = SearchForm()
    start_page = (i * 10) - 10
    result_per_page = 10

    def create_result(user_id,start_page,result_per_page,tittle):
        with mysql.connection.cursor() as cursor:
            search_query = """ SELECT b.book_id,b.tittle,b.num_pages,b.publication_date,b.isbn, 
                            p.name,a.name,m_add.full_name FROM books b
                            LEFT JOIN publishers p ON b.publisher_id = p.publisher_id 
                            LEFT JOIN authors a ON b.author_id = a.author_id 
                            LEFT JOIN members m_add ON b.added_by = m_add.member_id
                            INNER JOIN collections c ON c.book_id = b.book_id
                            INNER JOIN members m ON c.member_id = m.member_id
                            where c.member_id = %s and b.tittle LIKE '%%%s%%' """ % (user_id,tittle)
            cursor.execute(search_query + "LIMIT %s,%s" % (start_page,result_per_page))
            result = cursor.fetchall()
            return result

    def count_collection(user_id,tittle):
        with mysql.connection.cursor() as cursor:
            collection_query = """ SELECT b.tittle,b.num_pages FROM books b
                            INNER JOIN collections c ON c.book_id = b.book_id
                            INNER JOIN members m ON c.member_id = m.member_id
                            where c.member_id = %s and b.tittle LIKE '%%%s%%' """ % (user_id,tittle)
            cursor.execute(collection_query)
            total_collection = cursor.rowcount
            total_pages = ceil(total_collection/10)
            return (total_collection,total_pages)

    user_id = session["id"]
    tittle = ''

    if request.method == "POST":
        tittle = search_form.search.data
        if tittle:
            i, start_page = 1, 0
            on_search = True
            # below to check if there is some input with single quotation or percent, to prevent SQL SYNTAX error 
            tittle = tittle.replace("\'","\\'")
            tittle = tittle.replace("%","\%")
            # best solution i found so far
            total_collection = count_collection(user_id,tittle)[0]
            total_pages = count_collection(user_id,tittle)[1]
            if total_collection == 0:
                flash("No Data Found")

            session["search"] = tittle
            session["total_query"] = total_collection
            session["total_pages"] = total_pages
            session["on_search"] = on_search 

        else:
            tittle = session["search"]
            total_collection = session["total_query"]
            total_pages = session["total_pages"]
            on_search = session["on_search"]

        global_total_collection = session["global_total_query"]
        result = create_result(user_id,start_page,result_per_page,tittle)
        return render_template('collection.html',form=search_form,result=result,total_pages=total_pages, \
                start_page=start_page,total_query=total_collection,current_page=i, \
                global_total_query=global_total_collection,on_search=on_search)


    total_collection = count_collection(user_id,tittle)[0]
    global_total_collection = total_collection
    total_pages = count_collection(user_id,tittle)[1]
    on_search = False
    
    result = create_result(user_id,start_page,result_per_page,tittle)

    session["search"] = tittle
    session["total_query"] = total_collection
    session["total_pages"] = total_pages
    session["on_search"] = on_search 
    session["global_total_query"] = global_total_collection

    return render_template('collection.html',form=search_form,result=result,total_pages=total_pages, \
            start_page=start_page,total_query=total_collection,current_page=i, \
            global_total_query=global_total_collection,on_search=on_search)

@site.route('/delete_collection/<int:book_id>',methods = ['POST'])
def delete_collection(book_id):

    member_id = session['id']
    if request.method == "POST":

        with mysql.connection.cursor() as cursor:
            check_query = "SELECT tittle FROM books WHERE book_id = %s;"
            delete_query = "DELETE FROM collections WHERE member_id = %s and book_id = %s;"
            cursor.execute(check_query,(book_id,))
            book_tittle = cursor.fetchone()
            cursor.execute(delete_query,(member_id,book_id))
            mysql.connection.commit()

        flash(f"-->{book_tittle[0]}<-- has deleted from your Collections",category='success')
        return redirect(url_for('site.collection'))

    # TODO
    # Design and Create Note Pages
    # Make dinamic search value when next page
    # refactor and make clean pagination
