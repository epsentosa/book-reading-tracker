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
from math import ceil

site = Blueprint('site',__name__,static_folder="static")

@site.route('/')
@site.route('/home',methods = ['POST','GET'])
def home_page():
    if "user" in session:
        msg = f"Succesfully Login for user {session['user']}"

        return render_template("home.html",msg=msg)

    return redirect(url_for('site.login_page'))

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
            name = "SELECT full_name FROM members WHERE email = %s;"
            cursor.execute(email_check,(email,))
            is_email = cursor.fetchone()
            if is_email:
                cursor.execute(password_check,(email,))
                password_check = cursor.fetchone()[0]
                is_password = bcrypt.check_password_hash(password_check,password)
                if is_password:
                    cursor.execute(name,(email,))
                    name = cursor.fetchone()[0]
                    session['user'] = name
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
@site.route('/search/page/<int:i>',methods = ['POST','GET'])
def search(i = 1):
    if "user" not in session:
        return redirect(url_for('site.home_page'))

    form = SearchForm()
    start_page = (i * 10) - 10
    result_per_page = 10
    if request.method == "POST":

        def create_result(title,start_page,result_per_page):
            with mysql.connection.cursor() as cursor:
                search_query = """ SELECT b.book_id,b.tittle,b.num_pages,b.publication_date,b.isbn,p.name,a.name FROM books b 
                                    LEFT JOIN publishers p ON b.publisher_id = p.publisher_id 
                                    LEFT JOIN authors a ON b.author_id = a.author_id 
                                    WHERE b.tittle LIKE '%%%s%%'""" % title
                cursor.execute(search_query + "LIMIT %s,%s" % (start_page,result_per_page))
                result = cursor.fetchall()
                return result

        title = form.search.data
        if title:
            i, start_page = 1, 0
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
        
            session["search"] = title
            session["total_query"] = total_query_result
            session["total_pages"] = total_pages

        else:
            title = session["search"]
            total_query_result = session["total_query"]
            total_pages = session["total_pages"]
            
        result = create_result(title,start_page,result_per_page)

        return render_template('search.html',form=form,result=result,total_query=total_query_result,total_pages=total_pages,start_page=start_page,current_page=i)

    session.pop('search',None)
    session.pop('total_query',None)
    session.pop('total_pages',None)
    return render_template('search.html',form=form)

    # TODO --> Define Add Book if no result
