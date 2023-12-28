
def add_file_result_url(csv_file, column_name):
    csv_file.insert(3, column_name, "")


def populate_file_result_url(csv_file, url_dict, column_name):
    for index, row in csv_file.iterrows():
        file_id = row['file_id']
        if file_id in url_dict:
            csv_file.at[index, column_name] = url_dict[file_id]


def save_new_file(csv_file, file_name):
    csv_file.to_csv(file_name, index=False)
    return file_name
