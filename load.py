#|##################################################################################################################################################################################|
#																									
#									/$$   /$$                                   /$$ /$$                 /$$       /$$$$$$$  /$$        /$$$$$$  /$$     /$$
#									| $$  | $$                                  | $$|__/                | $$      | $$__  $$| $$       /$$__  $$|  $$   /$$/
#									| $$  | $$ /$$   /$$ /$$$$$$/$$$$   /$$$$$$ | $$ /$$  /$$$$$$       | $$      | $$  \ $$| $$      | $$  \ $$ \  $$ /$$/ 
#									| $$$$$$$$| $$  | $$| $$_  $$_  $$ /$$__  $$| $$| $$ |____  $$      | $$      | $$$$$$$/| $$      | $$$$$$$$  \  $$$$/  
#									| $$__  $$| $$  | $$| $$ \ $$ \ $$| $$  \ $$| $$| $$  /$$$$$$$      | $$      | $$____/ | $$      | $$__  $$   \  $$/   
#									| $$  | $$| $$  | $$| $$ | $$ | $$| $$  | $$| $$| $$ /$$__  $$      | $$      | $$      | $$      | $$  | $$    | $$    
#									| $$  | $$|  $$$$$$$| $$ | $$ | $$|  $$$$$$/| $$| $$|  $$$$$$$      | $$      | $$      | $$$$$$$$| $$  | $$    | $$    
#									|__/  |__/ \____  $$|__/ |__/ |__/ \______/ |__/|__/ \_______/      |__/      |__/      |________/|__/  |__/    |__/    
#											/$$  | $$                                                                                                    
#											|  $$$$$$/                                                                                                    
#											\______/                                                                                                     
#									
#|##################################################################################################################################################################################|
#|                                                                                                                                                                             		|
#|	COPYRIGHT BY DARIO NÜSSLER                                                                                                                                                      |
#|	DIESER CODE DARF NICHT BEARBEITET WERDEN!                                                                                                                                       |
#|	DIESER CODE DARF AUCH NICHT OHNE ERLAUBNIS BENUTZT WERDEN                                                                                                                       |
#|	DIESER CODE DARF AUCH NICHT WEITERGEGEBEN WERDEN                                                                                                                                |
#|	DIESER COPYRIGHT HINWEISS DARF NICHT ENTFERNT WERDEN																														 	|
#|	DIESER COPYRIGHT GILT UNTER DEM SWISS-MADE SCHUTZ                                                                                                                               |
#|                                                                        													                                                        |
#|##################################################################################################################################################################################|

import functools
import logging
import threading
import tkinter as tk
from os.path import dirname, join

import semantic_version
import sys
import time

import l10n
import myNotebook as nb
from config import config, appname, appversion
from py_discord_sdk import discordsdk as dsdk

plugin_name = "DiscordPresence"

logger = logging.getLogger(f'{appname}.{plugin_name}')

CLIENT_ID = 1006840798614142986

VERSION = '3.1.0'
planet = '<Hidden>'
landingPad = '2'

this = sys.modules[__name__]


def callback(result):
    logger.info(f'Callback: {result}')
    if result == dsdk.Result.ok:
        logger.info("Successfully set the activity!")
    elif result == dsdk.Result.transaction_aborted:
        logger.warning(f'Transaction aborted due to SDK shutting down: {result}')
    else:
        logger.error(f'Error in callback: {result}')
        raise Exception(result)


def update_presence():
    if isinstance(appversion, str):
        core_version = semantic_version.Version(appversion)

    elif callable(appversion):
        core_version = appversion()

    logger.info(f'Core EDMC version: {core_version}')
    if core_version < semantic_version.Version('5.0.0-beta1'):
        logger.info('EDMC core version is before 5.0.0-beta1')
        if config.getint("disable_presence") == 0:
            this.activity.state = this.presence_state
            this.activity.details = this.presence_details
            #this.activity.assets.large_text = this.presence_cmdr
            this.activity.assets.large_image = "bg_logo"
    else:
        logger.info('EDMC core version is at least 5.0.0-beta1')
        if config.get_int("disable_presence") == 0:
            this.activity.state = this.presence_state
            this.activity.details = this.presence_details
            #this.activity.assets.large_text = this.presence_cmdr
            this.activity.assets.large_image = "bg_logo"

    this.activity.timestamps.start = int(this.time_start)
    this.activity_manager.update_activity(this.activity, callback)


def plugin_prefs(parent, cmdr, is_beta):
    """
    Return a TK Frame for adding to the EDMC settings dialog.
    """
    if isinstance(appversion, str):
        core_version = semantic_version.Version(appversion)

    elif callable(appversion):
        core_version = appversion()

    logger.info(f'Core EDMC version: {core_version}')
    if core_version < semantic_version.Version('5.0.0-beta1'):
        logger.info('EDMC core version is before 5.0.0-beta1')
        this.disablePresence = tk.IntVar(value=config.getint("disable_presence"))
    else:
        logger.info('EDMC core version is at least 5.0.0-beta1')
        this.disablePresence = tk.IntVar(value=config.get_int("disable_presence"))

    frame = nb.Frame(parent)
    nb.Checkbutton(frame, text="Disable Presence", variable=this.disablePresence).grid()
    nb.Label(frame, text='Version %s' % VERSION).grid(padx=10, pady=10, sticky=tk.W)

    return frame


def prefs_changed(cmdr, is_beta):
    """
    Save settings.
    """
    config.set('disable_presence', this.disablePresence.get())
    update_presence()


def plugin_start3(plugin_dir):
    this.plugin_dir = plugin_dir
    this.discord_thread = threading.Thread(target=check_run, args=(plugin_dir,))
    this.discord_thread.setDaemon(True)
    this.discord_thread.start()
    return 'DiscordPresence'


def plugin_stop():
    this.activity_manager.clear_activity(callback)
    this.call_back_thread = None


def journal_entry(cmdr, is_beta, system, station, entry, state):
    global planet
    global landingPad
    presence_state = this.presence_state
    presence_details = this.presence_details
    presence_cmdr = cmdr
    if entry['event'] == 'StartUp':
        presence_state = ('System: {system}🌌').format(system=system)
        if station is None:
            presence_details = "Fliegt im normalen Raum"
        else:
            presence_details = ('Angedockt: {station}🚩').format(station=station)
    elif entry['event'] == 'Location':
        presence_state = ('System: {system}🌌').format(system=system)
        if station is None:
            presence_details = "Fliegt im normalen Raum"
        else:
            presence_details = ('Angedockt: {station}🚩').format(station=station)
            
    elif entry['event'] == 'Undocked' or entry['event'] == 'DockingCancelled' or entry['event'] == 'DockingTimeout':
        presence_details = ('Fliegt um: {station}').format(station=entry['StationName'])
    # Planetary events
    elif entry['event'] == 'ShipyardSwap':
        presence_state = ('🎯 Ziel: {system}🌌').format(system=entry['Name'])
        presence_details = ('⌛ Warte auf FSD')
    elif entry['event'] == 'ApproachBody':
        presence_details = ('🌎 Annäherung: {body}').format(body=entry['Body'])
        planet = entry['Body']
    elif entry['event'] == 'Touchdown' and entry['PlayerControlled']:
        presence_details = ('🛬 Gelandet: {body}').format(body=planet)
    elif entry['event'] == 'Liftoff' and entry['PlayerControlled']:
        if entry['PlayerControlled']:
            presence_details = ('Fliegt um: {body}').format(body=planet)
        else:
            presence_details = ('🚗 auf: {body}').format(body=planet)
    elif entry['event'] == 'LeaveBody':
        presence_details = "Im Supercruise 🛰️"
    elif entry['event'] == 'StartJump':
        presence_state = ('⌛ Springt')
        if entry['JumpType'] == 'Hyperspace':
            presence_details = ('Springt zum System {system}').format(system=entry['StarSystem'])
        elif entry['JumpType'] == 'Supercruise':
            presence_details = ('🚀 FSA aufladen...')
    elif entry['event'] == 'SupercruiseEntry':
        presence_state = ('System: {system}🌌').format(system=system)
        presence_details = "Im Supercruise 🛰️"
    elif entry['event'] == 'SupercruiseExit':
        presence_state = ('System: {system}🌌').format(system=system)
        presence_details = "Fliegt im normalen Raum"
    elif entry['event'] == 'FSDJump':
        presence_state = ('System: {system}🌌').format(system=system)
        presence_details = "Im Supercruise 🛰️"
    elif entry['event'] == 'FSDTarget':
        presence_state = ('🎯 Ziel: {system}🌌').format(system=entry['Name'])
        presence_details = ('⌛ Warte auf FSD')
    elif entry['event'] == 'Docked':
        presence_state = ('System: {system}🌌').format(system=system)
        presence_details = ('Angedockt: {station}🚩').format(station=station)
    elif entry['event'] == 'Undocked':
        presence_state = ('System: {system}🌌').format(system=system)
        presence_details = "Fliegt im normalen Raum"
    elif entry['event'] == 'ShutDown':
        presence_state = "Lade KMDT-Schnittstelle..."
        presence_details = ''
    elif entry['event'] == 'DockingGranted':
        landingPad = entry['LandingPad']
    elif entry['event'] == 'Music':
        if entry['MusicTrack'] == 'MainMenu':
            presence_state = "Lade KMDT-Schnittstelle..."
            presence_details = ''
    elif entry['event'] == 'LaunchSRV':
        presence_state = "System: {system}🌌"
        presence_details = ('🚗 auf: {body}').format(body=planet)
    elif entry['event'] == 'DockSRV':
        presence_details = ('🛬 Gelandet: {body}').format(body=planet)

    if presence_state != this.presence_state or presence_details != this.presence_details:
        this.presence_state = presence_state
        this.presence_details = presence_details
        this.presence_cmdr = presence_cmdr
        update_presence()


def check_run(plugin_dir):
    plugin_path = join(dirname(plugin_dir), plugin_name)
    retry = True
    while retry:
        time.sleep(1 / 10)
        try:
            this.app = dsdk.Discord(CLIENT_ID, dsdk.CreateFlags.no_require_discord, plugin_path)
            retry = False
        except Exception:
            pass

    this.activity_manager = this.app.get_activity_manager()
    this.activity = dsdk.Activity()

    this.call_back_thread = threading.Thread(target=run_callbacks)
    this.call_back_thread.setDaemon(True)
    this.call_back_thread.start()
    this.presence_state = ('Lade KMDT-Schnittstelle...')
    this.presence_details = ''
    this.time_start = time.time()

    this.disablePresence = None

    update_presence()


def run_callbacks():
    try:
        while True:
            time.sleep(1 / 10)
            this.app.run_callbacks()
    except Exception:
        check_run(this.plugin_dir)
