import sys

from PyQt5.QtWidgets import *
from PyQt5 import uic

from datetime import date

import numpy as np
import glob
import os

import sounddevice as sd
import soundfile as sf

import random
import pickle

PlayerUI = './playWav_single.ui'
root = './src/wavs' # Load wav files ( format : wav_name.wav )
t_path = './src/text/.txt' # Load text meta ( format : wav_name | text )
save_path = './save.ar' # Save current works
subfolder_exist = True # If there are multipl models existed in wavs folder
num_utters = 40 # Number of utterances to be tested

def get_models(root, subfolder_exist=True):
    if subfolder_exist:
        wav_list = sorted(glob.glob(os.path.join(root, '**/*.wav')))
        model_list = {}
        speaker_id = 0
        subfolder_list = glob.glob(os.path.join(root, '*'))
        for subfolder in subfolder_list:
            model_name = subfolder.split('\\')[-1]
            if model_name not in model_list:
                model_list[model_name] = speaker_id
                speaker_id += 1
    else:
        wav_list = sorted(glob.glob(os.path.join(root, '*.wav')))
        model_list = {'single_model':0}
    return wav_list, model_list

def readText(t_path):
    t_list = {}
    with open(t_path, 'r') as f:
        lines =f.readlines()
        for line in lines:
            if line.startswith('\ufeff'):
                line = line.replace('\ufeff','')
            wav_path, text = line.split('|')
            index = wav_path.split('.')[0]
            t_list[index] = text
    return t_list

class MainDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self, None)
        uic.loadUi(PlayerUI, self)

        if not(self.load()):
            self.PS['wav_list'], self.PS['model_list'] = get_models(root, subfolder_exist)
            random.shuffle(self.PS['wav_list'])
            self.PS['text_list'] = readText(t_path)
            self.PS['score'] = np.zeros(len(self.PS['model_list']))
            self.PS['index'] = 0

        self.button_options = [self.radioButton_1, self.radioButton_2, self.radioButton_3, self.radioButton_4,
                               self.radioButton_5, self.radioButton_6, self.radioButton_7, self.radioButton_8,
                               self.radioButton_9]
        self.playWaveButton.clicked.connect(lambda: self.PlayVoice(self.PS['wav_list'][self.PS['index']]))
        self.nextButton.clicked.connect(lambda: self.NextSet())
        self.saveButton.clicked.connect(lambda: self.save())
        self.instButton.clicked.connect(lambda: self.PlayVoice(self.PS['wav_list'][self.PS['index']]))
        self.textBrowser.setText(self.findText(self.PS['wav_list'][self.PS['index']]))

    def findText(self, wav_path):
        index = wav_path.split('\\')[-1].split('.')[0]
        return self.PS['text_list'][index]

    def shuffle_list(self, wav_list):
        random.shuffle(wav_list)
        return wav_list

    def PlayVoice(self, dir):
        data, fs = sf.read(dir, dtype='float32')
        sd.play(data, fs)

    def save(self):
        f = open(save_path, 'wb')
        pickle.dump(self.PS, f)
        sys.exit(app.exec())

    def load(self):
        try:
            f = open(save_path, 'rb')
            self.PS = pickle.load(f)
            f.close()
        except:
            self.PS = {}
            return False
        return True

    def NextSet(self):
        # Save score
        for i, button in enumerate(self.button_options):
            if button.isChecked():
                curr_wav = self.PS['wav_list'][self.PS['index']]
                if subfolder_exist:
                    model_name = curr_wav.split("\\")[-2]
                else:
                    model_name = 'single_model'
                self.PS['score'][self.PS['model_list'][model_name]] += (8 - i) * 0.5 + 1

        self.PS['index'] += 1

        # When finished
        if self.PS['index'] == len(self.PS['wav_list']): # wavList 에 남은 음성 pair 가 없다면 calcResult 함수를 출력
            msg = QMessageBox()
            msg.setWindowTitle('테스트 완료')
            final_msg = '수고하셨습니다'
            msg.setText(final_msg)

            today = date.today()
            with open('test_result_{}.csv'.format(today),'w') as fs:
                for i, model_name in enumerate(self.PS['model_list']):
                    fs.write(model_name + '|' + str(self.PS['score'][i] / num_utters) + '\n')

            result = msg.exec_()
            if result==QMessageBox.Ok:
                sys.exit(app.exec())

        self.textBrowser.setText(self.findText(self.PS['wav_list'][self.PS['index']]))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_dialog = MainDialog()
    main_dialog.show()
    app.exec_()