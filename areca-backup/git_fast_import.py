import glob
import json
import zipfile
import tarfile
import os
import sys

import arrow


def main():
    data_dir = 'data/'
    infos = []
    
    for info_filename in glob.glob(data_dir + '/*/info.json'):
        with open(info_filename) as file:
            info = json.loads(file.read())
        
        info['date'] = arrow.get(info['date'])
            
        infos.append(info)
    
    infos = sorted(infos, key=lambda d:d['date'])
    
    out_write = sys.stdout.write
    
    def out_bwrite(data):
        sys.stdout.flush()
        sys.stdout.buffer.write(data)
        sys.stdout.flush()
    
    for info in infos:
        dirname = os.path.join(data_dir, info['slug'])
        
        for filename in glob.glob(dirname + '/*src*'):
            archive_filename = filename
            break
        else:
            raise Exception('Cannot find archive file.')
        
        sys.stderr.write('=== {}\n'.format(info['slug']))
        
        def get_files():
            if archive_filename.endswith('zip'):
                file = zipfile.ZipFile(archive_filename)
                
                for name in file.namelist():
                    if name.startswith('areca-'):
                        fixed_name = name.split('/', 1)[-1].replace('//', '/')
                    else:
                        fixed_name = name
                    
                    if not name.endswith('/'):
                        yield fixed_name, file.read(name)
            else:
                file = tarfile.open(archive_filename)
                
                for name in file.getnames():
                    try:
                        yield name, file.extractfile(name).read()
                    except AttributeError:
                        # Not a file
                        pass
        
        out_write('commit refs/heads/master\n')
        out_write('committer Areca Backup <> {} +0000\n'.format(info['date'].timestamp))
        
        commit_message = 'Release {}'.format(info['slug']).encode()
        out_write('data {}\n'.format(len(commit_message)))
        out_bwrite(commit_message)
        out_write('\n')
        out_write('deleteall\n')
        
        for filename, data in get_files():
            out_write('M 644 inline {}\n'.format(filename))
            out_write('data {}\n'.format(len(data)))
            out_bwrite(data)
            out_write('\n')
        
        out_write('\n')


if __name__ == '__main__':
    main()