#!/usr/bin/env python
# -*- coding: latin-1 -*-
import atexit
import codecs
import csv
import random
from os.path import join
from statistics import mean

import yaml
from psychopy import visual, event, logging, gui, core, constants

from misc.screen_misc import get_screen_res, get_frame_rate
from itertools import combinations_with_replacement, product

#GLOBALS
clock=core.Clock()
RESULTS = list()  # lista, w której b?d? zapisywane wyniki
RESULTS.append(['PART_ID', 'Group', 'Trial_no', 'Stim_type', 'Reaction_time', 'Correctness',"Experiment", 'Sex', 'Age' ]) #dodaje nazwy kolumn, bez danych



@atexit.register
def save_beh_results(): #funkcja zapisujaca wyniki ka?dego badanego w pliku csv
    with open(join('results', PART_ID + '_beh.csv'), 'w', encoding='utf-8') as beh_file:
        beh_writer = csv.writer(beh_file)
        beh_writer.writerows(RESULTS)
    logging.flush()


def show_image(win, file_name, size, key='f7'): #funkcja wyswietlajaca obrazki
    image = visual.ImageStim(win=win, image=file_name, interpolate=True, size=size)
    image.draw()
    win.flip()
    return


def show_info(win, file_name, insert=''): #funkcja wyswietlajaca tekst; insert daje mozliwosc dopisania czegos
    msg = read_text_from_file(file_name, insert=insert)
    msg = visual.TextStim(win, color='black', text=msg, height=25, wrapWidth=SCREEN_RES['width'])
    msg.draw()
    win.flip()
    key = event.waitKeys(keyList=['f7', 'space'])
    if key == ['f7']:
        abort_with_error(
            'Experiment finished by user on info screen! F7 pressed.')
    win.flip()




def show_movie(win, file_name): #funkcja wyswietlajaca filmiki do prymowania
    file_name = './videos/' + file_name
    movie = visual.MovieStim2(win, filename=file_name, size = 1440)
    movie.loadMovie(file_name)
    movie.play()
    clock.reset()
    while clock.getTime() <= float(movie.duration):
        clicked = event.getKeys(keyList=['f7', 'space'])
        movie.draw()
        if clicked == ['f7']:
            logging.critical(
                'Experiment finished by user! {} pressed.'.format(key[0]))
            exit(0)
        if clicked == ['space']:
            break
        win.flip()
    movie.stop()
    return




def read_text_from_file(file_name, insert=''): #nieostotne, potrzebne do show_info
    """
    Method that read message from text file, and optionally add some
    dynamically generated info.
    """
    if not isinstance(file_name, str):
        logging.error('Problem with file reading, filename must be a string')
        raise TypeError('file_name must be a string')
    msg = list()
    with codecs.open(file_name, encoding='utf-8', mode='r') as data_file:
        for line in data_file:
            if not line.startswith('#'):  # if not commented line
                if line.startswith('<--insert-->'):
                    if insert:
                        msg.append(insert)
                else:
                    msg.append(line)
    return ''.join(msg)


def check_exit(key='f7'): #nieistotne
    """
    Check (during procedure) if experimentator doesn't want to terminate.
    """
    stop = event.getKeys(keyList=[key])
    if stop:
        abort_with_error(
            'Experiment finished by user! {} pressed.'.format(key))


def abort_with_error(err):#nieostotne
    """
    Call if an error occured.
    """
    logging.critical(err)
    raise Exception(err)


def dialog_pulp():
    info={'IDENTYFIKATOR': '', u'P\u0141E\u0106': ['M', "K"], 'WIEK': '20'} #to 20 jest domyslne ale mozna zmieniac
    dictDlg=gui.DlgFromDict(
        dictionary=info, title='Go/No Go Test')
    if not dictDlg.OK:
        abort_with_error('Info dialog terminated.')
    return info


def main():
    global PART_ID, Group, Sex, Age #
    info = dialog_pulp()
    conf=yaml.safe_load(open('config.yaml', encoding='utf-8'))
    win=visual.Window(list(SCREEN_RES.values()), fullscr=False, monitor='testMonitor', units='pix', screen=0, color=conf['BACKGROUND_COLOR'])
    event.Mouse(visible=False, newPos=None, win=win)
    FRAME_RATE=get_frame_rate(win)

    if FRAME_RATE != conf['FRAME_RATE']: #niewa?ne
        dlg=gui.Dlg(title="Critical error")
        dlg.addText(
            'Wrong no of frames detected: {}. Experiment terminated.'.format(FRAME_RATE))
        dlg.show()
        return None

    PART_ID=info['IDENTYFIKATOR']
    Sex = info[u'P\u0141E\u0106']
    Age = info['WIEK']
    logging.LogFile("".join(['results/', PART_ID, '_', Sex, '_', Age + '.log']), level=logging.INFO)  # errors logging
    logging.info('FRAME RATE: {}'.format(FRAME_RATE))
    logging.info('SCREEN RES: {}'.format(SCREEN_RES.values()))

    show_info(win, join('.', 'messages', 'hello.txt'))
    Trial_no = 0
    Trial_no += 1

    show_info(win, join('.', 'messages', 'before_training.txt'))

    show_movie(win, 'neutral.mp4')
    # wywolaj funkcje pokazywania filmiku

    show_info(win, join('.', 'messages', 'beforebefore_experiment.txt'))
    part_of_experiment(win, conf, 'training')
    show_info(win, join('.', 'messages', 'before_experiment.txt'))
    part_of_experiment(win, conf, 'experiment')


        # === Cleaning time ===
    #save_beh_results() i teraz zapisuje tylko raz wyniki yay
    logging.flush()
    show_info(win, join('.', 'messages', 'end.txt'))
    win.close()

def trial(win, stim, conf):
    for frameN in range(conf['FRAMES_BETWEEN_STIMS']):
        win.flip()
    win.callOnFlip(clock.reset)
    event.clearEvents()
    Reaction_time = "NA"
    for frameN in range(conf['STIM_DURATION_IN_FRAMES']):
        stim.draw()
        win.flip()
        response = event.getKeys()
        if response == conf["REACTION_KEYS"]:
            Reaction_time = clock.getTime()
            break
    return Reaction_time, response


def if_correct(response, go_no_go, conf):
    if go_no_go == 'Go' and response == conf['REACTION_KEYS']:
        return True
    elif go_no_go == 'Go2' and response == conf['REACTION_KEYS']:
        return True
    return False


def part_of_experiment(win, conf, experiment):

    go_stim = visual.ImageStim(win=win, image='./images/GO_stim.png',interpolate=True, size =(conf['STIM_SIZE'],conf['STIM_SIZE']))
    go2_stim = visual.ImageStim(win=win, image='./images/GO2_stim.png',interpolate=True, size =(conf['STIM_SIZE'],conf['STIM_SIZE']))
    nogo_stim = visual.ImageStim(win=win, image='./images/NOGO_stim.png',interpolate=True, size =(conf['STIM_SIZE'],conf['STIM_SIZE']))

    allstimlist = []
    if experiment == "training":
        for x in range(conf['NO_GO_TRIALS_TRAINING']):
            allstimlist.append("Go")
        for x in range(conf['NO_GO2_TRIALS_TRAINING']):
                allstimlist.append("Go2")
        for x in range(conf['NO_NO_GO_TRIALS_TRAINING']):
            allstimlist.append("NoGo")
    elif experiment == "experiment":
        for x in range(conf['NO_GO_TRIALS_EXPERIMENT']):
            allstimlist.append("Go")
        for x in range(conf['NO_GO2_TRIALS_EXPERIMENT']):
                allstimlist.append("Go2")
        for x in range(conf['NO_NO_GO_TRIALS_EXPERIMENT']):
            allstimlist.append("NoGo")


    Stim_type = "NA"
    for Trial_no in range(len(allstimlist)):

        previousstim = Stim_type
        Stim_type = random.choice(allstimlist)
        if previousstim == "NA":
            Stim_type = "Go"
        while Stim_type == previousstim and Stim_type != "Go" and allstimlist.count(Stim_type) != len(allstimlist):
            Stim_type = random.choice(allstimlist)
        #stim_type to rand czyli zmienna zapisuj?ca co si? sta?o po random.choice, wynik losowania z listy
        if Stim_type == "Go":
            Reaction_time, response = trial(win, go_stim, conf)
            Correctness = if_correct(response, Stim_type, conf)
            allstimlist.remove("Go")
        elif Stim_type == "NoGo":
            Reaction_time, response = trial(win, nogo_stim, conf)
            Correctness = if_correct(response, Stim_type, conf)
            allstimlist.remove("NoGo")
        elif Stim_type == "Go2":
            Reaction_time, response = trial(win, go2_stim, conf)
            Correctness = if_correct(response, Stim_type, conf)
            allstimlist.remove("Go2")

        RESULTS.append([PART_ID, Group, Trial_no, Stim_type, Reaction_time, Correctness,experiment, Sex, Age ])


if __name__ == '__main__':
    PART_ID=''
    SCREEN_RES=get_screen_res()
    main()