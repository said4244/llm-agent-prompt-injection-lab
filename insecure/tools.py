###############################
##  TOOLS  (VULNERABLE build)
##
##  The agent is given three tools. Two of them are exploitable:
##    - GetUserTransactions  -> SQL injection (see transaction_db.py)
##    - ExportTransactionsToFile -> OS command injection (os.system below)
###############################
import json
import os

from dotenv import load_dotenv
from langchain.agents import Tool

from transaction_db import TransactionDb

load_dotenv()

# Host:port used in the link returned by the export tool. Override with
# EXPORT_HOST in your .env so no personal/lab IP is baked into the code.
EXPORT_HOST = os.getenv("EXPORT_HOST", "http://localhost:8501")


def get_current_user(input: str):
    db = TransactionDb()
    user = db.get_user(1)
    db.close()
    return user


get_current_user_tool = Tool(
    name='GetCurrentUser',
    func=get_current_user,
    description="Returns the current user for querying transactions."
)


def get_transactions(userId: str):
    """Returns the transactions associated to the userId provided by running this query: SELECT * FROM Transactions WHERE userId = ?."""
    try:
        db = TransactionDb()
        transactions = db.get_user_transactions(userId)
        db.close()
        return transactions
    except Exception as e:
        return f"Error: {e}'"


get_recent_transactions_tool = Tool(
    name='GetUserTransactions',
    func=get_transactions,
    description="Returns the transactions associated to the userId provided by running this query: SELECT * FROM Transactions WHERE userId = provided_userId."
)


def export_transactions_to_file(user_id):
    try:
        if not os.path.exists("exports"):
            os.makedirs("exports")

        # VULN 3 (OS command injection): the filename is built from unvalidated
        # user_id and then interpolated straight into a shell command. A user_id
        # like `1; <command>` runs <command> on the host as the service account.
        filename = f"transaction-{user_id}"
        file_path = f"exports/{filename}"

        db = TransactionDb()
        transactions = db.get_user_transactions(1)
        db.close()

        command = f"echo '{transactions}' > {file_path}"
        os.system(command)  # <-- the vulnerable call

        return (
            f"Transactions for user {user_id} exported successfully. "
            f"Access file at: {EXPORT_HOST}/{file_path}"
        )
    except Exception as e:
        return f"Error exporting transactions: {str(e)}"


export_transactions_tool = Tool(
    name='ExportTransactionsToFile',
    func=export_transactions_to_file,
    description="Exports transactions for a specific user to a text file. Input format: user_id (e.g., '1')"
)
