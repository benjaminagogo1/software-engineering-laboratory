

def run(connection):
      connection.execute(
            """
            ALTER TABLE expenses
            ADD COLUMN user_id INTEGER
            """ 
      )