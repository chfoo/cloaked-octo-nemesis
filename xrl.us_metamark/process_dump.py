import lzma


def main():
    table = []

    with lzma.open('/home/chris/Desktop/metamark-urls.tsv.xz') as file:
        for index, line in enumerate(file):
            if index % 10000 == 0:
                print(index)

            url, shortlink = line.rsplit(b'\t', 1)
            shortcode = shortlink.rsplit(b'/', 1)[-1].strip()

            table.append((shortcode, url))

    with open('output.txt', 'wb') as file:
        file.write(b'#FORMAT: BEACON\n')
        file.write(b'#PREFIX: http://xrl.us/\n')
        file.write('#CREATOR: Ask Bjørn Hansen http://metamark.net/\n'.encode('utf-8'))
        file.write(b'#HOMEPAGE: http://urlte.am/\n\n')

        for shortcode, url in sorted(table):
            file.write(shortcode)
            file.write(b'|')
            file.write(url)
            file.write(b'\n')


if __name__ == '__main__':
    main()
