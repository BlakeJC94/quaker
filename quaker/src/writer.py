import os

# TODO docs
# TODO typehint
def write_content(download, output_file):
    mode = "a" if os.path.exists(output_file) else "w"
    with open(output_file, mode, encoding="utf-8") as csvfile:
        lines = download.iter_lines(decode_unicode=True)
        if mode == "a":  # Skip header if appending to file
            _ = next(lines)
        csvfile.writelines(line + "\n" for line in lines)

