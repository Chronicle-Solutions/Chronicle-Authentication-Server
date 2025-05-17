from flask import Flask, request, abort
import sqlite3
import mariadb
from argon2 import PasswordHasher

app = Flask(__name__)

@app.post("/login/<envName>/")
def post_login(envName: str):
    userid = request.json.get("operatorID")
    passwd = request.json.get("password")
    with sqlite3.Connection("./db.sqlite") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT dbAuthHost, dbAuthUsername, dbAuthPassword, dbAuthPort, dbAuthName FROM environments WHERE envName = ?", (envName,))
        row = cursor.fetchone()
    # print(userid, passwd)
    host, username, password, port, name = row
    with mariadb.connect(
        host=host,
        user=username,
        password=password,
        db=name,
        port=port
    ) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT operatorID, password, accessProfileID from OPERATORS where operatorID = %s", (userid,))
        oprID, storedPw, apid = cursor.fetchone()
        ph = PasswordHasher()
        isValid = False
        try:
            isValid = ph.verify(storedPw, passwd)
        except:
            pass
        if not isValid:
            # Get the Access Profile Data
            abort(401)
        cursor.execute("SELECT userID, password FROM ACCESS_PROFILES WHERE accessProfileID = %s", (apid,))
        accessUsername, accessPassword = cursor.fetchone()
        return {
            "operatorID": userid,
            "apUser": accessUsername,
            "apPass": accessPassword,
            "apHost": host,
            "apName": name,
            "apPort": str(port)
        }

        


@app.get("/environments")
def get_environment_names():
    with sqlite3.Connection("./db.sqlite") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT envName FROM environments;")
        return [x[0] for x in cursor.fetchall()]

def ensureDB():
    with sqlite3.Connection("./db.sqlite") as conn:
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS environments(
                            environmentID integer primary key autoincrement,
                            envName        varchar(30),
                            dbAuthHost     varchar(40),
                            dbAuthUsername varchar(40),
                            dbAuthPassword varchar(40),
                            dbAuthPort     int,
                            dbAuthName     varchar(40)
                       )""")



if __name__ == "__main__":
    ensureDB()
    app.run()