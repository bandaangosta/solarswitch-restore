#!/bin/bash

# Restore full measurements backups to solarswitch database
# Each measurement is stored in its individual csv file, all of them later zipped.
# Main script was obtained from https://github.com/fabio-miranda/csv-to-influxdb

echo "Uncompressing $1 ..."
echo

rm /tmp/backup_*.csv
unzip $1 -d /tmp

ACTIVATE=venv/bin/activate
TOINFLUX=csv-to-influxdb.py
source $ACTIVATE

echo
echo "Restoring 'power' measurement..."
echo
#python $TOINFLUX -i /tmp/backup_power.csv --dbname solarswitch --metricname power --tagcolumns location --timecolumn time --timeformat '%Y-%m-%dT%H:%M:%SZ'

echo
echo "Restoring 'energy' measurement..."
echo
#python $TOINFLUX -i /tmp/backup_energy.csv --dbname solarswitch --metricname energy --tagcolumns location --timecolumn time --timeformat '%Y-%m-%dT%H:%M:%SZ'

echo
echo "Restoring 'frequency' measurement..."
echo
#python $TOINFLUX -i /tmp/backup_frequency.csv --dbname solarswitch --metricname frequency --tagcolumns location --timecolumn time --timeformat '%Y-%m-%dT%H:%M:%SZ'

echo
echo "Restoring 'powerfactor' measurement..."
echo
#python $TOINFLUX -i /tmp/backup_powerFactor.csv --dbname solarswitch --metricname powerFactor --tagcolumns location --timecolumn time --timeformat '%Y-%m-%dT%H:%M:%SZ'

echo
echo "Restoring 'relays' measurement..."
echo
#python $TOINFLUX -i /tmp/backup_relays.csv --dbname solarswitch --metricname relays --timecolumn time --timeformat '%Y-%m-%dT%H:%M:%SZ'

echo
echo "Restoring 'current' measurement..."
echo
#python $TOINFLUX -i /tmp/backup_current.csv --dbname solarswitch --metricname current --fieldcolumns value,value_raw --tagcolumns flow,location  --timecolumn time --timeformat '%Y-%m-%dT%H:%M:%SZ'

echo
echo "Restoring 'voltage' measurement..."
echo
python $TOINFLUX -i /tmp/backup_voltage.csv --dbname solarswitch --metricname voltage --fieldcolumns value,value_raw --tagcolumns flow,location  --timecolumn time --timeformat '%Y-%m-%dT%H:%M:%SZ'

deactivate
