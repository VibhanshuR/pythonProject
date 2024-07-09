def add_entries():
    entries = []
    while True:
        user_input = input("Enter age and name (or 0 to stop): ")
        if user_input == "0":
            break
        else:
            try:
                age, name = user_input.split()
                age = int(age)
                entries.append((age, name))
            except ValueError:
                print("Invalid input. Please enter in 'age name' format.")
    return entries


def search_entry(entries):
    search_name = input("Enter the name you want to search: ")
    results = [entry for entry in entries if entry[1].lower() == search_name.lower()]

    if results:
        for result in results:
            print(f"Name: {result[1]}, Age: {result[0]}")
    else:
        print("No results found.")


def main():
    entries = add_entries()
    search_entry(entries)


if __name__ == "__main__":
    main()