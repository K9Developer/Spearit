from databases import engine
from databases.base import Base
from spear_head import SpearHead

def main():
    # TODO: use alembic when database structure is stable
    print("REMEMBER: If changed table, delete DB file to recreate!")
    Base.metadata.create_all(engine.engine)
    sh = SpearHead()
    sh.start()


if __name__ == "__main__":
    main()