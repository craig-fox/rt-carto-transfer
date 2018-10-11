import csv

csvName = 'csv/' + 'vw_custom_what_events' + '.csv'

with open(csvName) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    newline_count = 0
    for row in csv_reader:
        if line_count == 0:
            print(f'Column names are {", ".join(row)}')
            line_count += 1
        else:
            #print('Row {row}'.format(row=row))
            for field in row:
                if("\n" in field):
                    print('Newline in field {field}, row {row}'.format(field=field.replace("\n", "Z"), row=line_count))
                    print(str(row).strip('[]'))
                    newline_count += 1
            line_count += 1
    print(f'Processed {line_count} lines.')
    print(f'Found {newline_count} newlines.')
