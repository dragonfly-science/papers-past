import os
import click
import logging
from lxml import etree


def parse_xml(xml_file, out_file):

    with open(xml_file, 'r') as f:
        tree = etree.parse(f)

    with open(out_file, 'w') as f:
        for textline in tree.xpath('//TextLine'):
            f.write(' '.join(textline.xpath('String/@CONTENT')) + '\n')

    # Delete xml file to save disk space
    os.remove(xml_file)


def get_output_filepath(xml_file, out_dir):
    out_file = (xml_file
        .split('/',4)[-1]
        .replace('/','_')
        .replace('_MM_01', '')
        .replace('.xml','.txt')
    )
    return os.path.join(out_dir, out_file)

@click.command()
@click.option('--xml_dir', help='Path to xml files')
@click.option('--out_dir', help='Path to save files')
@click.option('--log_level', default='INFO', help='Log level (default: INFO)')
def main(xml_dir, out_dir, log_level):

    # Set logger config
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logging.info("Creating directory: {}".format(out_dir))
    if not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    captured_errors = {'file': [], 'error': []}
    for root, dirs, files in os.walk(xml_dir):
        for f in files:
            if f.endswith('.xml') and f != "mets.xml":
                fp = os.path.join(root, f)
                out = get_output_filepath(fp, out_dir)
                try:
                    # Extract and save text
                    logging.debug('Parsing xml {} to {}'.format(fp, out))
                    parse_xml(fp, out)
                except etree.XMLSyntaxError as e:
                    captured_errors['file'].append(fp)
                    captured_errors['error'].append(e)

    if len(captured_errors['file']) > 0:
        print('Captured errors for the following files:')
        for f, e in zip(captured_errors['file'], captured_errors['error']):
            print(f, e, '\n')
        raise RuntimeError()


if __name__ == '__main__':
    main()
