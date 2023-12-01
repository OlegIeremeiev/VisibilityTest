from tkinter import Tk, Toplevel, Frame, Label, Button, Radiobutton, Spinbox, Entry, StringVar, EW, NSEW, NS, NW, E, W, N, S,  Canvas, FLAT, SUNKEN, RAISED, GROOVE, SOLID, RIDGE, DISABLED, NORMAL, END
from tkinter import ttk, font
import yaml
import re
import os, platform
from pathlib import Path, PosixPath
from PIL import Image, ImageTk
import _thread
from abc import ABC, abstractmethod
import random
import time


class GUI:

    language = {
        'ua': {
            'exit': "Вихід",
            'exit_question': "Вийти з програми?",
            'yes': "Так",
            'no': "Ні",
            'survey': "Опитування",
            'survey_mistake': "Некоректні дані"
        }
    }
    cur_lang = 'ua'

    def __init__(self):
        self.tk = Tk()
        self.tk.grid()
        self.tk.protocol("WM_DELETE_WINDOW", lambda parent=self.tk: self.__dialog_quit(parent))
        self.tk.resizable(False, False)

        is_need_survey = False
        path = Path('images')

        if not path.exists():
            path.mkdir()
            # or
            # if not os.path.isdir('images'):
            # os.makedirs('images')
            is_need_survey = True
        elif not any(path.iterdir()):
            is_need_survey = True
        
        path = Path('results')
        if not path.exists():
            path.mkdir()
            is_need_survey = True

        if not list(filter(os.path.isfile, path.glob('*survey.yaml'))):
            print(False)
            is_need_survey = True

        self.imgFrame = ImageFrame(self.tk)
        if is_need_survey:
            self.__survey_dialog(self.tk)
            self.imgFrame.configure({'b4': {'state': DISABLED}, 'b5': {'state': DISABLED}})
            # demo
        else:
            file = list(path.glob('*survey.yaml'))[0]
            with file.open('r') as f:
                self.__parse_survey(yaml.safe_load(f))
            
            pass
            # is_need_survey = False
            # do surve

            # if not os.path.exists('images'):
            # print(False)
        #     os.makedirs('images')
        #     is_need_survey = True

        # if not is_need_survey:
        # self.data = img.get_data()
        

    def __survey_dialog(self, parent):
        win = ModalDialog(parent=parent, title=self.language[self.cur_lang]['survey']).get_dialog()
        win.protocol("WM_DELETE_WINDOW", lambda parent=win: self.__dialog_quit(parent))
        survey = SurveyFrame(win)
        action = lambda: self.__survey_save(win, survey.get_data())
        survey.set_button_action(action)


    def __survey_save(self, dialog, data:dict):
        # check data

        if not data:
            win = ModalDialog(parent=dialog, title=self.language[self.cur_lang]['survey']).get_dialog()
            Label(win, text=self.language[self.cur_lang]['survey_mistake']).grid(column=0, row=0, sticky=NS, padx=10, pady=2)
            Button(win, text=self.language[self.cur_lang]['yes'], command=win.destroy, width=5).grid(column=0,row=1, sticky=NSEW, padx=10, pady=5)
            # win.focus_set()
        else:
            self.yaml = YAML()
            self.yaml.write(data, True)
            self.imgFrame.configure({'b4': {'state': NORMAL}, 'b5': {'state': NORMAL}})
            dialog.destroy()
            self.__parse_survey(data)


    def __dialog_quit(self, parent):
        win = ModalDialog(parent=parent, title=self.language[self.cur_lang]['exit']).get_dialog()
        Label(win, text=self.language[self.cur_lang]['exit_question']).grid(column=0, row=0, columnspan=2, sticky=NS, padx=10, pady=2)
        Button(win, text=self.language[self.cur_lang]['yes'], command=parent.quit, width=5).grid(column=0,row=1, sticky=NSEW, padx=10, pady=5)
        Button(win, text=self.language[self.cur_lang]['no'], command=win.destroy, width=5).grid(column=1,row=1, sticky=NSEW, padx=10, pady=5)

    def __parse_survey(self, data: dict):
        self.imgFrame.configure({'name': {'text':data['name']}})
        # pass

    def start(self):
        self.tk.mainloop()


class ModalDialog:

    def __init__(self, parent=None, title="Інформація",  modal=True, resizable=[False, False]):
        self.win = Toplevel(parent)
        self.win.grid()
        self.win.resizable(*resizable)
        self.win.title(title)

        if modal:
            self.__dialog_make_modal(parent)


    def __dialog_make_modal(self, parent):
        # make modal
        self.win.focus_set() # принять фокус ввода,
        self.win.grab_set() # запретить доступ к др. окнам, пока открыт диалог (not Linux)
        # self.win.wait_window() # not for quit
        self.win.transient(parent) # + Linux(запретить доступ к др. окнам)


    def get_dialog(self):
        return self.win


class CustomFrame(ABC):

    def __init__(self, parent: Tk):
        frame = Frame(parent)
        self._layout(frame)


    def _layout(self, frame:Frame) -> None:
        frame.grid()
        self.font = font.nametofont('TkDefaultFont')
        self.font['size'] += 2


    @abstractmethod
    def get_frame(self) -> Frame:
        pass

    @abstractmethod
    def configure(self, widgets_config:dict) -> None:
        pass


class SurveyFrame(CustomFrame):
    language = {
        'ua': {
            'intro': "Контрольні питання щодо умов проведення\nекспериментів з візуальної помітності завад",
            'name': "Ім'я:",
            'name_hint':"Ім'я, прізвище, група",
            'age': "Вік:",
            'device_type': ["Тип пристрою:", "Монітор", "Ноутбук", "Проектор", "Інше"],
            'device': "Модель пристрою:",
            'screen_size': "Діагональ екрану:",
            'resolution': "Роздільна здатність:",
            'resolution_hint': "1920x1080",
            'luminance': "Яскравість екрану (%):",
            'light': ["Освітлення приміщення:","штучне","природне"],
            'description': "Вказані фактори мають значний вплив\nна результати і їх необхідно вказати",
            'save':"Зберегти"
        }
    }
    cur_leng = 'ua'


    def __init__(self, parent=None):
        super().__init__(parent)
        self.tk = parent
        self.__set_default_values()


    def _layout(self, frame: Frame) -> None:
        self.__frame = frame
        super()._layout(frame)
        self.labels = dict()
        Label(frame, text=self.language[self.cur_leng]['intro'], anchor="w", justify="left") \
                .grid(row=0, column=0, columnspan=2, sticky=EW, padx=5, pady=2)
        
        self.labels['name'] = Label(frame, text=self.language[self.cur_leng]['name'], anchor="w", justify="left")
        self.labels['name'].grid(row=1, column=0, sticky=EW, padx=5, pady=2)
        self.name = EntryWithHint(frame, hint=self.language[self.cur_leng]['name_hint'])
        self.name.config(width=30)
        self.name.grid(row=1, column=1, sticky=EW, padx=5, pady=2)
        
        self.labels['age'] = Label(frame, text=self.language[self.cur_leng]['age'], anchor="w", justify="left")
        self.labels['age'].grid(row=2, column=0, sticky=EW, padx=5, pady=2)
        self.age = Spinbox(frame, from_=10, to=100, width=10, textvariable=StringVar(value=10))
        self.age.grid(row=2, column=1, sticky=EW, padx=5, pady=2)
        
        self.labels['device_type'] = Label(frame, text=self.language[self.cur_leng]['device_type'][0], anchor="w", justify="left")
        self.labels['device_type'].grid(row=3, column=0, sticky=EW, padx=5, pady=2)
        def_device = StringVar(value=self.language[self.cur_leng]['device_type'][1])   
        self.device_type = ttk.Combobox(frame, textvariable=def_device, values=self.language[self.cur_leng]['device_type'][1:], width=15)
        # lst = Listbox(frame, listvariable=Variable(value=), width=15)
        self.device_type.grid(row=3, column=1, sticky=EW, padx=5, pady=2)
        
        self.labels['device'] = Label(frame, text=self.language[self.cur_leng]['device'], anchor="w", justify="left")
        self.labels['device'].grid(row=4, column=0, sticky=EW, padx=5, pady=2)
        self.device = Entry(frame, width=20)
        self.device.grid(row=4, column=1, sticky=EW, padx=5, pady=2)
        
        self.labels['screen_size'] = Label(frame, text=self.language[self.cur_leng]['screen_size'], anchor="w", justify="left")
        self.labels['screen_size'].grid(row=5, column=0, sticky=EW, padx=5, pady=2)
        self.screen = Entry(frame, width=15)
        self.screen.grid(row=5, column=1, sticky=EW, padx=5, pady=2)
        
        self.labels['resolution'] = Label(frame, text=self.language[self.cur_leng]['resolution'], anchor="w", justify="left")
        self.labels['resolution'].grid(row=6, column=0, sticky=EW, padx=5, pady=2)
        self.resol = EntryWithHint(frame, hint=self.language[self.cur_leng]['resolution_hint']) # split by x_ua, x_en
        self.resol.config(width=15)
        self.resol.grid(row=6, column=1, sticky=EW, padx=5, pady=2)
        
        self.labels['luminance'] = Label(frame, text=self.language[self.cur_leng]['luminance'], anchor="w", justify="left")
        self.labels['luminance'].grid(row=7, column=0, sticky=EW, padx=5, pady=2)
        self.lum = Spinbox(frame, from_=-1, to=100, width=10, textvariable=StringVar(value=-1))
        self.lum.grid(row=7, column=1, sticky=EW, padx=5, pady=2)
        
        self.labels['light'] = Label(frame, text=self.language[self.cur_leng]['light'][0], anchor="w", justify="left")
        self.labels['light'].grid(row=8, column=0, sticky=EW, padx=5, pady=2)
        self.light = ttk.Combobox(frame, values=self.language[self.cur_leng]['light'][1:], width=15)
        self.light.grid(row=8, column=1, sticky=EW, padx=5, pady=2)
        
        Label(frame, text=self.language[self.cur_leng]['description'], anchor="w", justify="left") \
                .grid(row=9, column=0, columnspan=2, sticky=EW, padx=5, pady=2)
        self.button = Button(frame,text=self.language[self.cur_leng]['save'])
        self.button.grid(row=10, column=0, columnspan=2, padx=5, pady=(2,5))


    def __set_default_values(self):
        # put resolution
        self.resol.delete(0, END)
        self.resol.insert(0,f"{self.tk.winfo_screenwidth()}x{self.tk.winfo_screenheight()}")
        self.resol.config(fg='black')


    def get_data(self) -> dict:

        if self.__data_check():
            data = {
                'name': self.name.get(),
                'age': int(self.age.get()),
                'device_type': self.device_type.current(),
                'device': self.device.get(),
                'screen_size': float(self.screen.get()),
                'resolution': re.split('[xXхХ]',self.resol.get()),
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

        if int(self.age.get()) == 10:
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

        if not self.resol.get() or len(re.split('[xXхХ]',self.resol.get())) < 2 or \
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
    

    def configure(self, widgets_config:dict) -> None:
        pass
    

    def set_button_action(self, command):
        self.button.config(command=command)


class ImageFrame(CustomFrame):
    impath = 'images'
    ref = ['I01.bmp','I02.bmp','I03.bmp']
    dist = ['I01_01_5.bmp','I02_01_1.bmp','I03_01_2.bmp']

    language= {
        'ua': {
            'b1': "Непомітні завади",
            'b2': "Малопомітні завади",
            'b3': "Помітні завади",
            'b4': "<< Назад",
            'b5': "Далі >>",
            'notification': "Примітка: зір кожного індивідуальний і залежить від\nвіку, самопочуття, втоми, пристрою та інших факторів.\nТому результати тестів можуть мати відмінності.",
        }
    }
    cur_leng = 'ua'


    def __init__(self, parent:Tk=None) -> None:
        super().__init__(parent)


    def _layout(self, frame: Frame) -> None:
        self.__frame = frame
        super()._layout(frame)
        self.imageobj = None
        self.dist_canvas = ZoomedCanvas(frame, image=self.imageobj)
        self.dist_canvas.grid(row=1, column=0, padx=5, pady=2)
        self.ref_canvas = ZoomedCanvas(frame, image=self.imageobj)
        self.ref_canvas.grid(row=1, column=1, padx=(0,5), pady=2)
        
        self.dist_canvas.bind("<Motion>",self.mouse_motion)
        self.ref_canvas.bind("<Motion>",self.mouse_motion)
        frame.bind("<Motion>",self.mouse_motion)

        fr1 = Frame(frame)
        fr1.grid(row=0, column=0, columnspan=2, padx=6, pady=5, sticky=EW)
        fr1.columnconfigure(1, weight=1)
        self.name = Label(fr1, text="Name", anchor="w", justify="left")
        self.name.grid(row=0, column=0, padx=(5,10), pady=2, sticky=W)
        self.progress = ttk.Progressbar(fr1, orient="horizontal", length=300, value=50)
        self.progress.grid(row=0, column=1, padx=5, pady=2, sticky=S+E+W)
        self.r1 = Radiobutton(fr1, text="EN")
        self.r1.grid(row=0, column=2, padx=5, pady=2, sticky=E)
        self.r2 = Radiobutton(fr1, text="UA")
        self.r2.grid(row=0, column=3, padx=5, pady=2, sticky=E)


        fr2 = Frame(frame, bd=2, relief=RIDGE)
        fr2.grid(row=2, column=0, columnspan=2, padx=6, pady=2, sticky=EW)
        fr2.grid_columnconfigure(0, weight=1)
        # fr2.grid_columnconfigure(1, weight=0)
        fr2.grid_columnconfigure(2, weight=1)

        self.b1 = Button(fr2, text=self.language[self.cur_leng]['b1'], width=20, height=2)
        self.b1.grid(row=0, column=0, padx=5, pady=2, sticky=E)
        self.b2 = Button(fr2, text=self.language[self.cur_leng]['b2'], width=20, height=2)
        self.b2.grid(row=0, column=1, padx=5, pady=2)
        self.b3 = Button(fr2, text=self.language[self.cur_leng]['b3'], width=20, height=2)
        self.b3.grid(row=0, column=2, padx=5, pady=2, sticky=W)

        fr3 = Frame(frame)
        fr3.grid(row=3, column=0, columnspan=2, padx=6, pady=6, sticky=EW)
        Label(fr3, text=self.language[self.cur_leng]['notification'], anchor="w", justify="left") \
            .grid(row=0, column=0, padx=(5,10), pady=2, sticky=W)
        self.b4 = Button(fr3, text=self.language[self.cur_leng]['b4'], width=15, height=2)
        self.b4.grid(row=0, column=1, padx=5, pady=2, sticky=E)
        self.b5 = Button(fr3, text=self.language[self.cur_leng]['b5'], width=15, height=2)
        self.b5.grid(row=0, column=2, padx=5, pady=2, sticky=E)
        fr3.grid_columnconfigure(1, weight=1)


    def set_images(self) -> None:
        path = os.path.join(self.impath, 'I01.bmp')
        self.imageobj = Image.open(path, mode='r')

        pass

    def get_frame(self) -> Frame:
        return self.__frame

    def configure(self, widgets_config:dict) -> None:
        widgets = widgets_config.keys()

        for widget in widgets:
            getattr(self,widget).config(**widgets_config[widget])

    # def get_data(self):
        # return self.canvas.photoimg

    def mouse_motion(self, event):
        # _thread.start_new_thread(self.canvas_zooming, (event,) )
        cx = 0
        cy = 0
        if isinstance(event.widget, Canvas): 
            cx = event.x-4
            cy = event.y-4
            # cx=self.winfo_pointerx() - self.winfo_rootx()
            # cy=self.winfo_pointery() - self.winfo_rooty()
        self.dist_canvas.after(0, self.dist_canvas.canvas_zooming(event, cx, cy))
        self.ref_canvas.after(0, self.ref_canvas.canvas_zooming(event, cx, cy))


class ZoomedCanvas(Canvas):

    def __init__(self, master: Frame = None, image=None) -> None:
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
        self.pilzoom = image.resize((w*2, h*2), Image.ANTIALIAS)
        self.create_image(4, 4, image=self.photoimg, anchor=NW)
        self.is_zoomed = False



    def canvas_zooming(self, event, cx, cy):
        if isinstance(event.widget, Canvas) and self.photoimg is not None: 
            # cx=self.winfo_pointerx() - self.winfo_rootx()
            # cy=self.winfo_pointery() - self.winfo_rooty()

            area = (cx, cy, cx+self.photoimg.width(), cy+self.photoimg.height())
            self.tmp = ImageTk.PhotoImage(self.pilzoom.crop(area))
            self.create_image(4, 4, image=self.tmp, anchor=NW)
            # self.create_image(-cx, -cy, image=self.zoomimg, anchor=NW)
            self.is_zoomed = True

        else:
            if self.is_zoomed:
                self.create_image(4, 4, image=self.photoimg, anchor=NW)
                self.is_zoomed = False



class YAML:
    path="results"
    
    def set_path(self, path:str=""):
        self.path = path


    def write(self, data:dict, is_survey=False):
        yaml_string=yaml.dump(data)

        if is_survey:
            fname = os.path.join(self.path, data['name']+'_survey.yaml')
        else:
            fname = os.path.join(self.path, data['name']+'_exp'+str(random.randint(1000,9999))+'.yaml')

        with open(fname,"w") as file:
            yaml.dump(data, file, allow_unicode=True)


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


if __name__ == "__main__":
    GUI().start()
