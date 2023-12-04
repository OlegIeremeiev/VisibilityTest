import yaml
# from pathlib import Path
import os


class ImageRegulator:

    def __init__(self):
        data = dict()
        data['version'] = 0.1

        # eval statistics by the experiments
        data = self.eval_statistics(data)

        # verify existed
        loaded_data = YAML.read(name='imageconf.yaml', path='images')
        if loaded_data['version'] == data['version']:
            print('Warning! Version already existed!')

        else:
            # save new + backup
            YAML.write(loaded_data, f'imageconf_{loaded_data['version']}.yaml.bak', 'images')
            YAML.write(data, 'imageconf.yaml', 'images')

    def eval_statistics(self, data) -> dict:
        pass


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
