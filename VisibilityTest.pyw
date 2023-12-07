import threading
import webbrowser
from tkinter import Tk, Toplevel, Frame, Label, Button, Entry, StringVar, NSEW, N, S, E, W, \
    Canvas, RIDGE, DISABLED, NORMAL, END, Scale, IntVar, HORIZONTAL, Checkbutton, RAISED, SUNKEN, FLAT, Text, WORD
from tkinter import ttk, font
import yaml
import re
import os
import platform
from pathlib import Path
from PIL import Image, ImageTk
from abc import ABC, abstractmethod
import random
import time
import requests


class GUI:
    cur_lang = 'ua'
    version = 0.3
    conf_version: float
    r_version: float = None
    r_conf_version: float
    is_loading: bool
    is_cancel: bool

    def __init__(self):
        """Tkinter application class initialization
        :rtype: App class
        """
        self.network = None
        # init window
        self.tk = Tk()
        self.tk.grid()
        self.tk.protocol("WM_DELETE_WINDOW", lambda parent=self.tk: CustomDialog.quit_dialog(parent, self.cur_lang))
        self.tk.resizable(False, False)

        # main frame
        self.imgFrame = ImageFrame(self.tk)
        self.imgFrame.init_lang_action(self)
        self.experiment = Experiment(self)
        self.lock_buttons(True)
        self.__check_folders()
        self.is_loaded_survey = False
        self.load_frame: LoadFrame | None = None

    @staticmethod
    def __check_folders():
        """
        Check if folders are existed
        """
        path = Path('images')
        if not path.exists():
            path.mkdir()
            # or
            # if not os.path.isdir('images'):
            # os.makedirs('images')
        path = Path('results')
        if not path.exists():
            path.mkdir()

    def __begin_action(self):
        surveys = list(filter(os.path.isfile, Path('results').glob('*survey.yaml')))
        self.is_filling_survey = False
        if not surveys:
            # todo: release demo mode
            self.is_filling_survey = True
            self.__survey_dialog(self.tk)
            # self.imgFrame.tk.title(self.imgFrame.language[self.cur_lang]['title']+"[ demo ]")

        if surveys and not self.is_loaded_survey:
            self.__survey_parse(YAML.read(surveys[0]))
            self.experiment.mode = 'full'

        if not self.is_filling_survey:
            self.load_dialog(self.tk)

    def load_dialog(self, parent_tk):
        win = CustomDialog.load_dialog(parent_tk, self.cur_lang)
        self.load_frame = LoadFrame(win, self.cur_lang)
        self.load_frame.configure(
            {'start': {'command': lambda top=win: self.__start_experiment(top)},
             'load_1': {'command': lambda: threading.Thread(target=self.__load_start).start()},
             'load_all': {'command': lambda: threading.Thread(target=self.__load_start, args=(True,)).start()}})

        local_images = list(filter(os.path.isfile, Path('images').glob('I*.bmp')))
        local_config = list(filter(os.path.isfile, Path('images').glob('imageconf*.yaml')))
        if local_config:
            conf = YAML.read(local_config[0])
            total = len(conf['images']) + len(conf['references'])
        else:
            total = len(local_images)
        num = len(local_images)

        if total == 0 and num == 0:  # division by zero
            self.load_frame.configure(
                {'lbl1': {'text': self.load_frame.language[self.cur_lang]['progress']
                                      .format(num, total, 0)},
                 'progress': {'value': 0}})
        else:
            self.load_frame.configure(
                {'lbl1': {'text': self.load_frame.language[self.cur_lang]['progress']
                                      .format(num, total, round(num / total, 2) * 100)},
                 'progress': {'value': round(num / total, 2) * 100}})
        self.is_loading = False
        self.is_cancel = False

    def __load_start(self, is_all: bool = False):
        # if not self.load_frame.isinternet.get():
        #     CustomDialog.ok_dialog(self.tk, self.cur_lang, 'noinettitle', 'noinetmessage')
        #     return
        # print(asyncio.all_tasks())
        if not self.is_loading:
            self.__load_button_update(is_all, 'stop')
            self.is_cancel = False
            self.is_loading = True
            self.__load_tasks_manager(is_all)
            self.__load_button_update(is_all, 'load_button')
            self.is_loading = False
        else:
            self.is_cancel = True

    def __load_tasks_manager(self, is_all: bool):
        if not is_all:
            if not self.__init_experiment():
                return
            dist_im, local_im = self.__get_downloadable_list()
        else:
            confs = list(filter(os.path.isfile, Path('images').glob('imageconf*.yaml')))
            if not confs:
                return

            config = YAML.read(confs[0].name, 'images')
            dist_im = set(list(config['images'].keys()) +
                          list(config['references']))
            local_im = set([item.name for item in list(filter(os.path.isfile, Path('images').glob('I*.bmp')))])

        load_list = list(set(dist_im) - set(local_im))
        total = len(dist_im)
        exist = total - len(load_list)
        self.__sync_gui_update(exist, total, is_all)

        # downloaded = asyncio.Queue(maxsize=5)
        for item in load_list:
            if self.is_cancel:
                return

            file_name = item
            self.network.download_file(file_name, file_id=self.network.images[file_name]['fileid'])
            exist += 1
            self.__sync_gui_update(exist, total, is_all)

    def __load_button_update(self, is_all: bool, text_type: str):
        if is_all:
            self.load_frame.configure(
                {'load_all': {'text': self.load_frame.language[self.cur_lang][text_type]}})
        else:
            self.load_frame.configure(
                {'load_1': {'text': self.load_frame.language[self.cur_lang][text_type]}})

    def __sync_gui_update(self, current: int, total: int, is_all: bool):
        self.load_frame.configure(
            {'lbl1': {'text': self.load_frame.language[self.cur_lang]['progress']
                                  .format(current, total, round(current / total * 100))},
             'progress': {'value': round(current / total * 100, 2)}})
        if not is_all:
            self.load_frame.configure(
                {'lbl2': {'text': self.load_frame.language[self.cur_lang]['load_single']
                                      .format(round((total - current) * 589878 / 1024 / 1024, 1))}})
        else:
            self.load_frame.configure(
                {'lbl3': {'text': self.load_frame.language[self.cur_lang]['load_all']
                                      .format(round((total - current) * 589878 / 1024 / 1024 / 1024, 2))}})

    def __config_update(self):
        # async
        pattern = r'imageconf_\d{1,2}\.\d{1,2}\.yaml'

        remote_config = [re.findall(pattern, name) for name in list(self.network.yaml_files.keys())]
        remote_config = list(map(lambda x: x[0], filter(None, remote_config)))

        local_config = list(filter(os.path.isfile, Path('images').glob('imageconf*.yaml')))
        if not local_config:
            self.network.download_file(file_name=remote_config[0], file_id=self.network.yaml_files[remote_config[0]])
            return

        l_version = re.search(r'\d{1,2}\.\d{1,2}', local_config[0].name).group(0)
        r_version = re.search(r'\d{1,2}\.\d{1,2}', remote_config[0]).group(0)
        self.conf_version = float(l_version)
        self.r_conf_version = float(r_version)

        # modified time
        lmtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(Path(local_config[0]).stat().st_mtime))
        cloudtime = self.network.yaml_files[remote_config]['modified']
        rmtime = time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(cloudtime, '%a, %d %b %Y %H:%M:%S %z'))

        if float(l_version) < float(r_version) or lmtime < rmtime:
            os.rename(os.path.join('images', local_config[0].name),
                      os.path.join('images', local_config[0].name + '.bak'))
            # await
            self.network.download_file(file_name=remote_config[0], file_id=self.network.yaml_files[remote_config[0]])

    def __get_downloadable_list(self) -> (list[str], list[str]):
        if self.experiment.status != 'init':
            return [], []

        dist_im = set([item[0] for item in self.experiment.pairs])
        ref_im = set([item[1] for item in self.experiment.pairs])
        dist_im.update(ref_im)

        local_im = set([item.name for item in list(filter(os.path.isfile, Path('images').glob('I*.bmp')))])
        return list(dist_im), list(local_im)

    def __survey_dialog(self, parent_tk):
        win = CustomDialog.survey_dialog(parent_tk, self.cur_lang)
        survey = SurveyFrame(win, self.cur_lang)
        survey.configure({'button': {'command': lambda: self.__survey_save(win, survey.get_data())}})

    def __survey_save(self, dialog, data: dict):
        """
        Create custom dialog windows for saving user experiments data to file
        :param dialog: parent window
        :param data: gathered data to save
        """
        if not data:
            CustomDialog.ok_dialog(dialog, self.cur_lang, 'survey', 'survey_mistake')
            # win.focus_set()
        else:
            YAML.write(data, f'{data["name"]}_survey.yaml', 'results')
            Network.upload_file(data['name'], f'{data["name"]}_survey.yaml', 'results')
            dialog.destroy()
            self.experiment.mode = 'demo'
            self.__survey_parse(data)
            self.is_filling_survey = False

    def __survey_parse(self, data: dict):
        self.imgFrame.configure({'name': {'text': data['name']}})
        self.is_loaded_survey = True
        # todo: display additional user information

    def lock_buttons(self, state: bool):
        if state:
            self.imgFrame.configure({'b1': {'state': DISABLED}, 'b2': {'state': DISABLED},
                                     'b3': {'state': DISABLED}, 'b4': {'state': DISABLED}})
            self.imgFrame.configure({'b5': {'text': self.imgFrame.language[self.imgFrame.cur_lang]['start'],
                                            'command': lambda: self.__begin_action(), 'state': NORMAL}})
        else:
            # demo or full
            self.imgFrame.configure({'b1': {'state': NORMAL}, 'b2': {'state': NORMAL},
                                     'b3': {'state': NORMAL}, 'b4': {'state': NORMAL}})
            self.imgFrame.configure({'b5': {'text': self.imgFrame.language[self.imgFrame.cur_lang]['b5']}})

    def start(self):
        self.tk.mainloop()

    def __init_experiment(self) -> bool:
        if self.network is None or not self.network.json:
            self.network = Network()
            self.network.get_json()
            self.network.get_basics()
            # update config
            self.__config_update()

        if self.experiment.status != 'init':
            success = self.experiment.init_experiment()
            if not success:
                print('not init experiment')
                CustomDialog.ok_dialog(self.tk, self.cur_lang, 'noexpertitle', 'noexpermessage')
                return False
            return True
        return True

    def __start_experiment(self, win: Tk | Toplevel):

        if not self.__init_experiment():
            return
        dist_im, local_im = self.__get_downloadable_list()
        load_list = list(set(dist_im) - set(local_im))
        total = len(dist_im)
        exist = total - len(load_list)
        self.__sync_gui_update(exist, total, False)

        if len(set(dist_im) - set(local_im)) > 0:
            CustomDialog.ok_dialog(win, self.cur_lang, 'needloadtitle', 'needloadmessage')
            return

        print(f"start experiment ({self.experiment.mode})")
        self.lock_buttons(False)
        win.destroy()
        # self.experiment.mode == "demo" / "full"
        self.experiment.start_experiment()


class CustomFrame(ABC):

    def __init__(self, parent: Tk):
        frame = Frame(parent)
        self.tk = parent
        self._layout(frame)

    def _layout(self, frame: Frame) -> None:
        frame.grid()
        self.font = font.Font(font=font.nametofont('TkDefaultFont'))
        self.font['size'] = 11
        self.tk.option_add("*Font", self.font)

    @abstractmethod
    def get_frame(self) -> Frame:
        pass

    def configure(self, widgets_config: dict) -> None:
        widgets = widgets_config.keys()
        for widget in widgets:
            getattr(self, widget).config(**widgets_config[widget])


class SurveyFrame(CustomFrame):
    language = {
        'ua': {
            'intro': "Контрольні питання щодо умов проведення\nекспериментів з візуальної помітності завад",
            'name': "Ім'я:",
            'name_hint': "Ім'я, прізвище, група",
            'age': "Вік:",
            'device_type': ["Тип пристрою:", "Монітор", "Ноутбук", "Проектор", "Інше"],
            'device': "Модель пристрою:",
            'screen_size': "Діагональ екрану:",
            'resolution': "Роздільна здатність:",
            'resolution_hint': "1920x1080",
            'luminance': "Яскравість екрану (%):",
            'light': ["Освітлення приміщення:", "штучне", "природне"],
            'description': "Перелічені фактори суттєво впливають\nна результати експериментів і є " +
                           "обов'язковими для внесення\n(використовуються лише для статистичних досліджень)",
            'save': "Зберегти"
        },
        'en': {
            'intro': "Control questions about the conditions for\nconducting experiments on the distortions visibility",
            'name': "Name:",
            'name_hint': "Name, Surname",
            'age': "Age:",
            'device_type': ["Device type:", "Monitor", "Laptop", "Projector", "Other"],
            'device': "Device model:",
            'screen_size': "Screen diagonal:",
            'resolution': "Resolution:",
            'resolution_hint': "1920x1080",
            'luminance': "Screen brightness (%):",
            'light': ["Room lighting:", "artificial", "natural"],
            'description': "The listed factors significantly affect\nthe results of experiments and " +
                           "are mandatory to enter\n(used only for statistical studies)",
            'save': "Save"

        }
    }
    cur_lang = 'ua'

    def __init__(self, parent: Tk | Toplevel | None = None, lang: str = 'ua'):
        self.cur_lang = lang
        super().__init__(parent)
        self.__set_default_values()

    def _layout(self, frame: Frame) -> None:
        self.__frame = frame
        super()._layout(frame)
        self.labels = dict()
        Label(frame, text=self.language[self.cur_lang]['intro'], anchor="w", justify="left") \
            .grid(row=0, column=0, columnspan=2, sticky=E + W, padx=5, pady=2)

        self.labels['name'] = Label(frame, text=self.language[self.cur_lang]['name'], anchor="w", justify="left")
        self.labels['name'].grid(row=1, column=0, sticky=E + W, padx=5, pady=2)
        self.name = EntryWithHint(frame, hint=self.language[self.cur_lang]['name_hint'])
        self.name.config(width=30)
        self.name.grid(row=1, column=1, sticky=E + W, padx=5, pady=2)

        self.labels['age'] = Label(frame, text=self.language[self.cur_lang]['age'], anchor="w", justify="left")
        self.labels['age'].grid(row=2, column=0, sticky=E + W, padx=5, pady=2)
        self.age = Scale(frame, variable=IntVar(value=0), from_=0, to=100, orient=HORIZONTAL)
        # self.age = Spinbox(frame, from_=10, to=100, width=10, textvariable=StringVar(value=str(10)))
        self.age.grid(row=2, column=1, sticky=E + W, padx=5, pady=2)

        self.labels['device_type'] = Label(frame, text=self.language[self.cur_lang]['device_type'][0], anchor="w",
                                           justify="left")
        self.labels['device_type'].grid(row=3, column=0, sticky=E + W, padx=5, pady=2)
        def_device = StringVar(value=self.language[self.cur_lang]['device_type'][1])
        self.device_type = ttk.Combobox(frame, textvariable=def_device,
                                        values=self.language[self.cur_lang]['device_type'][1:], width=15,
                                        state="readonly")
        # lst = Listbox(frame, listvariable=Variable(value=), width=15)
        self.device_type.grid(row=3, column=1, sticky=E + W, padx=5, pady=2)

        self.labels['device'] = Label(frame, text=self.language[self.cur_lang]['device'], anchor="w", justify="left")
        self.labels['device'].grid(row=4, column=0, sticky=E + W, padx=5, pady=2)
        self.device = Entry(frame, width=20)
        self.device.grid(row=4, column=1, sticky=E + W, padx=5, pady=2)

        self.labels['screen_size'] = Label(frame, text=self.language[self.cur_lang]['screen_size'], anchor="w",
                                           justify="left")
        self.labels['screen_size'].grid(row=5, column=0, sticky=E + W, padx=5, pady=2)
        self.screen = Entry(frame, width=15)
        self.screen.grid(row=5, column=1, sticky=E + W, padx=5, pady=2)

        self.labels['resolution'] = Label(frame, text=self.language[self.cur_lang]['resolution'], anchor="w",
                                          justify="left")
        self.labels['resolution'].grid(row=6, column=0, sticky=E + W, padx=5, pady=2)
        self.resol = EntryWithHint(frame, hint=self.language[self.cur_lang]['resolution_hint'])  # split by x_ua, x_en
        self.resol.config(width=15)
        self.resol.grid(row=6, column=1, sticky=E + W, padx=5, pady=2)

        self.labels['luminance'] = Label(frame, text=self.language[self.cur_lang]['luminance'], anchor="w",
                                         justify="left")
        self.labels['luminance'].grid(row=7, column=0, sticky=E + W, padx=5, pady=2)
        self.lum = Scale(frame, variable=IntVar(value=-1), from_=-1, to=100, orient=HORIZONTAL)
        # self.lum = Spinbox(frame, from_=-1, to=100, width=10, textvariable=StringVar(value=str(-1)))
        self.lum.grid(row=7, column=1, sticky=E + W, padx=5, pady=2)

        self.labels['light'] = Label(frame, text=self.language[self.cur_lang]['light'][0], anchor="w", justify="left")
        self.labels['light'].grid(row=8, column=0, sticky=E + W, padx=5, pady=2)
        self.light = ttk.Combobox(frame, values=self.language[self.cur_lang]['light'][1:], width=15, state="readonly")
        self.light.grid(row=8, column=1, sticky=E + W, padx=5, pady=2)

        Label(frame, text=self.language[self.cur_lang]['description'], anchor="w", justify="left") \
            .grid(row=9, column=0, columnspan=2, sticky=E + W, padx=5, pady=2)
        self.button = Button(frame, text=self.language[self.cur_lang]['save'])
        self.button.grid(row=10, column=0, columnspan=2, padx=5, pady=(2, 5))

    def __set_default_values(self):
        # put resolution
        self.resol.delete(0, END)
        self.resol.insert(0, f"{self.tk.winfo_screenwidth()}x{self.tk.winfo_screenheight()}")
        self.resol.config(fg='black')

    def get_data(self) -> dict:

        if self.__data_check():
            data = {
                'name': self.name.get(),
                'age': int(self.age.get()),
                'device_type': self.device_type.current(),
                'device': self.device.get(),
                'screen_size': float(self.screen.get()),
                'resolution': re.split('[xXхХ]', self.resol.get()),
                'luminance': int(self.lum.get()),
                'light': self.light.current(),
                'mark': time.time(),
                'os': [platform.system(), platform.release(), platform.version()]
            }
        else:
            data = dict()
        return data

    def __data_check(self) -> bool:
        is_success = True

        if not self.name.get() or self.name['fg'] == 'grey':
            self.labels['name'].config(fg='red')
            is_success = False
        else:
            self.labels['name'].config(fg='black')

        if int(self.age.get()) == 0:
            self.labels['age'].config(fg='red')
            is_success = False
        else:
            self.labels['age'].config(fg='black')

        if not self.device_type.get():
            self.labels['device_type'].config(fg='red')
            is_success = False
        else:
            self.labels['device_type'].config(fg='black')

        if not self.device.get():
            self.labels['device'].config(fg='red')
            is_success = False
        else:
            self.labels['device'].config(fg='black')

        if not self.screen.get() or not self.screen.get().replace(".", "").replace(",", "").isnumeric():
            self.labels['screen_size'].config(fg='red')
            is_success = False
        else:
            self.labels['screen_size'].config(fg='black')

        if not self.resol.get() or len(re.split('[xXхХ]', self.resol.get())) < 2 or \
                self.resol['fg'] == 'grey':
            self.labels['resolution'].config(fg='red')
            is_success = False
        else:
            self.labels['resolution'].config(fg='black')

        if int(self.lum.get()) == -1:
            self.labels['luminance'].config(fg='red')
            is_success = False
        else:
            self.labels['luminance'].config(fg='black')

        if not self.light.get():
            self.labels['light'].config(fg='red')
            is_success = False
        else:
            self.labels['light'].config(fg='black')

        return is_success

    def get_frame(self) -> Frame:
        return self.__frame


class LoadFrame(CustomFrame):
    language = {
        'ua': {
            'load_notification': "Для проведення актуальних експериментів необхідно підключення до Інтернет\n" +
                                 "(оновлення конфігурації, завантаження зображень, відправка результатів).\n" +
                                 "Пряме посилання на хмарне сховище:",
            'link': "https://e.pcloud.link/publink/show?code=kZqDKsZ2AgMjJJTgpBAc2pfWpDzi55iOysX",
            'checkbutton': "Дозволити підключення до мережі Інтернет",
            'exist': "Наявність тестових зображень (вибірково до 75 на кожний експеримент):",
            'load_single': "Завантажити для одного експерименту (до {:.1f} Мб)",
            'load_all': "Завантажити всі зображення (до {:.2f} Гб)",
            'load_button': "Завантажити",
            'stop': "Зупинити",
            'start': "Почати",
            'cancel': "Відміна",
            'progress': "{:d} з {:d} ({:.0f}%)"
        },
        'en': {
            'load_notification': "To conduct actual experiments, you need an Internet connection\n"+
                                 "(updating the configuration, downloading images, sending results).\n"+
                                 "Direct link to cloud storage:",
            'link': "https://e.pcloud.link/publink/show?code=kZqDKsZ2AgMjJJTgpBAc2pfWpDzi55iOysX",
            'checkbutton': "Allow connection to the Internet",
            'exist': "Availability of test images (selectively up to 75 for each experiment):",
            'load_single': "Download for one experiment (up to {:.1f} MB)",
            'load_all': "Download all images (up to {:.2f} GB)",
            'load_button': "Download",
            'stop': "Stop",
            'start': "Start",
            'cancel': "Cancel",
            'progress': "{:d} from {:d} ({:.0f}%)"
        }
    }
    cur_lang = 'ua'

    def __init__(self, parent: Tk | Toplevel | None = None, lang: str = 'ua'):
        self.cur_lang = lang
        super().__init__(parent)

    def _layout(self, frame: Frame) -> None:
        self.__frame = frame
        super()._layout(frame)
        self.labels = dict()
        frame.grid_columnconfigure(0, weight=1, uniform="load_group")
        frame.grid_columnconfigure(1, weight=1, uniform="load_group")
        frame.grid_columnconfigure(2, weight=1, uniform="load_group")
        frame.grid_columnconfigure(3, weight=1, uniform="load_group")

        Label(frame, text=self.language[self.cur_lang]['load_notification'], anchor="w", justify="left") \
            .grid(row=0, column=0, columnspan=4, sticky=E + W, padx=5, pady=(2, 0))

        link = Label(frame, text=self.language[self.cur_lang]['link'], fg="blue", cursor="hand2",
                     anchor="w", justify="left")
        link.grid(row=1, column=0, columnspan=4, sticky=E + W, padx=5, pady=(0, 2))
        link.bind("<Button-1>", lambda e: LoadFrame.callback(self.language[self.cur_lang]['link']))

        # self.isinternet = IntVar(value=1)
        # # self.isinternet.set(1)
        # self.chk = Checkbutton(frame, text=self.language[self.cur_lang]['checkbutton'], variable=self.isinternet)
        # self.chk.grid(row=2, column=0, columnspan=4, sticky=W, padx=5, pady=2)
        # self.chk['command'] = lambda: self.get_check()
        # print(self.isinternet.get())
        # self.chk.toggle()
        # print(self.isinternet.get())

        Label(frame, text=self.language[self.cur_lang]['exist'], anchor="w", justify="left") \
            .grid(row=3, column=0, columnspan=4, sticky=E + W, padx=5, pady=2)
        self.progress = ttk.Progressbar(frame, orient="horizontal", length=100, value=0)
        # pb = ttk.Progressbar(root, mode="determinate")
        self.progress.grid(row=4, column=0, columnspan=3, padx=5, pady=(2, 5), sticky=E + W)
        self.lbl1 = Label(frame, text=self.language[self.cur_lang]['progress'].format(0, 0, 0), anchor="w",
                          justify="left")
        self.lbl1.grid(row=4, column=3, sticky=E + W, padx=5, pady=(2, 5))

        self.lbl2 = Label(frame, text=self.language[self.cur_lang]['load_single'].format(45), anchor="w",
                          justify="left")
        self.lbl2.grid(row=5, column=0, columnspan=3, sticky=E + W, padx=5, pady=2)
        self.load_1 = Button(frame, text=self.language[self.cur_lang]['load_button'])
        self.load_1.grid(row=5, column=3, sticky=E + W, padx=5, pady=(2, 5))

        self.lbl3 = Label(frame, text=self.language[self.cur_lang]['load_all'].format(1.7), anchor="w", justify="left")
        self.lbl3.grid(row=6, column=0, columnspan=3, sticky=E + W, padx=5, pady=2)
        self.load_all = Button(frame, text=self.language[self.cur_lang]['load_button'])
        self.load_all.grid(row=6, column=3, sticky=E + W, padx=5, pady=(2, 5))

        self.start = Button(frame, text=self.language[self.cur_lang]['start'], width=20)
        self.start.grid(row=7, column=0, columnspan=2, sticky=NSEW, padx=5, pady=(5, 10))
        self.cancel = Button(frame, text=self.language[self.cur_lang]['cancel'], width=20)
        self.cancel.grid(row=7, column=2, columnspan=2, sticky=NSEW, padx=5, pady=(5, 10))
        self.cancel['command'] = self.tk.destroy

    # def get_check(self) -> int:
    #     print(self.isinternet.get())
    #     return self.isinternet.get()

    def get_frame(self) -> Frame:
        return self.__frame

    @staticmethod
    def callback(url):
        webbrowser.open_new_tab(url)


class ImageFrame(CustomFrame):
    impath = 'images'
    gui_link: GUI

    lang_list = {'en': 'EN', 'ua': 'UA'}
    language = {
        'ua': {
            'b1': "Непомітні завади",
            'b2': "Малопомітні завади",
            'b3': "Помітні завади",
            'b4': "<< Назад",
            'b5': "Далі >>",
            'notification': "Примітка: зір кожного індивідуальний і залежить від\nвіку, самопочуття, втоми, " +
                            "пристрою та інших факторів.\nТому результати тестів можуть відрізнятися.",
            'start': "Розпочати",
            'save': "Зберегти",
            'title': "Visibility Test",
            'instruction': "Інструкція"
        },
        'en': {
            'b1': "Invisible distortions",
            'b2': "Barely visible distortions",
            'b3': "Noticeable distortions",
            'b4': "<< Previous",
            'b5': "Next >>",
            'notification': "Note: everyone's vision is individual and\ndepends on age, health, fatigue, device and\n" +
                            "other factors. Therefore, test results may vary",
            'start': "Start",
            'save': "Save",
            'title': "Visibility Test",
            'instruction': "Instruction"
        }
    }
    cur_lang = 'ua'

    def __init__(self, parent: Tk = None) -> None:
        self.dist_img = None
        self.ref_img = None
        self.selection: int = 0
        super().__init__(parent)

    def _layout(self, frame: Frame) -> None:
        self.__frame = frame
        super()._layout(frame)
        self.tk.title(self.language[self.cur_lang]['title'])

        self.ref_canvas = ZoomedCanvas(frame)
        self.ref_canvas.grid(row=1, column=0, padx=10, pady=2)
        self.dist_canvas = ZoomedCanvas(frame)
        self.dist_canvas.grid(row=1, column=1, padx=(0, 10), pady=2)

        self.dist_canvas.bind("<Motion>", self.mouse_motion)
        self.ref_canvas.bind("<Motion>", self.mouse_motion)
        frame.bind("<Motion>", self.mouse_motion)

        fr1 = Frame(frame)
        fr1.grid(row=0, column=0, columnspan=2, padx=6, pady=5, sticky=E + W)
        fr1.columnconfigure(1, weight=1)
        self.name = Label(fr1, text="Name", anchor="w", justify="left")
        self.name.grid(row=0, column=0, padx=(5, 10), pady=2, sticky=W)
        self.progress = ttk.Progressbar(fr1, orient="horizontal", length=300, value=0)
        self.progress.grid(row=0, column=1, padx=5, pady=2, sticky=S + E + W)

        self.lang = ttk.Combobox(fr1, values=list(self.lang_list.values()), width=15, state="readonly")
        self.lang.current(1)
        self.lang.grid(row=0, column=2, padx=5, pady=2, sticky=E)

        fr2 = Frame(frame, bd=2, relief=RIDGE)
        fr2.grid(row=2, column=0, columnspan=2, padx=12, pady=5, sticky=E + W)
        fr2.grid_columnconfigure(0, weight=1)
        # fr2.grid_columnconfigure(1, weight=0)
        fr2.grid_columnconfigure(2, weight=1)
        self.b1 = Button(fr2, text=self.language[self.cur_lang]['b1'], width=20, height=2,
                         command=lambda: self.__visibility_action(1, True), relief=RAISED)
        self.b1.grid(row=0, column=0, padx=5, pady=2, sticky=E)
        self.b2 = Button(fr2, text=self.language[self.cur_lang]['b2'], width=20, height=2,
                         command=lambda: self.__visibility_action(2, True), relief=RAISED)
        self.b2.grid(row=0, column=1, padx=5, pady=2)
        self.b3 = Button(fr2, text=self.language[self.cur_lang]['b3'], width=20, height=2,
                         command=lambda: self.__visibility_action(3, True), relief=RAISED)
        self.b3.grid(row=0, column=2, padx=5, pady=2, sticky=W)

        fr3 = Frame(frame)
        fr3.grid(row=3, column=0, columnspan=2, padx=6, pady=6, sticky=E + W)
        self.notification = Label(fr3, text=self.language[self.cur_lang]['notification'], anchor="w", justify="left")
        self.notification.grid(row=0, rowspan=2, column=0, padx=(5, 10), pady=2, sticky=W + S + N)

        self.instruction = Button(fr3, text=self.language[self.cur_lang]['instruction'], width=20, height=1,
                                  command=lambda: CustomDialog.instruction_dialog(self.tk, self.cur_lang, self.font))
        self.instruction.grid(row=0, column=1, padx=5, pady=2, sticky=N + W)
        sign = Label(fr3, text="OlegIeremeiev", fg="blue", cursor="hand2", anchor="w", justify="right")
        sign.grid(row=1, column=1, padx=5, pady=(0, 2), sticky=S + W)
        sign.bind("<Button-1>", lambda e: LoadFrame.callback("https://github.com/OlegIeremeiev/VisibilityTest"))

        self.b4 = Button(fr3, text=self.language[self.cur_lang]['b4'], width=15, height=2)
        self.b4.grid(row=0, rowspan=2, column=2, padx=5, pady=2, sticky=E + S + N)
        self.b5 = Button(fr3, text=self.language[self.cur_lang]['b5'], width=15, height=2)
        self.b5.grid(row=0, rowspan=2, column=3, padx=5, pady=2, sticky=E + S + N)
        fr3.grid_columnconfigure(1, weight=1)

    def __visibility_action(self, button_id: int, action: bool = True):

        match button_id:
            case 0:
                self.b1['relief'] = RAISED
                self.b2['relief'] = RAISED
                self.b3['relief'] = RAISED
                self.selection = 0
            case 1:
                self.b2['relief'] = RAISED
                self.b3['relief'] = RAISED
                if not action:
                    self.b1['relief'] = SUNKEN
                    self.selection = 1
                elif self.b1['relief'] == RAISED:
                    self.selection = 1
                    self.b1['relief'] = SUNKEN
                else:
                    self.selection = 0
                    self.b1['relief'] = RAISED
            case 2:
                self.b1['relief'] = RAISED
                self.b3['relief'] = RAISED
                if not action:
                    self.b2['relief'] = SUNKEN
                    self.selection = 2
                elif self.b2['relief'] == RAISED:
                    self.selection = 2
                    self.b2['relief'] = SUNKEN
                else:
                    self.selection = 0
                    self.b2['relief'] = RAISED
            case 3:
                self.b1['relief'] = RAISED
                self.b2['relief'] = RAISED
                if not action:
                    self.b3['relief'] = SUNKEN
                    self.selection = 3
                elif self.b3['relief'] == RAISED:
                    self.selection = 3
                    self.b3['relief'] = SUNKEN
                else:
                    self.selection = 0
                    self.b3['relief'] = RAISED
        if self.selection == 0:
            self.b4['state'] = DISABLED
            self.b5['state'] = DISABLED
        else:
            self.b4['state'] = NORMAL
            self.b5['state'] = NORMAL

    def set_selection(self, value: int = 0):
        if value not in [0, 1, 2, 3]:
            value = 0
        self.__visibility_action(value, False)

    def get_selection(self) -> int:
        return self.selection

    def set_ref_image(self, image_name: str) -> None:
        path = os.path.join(self.impath, image_name)
        self.ref_img = Image.open(path, mode='r')
        self.ref_canvas.set_image(self.ref_img)

    def set_dist_image(self, image_name: str) -> None:
        path = os.path.join(self.impath, image_name)
        self.dist_img = Image.open(path, mode='r')
        self.dist_canvas.set_image(self.dist_img)

    def get_frame(self) -> Frame:
        return self.__frame

    def init_lang_action(self, gui: GUI):
        self.gui_link = gui
        self.lang.bind('<<ComboboxSelected>>', lambda: self.__select_lang())

    def __select_lang(self) -> None:
        lang = self.lang.get().lower()
        self.cur_lang = lang
        self.notification['text'] = self.language[self.cur_lang]['notification']
        self.instruction['text'] = self.language[self.cur_lang]['instruction']
        self.b1['text'] = self.language[self.cur_lang]['b1']
        self.b2['text'] = self.language[self.cur_lang]['b2']
        self.b3['text'] = self.language[self.cur_lang]['b3']
        self.b4['text'] = self.language[self.cur_lang]['b4']

        self.b5['text'] = self.language[self.cur_lang]['start'] if self.b4['state'] == DISABLED else (
            self.language)[self.cur_lang]['b5']
        self.gui_link.cur_lang = lang

    def mouse_motion(self, event):
        cx = 0
        cy = 0
        if isinstance(event.widget, Canvas):
            cx = event.x - 4
            cy = event.y - 4
            # cx=self.winfo_pointerx() - self.winfo_rootx()
            # cy=self.winfo_pointery() - self.winfo_rooty()
        self.dist_canvas.after(0, self.dist_canvas.canvas_zooming(event, cx, cy))
        self.ref_canvas.after(0, self.ref_canvas.canvas_zooming(event, cx, cy))


class ZoomedCanvas(Canvas):
    photoimg: ImageTk.PhotoImage | None
    tmp: ImageTk.PhotoImage

    def __init__(self, master: Frame = None) -> None:
        # self.image = image
        # if image is None:
        w, h = (512, 384)
        super().__init__(master, height=h, width=w)
        self.photoimg = None
        self.pilzoom = None
        # else:
        #     self.photoimg = ImageTk.PhotoImage(image)
        #     w, h = image.size
        #     self.pilzoom = image.resize((w*2, h*2), Image.ANTIALIAS)
        #     # self.zoomimg = self.photoimg._PhotoImage__photo.zoom(2)
        #     super().__init__(master, height=h, width=w)
        #     self.create_image(4, 4, image=self.photoimg, anchor=NW)
        self.is_zoomed = False
        self.config(bd=2, relief=RIDGE)

    def set_image(self, image):
        self.photoimg = ImageTk.PhotoImage(image)
        w, h = image.size
        self.pilzoom = image.resize((w * 2, h * 2), Image.LANCZOS)
        self.create_image(4, 4, image=self.photoimg, anchor=N + W)
        self.is_zoomed = False

    def canvas_zooming(self, event, cx, cy):
        if isinstance(event.widget, Canvas) and self.photoimg is not None:
            # cx=self.winfo_pointerx() - self.winfo_rootx()
            # cy=self.winfo_pointery() - self.winfo_rooty()

            area = (cx, cy, cx + self.photoimg.width(), cy + self.photoimg.height())
            self.tmp = ImageTk.PhotoImage(self.pilzoom.crop(area))
            self.create_image(4, 4, image=self.tmp, anchor=N + W)
            # self.create_image(-cx, -cy, image=self.zoomimg, anchor=NW)
            self.is_zoomed = True

        else:
            if self.is_zoomed:
                self.create_image(4, 4, image=self.photoimg, anchor=N + W)
                self.is_zoomed = False


class EntryWithHint(Entry):
    def __init__(self, master=None, hint="", color='grey'):
        super().__init__(master)
        self.hint = hint
        self.hint_color = color
        self.default_fg_color = self['fg']
        self.bind("<FocusIn>", self.foc_in)
        self.bind("<FocusOut>", self.foc_out)

        self.put_hint()

    def put_hint(self):
        self.insert(0, self.hint)
        self['fg'] = self.hint_color

    def foc_in(self, *args):
        if self['fg'] == self.hint_color:
            self.delete('0', 'end')
            self['fg'] = self.default_fg_color

    def foc_out(self, *args):
        if not self.get():
            self.put_hint()


class Experiment:
    # todo: demo шаблон значення, з заміною на актуальні для поточної ситуації

    def __init__(self, gui: GUI):
        self.gui = gui
        self.status = 'none'
        self.mode = 'none'
        self.rounds = 10
        self.round = 0
        self.pairs = []
        self.results = []
        self.returns: int = 0
        self.begin_time: float = 0
        self.end_time: float = 0
        self.times = []

    @staticmethod
    def get_images_stats(images: list, config: dict | None) -> (list, list, list):
        if not config:
            return images, [], []

        less_half = []
        more_half = []
        over_limited = []
        limit = int(config['limit'])
        for im in images:
            if int(config['images'][im]) < round(limit / 2):
                less_half.append(im)
            elif int(config['images'][im]) < round(limit * 0.9):
                more_half.append(im)
            else:
                over_limited.append(im)
        return less_half, more_half, over_limited

    @staticmethod
    def generate_pairs(images: list, number: int) -> set:
        pairs = set()
        while len(pairs) < number:
            name = random.choice(images)
            ref = re.match(r'I\d{2}', name).group(0) + '.bmp'
            pairs.add((name, ref))
        return pairs

    def init_experiment(self) -> bool:

        confs = list(filter(os.path.isfile, Path('images').glob('imageconf*.yaml')))
        config = YAML.read(confs[0].name, 'images') \
            if confs else None

        if config:
            images = list(config['images'].keys())
            if not self.gui.r_version:
                self.gui.r_version = float(config['app_version'])
            if self.gui.r_version > self.gui.version:
                CustomDialog.ok_link_dialog(self.gui.tk, self.gui.cur_lang, 'newveriontitle',
                                            'newversionmessage', 'newversionlink')
        else:
            images = list(filter(os.path.isfile, Path('images').glob('I*.bmp')))

        if len(images) < self.rounds * 2:
            # not enough, no test
            return False

        self.status = 'init'
        # distribution
        less_half, more_half, over_limited = self.get_images_stats(images, config)

        num_lowest = 0
        num_half = 0
        num_highest = 0
        if len(less_half) > 0.5 * len(images):
            num_lowest = self.rounds
        elif len(less_half) > 0.5 * len(images):
            num_lowest = min(round(self.rounds * 0.75), len(less_half))
            num_half = min(self.rounds - num_lowest, len(more_half))
            num_highest = self.rounds - (num_lowest + num_half)
            # 75 / 25
            # 10 / 90
            # 10 / min(90,65) / 25
        else:
            num_lowest = min(round(self.rounds * 0.5), len(less_half))
            num_highest = min(round(self.rounds * 0.25), len(over_limited))
            num_half = min(self.rounds - (num_lowest + num_highest), len(more_half))
            num_highest = self.rounds - (num_lowest + num_half)

        pairs = self.generate_pairs(less_half, num_lowest)
        pairs.update(self.generate_pairs(more_half, num_half))
        pairs.update(self.generate_pairs(over_limited, num_highest))

        self.pairs = list(pairs)
        self.results = [0] * self.rounds
        self.times = [0.0] * self.rounds
        self.round = 0
        return True

    def start_experiment(self):
        self.status = 'started'
        self.gui.imgFrame.configure({'b4': {'command': lambda: self.__previous_action()}})
        self.gui.imgFrame.configure({'b5': {'command': lambda: self.__next_action()}})
        self.begin_time = time.time()
        self.__set_round(0)

    def __set_round(self, r: int):
        self.round = r
        self.__b4_b5_options()
        self.gui.imgFrame.set_selection(self.results[self.round])
        self.gui.imgFrame.configure({'progress': {'value': round(self.round / (self.rounds - 1) * 100)}})
        self.gui.imgFrame.set_ref_image(self.pairs[r][1])
        self.gui.imgFrame.set_dist_image(self.pairs[r][0])

    def __next_action(self):
        if self.round >= self.rounds:
            return
        if self.round == self.rounds - 1:
            self.__save_results()
            return
        self.results[self.round] = self.gui.imgFrame.get_selection()
        if self.round < self.rounds - 1:
            if self.returns > 0:
                self.returns -= 1
            if self.returns == 0:
                self.times[self.round] = time.time()
            self.__set_round(self.round + 1)

    def __previous_action(self):
        if self.round < 0:
            return
        self.results[self.round] = self.gui.imgFrame.get_selection()
        if self.round > 0:
            self.returns += 1
            self.__set_round(self.round - 1)

    def __b4_b5_options(self):
        if self.round == self.rounds - 1:
            self.gui.imgFrame.configure({'b5': {'text': self.gui.imgFrame.language[self.gui.cur_lang]['save']}})
        else:
            self.gui.imgFrame.configure({'b5': {'text': self.gui.imgFrame.language[self.gui.cur_lang]['b5']}})

    def __save_results(self):
        self.end_time = time.time()
        self.times[-1] = self.end_time
        self.results[self.round] = self.gui.imgFrame.get_selection()  # the last selection

        saved_result = dict()
        saved_result['name'] = YAML.read(list(filter(os.path.isfile, Path('results').glob('*survey.yaml')))[0])['name']
        saved_result['begin_time'] = self.__formatted_time('%Y-%m-%d %H:%M:%S', self.begin_time)
        saved_result['end_time'] = self.__formatted_time('%Y-%m-%d %H:%M:%S', self.end_time)
        saved_result['markers'] = [self.begin_time, self.end_time]
        saved_result['rnd'] = random.randint(1000000, 9999999)
        saved_result['conf_version'] = self.gui.conf_version
        saved_result['app_version'] = self.gui.version

        res = []
        for i, p in enumerate(self.pairs):
            res.append([p[0], self.results[i], self.times[i]])
        print(res)
        saved_result['results'] = res

        file_name = f"{saved_result['name']} {self.__formatted_time('%Y-%m-%d %H.%M.%S', self.begin_time)}.yaml"
        YAML.write(saved_result, file_name, 'results')

        Network.upload_file(saved_result['name'], file_name, 'results')
        # to do yaml
        # to do upload
        self.__clear()
        CustomDialog.ok_dialog(self.gui.tk, self.gui.cur_lang, 'savetitle', 'savemessage')
        self.gui.lock_buttons(True)
        # self.gui.load_dialog(self.gui.tk)

    @staticmethod
    def __formatted_time(pattern: str, t: float) -> str:
        return time.strftime(pattern, time.localtime(t))

    def __clear(self):
        self.round = 0
        self.pairs = []
        self.results = []
        self.status = 'none'
        self.gui.imgFrame.set_selection(0)
        # self.gui.imgFrame.set_ref_image(None)
        self.returns = 0
        self.begin_time = 0
        self.end_time = 0
        self.times = []


class Demo(Experiment):
    pass


# static classes
class ModalDialog:
    """Unified modal dialog for the app"""

    @staticmethod
    def create_dialog(parent_window: Tk = None, title: str = "Info", modal: bool = True,
                      resizable=(False, False)) -> Toplevel:
        win = Toplevel(parent_window)
        win.grid()
        win.resizable(*resizable)
        win.title(title)

        # parent_window.eval('tk::PlaceWindow . center')
        coords = (parent_window.winfo_x(), parent_window.winfo_y(), parent_window.winfo_width(),
                  parent_window.winfo_height())
        win.geometry(f'+{round(coords[0] + coords[2] / 2)}+{round(coords[1] + coords[3] / 2)}')

        if modal:
            ModalDialog.__dialog_make_modal(win, parent_window)
        return win

    @staticmethod
    def __dialog_make_modal(window, parent_window):
        """
        Make a modal dialog if required
        :param parent_window: parent window
        """
        window.focus_set()  # принять фокус ввода,
        window.grab_set()  # Запретить доступ к др. окнам, пока открыт диалог (not Linux)
        # self.win.wait_window() # not for quit
        window.transient(parent_window)  # + Linux(запретить доступ к др. окнам)


class CustomDialog:

    @staticmethod
    def _messages(current_lang: str) -> dict:
        language = {
            'ua': {
                'exit': "Вихід",
                'exit_question': "Вийти з програми?",
                'yes': "Так",
                'no': "Ні",
                'survey': "Опитування",
                'survey_mistake': "Некоректні дані",
                'load': "Завантаження",
                'noinetmessage': "Немає дозволу на\nпідключення до Інтернет",
                'noinettitle': "Немає дозволу",
                'noexpertitle': "Помилка експерименту",
                'noexpermessage': "Неможливо запустити експеримент,\nнедостатня кількість зображень",
                'needloadtitle': "Необхідне завантаження",
                'needloadmessage': "Необхідно завантажити відсутні\nзображення для початку експерименту",
                'newveriontitle': "Оновлення програми",
                'newversionmessage': "Опубліковано нову версію програми.\nБудь-ласка оновіть за посиланням:",
                'newversionlink': "https://github.com/OlegIeremeiev/VisibilityTest",
                'savetitle': "Збереження",
                'savemessage': "Результат успішно збережено",
                'instructiontitle': "Інструкція",
                'instructionmessage':
                    """Тест з візуальної помітності завад на зображенні
Мета: визначити візуальну помітність дефектів на зображеннях зі спотвореннями (справа) враховуючи фактори індивідуальності зору, віку, характеристик пристроїв відображення тощо. За результатами тестів можливо буде визначено типи завад і допустимі їх інтенсивності, що практично непомітні для людини
Інтерфейс програми:
- два зображення: оригінал (зліва) і з завадами (справа)
- кнопки вибору інтенсивності завад (невидимі / малопомітні / явно помітні)
- кнопки переходу між раундами (назад / далі)
- прогрес-бар для індикації ступеню проходження тесту
Примітка: зображення при наведенні збільшуються в 2 рази, при виведенні курсору за межі зображення повертається початковий масштаб
Завдання: 
На кожному раунді тесту відображаються два зображення (оригінальне зліва і з завадами - справа). 
Якщо відразу бачите відмінність окремих пікселів або фрагментів у зображеннях без збільшення масштабу або вони достатньо сильні на збільшеному масштабі - то завади "помітні", якщо на оригінальному масштабі різницю не помітно і проявляються лише незначні відмінності при збільшеному масштабі - такі завади "малопомітні", а якщо не побачили різниці і при збільшеному масштабі, то позначаємо "непомітні". Рекомендація - кожній парі зображень приділяти увагу не більше 5-7 секунд, ключовим є враження "на перший погляд". 
Програма повністю автономна: автоматично завантажує необхідні зображення з хмари і здатна відправляти в хмару отримані результати. За наведеними посиланнями можна і самостійно як завантажити всі зображення і розмістити в папці "images", так і завантажити отримані результати у формати yaml-файлів (будуть дублікатами, якщо не було обмежень в роботі мережі Інтернет).
"""
            },
            'en': {
                'exit': "Exit",
                'exit_question': "Exit the program?",
                'yes': "Yes",
                'no': "No",
                'survey': "Survey",
                'survey_mistake': "Incorrect data",
                'load': "Loading",
                'noinetmessage': "No permission to\nconnect to the Internet",
                'noinettitle': "No permission",
                'noexpertitle': "Experiment error",
                'noexpermessage': "Unable to run experiment, insufficient number of images",
                'needloadtitle': "Download required",
                'needloadmessage': "The missing images must be loaded to start the experiment",
                'newveriontitle': "Update the program",
                'newversionmessage': "A new version of the program has been\npublished. Please update using the link:",
                'newversionlink': "https://github.com/OlegIeremeiev/VisibilityTest",
                'savetitle': "Saving",
                'savemessage': "The result was saved successfully",
                'instructiontitle': "todo",
                'instructionmessage': "todo"
            }
        }
        return language[current_lang]

    @staticmethod
    def quit_dialog(parent_window: Tk | Toplevel | None, language):
        """
        Create custom dialog window for program quit
        :param parent_window: main frame to which this dialog needs to be attached
        :param language: selected language for all messages
        """
        messages = CustomDialog._messages(language)
        win = ModalDialog.create_dialog(parent_window, title=messages['exit'])

        Label(win, text=messages['exit_question']) \
            .grid(column=0, row=0, columnspan=2, sticky=N + S, padx=10, pady=2)
        Button(win, text=messages['yes'], command=parent_window.quit, width=5) \
            .grid(column=0, row=1, sticky=NSEW, padx=10, pady=5)
        Button(win, text=messages['no'], command=win.destroy, width=5) \
            .grid(column=1, row=1, sticky=NSEW, padx=10, pady=5)

    @staticmethod
    def survey_dialog(parent_window: Tk | Toplevel | None, language) -> Toplevel:
        messages = CustomDialog._messages(language)
        win = ModalDialog.create_dialog(parent_window, title=messages['survey'])
        win.protocol("WM_DELETE_WINDOW", lambda parent=win: CustomDialog.quit_dialog(parent, language))
        return win

    @staticmethod
    def ok_dialog(parent_window: Tk | Toplevel | None, language, title_type, message_type):
        messages = CustomDialog._messages(language)
        win = ModalDialog.create_dialog(parent_window, title=messages[title_type])
        Label(win, text=messages[message_type]) \
            .grid(column=0, row=0, sticky=N + S, padx=10, pady=2)
        Button(win, text=messages['yes'], command=win.destroy, width=5) \
            .grid(column=0, row=1, sticky=N + S, padx=10, pady=5)

    @staticmethod
    def ok_link_dialog(parent_window: Tk | Toplevel | None, language, title_type: str, message_type: str,
                       link_type: str):
        messages = CustomDialog._messages(language)
        win = ModalDialog.create_dialog(parent_window, title=messages[title_type])
        Label(win, text=messages[message_type]) \
            .grid(column=0, row=0, sticky=N + S, padx=10, pady=2)
        link = Label(win, text=messages[link_type], fg="blue", cursor="hand2")
        link.grid(column=0, row=1, sticky=N + S, padx=10, pady=2)
        link.bind("<Button-1>", lambda e: (CustomDialog.callback(messages[link_type]),
                                           win.destroy()))
        Button(win, text=messages['yes'], command=win.destroy, width=5) \
            .grid(column=0, row=2, sticky=N + S, padx=10, pady=5)

    @staticmethod
    def callback(url):
        webbrowser.open_new_tab(url)

    @staticmethod
    def load_dialog(parent_window: Tk | Toplevel | None, language) -> Toplevel:
        messages = CustomDialog._messages(language)
        win = ModalDialog.create_dialog(parent_window, title=messages['load'])
        # win.protocol("WM_DELETE_WINDOW", lambda parent=win: CustomDialog.quit_dialog(parent, language))
        return win

    @staticmethod
    def instruction_dialog(parent_window: Tk | Toplevel | None, language, custom_font:font):
        messages = CustomDialog._messages(language)
        win = ModalDialog.create_dialog(parent_window, title=messages['instructiontitle'])
        win.geometry(f'+{parent_window.winfo_x()}+{parent_window.winfo_y()}')

        text = Text(win, height=25, width=90, wrap=WORD, font=custom_font, relief=FLAT)
        text.insert(1.0, messages['instructionmessage'])
        text.grid(column=0, row=0, sticky=N + S, padx=10, pady=2)
        text.config(state=DISABLED)
        bold = font.Font(font=custom_font)
        bold['weight'] = 'bold'
        text.tag_config('bold', font=bold)
        text.tag_add('bold','2.0', '2.4')
        text.tag_add('bold','3.0', '3.18')
        text.tag_add('bold','8.0', '8.8')
        text.tag_add('bold','9.0', '9.8')
        but = Button(win, text=messages['yes'], command=win.destroy, width=5)
        but.grid(column=0, row=1, sticky=N + S, padx=10, pady=5)
        text['bg'] = but['bg']


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


class Network:
    yaml_files: dict
    images: dict

    def __init__(self):
        self.folder_id = 'kZqDKsZ2AgMjJJTgpBAc2pfWpDzi55iOysX'
        self.path = 'images'
        self.json = dict()

    # @staticmethod
    def get_json(self):
        session = requests.Session()
        url = 'https://eapi.pcloud.com/showpublink'
        post = session.post(url, data={'code': self.folder_id})
        self.json = post.json()

    def get_basics(self):
        self.yaml_files = self.get_filtered_file_list('yaml')
        self.images = self.get_filtered_file_list('bmp')

    def get_filtered_file_list(self, extension: str = 'bmp') -> dict[str, str]:
        parsed = self.json['metadata']['contents']

        file_list = dict()
        if extension is None:
            file_list = {k['name']: k['fileid'] for k in parsed}
        else:
            for k in parsed:
                if extension in k['name']:
                    file_list[k['name']] = {'fileid': k['fileid'], 'modified': k['modified']}

        return file_list

    def download_file(self, file_name: str, file_id: str):
        url = 'https://eapi.pcloud.com/getpubtextfile'
        session = requests.Session()
        post = session.post(url, data={'code': self.folder_id, 'fileid': file_id})

        p = post.content
        with open(os.path.join(self.path, file_name), 'wb') as f:
            f.write(p)
        # direct link: https://e.pcloud.link/publink/show?code=kZqDKsZ2AgMjJJTgpBAc2pfWpDzi55iOysX

    @staticmethod
    def upload_file(user_name, file_name: str, path: str) -> dict:

        url = 'https://eapi.pcloud.com/uploadtolink'
        code = 'CiaZKQ9Pomdr4MHEse2m09UOXhxGxQf7'

        files = {file_name: open(os.path.join(path, file_name), 'rb')}
        session = requests.Session()
        post = session.post(url, data={'code': code, 'names': user_name}, files=files)
        return post.json()


if __name__ == "__main__":
    GUI().start()
