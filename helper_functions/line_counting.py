def _make_gen(reader):
    # http://stackoverflow.com/questions/19001402/how-to-count-the-total-number-of-lines-in-a-text-file-using-python
    b = reader(1024 * 1024)
    while b:
        yield b
        b = reader(1024 * 1024)


def count_lines(path):
    # http://stackoverflow.com/questions/19001402/how-to-count-the-total-number-of-lines-in-a-text-file-using-python
    print('Counting lines of file: "' + path + '" ...')
    file = open(path, 'rb')
    f_gen = _make_gen(file.read)
    return sum(buf.count(b'\n') for buf in f_gen)
