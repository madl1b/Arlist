import sqlite3 as sl 

def buildSamplesDatabase():
    conn = sl.connect('samples.db')

    c = conn.cursor()

    samples = """
        CREATE TABLE samples (
            id text not NULL primary key,
            album text,
            name text, 
            instrumenality integer, 
            acousticness integer, 
            speechiness integer, 
            danceability integer, 
            album REFERENCES albums(id)
        )
    """

    # albums table included to accommodate more album related features in the future.
    albums = """
        CREATE TABLE albums (
            id text not NULL primary key,
            name text
        )
    """

    c.execute(albums)
    c.execute(samples)
    conn.commit()
    conn.close()






