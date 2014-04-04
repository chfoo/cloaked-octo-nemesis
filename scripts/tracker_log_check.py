'''Go through the tracker logs looking for bad SHA1s.'''
import argparse
import json


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('file', type=argparse.FileType('r'))

    args = arg_parser.parse_args()

#     bad_ips = set()

    for line in args.file:
        info = json.loads(line)

        hash_val = info['id']['lua_hash']

        if hash_val != '7e4703a8d706b5ebf2e462e9e3c47390cc2e27e6':
            print(info['item'])
#             bad_ips.add(info['ip'])

#     print(bad_ips)


if __name__ == '__main__':
    main()
