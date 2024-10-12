import os


def rename_files(directory):
    for filename in os.listdir(directory):

        if filename == "__init__.py":
            continue

        file_path = os.path.join(directory, filename)

        if os.path.isfile(file_path):
            new_filename = "test_" + filename
            new_file_path = os.path.join(directory, new_filename)

            os.rename(file_path, new_file_path)
            print(f"Renamed: {filename} -> {new_filename}")

directory_path = "tests"
rename_files(directory_path)