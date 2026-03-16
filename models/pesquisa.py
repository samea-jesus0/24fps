from extensions import db

class Search(db.Model):
    __tablename__ = "pesquisas"

    id = db.Column(db.Integer, primary_key=True)
    movie_name = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<Pesquisa {self.movie_name}>"