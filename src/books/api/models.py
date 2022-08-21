from sqlalchemy.ext.automap import automap_base
from books.api import engine

Base = automap_base()

Base.prepare(autoload_with=engine)
table = Base.classes

Authors = table.authors
Books = table.books
Collections = table.collections
Members = table.members
Notes = table.notes
Publishers = table.publishers
