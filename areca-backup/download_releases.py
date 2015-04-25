import os
import re
import json

import requests
import lxml.html
import arrow


def main():
    if not os.path.exists('data'):
        os.mkdir('data')

    response = requests.get('http://sourceforge.net/projects/areca/files/areca-stable/')
    response.raise_for_status()
    html_element = lxml.html.document_fromstring(response.content)

    for element in html_element.find_class("folder"):
        if element.tag != 'tr':
            continue

        slug = element.get('title')
        version = slug.split('-', 1)[-1]

        for subelement in element.findall('td/abbr'):
            date = arrow.get(subelement.get('title'))
            break
        else:
            raise Exception('Date not found')

        print('Found', version, date)

        if not re.match(r'[a-zA-Z0-9._-]+$', slug):
            raise Exception('Slug is not safe.')

        release_dirname = os.path.join('data', slug)

        if os.path.exists(release_dirname):
            continue

        release_dirname_tmp = release_dirname + '-tmp'
        os.mkdir(release_dirname_tmp)

        with open(os.path.join(release_dirname_tmp, 'info.json'), 'w') as file:
            file.write(json.dumps({
                'slug': slug,
                'date': date.isoformat(),
                'version': version,
            }))

        response = requests.get('http://sourceforge.net/projects/areca/files/areca-stable/{}'.format(slug))
        response.raise_for_status()

        match = re.search(r'http://sourceforge\.net/projects/areca/files/areca-stable/.*/(areca-[a-zA-Z0-9._-]+-src\.[a-z.]+)/download', response.text)

        if not match:
            raise Exception('Could not find source download link')

        print('Download', match.group(1))
        response = requests.get(match.group(0))
        response.raise_for_status()

        with open(os.path.join(release_dirname_tmp, match.group(1)), 'wb') as file:
            file.write(response.content)

        os.rename(release_dirname_tmp, release_dirname)


if __name__ == '__main__':
    main()
