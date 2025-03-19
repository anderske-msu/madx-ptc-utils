from logging import warning
import argparse
import pathlib

# TODO Fix bug that leaves some lines uncommented
# Use lattice_1IO.seq as test file


def comment_out(line: str, char: str):
    return char + " " + line


def relpace_keyword(
    filename: pathlib.PosixPath,
    keyword: str,
    newfilename: pathlib.PosixPath,
    char: str = "!",
):
    markers = []

    # read file
    with open(filename, "r") as original:
        data = original.readlines()

    for line in data:
        if keyword in line:
            element = line.split(":")[0]
            markers.append(element)

    for ln, line in enumerate(data):
        rmline = False
        defined_element = line.split(":")[0]  # Where the element is defined
        lattice_element = line.split(",")[0]  # Where the element is placed

        if line.startswith(char):
            pass  # skip commented lines

        elif defined_element in markers:
            rmline = True

        elif lattice_element in markers:
            rmline = True

        if rmline:
            data[ln] = comment_out(line, char)
            print("Commented out: " + line)

    data = str.join("", data)

    with open(newfilename, "w") as modified:
        modified.write(data)

    print("New file saved as " + newfilename.as_posix())


def main():
    # variables

    description = (
        "Remove keywords/elements from a MAD-X sequence file by commenting "
        "them out. Creates a new file with the same name as the original, but with "
        "'_new' appended to the end of the filename."
    )

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "filename", type=pathlib.PosixPath, help="The MAD-X sequence file to modify."
    )
    parser.add_argument("keywords", type=str, nargs="*", help="Keywords to remove.")
    args = parser.parse_args()
    filename = args.filename
    keywords = args.keywords

    newfilename = pathlib.Path("./" + filename.stem + "_new.seq").absolute()

    if not keywords:
        warning("No keywords given")

    if not filename.exists():
        raise Exception("File does not exist")

    else:
        for i, kywrd in enumerate(keywords):
            if i >= 1:
                filename = newfilename

            relpace_keyword(filename, kywrd, newfilename)


if __name__ == "__main__":
    main()
