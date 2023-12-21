import csv
import os
from datetime import datetime
from pathlib import Path
import numpy as np
import yaml


class Analyzer:

    def __init__(self):

        all_yaml = list(filter(os.path.isfile, Path('results').glob('*.yaml')))
        survey_yaml = list(filter(os.path.isfile, Path('results').glob('*survey.yaml')))
        self.results_yaml = list(set(all_yaml) - set(survey_yaml))
        self.ids = {}
        self.images = {}
        self.times = {}
        self.duplicates = []
        self.stats = {}
        self.warning = []
        self.max_length = 0


    def parse_data(self):
        self.ids = {}
        self.images = {}
        self.duplicates = []
        for result in self.results_yaml:
            data = YAML.read(result.name, 'results')

            # check for duplicates
            if data['rnd'] not in self.ids:

                # if 'begin_time' not in data:
                #     q = 0
                # gather information
                tmp = {'id': data['rnd'],
                       'name': data['name'],
                       'begin_time': data['begin_time']}
                tb = datetime.strptime(data['begin_time'], '%Y-%m-%d %H:%M:%S')
                te = datetime.strptime(data['end_time'], '%Y-%m-%d %H:%M:%S')
                tmp['time'] = (te - tb).total_seconds()
                tmp['filename'] = result.name
                tmp['images'] = [item[0] for item in data['results']]
                self.ids[data['rnd']] = tmp

                # add image selections and times per round
                self.__add_images(data)

            else:
                self.duplicates.append({'name': data['name'], 'id': data['rnd'], 'time': data['begin_time'],
                                        'filename': result.name})

    def __add_images(self, data: dict):
        for c, item in enumerate(data['results']):
            # t1 = item[2]
            # t2 = data['markers'][0]
            # t3 = data['results'][c - 1] if c > 0 else 0
            td = item[2] - (data['results'][c - 1][2] if c > 0 else data['markers'][0])
            if item[0] not in self.images:
                self.images[item[0]] = {data['rnd']: item[1]}
                self.times[item[0]] = {data['rnd']: td}
            else:
                self.images[item[0]][data['rnd']] = item[1]
                self.times[item[0]][data['rnd']] = td

    def get_stats(self):
        self.stats = {}
        for im in self.images:
            values = list(self.images[im].values())
            unique = list(set(values))

            if len(values) > self.max_length:
                self.max_length = len(values)

            tmp = {'number': len(values),
                   'min': min(values),
                   'max': max(values),
                   'avg': round(sum(values) / max(len(values), 1), 3),
                   'unique': unique,
                   'count': len(list(set(values))),
                   'std': round(np.std(values), 4)
                   }
            self.stats[im] = tmp
            if 1 in unique and 3 in unique:
                self.warning.append(im)

    def write_stats(self):
        data = []
        keys = list(self.stats.keys())
        keys.sort()
        for im in keys:
            data.append([im, *list(self.stats[im].values())])
        CSV.write(data, name='csv_stats.csv', header=['image', *list(self.stats['I01_01_1.bmp'].keys())])

    def write_images(self):
        data = []
        keys = list(self.images.keys())
        keys.sort()
        for im in keys:
            data.append([im, *sorted(list(self.images[im].values()))])
        CSV.write(data, name='csv_images.csv', header=['image', *('N'*self.max_length)])

    def write_warnings_images(self):
        data = []
        keys = list(self.images.keys())
        keys.sort()
        max_vals = 0
        for im in keys:
            if self.stats[im]['std'] > 0.5:
                tmp = [im, self.stats[im]['number'], self.stats[im]['avg'], self.stats[im]['std']]
                max_vals = max(max_vals, len(self.images[im]))
                for _id in self.images[im]:
                    tmp.append(f'{_id} ({self.images[im][_id]}, {round(self.ids[_id]["time"])})')
                data.append(tmp)
        CSV.write(data, name='csv_warnings_images.csv', header=['image', 'number', 'avg', 'std', *(['id']*max_vals)])

    def write_warnings_names(self):
        data = {}
        keys = list(self.images.keys())
        keys.sort()
        max_vals = 0
        for im in keys:
            if self.stats[im]['std'] > 0.5:

                avg = self.stats[im]['avg']
                std = self.stats[im]['std']
                # tmp = [im, self.stats[im]['number'], self.stats[im]['avg'], self.stats[im]['std']]
                # max_vals = max(max_vals, len(self.images[im]))
                for _id in self.images[im]:
                    if not avg - 1.8 * std <= self.images[im][_id] <= avg + 1.8 * std:
                        if _id not in data:
                            data[_id] = []
                        data[_id].append(f"{im} ({self.images[im][_id]}, {round(self.ids[_id]['time'])} / {self.stats[im]['number']}, {self.stats[im]['avg']}, {self.stats[im]['std']})")

        exprt = []
        for key in data:
            max_vals = max(max_vals, len(data[key]))
            exprt.append([f"{self.ids[key]['name']} ({key})", *data[key]])

        CSV.write(exprt, name='csv_warnings_names.csv', header=['name', *(['image']*max_vals)])



class YAML:
    @staticmethod
    def read(name: str, path: str = "") -> dict:
        try:
            with open(os.path.join(path, name), 'r') as file:
                data = yaml.safe_load(file)
        except UnicodeDecodeError:
            with open(os.path.join(path, name), 'r', encoding='windows-1251') as file:
                data = yaml.safe_load(file)
        return data

    @staticmethod
    def write(data: dict, name: str, path: str = ""):
        with open(os.path.join(path, name), "w") as file:
            yaml.dump(data, file, allow_unicode=True)


class CSV:
    @staticmethod
    def write(data, name: str, header: list, path: str = ""):
        with open(os.path.join(path, name), 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            # write the header
            if header:
                writer.writerow(header)
            # write multiple rows
            writer.writerows(data)


if __name__ == "__main__":

    # init
    analyzer = Analyzer()

    # obtain data
    analyzer.parse_data()

    print('-'*10+'Duplicates'+'-'*10)
    print(analyzer.duplicates)
    # another similar id file ?
    print('-' * 30)

    analyzer.get_stats()
    print('-'*11+'Warnings'+'-'*11)
    print('\n'.join(analyzer.warning))
    # another similar id file ?
    print('-' * 30)

    analyzer.write_images()
    analyzer.write_stats()
    analyzer.write_warnings_images()
    analyzer.write_warnings_names()
    #
    # datetime.combine(date.today(), exit) - datetime.combine(date.today(), enter)

    # a = np.array([[1, 4, 5], [1, 4, 5, 8]], float)
    # print(a)
