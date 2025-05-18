from flask import Flask, request, abort
import sqlite3
import mariadb
from argon2 import PasswordHasher

app = Flask(__name__)


def getAuthCredentials(envName):
    with sqlite3.Connection("./db.sqlite") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT dbAuthHost, dbAuthUsername, dbAuthPassword, dbAuthPort, dbAuthName FROM environments WHERE envName = ?", (envName,))
        row = cursor.fetchone()
    # print(userid, passwd)
    return row

@app.post("/login/<envName>/")
def post_login(envName: str):
    host, username, password, port, name = getAuthCredentials(envName)
    userid = request.json.get("operatorID")
    passwd = request.json.get("password")

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
        if apid is None:
            return {"errorMsg": "The operator successfully authenticated with the server but no access profile has been assigned."}, 401
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

        


@app.get("/environments/<clientID>")
def get_environment_names(clientID: str):
    with sqlite3.Connection("./db.sqlite") as conn:
        cursor = conn.cursor()
        # Check if environments exist.
        cursor.execute("SELECT * FROM clientEnvironments WHERE clientID = ?;", (clientID,))
        rows = cursor.fetchall()
        if(len(rows) <= 0):
            return populateDefaultEnvironments(clientID)
        else:
            return [x[1] for x in rows]

def populateDefaultEnvironments(clientID):
    with sqlite3.Connection("./db.sqlite") as conn:
        cursor = conn.cursor()
        print("INSERT INTO clientEnvironments (envName, clientID, dbAuthHost, dbAuthUsername, dbAuthPassword, dbAuthPort, dbAuthName) SELECT envName, ?, dbAuthHost, dbAuthUsername, dbAuthPassword, dbAuthPort, dbAuthName FROM environments WHERE autoAdd = 1;", (clientID,))
        cursor.execute("INSERT INTO clientEnvironments (envName, clientID, dbAuthHost, dbAuthUsername, dbAuthPassword, dbAuthPort, dbAuthName) SELECT envName, ?, dbAuthHost, dbAuthUsername, dbAuthPassword, dbAuthPort, dbAuthName FROM environments WHERE autoAdd = 1;", (clientID,))
        conn.commit()
        cursor.execute("SELECT * FROM clientEnvironments WHERE clientID = ?;", (clientID,))
        return [x[1] for x in cursor.fetchall()]

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
                            dbAuthName     varchar(40),
                            autoAdd integer default 0
                       )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS clientEnvironments
                        (
                            environmentID  integer
                                primary key autoincrement,
                            envName        varchar(30),
                            clientID       varchar(30),
                            dbAuthHost     varchar(40),
                            dbAuthUsername varchar(40),
                            dbAuthPassword varchar(40),
                            dbAuthPort     int,
                            dbAuthName     varchar(40),
                            UNIQUE (envName, clientID)
                        );""")
        conn.commit()


ensureDB()

if __name__ == "__main__":
    app.run()
