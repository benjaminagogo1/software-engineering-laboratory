def read_int(prompt):
    value = input(prompt)

    try:
        return int(value)
    except ValueError:
        print("Invalid input. Please enter a number.")
        return None
    
def read_float(prompt):
    value = input(prompt)

    try:
        return float(value)
    except ValueError:
        print("Invalid input: Please enter a number.")
        return None

