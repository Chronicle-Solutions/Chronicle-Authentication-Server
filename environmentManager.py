import sqlite3
import mariadb
from getpass import getpass
from traceback import print_exc

def main():
    printWelcome()
    
    while True:
        option = printMenu()
        match option:
            case "1":
                listEnvironments()
            case "2":
                listClientEnvs()
            case "3":
                addEnvironment()
            case "3":
                addClientEnvironment()
            case "5":
                deleteEnvironment()
            case "6":
                editEnvironment()
            case "7":
                listClients()
            case "8":
                print("Exiting...")
                break
            case _:
                print("Invalid option. Please try again.")


def printWelcome():
    print(r"""   ________                     _      __        _____                      _ __           ___                ___            __  _           
  / ____/ /_  _________  ____  (_)____/ /__     / ___/___  _______  _______(_) /___  __   /   |  ____  ____  / (_)________ _/ /_(_)___  ____ 
 / /   / __ \/ ___/ __ \/ __ \/ / ___/ / _ \    \__ \/ _ \/ ___/ / / / ___/ / __/ / / /  / /| | / __ \/ __ \/ / / ___/ __ `/ __/ / __ \/ __ \
/ /___/ / / / /  / /_/ / / / / / /__/ /  __/   ___/ /  __/ /__/ /_/ / /  / / /_/ /_/ /  / ___ |/ /_/ / /_/ / / / /__/ /_/ / /_/ / /_/ / / / /
\____/_/ /_/_/   \____/_/ /_/_/\___/_/\___/   /____/\___/\___/\__,_/_/  /_/\__/\__, /  /_/  |_/ .___/ .___/_/_/\___/\__,_/\__/_/\____/_/ /_/ 
                                                                              /____/         /_/   /_/                                       """)
    print(r"""    ______           _                                       __     __  ___                                 
   / ____/___ _   __(_)________  ____  ____ ___  ___  ____  / /_   /  |/  /___ _____  ____ _____ ____  _____
  / __/ / __ \ | / / / ___/ __ \/ __ \/ __ `__ \/ _ \/ __ \/ __/  / /|_/ / __ `/ __ \/ __ `/ __ `/ _ \/ ___/
 / /___/ / / / |/ / / /  / /_/ / / / / / / / / /  __/ / / / /_   / /  / / /_/ / / / / /_/ / /_/ /  __/ /    
/_____/_/ /_/|___/_/_/   \____/_/ /_/_/ /_/ /_/\___/_/ /_/\__/  /_/  /_/\__,_/_/ /_/\__,_/\__, /\___/_/     
                                                                                         /____/             """)
    print("Version 0.1.0")


def listEnvironments(client_id: str | None = None):
    with sqlite3.Connection("./db.sqlite") as conn:
        cursor = conn.cursor()
        if client_id is None:
            cursor.execute("SELECT * FROM environments")
        else:
            cursor.execute("SELECT * FROM clientEnvironments WHERE clientID = ?", [client_id])
        headers = [header[0] for header in cursor.description]
        rows = cursor.fetchall()
        print_table(headers, rows)
        

def print_row_sep(lengths: list[int]):
    print("+", end="")
    for i in lengths:
        print("-" * i, end="")
        print("+", end="")
    print()

def print_table(headers: list[str], rows: list):
    lengths = [0] * len(headers)
    for i in range(len(headers)):
        lengths[i] = max(len(headers[i]), *[len(str(row[i]).strip()) for row in rows]) + 4
    
    print_row_sep(lengths)

    print("|", end="")
    for i in range(len(headers)):
        print(f"{headers[i]:^{lengths[i]}}", end="")
        print("|", end="")
    print()
    print_row_sep(lengths)

    for row in rows:
        print("|", end="")
        for i in range(len(row)):
            print(f"{str(row[i]).strip():^{lengths[i]}}", end="")
            print("|", end="")
        print()
    print_row_sep(lengths)


def listClientEnvs():
    client_id = input("Enter Client ID: ")
    listEnvironments(client_id)

def addEnvironment():
    listEnvironments()
    print("Creating new Environment")
    env_name = input("Environment Name: ")
    db_host = input("Database Host: ")
    db_uname = input("Database Username: ")
    db_pass = getpass("Database Password: ")
    db_port = input("Database Port [Default 3306]: ")
    db_name = input(f"Database Name [Default: {env_name}]: ")
    auto_add = input("Auto Add? y/[N]").lower() == "y"

    # Convert port from string to int. Default: 3306
    db_port = int(db_port) if db_port.isdigit() else 3306
        

    test_connection = input("Test Credentials? [Y]/n").lower() == "n"

    connection_succeeded = not test_connection
    
    if test_connection:
        with mariadb.connect(
            host=db_host,
            user=db_uname,
            passwd=db_pass,
            db=db_name,
            port=db_port
        ) as conn:
            try:
                # Connect and see if we have access to the needed tables.
                cursor = conn.cursor()
                print("Testing Operator Selection")
                cursor.execute("SELECT * FROM OPERATORS")
                print(f"{cursor.rowcount} Operators Found")

                cursor.fetchall()

                print("Testing Access Profile Selection")
                cursor.execute("SELECT * FROM ACCESS_PROFILES")
                print(f"{cursor.rowcount} Access Profiles Found")

                cursor.fetchall()
                connection_succeeded = True
            except Exception as ex:
                print("Error while performing operation. Traceback Follows")
                print_exc()
                print("-" * 30)
                print("Connection Test Failed. Aborting!")
                return
                

    if connection_succeeded:
        with sqlite3.Connection("./db.sqlite") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO environments (envName, dbAuthHost, dbAuthUsername, dbAuthPassword, dbAuthPort, dbAuthName, autoAdd) VALUES (?, ?, ?, ?, ?, ?, ?);",
                           env_name, db_host, db_uname, db_pass, db_port, db_name, 1 if auto_add else 0)
            conn.commit()
            print("Environment Created.")


def listClients():
    with sqlite3.Connection("./db.sqlite") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT clientID FROM clientEnvironments")
        print_table(["Client ID"], cursor.fetchall())

def printMenu():
    print("1. List Global Environments")
    print("2. List Client Environments")
    print("3. Add Global Environment")
    print("4. Add Client Environment")
    print("5. Delete Environment")
    print("6. Edit Environment")
    print("7: List Known Clients")
    print("8. Exit")
    return input("Select an option: ")

if __name__ == "__main__":
    main()
