import csv
import os
import pyodbc

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient

# Key Vault Name
KEY_VAULT_NAME = "key-vault000"

KEY_VAULT_URL = f"https://{KEY_VAULT_NAME}.vault.azure.net/"

credential = DefaultAzureCredential()

secret_client = SecretClient(
    vault_url=KEY_VAULT_URL,
    credential=credential
)

def get_secret(secret_name):
    return secret_client.get_secret(secret_name).value

# Read secrets from Key Vault
storage_account_name = get_secret("storage-account-name")
storage_container_name = get_secret("storage-container-name")

sql_server = get_secret("sql-server")
sql_database = get_secret("sql-database")
sql_username = get_secret("sql-username")
sql_password = get_secret("sql-password")

# Upload CSV to Blob Storage
def upload_csv():
    account_url = (
        f"https://{storage_account_name}.blob.core.windows.net"
    )

    blob_service_client = BlobServiceClient(
        account_url=account_url,
        credential=credential
    )

    container_client = (
        blob_service_client.get_container_client(
            storage_container_name
        )
    )

    with open("customers.csv", "rb") as data:
        container_client.upload_blob(
            name="customers.csv",
            data=data,
            overwrite=True
        )

    print("CSV uploaded successfully")

# SQL Connection
def get_connection():

    connection_string = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server=tcp:{sql_server},1433;"
        f"Database={sql_database};"
        f"Uid={sql_username};"
        f"Pwd={sql_password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
    )

    return pyodbc.connect( connection_string, timeout=120 )

def load_to_sql():

    try:
        print("================================")
        print("SQL DEBUG INFORMATION")
        print("================================")

        print("Server:", sql_server)
        print("Database:", sql_database)
        print("Username:", sql_username)

        print("Connecting to SQL...")

        conn = get_connection()

        print("Connected to SQL")

        cursor = conn.cursor()

        with open("customers.csv") as file:

            reader = csv.DictReader(file)

            for row in reader:

                print(f"Inserting {row['customer_id']}")

                cursor.execute(
                    """
                    INSERT INTO dbo.customers
                    (customer_id,name,email,status)
                    VALUES (?,?,?,?)
                    """,
                    row["customer_id"],
                    row["name"],
                    row["email"],
                    row["status"]
                )

        conn.commit()

        print("Commit successful")

        cursor.close()
        conn.close()

        print("Data inserted successfully")

    except Exception as e:

        print("================================")
        print("SQL ERROR OCCURRED")
        print("================================")
        print(str(e))
        print("================================")

if __name__ == "__main__":

    print("Starting Azure Container Loader...")

    upload_csv()

    print("Blob upload done")

    load_to_sql()

    print("SQL load done")

    print("Completed Successfully")
