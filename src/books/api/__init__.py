from flask_restful import Api
from flask_restful import Resource
from flask import jsonify
from books import mysql

class Search(Resource):
    def get(self,title):
        result = self.create_result(title)
        content = []
        for book_id,title,num_pages,pub_date,isbn,publisher,author,added_by in result:
            res = {"book_id":book_id,"title":title,"num_pages":num_pages,"pub_date":pub_date,
                    "isbn":isbn,"publisher":publisher,"author":author,"added_by":added_by}
            content.append(res)
            
        return jsonify(content)

    def create_result(self,title):
        with mysql.connection.cursor() as cursor:
            search_query = """SELECT b.book_id,b.title,b.num_pages,b.publication_date,
                              b.isbn,p.name,a.name,m.full_name
                              FROM books b LEFT JOIN publishers p ON b.publisher_id = p.publisher_id 
                              LEFT JOIN authors a ON b.author_id = a.author_id 
                              LEFT JOIN members m ON b.added_by = m.member_id
                              WHERE b.title LIKE '%%%s%%'""" % title
            cursor.execute(search_query)
            result = cursor.fetchall()
            return result

api = Api()

api.add_resource(Search,"/api/search/<string:title>")
