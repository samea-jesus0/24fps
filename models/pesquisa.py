from app import db

class Search(db.Model):
    __tablename__ = "searches"

    id = db.Column(db.Integer, primary_key=True)
    movie_name = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<Search {self.movie_name}>"