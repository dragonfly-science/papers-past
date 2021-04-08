import os
import click
import logging
from lxml import etree


def parse_xml(xml_file):

    with open(xml_file, 'r') as f:
        tree = etree.parse(f)

    with open(xml_file.replace('.xml', '.txt'), 'w') as f:
        for textline in tree.xpath('//TextLine'):
            f.write(' '.join(textline.xpath('String/@CONTENT')) + '\n')

    # Delete xml file
    os.remove(xml_file)


@click.command()
@click.option('--xml_dir', help='Path to xml files')
@click.option('--log_level', default='INFO', help='Log level (default: INFO)')
def main(xml_dir, log_level):

    # Set logger config
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    captured_errors = {'file': [], 'error': []}
    for root, dirs, files in os.walk(xml_dir):
        for f in files:
            if f.endswith('.xml') and f != "mets.xml":
                fp = os.path.join(root, f)
                try:
                    # Extract and save text
                    parse_xml(fp)
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
