#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
import ConfigParser
import argparse
import datetime
import help.vcenter as vcenter
import help.aws as aws
import logging


parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                 description="""Remove snapshots da AWS e do VCenter\nhttps://github.com/wvoliveira/gari.git""")

parser.add_argument('-d', '--datacenter', metavar='\b', help='vcenter or aws', required=True)
parser.add_argument('-c', '--config', metavar='\b', help='config file', required=True)
parser.add_argument('-w', '--whitelist', metavar='\b', help='whitelist file', required=True)
parser.add_argument('-f', '--force', help='force remove', action='store_true')
args = parser.parse_args()

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


def config_parser(section):
    config = ConfigParser.ConfigParser()
    config.read(args.config)
    if config.has_section(section):
        items_dict = dict(config.items(section))
        return items_dict
    else:
        logging.error("Variavel '{0}' inexistente no arquivo de configuracao".format(section))
        sys.exit(1)


def difference_date(date_):
    date = datetime.datetime.strptime(str(date_), '%Y-%m-%d %H:%M:%S')
    difference = abs(datetime.datetime.now() - date)
    return difference.days


def vcenter_remove_snapshots():
    try:
        logging.info('Lendo VCenter section do arquivo de configuracao')
        vcenter_args = config_parser('vcenter')
    except Exception as error:
        logging.error(error)
        sys.exit(2)

    try:
        logging.info('Lendo arquivo whitelist')
        with open(args.whitelist) as file:
            whitelist = file.read().splitlines()
    except Exception as error:
        logging.error(error)
        sys.exit(2)

    try:
        logging.info('Coletando variaveis')
        host = vcenter_args['host']
        user = vcenter_args['user']
        pwd = vcenter_args['pwd']
        snapshot_days = vcenter_args['snapshot_days']
    except Exception as error:
        logging.error(error)
        sys.exit(2)

    try:
        logging.info("Tentando se conectar no VCenter '{0}'".format(vcenter_args['host']))
        vcenter_conn = vcenter.VCenter(host, user, pwd)
    except Exception as error:
        logging.error(error)
        sys.exit(2)

    try:
        logging.info('Coletando informacoes de todas as VMs')
        vms = vcenter_conn.get_all_vms()
    except Exception as error:
        logging.error(error)
        sys.exit(2)

    logging.info('Numero de VMs: {0}'.format(len(vms)))

    logging.info('Verificando se existe snapshot nas VMs. Pode demorar um pouco (muito)')
    for index, vm in enumerate(vms, start=1):

        snapshot_list = vcenter_conn.snapshot_list(vm['name'])

        if len(snapshot_list) > 0:
            for snapshot in snapshot_list:
                create_time = snapshot['CreateTime'][:19]
                snapshot_name = snapshot['Name']
                vm_name = vm['name']

                difference_days = difference_date(datetime.datetime.strptime(str(create_time), '%Y-%m-%d %H:%M:%S'))

                if difference_days >= int(vcenter_args['snapshot_days']):
                    logging.info('Nome: {0}'.format(vm_name))
                    logging.info('Data da criacao: {0}'.format(create_time))
                    logging.info('Snapshot name: {0}'.format(snapshot_name))

                    if vm_name in whitelist:
                        logging.info('O snapshot existe ha mais de {0} dias, mas esta na whitelist'.format(snapshot_days))
                        continue
                    else:
                        if args.force:
                            logging.info("Removendo snapshot '{0}' da VM '{1}'".format(snapshot_name, vm_name))
                            try:
                                vcenter_conn.remove_snapshot(vm_name, snapshot_name)
                            except Exception as error:
                                logging.error(error)
                        else:
                            logging.info("Removeria o snapshot {0} da VM '{1}'".format(snapshot_name, vm_name))


def aws_remove_snapshots():
    try:
        logging.info('Lendo AWS section do arquivo de configuracao')
        aws_args = config_parser('aws')
    except Exception as error:
        logging.error(error)
        sys.exit(2)

    try:
        logging.info('Lendo arquivo whitelist')
        with open(args.whitelist) as file:
            whitelist = file.read().splitlines()
    except Exception as error:
        logging.error(error)
        sys.exit(2)

    try:
        logging.info('Coletando variaveis')
        region = aws_args['region']
        key_id = aws_args['key_id']
        access_key = aws_args['access_key']
        owner_id = aws_args['owner_id']
        snapshot_days = aws_args['snapshot_days']
    except Exception as error:
        logging.error(error)
        sys.exit(2)

    try:
        logging.info("Tentando se conectar na regiao '{0}'... ".format(aws_args['region']))
        aws_conn = aws.AWS(region, key_id, access_key, owner_id)
    except Exception as error:
        logging.error(error)
        sys.exit(2)

    logging.info('Coletando snapshots')
    snapshots = aws_conn.snapshots()

    logging.info('Numero de snapshots: {0}'.format(len(snapshots)))

    for info in snapshots:
        name = None
        if info.has_key('Tags'):
            for key in info['Tags']:
                if key['Key'] == 'Name':
                    name = key['Value'].split(' - ')[0]

        create_time = str(info['StartTime'])[:19]
        snapshot_id = info['SnapshotId']

        difference_days = difference_date(datetime.datetime.strptime(str(create_time), '%Y-%m-%d %H:%M:%S'))
        if difference_days > int(snapshot_days):
            logging.info('Nome: {0}'.format(name))
            logging.info('Data da criacao: {0}'.format(create_time))
            logging.info('Snapshot ID: {0}'.format(snapshot_id))

            if snapshot_id in whitelist:
                logging.info('O snapshot existe ha mais de {0} dias, mas esta na whitelist'.format(snapshot_days))
                continue
            else:
                if args.force:
                    logging.info('Removendo snapshot {0}... '.format(snapshot_id))
                    try:
                        aws_conn.delete_snapshot(snapshot_id)
                    except Exception as error:
                        logging.error(error)
                else:
                    logging.info('Removeria o snapshot {0}... '.format(snapshot_id))

def main():
    if args.datacenter.lower() == 'vcenter':
        vcenter_remove_snapshots()
    elif args.datacenter.lower() == 'aws':
        aws_remove_snapshots()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
