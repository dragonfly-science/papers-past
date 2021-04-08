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
@click.option('--xml_file', help='Path to xml files')
@click.option('--log_level', default='INFO', help='Log level (default: INFO)')
def main(xml_file, log_level):

    # Set logger config
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    captured_errors = {'file': [], 'error': []}

    # Extract and save text
    parse_xml(xml_file)



if __name__ == '__main__':
    main()
