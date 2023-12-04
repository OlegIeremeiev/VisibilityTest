import re
from pathlib import Path

import yaml
# from pathlib import Path
import os


class ImageRegulator:

    def __init__(self):
        data = dict()
        data['version'] = 0.21
        data['app_version'] = 0.2
        data['limit'] = 20

        # eval statistics by the experiments
        data = self.eval_statistics(data)

        all_images = self.generate_all_images()

        self.dict_add_absent(data['images'], all_images)
        data['references'] = self.list_ref()

        im_conf_list = list(filter(os.path.isfile, Path('images').glob('*.yaml')))

        if im_conf_list:
            loaded_data = YAML.read(im_conf_list[0])
            if loaded_data['version'] == data['version']:
                i = 0
                while os.path.isfile(os.path.join('images', f'imageconf_{loaded_data["version"]}.yaml.bak{i}')):
                    i += 1
                YAML.write(loaded_data, f'imageconf_{loaded_data["version"]}.yaml.bak{i}', 'images')
            else:
                # save new + backup
                YAML.write(loaded_data, f'imageconf_{loaded_data["version"]}.yaml.bak', 'images')
        YAML.write(data, f'imageconf_{data["version"]}.yaml', 'images')

    def eval_statistics(self, data: dict) -> dict:

        # get conf data
        im_conf_list = list(filter(os.path.isfile, Path('images').glob('*.yaml')))
        if im_conf_list:
            conf_data = YAML.read(im_conf_list[0])
            conf_images = conf_data['images']
        else:
            conf_images = dict()

        res_list = list(filter(os.path.isfile, Path('results').glob('*.yaml')))
        res_list = [x[0] for x in list(filter(lambda x: x, [re.findall(r'.*\d{4}-\d{2}-\d{2} \d{2}\.\d{2}\.\d{2}\.yaml', val.name) for val in res_list]))]

        res_data = dict()
        for res in res_list:
            rd = YAML.read(res,'results')
            for r in rd['results']:
                if r[0] in res_data:
                    res_data[r[0]] += 1
                else:
                    res_data[r[0]] = 1

        self.dict_add_absent(res_data, conf_images)
        data['images'] = res_data
        return data

    @staticmethod
    def dict_add_absent(main: dict, secondary: dict):
        for s in secondary:
            if s not in main:
                main[s] = secondary[s]

    @staticmethod
    def generate_all_images() -> dict:
        data = dict()
        for r in range(25):
            for d in range(24):
                for i in range(5):
                    key = 'I{:02d}_{:02d}_{:d}.bmp'.format(r+1, d+1, i+1)
                    data[key] = 0
        return data

    @staticmethod
    def list_ref() -> list:
        data = ['I{:02d}.bmp'.format(r+1) for r in range(25)]
        return data




class YAML:
    @staticmethod
    def read(name: str, path: str = "") -> dict:
        with open(os.path.join(path, name), 'r') as file:
            data = yaml.safe_load(file)
        return data

    @staticmethod
    def write(data: dict, name: str, path: str = ""):
        with open(os.path.join(path, name), "w") as file:
            yaml.dump(data, file, allow_unicode=True)


if __name__ == "__main__":
    ir = ImageRegulator()
