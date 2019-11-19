import ast
import configparser
import datetime
import io
import math
import numpy as np
import operator as op
import os
from picamera import PiCamera
from PIL import Image
from random import randint
import RPi.GPIO as GPIO
import sys
from threading import Thread, Event
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import traceback


VERSION = '1.1.12'

'''
TO DO:
help page?
'''

light_pin = 3


class Application(tk.Frame):
    '''
    Main application GUI and methods to run experiments
    '''
    def __init__(self, master):
        super().__init__(master)
        sys.excepthook = self.exception_logger
        self.txtsize = 10
        self.bkg = 'LightBlue2'
        self.bad_train = False
        self.bad_number = False
        width = 2592
        height = 1944
        self.cam_resolution = (width, height)
        self.cam_exposure_mode = 'auto'
        self.master = master
        self.CWD = os.getcwd()
        self.grid()
        self.configure(background=self.bkg)
        self.master.configure(background=self.bkg)
        self.winfo_toplevel().title("WormPie Experiment Designer    v" + VERSION)
        self.create_frames()
        self.setup_GPIO()

    def create_frames(self):
        self.designer_frame = tk.Frame(self)
        self.designer_frame.configure(background=self.bkg)
        self.designer_frame.grid(row=0, column=0)
        self.create_designer(self.designer_frame)

        self.main_buttons_frame = tk.Frame(self)
        self.main_buttons_frame.configure(background=self.bkg)
        self.main_buttons_frame.grid(row=1, column=0)

        self.check_focus_button = tk.Button(self.main_buttons_frame, text="Check  \n  Focus", command=self.check_focus, font=("Helvetica", self.txtsize))
        self.check_focus_button.grid(row=0, column=0, pady=5, padx=10)

        self.start_expmt_button = tk.Button(self.main_buttons_frame, text="Start\nExperiment", command=self.start_expmt, font=("Helvetica", self.txtsize))
        self.start_expmt_button.grid(row=0, column=1, pady=5, padx=10)

        self.report_frame = tk.Frame(self)
        self.report_frame.configure(background=self.bkg)
        self.report_frame.grid(row=2, column=0)
        self.running_label = tk.Label(self.report_frame, text=' ')
        self.time_remaining = tk.Label(self.report_frame, text=' ')
        self.running_label.grid(row=0, column=0)
        self.time_remaining.grid(row=0, column=1)
        self.running_label.configure(background=self.bkg)
        self.time_remaining.configure(background=self.bkg)

    def create_designer(self, designer_frame):
        self.input_fields = []

        row = 0
        self.load_save_frame = tk.Frame(designer_frame)
        self.load_save_frame.configure(background=self.bkg)
        self.load_save_frame.grid(row=row, column=0, pady=5, padx=10)
        self.load_settings_button = tk.Button(self.load_save_frame, text="Load settings", command=self.load_expmt, font=("Helvetica", self.txtsize))
        self.load_settings_button.grid(row=0, column=0, pady=5, padx=10)
        self.save_settings_button = tk.Button(self.load_save_frame, text="Save settings", command=self.save_expmt, font=("Helvetica", self.txtsize))
        self.save_settings_button.grid(row=0, column=1, pady=5, padx=10)

        row = 1
        self.image_directory = Directory(designer_frame, self.CWD, 'Destination directory: ', bkg=self.bkg)
        self.image_directory.grid(row=row, column=0)
        self.input_fields.append(self.image_directory)

        row = 2
        self.smaller_parameter_frame = tk.Frame(designer_frame)
        self.smaller_parameter_frame.configure(background=self.bkg)
        self.smaller_parameter_frame.grid(row=row, column=0, pady=5, padx=10)

        self.experiment_length = Time(self.smaller_parameter_frame, 'Experiment length: ', default=[3, 'hour'], bkg=self.bkg)
        self.experiment_length.grid(row=row, column=0, sticky='w')
        self.input_fields.append(self.experiment_length)

        row = 3
        self.train_interval = Time(self.smaller_parameter_frame, 'Train interval: ', default=[10, 'min'], bkg=self.bkg)
        self.train_interval.grid(row=row, column=0, sticky='w')
        self.train_interval.trace('w', self.check_train_size)
        self.input_fields.append(self.train_interval)

        row = 4
        self.img_per_train = Number(self.smaller_parameter_frame, 'Images per train: ', default=1, bkg=self.bkg)
        self.img_per_train.grid(row=row, column=0, sticky='w')
        self.img_per_train.trace('w', self.check_train_size)
        self.input_fields.append(self.img_per_train)

        row = 5
        self.framerate = Number(self.smaller_parameter_frame, 'Framerate (Hz): ', default=2, bkg=self.bkg)
        self.framerate.grid(row=row, column=0, sticky='w')
        self.framerate.trace('w', self.check_train_size)
        self.input_fields.append(self.framerate)

        row = 6
        self.rest = Time(self.smaller_parameter_frame, 'Rest before experiment: ', default=[10, 'sec'], bkg=self.bkg)
        self.rest.grid(row=row, column=0, sticky='w')
        self.input_fields.append(self.rest)

        row = 7
        self.file_prefix = Text(self.smaller_parameter_frame, 'Filename prefix: ', default='plate1', bkg=self.bkg, note='    (Can be blank)')
        self.file_prefix.grid(row=row, column=0, sticky='w')
        self.input_fields.append(self.file_prefix)

        row = 8
        self.time_format = Text(self.smaller_parameter_frame, 'Time format: ', default='%H_%M', bkg=self.bkg)
        self.time_format.grid(row=row, column=0, sticky='w')
        self.input_fields.append(self.time_format)

        row = 9
        self.light_off = Checkbox(self.smaller_parameter_frame, 'Turn off light when not imaging? ', default=True, bkg=self.bkg)
        self.light_off.grid(row=row, column=0, sticky='w')
        self.light_off.check.trace('w', self.flip_light)
        self.input_fields.append(self.light_off)
        LightOn.turn_off = self.light_off.get()

        self.check_train_size()

    def setup_GPIO(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(light_pin, GPIO.OUT)
        GPIO.output(light_pin, False)

    def load_expmt(self):
        config = configparser.ConfigParser(interpolation=None)
        filename = filedialog.askopenfilename(title="Select file", filetypes=[("config file", ".ini")], initialdir=self.CWD)
        if filename != '':
            config.read(filename)
            try:
                image_directory = config['experiment'].get('image_directory', '')
                experiment_length = config['experiment'].get('experiment_length', '')
                train_interval = config['experiment'].get('train_interval', '')
                img_per_train = config['experiment'].get('img_per_train', '')
                framerate = config['experiment'].get('framerate', '')
                rest = config['experiment'].get('rest', '')
                file_prefix = config['experiment'].get('file_prefix', '')
                time_format = config['experiment'].get('time_format', '')
                light_off = config['experiment'].get('light_off', '')
                self.image_directory.set(image_directory)
                self.experiment_length.set(experiment_length)
                self.train_interval.set(train_interval)
                self.img_per_train.set(img_per_train)
                self.framerate.set(framerate)
                self.rest.set(rest)
                self.file_prefix.set(file_prefix)
                self.time_format.set(time_format)
                self.light_off.set(light_off)
            except KeyError:
                messagebox.showerror('ERROR', 'Could not understand configuration file.\nNo settings loaded.')

    def save_expmt(self):
        config = configparser.ConfigParser(interpolation=None)
        config['experiment'] = {'image_directory': self.image_directory.get_as_str(),
                                'experiment_length': self.experiment_length.get_as_str(),
                                'train_interval': self.train_interval.get_as_str(),
                                'img_per_train': self.img_per_train.get_as_str(),
                                'framerate': self.framerate.get_as_str(),
                                'rest': self.rest.get_as_str(),
                                'file_prefix': self.file_prefix.get_as_str(),
                                'time_format': self.time_format.get_as_str(),
                                'light_off': self.light_off.get_as_str()}
        filename = filedialog.asksaveasfilename(title="Select file", filetypes=[("config file", ".ini")], initialdir=self.CWD)
        if not filename.endswith('.ini'):
            filename = filename + '.ini'
        with open(filename, 'w') as configfile:
            config.write(configfile)

    def check_focus(self):
        messagebox.showinfo('Show Preview', 'The preview window will fill the whole screen.\nPress <Enter> to make it go away.')
        with LightOn():
            if hasattr(self, 'cam') and not self.cam.closed:
                self.cam.start_preview(resolution=(1440, 1080))
                messagebox.showinfo('Show Preview', 'The preview window will fill the whole screen.\nPress <Enter> to make it go away.')
                if not self.cam.closed:
                    self.cam.stop_preview()
            else:
                with PiCamera() as cam:
                    cam.resolution = self.cam_resolution
                    cam.exposure_mode = self.cam_exposure_mode
                    cam.start_preview(resolution=(1440, 1080))
                    messagebox.showinfo('Show Preview', 'The preview window will fill the whole screen.\nPress <Enter> to make it go away.')
                    cam.stop_preview()

    def start_expmt(self):
        if self.image_directory.get() == '':
            messagebox.showerror('Error', 'You must choose a folder to save the images in.')
            return
        if self.bad_train:
            messagebox.showerror('Error', 'The trains are either too long or too frequent.\nThe second train would begin before the first train finished.\nPlease adjust the parameters.')
            return
        if self.bad_number:
            messagebox.showerror('Error', 'Something is not a number.\nPlease double check your entries.')
            return
        better_time_format = self.check_time_format()
        if better_time_format or better_time_format == '':
            fix_fmt = messagebox.askyesnocancel("Time format", "Given the experiment parameters, I suggest you use the time format [" + better_time_format + '] instead of the one you entered [' + self.time_format.get() + "]\n\nYES: Use suggested format\nNO: Keep format the way you had it\nCANCEL: Don't start the experiment")
            if fix_fmt is None:
                return
            elif fix_fmt:
                self.time_format.set(better_time_format)
        self.start_expmt_button['command'] = self.kill_expmt
        self.start_expmt_button['text'] = "KILL\nExperiment"
        for field in self.input_fields:
            field.lock()
        t = Thread(target=self._start_expmt)
        t.start()

    def check_time_format(self):
        train_int = self.train_interval.get()
        experiment_length = self.experiment_length.get()
        fmt = self.time_format.get()
        needS = train_int % 60 != 0
        needM = (train_int % (60 * 60) != 0) and (experiment_length >= 60)
        needH = (train_int % (60 * 60 * 24) != 0) and (experiment_length >= (60 * 60))
        needD = experiment_length >= (60 * 60 * 24)
        fix = False
        if needS != ('%S' in fmt):
            fix = True
        if needM != ('%M' in fmt):
            fix = True
        if needH != ('%H' in fmt):
            fix = True
        if needD != ('%d' in fmt):
            fix = True
        if fix:
            return '_'.join([symbol for symbol in [needD * '%d', needH * '%H', needM * '%M', needS * '%S'] if symbol != ''])
        else:
            return False

    def _countdown(self):
        self.running_label.configure(text='Experiment initializing...')
        self.ETA_ready.wait()
        self.running_label.configure(text='Experiment running. ETA: ')
        while not self.sleeper.is_set():
            ETA = str(self.ETA - datetime.datetime.now()).split('.')[0]
            if ETA.startswith('-'):
                ETA = '00:00:00'
            self.time_remaining.configure(text=ETA)
            self.sleeper.wait(1)
        self.time_remaining.configure(text=' ')
        if hasattr(self, 'saver'):
            self.running_label.configure(text='Finishing saving images...')
            while self.saver.saving:
                time.sleep(0.1)
        self.running_label.configure(text='Experiment ended.')

    def _start_expmt(self):
        self.sleeper = Event()
        IMG_FORMAT = '.tif'
        self.ETA_ready = Event()
        t = Thread(target=self._countdown)
        t.start()
        img_per_train = math.floor(self.img_per_train.get())
        train_time = img_per_train / self.framerate.get()
        experiment_length = self.experiment_length.get()
        train_interval = self.train_interval.get()
        image_directory = self.image_directory.get()
        LightOn.light_off = self.light_off.get()
        if not image_directory.endswith('/'):
            image_directory = image_directory + '/'
        rest = self.rest.get()
        time_format = self.time_format.get()
        file_prefix = self.file_prefix.get()
        if img_per_train == 1:
            framerate = 10
        else:
            framerate = self.framerate.get()

        if not os.path.exists(image_directory):
            # self.supermakedirs(image_directory, 0o777)
            os.makedirs(image_directory)

        with PiCamera() as cam:
            with LightOn():
                self.cam = cam
                cam.resolution = self.cam_resolution
                cam.iso = 100
                self.sleeper.wait(3)
                cam.shutter_speed = cam.exposure_speed
                g = cam.awb_gains
                cam.awb_mode = 'off'
                cam.awb_gains = g
                cam.framerate = framerate
            session_start_at = datetime.datetime.now()
            trains_to_go = math.floor(experiment_length / train_interval)
            self.ETA = session_start_at + datetime.timedelta(seconds=rest + math.floor(experiment_length / train_interval) * train_interval + train_time)
            self.ETA_ready.set()
            self.sleeper.wait(rest)
            experimentStartTime = datetime.datetime.now()
            next_train_at = datetime.datetime.now()
            while not self.sleeper.is_set():
                outputs = [[io.BytesIO() for i in range(img_per_train)], False]
                secsIntoExpmt = (datetime.datetime.now() - experimentStartTime).total_seconds()
                sec_, usec = divmod(secsIntoExpmt * 1000000, 1000000)
                mins_, sec = divmod(sec_, 60)
                hours, mins = divmod(mins_, 60)
                checkTime = datetime.time(hour=int(hours), minute=int(mins), second=int(sec), microsecond=int(usec)).strftime(time_format)
                name_base = image_directory + ''.join([affix + '_' for affix in [file_prefix, checkTime] if affix != ''])
                self.saver = ImageSaver(outputs, name_base, IMG_FORMAT, self.cam_resolution)
                with LightOn():
                    t = Thread(target=self.saver.start)
                    t.start()
                    for i in range(len(outputs[0])):
                        if not self.sleeper.is_set():
                            cam.capture(outputs[0][i], 'yuv', use_video_port=True)  # do i not want capture_sequence? capture does allow me to interrupt
                    outputs[1] = True
                if trains_to_go:
                    trains_to_go = trains_to_go - 1
                    next_train_at = next_train_at + datetime.timedelta(seconds=train_interval)
                    timeToWait = next_train_at - datetime.datetime.now()
                    self.sleeper.wait(timeToWait.total_seconds())
                else:
                    self.sleeper.set()
        self.start_expmt_button['command'] = self.start_expmt
        self.start_expmt_button['text'] = "Start\nExperiment"
        for field in self.input_fields:
            field.unlock()
        self.check_train_size()

    # def supermakedirs(self, path, mode):
    #     if not path or os.path.exists(path):
    #         return []
    #     (head, tail) = os.path.split(path)
    #     res = self.supermakedirs(head, mode)
    #     os.mkdir(path)
    #     os.chmod(path, mode)
    #     res += [path]
    #     return res

    def kill_expmt(self):
        if messagebox.askokcancel("Kill experiment?", "Are you sure you want to end the experiment now?"):
            self.sleeper.set()

    def check_train_size(self, *args):
        try:
            if math.floor(float(self.img_per_train.get())) > 1:
                self.framerate.entry['state'] = 'normal'
                self.framerate.label['state'] = 'normal'
            else:
                self.framerate.entry['state'] = 'disabled'
                self.framerate.label['state'] = 'disabled'
        except tk.TclError:
            self.framerate.entry['state'] = 'disabled'
            self.framerate.label['state'] = 'disabled'
        except (SyntaxError, TypeError):
            pass
        try:
            train_time = self.img_per_train.get() / self.framerate.get()
            if train_time > self.train_interval.get():
                self.img_per_train.entry['bg'] = self.img_per_train.error_bkg = 'red'
                self.framerate.entry['bg'] = self.framerate.error_bkg = 'red'
                self.train_interval.entry['bg'] = self.train_interval.error_bkg = 'red'
                self.bad_train = True
            else:
                self.img_per_train.entry['bg'] = 'white'
                self.framerate.entry['bg'] = 'white'
                self.train_interval.entry['bg'] = 'white'
                self.img_per_train.error_bkg = False
                self.framerate.error_bkg = False
                self.train_interval.error_bkg = False
                self.bad_train = False
            self.bad_number = False
        except tk.TclError:
            self.img_per_train.entry['bg'] = self.img_per_train.error_bkg = 'red'
            self.framerate.entry['bg'] = self.framerate.error_bkg = 'red'
            self.train_interval.entry['bg'] = self.train_interval.error_bkg = 'red'
            self.bad_number = True
        except (SyntaxError, TypeError):
            pass

    def flip_light(self, *args):
        GPIO.output(light_pin, not self.light_off.get())
        LightOn.turn_off = self.light_off.get()

    def exception_logger(self, exctype, value, tb):
        log_path = r'/home/pi/Desktop/WormScopeEssential/errorlog.txt'
        with open(log_path, 'a') as log:
            log.write('________EXCEPTION_________ \n' + str(datetime.datetime.now()) + '\n')
            log.write('Traceback (most recent call last):\n')
            traceback.print_tb(tb, limit=None, file=log)
            log.write(str(exctype.__name__) + ': ' + str(value) + '\n')
            log.write('\n')
        messagebox.showerror('Error', 'Exception:\n' + str(exctype.__name__) + ': ' + str(value) + '\n\nCheck errorlog for full traceback.')


class ImageSaver():
    '''
    Saves images from a stream to a directory, then clears that stream position.
    Can run in its own thread so saving happens along side capture to keep memory use lower longer.
    '''
    def __init__(self, outputs, name_base, img_type, cam_resolution):
        self.outputs = outputs
        self.queue = outputs[0]
        self.name_base = name_base
        self.img_type = img_type
        self.saving = False
        self.fwidth = (cam_resolution[0] + 31) // 32 * 32
        self.fheight = (cam_resolution[1] + 15) // 16 * 16

    def start(self):
        self.saving = True
        need_serial = len(self.queue) > 1
        i = 0
        for i in range(1, len(self.queue)):
            waiting = True
            while waiting:
                if self.queue[i].tell() > 0:
                    self.save_image_from_stream_yuv(self.queue[i - 1], i, need_serial)
                    self.queue[i - 1] = None
                    waiting = False
        while not self.outputs[1]:
            pass
        self.save_image_from_stream_yuv(self.queue[i], i + 1)
        self.queue[i] = None
        self.saving = False

    # def save_image_from_stream_jpeg(self, stream_item, i):
    #     stream_item.seek(0)
    #     image = Image.open(stream_item)
    #     fname = self.name_base + str(i - 1) + self.img_type
    #     image.save(fname)
    #     stream_item.close()

    def save_image_from_stream_yuv(self, stream_item, i, need_serial):
        stream_item.seek(0)
        Y = np.fromstring(stream_item.getvalue(), dtype=np.uint8, count=self.fwidth * self.fheight).reshape((self.fheight, self.fwidth))
        image = Image.fromarray(Y)
        if need_serial:
            serial = str(i - 1)
        else:
            serial = ''
        fname = self.name_base + serial + self.img_type
        image.save(fname)
        stream_item.close()


class LightOn():
    '''
    Context managed object to handle the light.
    Turns on the light upon creation, and registers an ID with the class-level whos_on
    Turns off the light if the last one to leave.
    '''
    whos_on = []
    turn_off = None

    def __enter__(self):
        self.on_ID = self.random_with_N_digits(8)
        LightOn.whos_on.append(self.on_ID)
        GPIO.output(light_pin, True)
        time.sleep(0.5)
        return self

    def __exit__(self, type, value, traceback):
        LightOn.whos_on.pop(LightOn.whos_on.index(self.on_ID))
        if (len(LightOn.whos_on) == 0) and LightOn.turn_off:
            GPIO.output(light_pin, False)

    def random_with_N_digits(self, n):
        range_start = 10**(n - 1)
        range_end = (10**n) - 1
        return randint(range_start, range_end)


class WormPieVar():
    '''
    Generic type for vars. Inheirting allows for locking/unlocking when an experiment starts/ends
    '''
    label_width = 26
    label_height = 6

    def __init__(self):
        pass

    def lock(self):
        try:
            self.entry['disabledbackground'] = self.bkg
        except tk.TclError:
            self.entry['background'] = self.bkg
        if self.entry['state'] != 'disabled':
            self.entry['state'] = 'disabled'
            self.entry['disabledforeground'] = 'black'
        if hasattr(self, 'units_menu'):
            self.units_menu['background'] = self.bkg
            self.units_menu['state'] = 'disabled'
            self.units_menu['disabledforeground'] = 'black'
        if hasattr(self, 'choose_button'):
            self.choose_button['state'] = 'disabled'

    def unlock(self):
        self.entry['background'] = self.default_bkg
        self.entry['disabledforeground'] = self.default_dfg
        self.entry['state'] = 'normal'
        try:
            self.entry['disabledbackground'] = self.bkg
        except tk.TclError:
            self.entry['background'] = self.bkg
        if hasattr(self, 'units_menu'):
            self.units_menu['state'] = 'active'
            self.units_menu['background'] = self.default_dfg
            self.units_menu['disabledforeground'] = 'black'
        if hasattr(self, 'choose_button'):
            self.choose_button['state'] = 'active'


class MathableNumber(tk.StringVar):
    '''
    Var type to allow text entry of math. Returns the correct answer or None if empty.
    '''
    operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
                 ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.pow,
                 ast.USub: op.neg}

    def get_evaluated(self):
        if self.get() == '':
            return None
        return self.eval_(ast.parse(self.get(), mode='eval').body)

    def eval_(self, node):
        if isinstance(node, ast.Num):  # <number>
            return node.n
        elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
            return MathableNumber.operators[type(node.op)](self.eval_(node.left), self.eval_(node.right))
        elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
            return MathableNumber.operators[type(node.op)](self.eval_(node.operand))
        else:
            raise TypeError(node)


class Time(tk.Frame, WormPieVar):
    '''
    A math-able text entry and a multi-select for time units.
    '''
    def __init__(self, parent, label, default, bkg, note=''):
        tk.Frame.__init__(self, parent)
        self.configure(background=bkg)

        self.units_dict = {'sec': 1, 'min': 60, 'hour': 60 * 60, 'day': 60 * 60 * 24}

        self.num = MathableNumber(self)
        self.num.set(default[0])
        self.num.trace('w', self.validate)
        self.units = tk.StringVar(self)
        self.units.set(default[1])

        self.label = tk.Label(self, text=label, anchor="e", width=WormPieVar.label_width, pady=WormPieVar.label_height)
        self.entry = tk.Entry(self, textvariable=self.num, width=5)
        self.units_menu = tk.OptionMenu(self, self.units, *self.units_dict)
        self.note = tk.Label(self, text=note, anchor="w", pady=WormPieVar.label_height)

        self.label.grid(row=0, column=0)
        self.label.configure(background=bkg)
        self.entry.grid(row=0, column=1)
        self.units_menu.grid(row=0, column=2)
        self.note.grid(row=0, column=3)
        self.note.configure(background=bkg)
        self.default_bkg = self.entry.cget("background")
        self.default_dfg = self.entry.cget("disabledforeground")
        try:
            self.default_dbg = self.entry.cget("disabledbackground")
        except tk.TclError:
            pass
        self.error_bkg = False
        self.bkg = bkg

    def get(self):
        # returns time in seconds
        if self.num.get_evaluated() is not None:
            return self.units_dict[self.units.get()] * self.num.get_evaluated()

    def get_as_str(self):
        return ' '.join([str(self.num.get()), self.units.get()])

    def set(self, s):
        num, units = s.split(' ')
        self.num.set(num)
        self.units.set(units)

    def trace(self, mode, func):
        self.num.trace(mode, func)
        self.units.trace(mode, func)

    def validate(self, *args):
        try:
            self.get()
            if self.error_bkg:
                self.entry['background'] = self.error_bkg
            else:
                self.entry['background'] = self.default_bkg
        except SyntaxError:
            self.entry['background'] = 'tomato'


class Number(tk.Frame, WormPieVar):
    '''
    A math-able text entry.
    '''
    def __init__(self, parent, label, default, bkg, note=''):
        tk.Frame.__init__(self, parent)
        self.configure(background=bkg)

        self.num = MathableNumber(self)
        self.num.set(default)
        self.num.trace('w', self.validate)

        self.label = tk.Label(self, text=label, anchor="e", width=WormPieVar.label_width, pady=WormPieVar.label_height)
        self.entry = tk.Entry(self, textvariable=self.num, width=5)
        self.note = tk.Label(self, text=note, anchor="w", pady=WormPieVar.label_height)

        self.label.grid(row=0, column=0)
        self.label.configure(background=bkg)
        self.entry.grid(row=0, column=1)
        self.note.grid(row=0, column=2)
        self.note.configure(background=bkg)
        self.default_bkg = self.entry.cget("background")
        self.default_dfg = self.entry.cget("disabledforeground")
        self.error_bkg = False
        self.bkg = bkg

    def get_as_str(self):
        return self.num.get()

    def get(self):
        return self.num.get_evaluated()

    def set(self, i):
        self.num.set(i)

    def trace(self, mode, func):
        self.num.trace(mode, func)

    def validate(self, *args):
        try:
            self.get()
            if self.error_bkg:
                self.entry['background'] = self.error_bkg
            else:
                self.entry['background'] = self.default_bkg
        except SyntaxError:
            self.entry['background'] = 'tomato'


class Text(tk.Frame, WormPieVar):
    '''
    Pretty basic text entry
    '''
    def __init__(self, parent, label, default, bkg, note=''):
        tk.Frame.__init__(self, parent)
        self.configure(background=bkg)

        self.txt = tk.StringVar(self)
        self.txt.set(default)

        self.label = tk.Label(self, text=label, anchor="e", width=WormPieVar.label_width, pady=WormPieVar.label_height)
        self.entry = tk.Entry(self, textvariable=self.txt, width=10)
        self.note = tk.Label(self, text=note, anchor="w", pady=WormPieVar.label_height)

        self.label.grid(row=0, column=0)
        self.label.configure(background=bkg)
        self.entry.grid(row=0, column=1)
        self.note.grid(row=0, column=2)
        self.note.configure(background=bkg)
        self.default_bkg = self.entry.cget("background")
        self.default_dfg = self.entry.cget("disabledforeground")
        self.error_bkg = False
        self.bkg = bkg

    def get(self):
        return self.txt.get()

    def set(self, s):
        self.txt.set(s)

    def get_as_str(self):
        return self.get()


class Checkbox(tk.Frame, WormPieVar):
    '''
    A checkbox
    '''
    def __init__(self, parent, label, default, bkg, note=''):
        tk.Frame.__init__(self, parent)
        self.configure(background=bkg)

        self.check = tk.IntVar(self)
        self.check.set(default)

        self.label = tk.Label(self, text=label, anchor="e", width=WormPieVar.label_width, pady=WormPieVar.label_height)
        self.entry = tk.Checkbutton(self, variable=self.check)
        self.note = tk.Label(self, text=note, anchor="w", pady=WormPieVar.label_height)

        self.label.grid(row=0, column=0)
        self.label.configure(background=bkg)
        self.entry.grid(row=0, column=1)
        self.entry.configure(background=bkg)
        self.note.grid(row=0, column=2)
        self.note.configure(background=bkg)
        self.default_bkg = self.entry.cget("background")
        self.default_dfg = self.entry.cget("disabledforeground")
        self.error_bkg = False
        self.bkg = bkg

    def get(self):
        return self.check.get()

    def set(self, i):
        self.check.set(i)

    def get_as_str(self):
        return self.get()


class Directory(tk.Frame, WormPieVar):
    '''
    Select a directory. Has function to enforce no-spaces (or whatver) but this is inactive right now
    '''
    def __init__(self, parent, CWD, label, default='', bkg=None):
        tk.Frame.__init__(self, parent)
        self.configure(background=bkg)

        self.dir = tk.StringVar(self)
        self.dir.set(default)
        self.CWD = CWD

        self.dir_label = tk.Label(self, text=label, pady=WormPieVar.label_height)
        self.entry = tk.Entry(self, textvariable=self.dir, width=50)
        # self.entry.trace('w', self.validate_entry)
        self.choose_button = tk.Button(self, text="Choose", command=self.choose_directory)  # , font=("Helvetica", self.txtsize)

        self.dir_label.grid(row=0, column=0, pady=5, padx=0)
        self.dir_label.configure(background=bkg)
        self.entry.grid(row=0, column=1, pady=5, padx=0)
        self.choose_button.grid(row=0, column=2, pady=5, padx=0)
        self.default_bkg = self.entry.cget("background")
        self.default_dfg = self.entry.cget("disabledforeground")
        self.error_bkg = False
        self.bkg = bkg

    def choose_directory(self):
        if self.dir.get() == '':
            dest_dir = self.CWD
        else:
            dest_dir = self.dir.get()
        directory = filedialog.askdirectory(initialdir=dest_dir)
        if directory != '':
            self.dir.set(directory)

    def get(self):
        return self.dir.get()

    def set(self, i):
        self.dir.set(i)

    def get_as_str(self):
        return self.get()

    def validate_entry(self, *args):
        entry = self.entry.get()
        if entry != entry.replace(' ', ''):
            self.entry.set(entry.replace(' ', ''))


if __name__ == '__main__':
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()
    GPIO.cleanup()
