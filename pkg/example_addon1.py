"""Example addon for Candle Controller / Webthings Gateway."""


import os
import sys
# This helps the addon find python libraries it comes with, which are stored in the "lib" folder. The "package.sh" file will download Python libraries that are mentioned in requirements.txt and place them there.
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')) 

import json
import time
#import datetime
#import requests  # noqa
#import threading
#import subprocess

# This loads the parts of the addon.
from gateway_addon import Database, Adapter, Device, Property
# Database - needed to read from the settings database. If your addon doesn't have any settings, then you don't need this.

# Adapter. Needed if you want to provide things' to the controller.
# Device. Needed if you want to provide things' to the controller.
# Property. Needed if you want to provide things' to the controller.

# APIHandler. Needed if you want to provide an API for a UI extension.
# APIResponse. Needed if you want to provide an API for a UI extension.

try:
    from .internet_radio_api_handler import *
    #print("APIHandler imported")
except Exception as ex:
    print("Error, unable to load APIHandler (which is used for UI extention): " + str(ex))


# Not sure what this is used for, but leave it in.
_TIMEOUT = 3

# Not sure what this is used for either, but leave it in.
_CONFIG_PATHS = [
    os.path.join(os.path.expanduser('~'), '.webthings', 'config'),
]

# Not sure what this is used for either, but leave it in.
if 'WEBTHINGS_HOME' in os.environ:
    _CONFIG_PATHS.insert(0, os.path.join(os.environ['WEBTHINGS_HOME'], 'config'))



class AddonAdapter(Adapter):
    """Adapter for addon """

    def __init__(self, verbose=False):
        """
        Initialize the object.

        verbose -- whether or not to enable verbose logging
        """

        #print("initialising adapter from class")
        self.pairing = False
        self.ready = False # set this to True once the init process is complete.
        self.addon_name = 'example-addon1'
        self.DEBUG = False
        self.name = self.__class__.__name__
        Adapter.__init__(self, self.addon_name, self.addon_name, verbose=verbose)



        # Setup persistence
        #for path in _CONFIG_PATHS:
        #    if os.path.isdir(path):
        #        self.persistence_file_path = os.path.join(
        #            path,
        #            'internet-radio-persistence.json'
        #        )
        #        print("self.persistence_file_path is now: " + str(self.persistence_file_path))

        self.addon_path = os.path.join(self.user_profile['addonsDir'], self.addon_name)
        #self.persistence_file_path = os.path.join(os.path.expanduser('~'), '.mozilla-iot', 'data', self.addon_name,'persistence.json')
        self.persistence_file_path = os.path.join(self.user_profile['dataDir'], self.addon_name, 'persistence.json')
        self.bluetooth_persistence_file_path = os.path.join(self.user_profile['dataDir'], 'bluetoothpairing', 'persistence.json')

        self.running = True
        
            
        # Get audio output options
        if sys.platform == 'darwin':
            print("running on a Mac")
			
			
        # Get persistent data
        try:
            with open(self.persistence_file_path) as f:
                self.persistent_data = json.load(f)
                if self.DEBUG:
                    print('self.persistent_data loaded from file: ' + str(self.persistent_data))
                try:
                    if 'audio_output' not in self.persistent_data:
                        if self.DEBUG:
                            print("audio output was not in persistent data, adding it now.")
                        if len(self.audio_controls) > 0:
                            self.persistent_data['audio_output'] = str(self.audio_controls[0]['human_device_name'])
                        else:
                            self.persistent_data['audio_output'] = ""
                except:
                    print("Error fixing audio output in persistent data")
                
                if self.DEBUG:
                    print("Persistence data was loaded succesfully.")
                    
                    
        except:
            if self.DEBUG:
                print("Could not load persistent data (if you just installed the add-on then this is normal)")
            try:
                first_audio_output = ""
                if len(self.audio_controls) > 0:
                    if 'human_device_name' in self.audio_controls[0]:
                        first_audio_output = self.audio_controls[0]['human_device_name']
                self.persistent_data = {'power':False,'station':'FIP','volume':100, 'audio_output':  first_audio_output, 'stations':[{'name':'FIP','stream_url':'http://direct.fipradio.fr/live/fip-midfi.mp3'}] }
            
            except Exception as ex:
                print("Error in handling missing persistent data file: " + str(ex))
                self.persistent_data = {'power':False,'station':'FIP','volume':100, 'audio_output': "", 'stations':[{'name':'FIP','stream_url':'http://direct.fipradio.fr/live/fip-midfi.mp3'}] }


        # LOAD CONFIG

        # self.persistent_data['current_stream_url'] = None
        self.radio_stations_names_list = []

        try:
            self.add_from_config()

        except Exception as ex:
            print("Error loading config: " + str(ex))

        if 'playing' not in self.persistent_data:
            self.persistent_data['playing'] = False

        if 'bluetooth_device_mac' not in self.persistent_data:
            self.persistent_data['bluetooth_device_mac'] = None
            
        if 'current_stream_url' not in self.persistent_data:
            self.persistent_data['current_stream_url'] = None


        # Start the API handler
        try:
            if self.DEBUG:
                print("starting api handler")
            self.api_handler = InternetRadioAPIHandler(self, verbose=True)
            #self.manager_proxy.add_api_handler(self.extension)
            if self.DEBUG:
                print("Extension API handler initiated")
        except Exception as e:
            if self.DEBUG:
                print("Failed to start API handler (this only works on gateway version 0.10 or higher). Error: " + str(e))


        # Give Bluetooth Pairing addon some time to reconnect to the speaker
        if self.persistent_data['bluetooth_device_mac'] != None:
            if not self.DEBUG:
                time.sleep(15)
        
        if self.bluetooth_device_check():
            if self.DEBUG:
                print("Bluetooth output device seems to be available (in theory)")
        
        if self.DEBUG:
            print("complete self.audio_output_options : " + str(self.audio_output_options))
        
        # Create the radio device
        try:
            internet_radio_device = InternetRadioDevice(self, self.radio_stations_names_list, self.audio_output_options)
            self.handle_device_added(internet_radio_device)
            if self.DEBUG:
                print("internet_radio_device created")
            self.devices['internet-radio'].connected = True
            self.devices['internet-radio'].connected_notify(True)

        except Exception as ex:
            print("Could not create internet_radio_device: " + str(ex))


        self.player = None

        # Restore volume
        #try:
        #    self.set_audio_volume(self.persistent_data['volume'])
        #except Exception as ex:
        #    print("Could not restore radio station: " + str(ex))


        # Restore station
        try:
            if self.persistent_data['station'] != None:
                if self.DEBUG:
                    print("Setting radio station to the one found in persistence data: " + str(self.persistent_data['station']))
                self.set_radio_station(self.persistent_data['station'])
            else:
                if self.DEBUG:
                    print("No radio station was set in persistence data")
        except Exception as ex:
            print("couldn't set the radio station name to what it was before: " + str(ex))


        # Restore power
        try:
            self.set_radio_state(bool(self.persistent_data['power']))
        except Exception as ex:
            print("Could not restore radio station: " + str(ex))

        #print("internet radio adapter init complete")

        self.ready = True

        if self.get_song_details:
            while self.running: # and self.player != None
                time.sleep(1)
            
                if self.persistent_data['playing'] == True:
                    try:
                        #if self.DEBUG:
                        #    print(str(self.adapter.poll_counter))
                        if self.poll_counter == 0:
                            self.now_playing = self.get_artist()
                    except Exception as ex:
                        print("error updating now_playing: " + str(ex))
            
                    #if self.adapter.playing:
                    self.poll_counter += 1
                    if self.poll_counter > 20:
                        self.poll_counter = 0
                    



    def add_from_config(self):
        """ This retrieves the addon settings from the controller """
        try:
            database = Database(self.addon_name)
            if not database.open():
                print("Error. Could not open settings database")
                return

            config = database.load_config()
            database.close()

        except:
            print("Error. Failed to open settings database. Closing proxy.")
            self.close_proxy() # this will purposefully "crash" the addon. It will then we restarted in two seconds, in the hope that the database is no longer locked by then
            return
            
        try:
            if not config:
                self.close_proxy()
                return

            # Let's start by setting the user's preference about debugging, so we can use that preference to output extra debugging information
            if 'Debugging' in config:
                self.DEBUG = bool(config['Debugging'])
                if self.DEBUG:
                    print("Debugging enabled")

            if self.DEBUG:
                print(str(config)) # Print the entire config data
                
            if 'A boolean setting' in config:
                self.persistent_data['a_boolean_setting'] = bool(config['A boolean setting']) # sometime you may want the addon settings to override the persistent value
                if self.DEBUG:
                    print("A boolean setting preference was in config: " + str(self.a_boolean_setting))

            if 'A number setting' in config:
                #print("-Debugging was in config")
                self.get_song_details = not bool(config['Do not get song details'])
                if self.DEBUG:
                    print("A number setting preference was in config: " + str(not self.a_number_setting))
            
            

        except Exception as ex:
            print("Error in add_from_config: " + str(ex))







    def set_state(self,state):
        print("in set_state with state: " + str(state))
        
        set_state
        


#
# MAIN SETTING OF THE RADIO STATES
#

    def set_radio_station(self, station_name):
        if self.DEBUG:
            print("Setting radio station to: " + str(station_name))
            
        try:
            if station_name.startswith('http'): # override to play a stream without a name
                url = station_name
                if self.DEBUG:
                    print("a stream was provided instead of a name")
                for station in self.persistent_data['stations']:
                    if station['stream_url'] == station_name: # doing an ugly swap,
                        if self.DEBUG:
                            print("station name reversed match")
                        station_name = station['name']
                        url = station['stream_url']
                        if str(station_name) != str(self.persistent_data['station']):
                            if self.DEBUG:
                                print("Saving station to persistence data")
                            self.persistent_data['station'] = str(station_name)
                            self.save_persistent_data()
                        
                        if self.DEBUG:
                            print("setting station name on thing")
                        
                        self.set_station_on_thing(str(station['name']))
                        
            else:
                url = ""
                for station in self.persistent_data['stations']:
                    if station['name'] == station_name:
                        #print("station name match")
                        url = station['stream_url']
                        if str(station_name) != str(self.persistent_data['station']):
                            if self.DEBUG:
                                print("Saving station to persistence data")
                            self.persistent_data['station'] = str(station_name)
                            self.save_persistent_data()
                        
                        if self.DEBUG:
                            print("setting station name on thing")
                        
                        self.set_station_on_thing(str(station['name']))
                        
        except Exception as ex:
            print("Error figuring out station: " + str(ex))

        try:
            if url.startswith('http') or url.startswith('rtsp'):
                if self.DEBUG:
                    print("URL starts with http or rtsp")
                if url.endswith('.m3u') or url.endswith('.pls'):
                    if self.DEBUG:
                        print("URL ended with .m3u or .pls (is a playlist): " + str(url))
                    url = self.scrape_url_from_playlist(url)
                    if self.DEBUG:
                        print("Extracted URL = " + str(url))

                self.persistent_data['current_stream_url'] =  url
                self.save_persistent_data()
                
                # get_artist preparation
                self.now_playing = ""
                self.set_song_on_thing(None)
                self.set_artist_on_thing(None)
                self.current_stream_has_now_playing_info = True # reset this, so get_artist will try to get now_playing info
                self.poll_counter = 18 # this will cause get_artist to be called again soon
                
                # Finally, if the station is changed, also turn on the radio (except for the first time)
                if self.in_first_run:
                    self.in_first_run = False
                    if self.DEBUG:
                        print("Set first_run to false")
                else:
                    if self.DEBUG:
                        print("Station changed. Next: turning on the radio\n")
                    self.set_radio_state(True)
                
            else:
                self.set_status_on_thing("Not a valid URL")
        except Exception as ex:
            print("Error handling playlist file: " + str(ex))




    def set_radio_state(self,power,also_call_volume=True):
        if self.DEBUG:
            print("in set_radio_state. Setting radio power to: " + str(power))
        
        if self.running == False:
            if self.DEBUG:
                print("tried to restart during unload?")
            return
            
        try:
            if self.DEBUG:
                print("self.persistent_data['power'] in set_radio_state: " + str(self.persistent_data['power']))
            if bool(power) != bool(self.persistent_data['power']):
                if self.DEBUG:
                    print("radio state changed from value in persistence.")
                self.persistent_data['power'] = bool(power)
                if self.DEBUG:
                    print("self.persistent_data['power'] = power? " + str(self.persistent_data['power']) + " =?= " + str(power))
                self.save_persistent_data()
            else:
                if self.DEBUG:
                    print("radio state same as value in persistence.")

                #if power:
                #    if self.player != None:
                #        self.player.terminate()
                #        self.player.kill()

            #
            #  turn on
            #
            if power:
                if self.player != None:
                    if self.DEBUG:
                        print("set_radio_state: warning, the player already existed. Stopping it first.")
                    try:
                        if self.respeaker_detected == False:
                            self.player.stdin.write(b'q')
                        self.player.terminate()
                        self.player = None
                    except Exception as ex:
                        print("error terminating omxplayer with Q command. Maybe it stopped by itself?: " + str(ex))
                        print("player.poll(): " + str( self.player.poll() ))
                        #self.player = None
                
                else:
                    if self.DEBUG:
                        print("self.player was still None")
                       
                       
                if self.respeaker_detected:
                    if self.DEBUG:
                        print("pkill omxplayer")
                    os.system('pkill omxplayer')
                    
                else:
                    if self.DEBUG:
                        print("pkill ffplay")
                    os.system('pkill ffplay')
                self.player = None
                
                # Checking audio output option
                
                bt_connected = False
                
                try:
                    if self.DEBUG:
                        print("self.persistent_data['audio_output']: " + str(self.persistent_data['audio_output']))
                    
                    if self.persistent_data['audio_output'] == 'Bluetooth speaker':
                        if self.DEBUG:
                            print("Doing bluetooth speaker connection check")
                        
                        
                        bluetooth_connection_check_output = run_command('amixer -D bluealsa scontents')
                        if len(bluetooth_connection_check_output) > 10:
                            bt_connected = True
                    
                        # Find out if another speaker was paired/connected through the Bluetooth Pairing addon
                        else:
                            if self.DEBUG:
                                print("Bluetooth device mac was None. Doing bluetooth_device_check")
                            if self.bluetooth_device_check():
                                if self.persistent_data['bluetooth_device_mac'] != None:
                                    bt_connected = True
                            else:
                                self.send_pairing_prompt("Please (re)connect a Bluetooth speaker using the Bluetooth pairing addon")
                                if self.DEBUG:
                                    print("bluetooth_device_check: no connected speakers?")
                    
                        if bt_connected:
                            if self.DEBUG:
                                print("Bluetooth speaker seems to be connected")
                            #environment["SDL_AUDIODRIVER"] = "alsa"
                            #environment["AUDIODEV"] = "bluealsa:" + str(self.persistent_data['bluetooth_device_mac'])
                            
                            
                            
                    elif sys.platform != 'darwin':
                            for option in self.audio_controls:
                                if self.DEBUG:
                                    print( str(option['human_device_name']) + " =?= " + str(self.persistent_data['audio_output']) )
                                if option['human_device_name'] == str(self.persistent_data['audio_output']):
                                    environment["ALSA_CARD"] = str(option['simple_card_name'])
                                    
                                    
                    # TODO: provide the option to fall back to normal speakers if the bluetooth speaker is disconnected?
                                    
                except Exception as ex:
                    print("Error in set_radio_state while doing audio output (bluetooth speaker) checking: " + str(ex))
                
                
                #kill_process('ffplay')
                
				
                logarithmic_volume = -6000 # start at 0
				
                # set the volume by starting omx-player with that volume
                # Somehow this volume doesn't match the volume from the set_audio_volume method, so it's a fall-back option.
                if also_call_volume == False and self.respeaker_detected == False:
                    
                    if self.persistent_data['volume'] > 0:
                    	#print("volume is now 1")
                        pre_volume = int(self.persistent_data['volume']) / 100
    					#print("pre_volume: " + str(pre_volume))
    					# OMXPlayer volume is between -6000 and 0 (logarithmic)
                        logarithmic_volume = 2000 * math.log(pre_volume)
    					#print("logarithmic_volume: " + str(logarithmic_volume))
                
               
                
                
                if self.respeaker_detected:
                    
                    environment = os.environ.copy()
                    
                    if bt_connected:
                    
                        environment["SDL_AUDIODRIVER"] = "alsa"
                        #environment["AUDIODEV"] = "bluealsa:" + str(self.persistent_data['bluetooth_device_mac'])
                        environment["AUDIODEV"] = "bluealsa:00:00:00:00:00:00"
                    
                        #my_command = "SDL_AUDIODRIVER=alsa UDIODEV=bluealsa:DEV=" + str(self.persistent_data['bluetooth_device_mac']) + " ffplay -nodisp -vn -infbuf -autoexit -volume " + str(self.persistent_data['volume']) + " " + str(self.persistent_data['current_stream_url'])
                        my_command = "ffplay -nodisp -vn -infbuf -autoexit -volume " + str(self.persistent_data['volume']) + " " + str(self.persistent_data['current_stream_url'])
                    
                    
                        if self.DEBUG:
                            print("Internet radio addon will call this subprocess command: " + str(my_command))
                            print("starting ffplay...")
                        self.player = subprocess.Popen(my_command, 
                                        env=environment,
                                        shell=True,
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
                
                
                    else:
                        #my_command = "ffplay -nodisp -vn -infbuf -autoexit" + str(self.persistent_data['current_stream_url']) + " -volume " + str(self.persistent_data['volume'])
                        my_command = ("ffplay", "-nodisp", "-vn", "-infbuf","-autoexit","-volume",str(self.persistent_data['volume']), str(self.persistent_data['current_stream_url']) )

                        if self.DEBUG:
                            print("Internet radio addon will call this subprocess command: " + str(my_command))
                            print("starting ffplay...")
                        self.player = subprocess.Popen(my_command, 
                                        env=environment,
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
                    
                else:
                    
                    #if self.persistent_data['audio_output'] == 'Built-in headphone jack':
                    #    omx_output = "local"
                    #else:
                    #    omx_output = "hdmi"
                    
                    omx_output = "alsa:sysdefault"
                    
                    if self.output_to_both:
                        omx_output = "both"
                    
                    if bt_connected:
                        omx_output = "alsa:bluealsa"
				
                    omx_command = "omxplayer -o " + str(omx_output) + " --vol " + str(logarithmic_volume) + " -z --audio_queue 10 --audio_fifo 10 --threshold 5 " + str(self.persistent_data['current_stream_url'])
                    if self.DEBUG:
                        print("\nOMX Player command: " + str(omx_command))
                    #omxplayer -o alsa:bluealsa
                
                    command_array = omx_command.split(' ')
                
                    #environment = os.environ.copy()
                    #environment["DISPLAY"] = ":0"
                
                    self.player = subprocess.Popen(command_array, 
                                        #env=environment,
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        bufsize=0,
                                        close_fds=True)
                
                if self.DEBUG:
                    print("self.player created")
                
                self.persistent_data['playing'] = True
                self.set_status_on_thing("Playing")
                
                if also_call_volume and self.respeaker_detected == False:
                    if self.DEBUG:
                        print("set_radio_state: alse setting volume")
                    time.sleep(1)
                    self.set_audio_volume(self.persistent_data['volume'])
                
     
            #
            #  turn off
            #
            else:
                if self.DEBUG:
                    print("turning off radio")
                self.persistent_data['playing'] = False
                self.set_status_on_thing("Stopped")
                self.get_artist() # sets now_playing data to none on the device and UI
                if self.player != None:
                    if self.DEBUG:
                        print("player object existed")
                    if self.respeaker_detected == False:
                        self.player.stdin.write(b'q')
                        self.player.stdin.flush()
                    self.player.terminate()
                    self.player.kill()
                    #os.system('pkill ffplay')
                    if self.respeaker_detected:
                        os.system('pkill ffplay')
                    else:
                        os.system('pkill omxplayer')
                    self.player = None
                
                else:
                    if self.DEBUG:
                        print("Could not stop the player because it wasn't running.")
                
            # update the UI
            self.set_state_on_thing(bool(power))

        except Exception as ex:
            print("Error setting radio state: " + str(ex))



    def set_audio_volume(self,volume):
        if self.DEBUG:
            print("Setting audio output volume to " + str(volume))
            print("self.player: " + str(self.player))
        
        set_volume_via_radio_state = False    
        if self.respeaker_detected:
            set_volume_via_radio_state = True # changes volume by completely restarting the player and giving it the new initial volume value
            
        if int(volume) != self.persistent_data['volume']:
            self.persistent_data['volume'] = int(volume)
            self.save_persistent_data()
            if self.DEBUG:
                print("Volume changed")
        else:
            if self.DEBUG:
                print("Volume did not change")
                
        try:
            if self.player != None and self.respeaker_detected == False:
                
                if self.DEBUG:
                    print("Trying dbus volume")

                omxplayerdbus_user = run_command('cat /tmp/omxplayerdbus.${USER:-root}')
                if self.DEBUG:
                    print("DBUS_SESSION_BUS_ADDRESS: " + str(omxplayerdbus_user))
                environment = os.environ.copy()
                if omxplayerdbus_user != None:
                    if self.DEBUG:
                        print("trying dbus-send")
                    environment["DBUS_SESSION_BUS_ADDRESS"] = str(omxplayerdbus_user).strip()
                    environment["DISPLAY"] = ":0"
                
                    if self.DEBUG:
                        print("environment: " + str(environment))
                    
                    dbus_volume = volume / 100
                    if self.DEBUG:
                        print("dbus_volume: " + str(dbus_volume))
                    
                    dbus_command = 'dbus-send --print-reply --session --reply-timeout=500 --dest=org.mpris.MediaPlayer2.omxplayer /org/mpris/MediaPlayer2 org.freedesktop.DBus.Properties.Set string:"org.mpris.MediaPlayer2.Player" string:"Volume" double:' + str(dbus_volume)
                    #export DBUS_SESSION_BUS_ADDRESS=$(cat /tmp/omxplayerdbus.${USER:-root})
                    dbus_process = subprocess.Popen(dbus_command, 
                                    env=environment,
                                    shell=True,				# Streaming to bluetooth seems to only work if shell is true. The position of the volume string also seemed to matter
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    close_fds=True)
                
                    stdout,stderr = dbus_process.communicate()
                    if len(stderr) > 4:
                        set_volume_via_radio_state = True
                    else:
                        set_volume_via_radio_state = False
                    
                    if self.DEBUG:
                        print("dbus stdout: " + str(stdout))
                        print("dbus stderr: " + str(stderr))
                
                    #dbus_result = dbus_process.stdout.read()
                    #dbus_process.stdout.close()
                
                    
                    
        except Exception as ex:
            print("Error trying to set volume via dbus: " + str(ex))
            set_volume_via_radio_state= True
            
        self.set_volume_on_thing(volume)
        #if self.player == None:
        
        if set_volume_via_radio_state:
            if self.DEBUG:
                print("WARNING: setting radio volume by restarting audio player instead")
            self.set_radio_state(self.persistent_data['power'],False)

        return



    



#
# SUPPORT METHODS
#

    def set_status_on_thing(self, status_string):
        if self.DEBUG:
            print("new status on thing: " + str(status_string))
        try:
            if self.devices['internet-radio'] != None:
                #self.devices['internet-radio'].properties['status'].set_cached_value_and_notify( str(status_string) )
                self.devices['internet-radio'].properties['status'].update( str(status_string) )
        except:
            print("Error setting status on internet radio device")


    def set_song_on_thing(self, song_string):
        #if self.DEBUG:
        #    print("new song on thing: " + str(song_string))
        try:
            if self.devices['internet-radio'] != None:
                #self.devices['internet-radio'].properties['status'].set_cached_value_and_notify( str(status_string) )
                self.devices['internet-radio'].properties['song'].update( str(song_string) )
        except:
            print("Error setting song on internet radio device")


    def set_artist_on_thing(self, artist_string):
        #if self.DEBUG:
        #    print("new artist on thing: " + str(artist_string))
        try:
            if self.devices['internet-radio'] != None:
                #self.devices['internet-radio'].properties['status'].set_cached_value_and_notify( str(status_string) )
                self.devices['internet-radio'].properties['artist'].update( str(artist_string) )
        except:
            print("Error setting artist on internet radio device")



    def set_state_on_thing(self, power):
        if self.DEBUG:
            print("new state on thing: " + str(power))
        try:
            if self.devices['internet-radio'] != None:
                self.devices['internet-radio'].properties['power'].update( bool(power) )
        except Exception as ex:
            print("Error setting power state on internet radio device:" + str(ex))



    def set_station_on_thing(self, station):
        if self.DEBUG:
            print("new station on thing: " + str(station))
        try:
            if self.devices['internet-radio'] != None:
                self.devices['internet-radio'].properties['station'].update( str(station) )
        except Exception as ex:
            print("Error setting station on internet radio device:" + str(ex))



    def set_volume_on_thing(self, volume):
        if self.DEBUG:
            print("new volume on thing: " + str(volume))
        try:
            if self.devices['internet-radio'] != None:
                self.devices['internet-radio'].properties['volume'].update( int(volume) )
            else:
                print("Error: could not set volume on internet radio thing, the thing did not exist yet")
        except Exception as ex:
            print("Error setting volume of internet radio device:" + str(ex))



    # Only called on non-darwin devices
    def set_audio_output(self, selection):
        if self.DEBUG:
            print("Setting audio output selection to: " + str(selection))
            
            
        if str(selection) == 'Bluetooth speaker':
            self.persistent_data['audio_output'] = str(selection)
            self.save_persistent_data()
            if self.devices['internet-radio'] != None:
                self.devices['internet-radio'].properties['audio output'].update( str(selection) )
            if self.persistent_data['power']:
                if self.DEBUG:
                    print("restarting radio with new audio output")
                self.set_radio_state(True)
            
        else:
            # Get the latest audio controls
            self.audio_controls = get_audio_controls()
            if self.DEBUG:
                print(self.audio_controls)
        
            try:        
                for option in self.audio_controls:
                    if str(option['human_device_name']) == str(selection):
                        if self.DEBUG:
                            print("CHANGING INTERNET RADIO AUDIO OUTPUT")
                        # Set selection in persistence data
                        self.persistent_data['audio_output'] = str(selection)
                        if self.DEBUG:
                            print("persistent_data is now: " + str(self.persistent_data))
                        self.save_persistent_data()
                    
                        if self.DEBUG:
                            print("new selection on thing: " + str(selection))
                        try:
                            if self.DEBUG:
                                print("self.devices = " + str(self.devices))
                            if self.devices['internet-radio'] != None:
                                self.devices['internet-radio'].properties['audio output'].update( str(selection) )
                        except Exception as ex:
                            print("Error setting new audio output selection:" + str(ex))
        
                        if self.persistent_data['power']:
                            if self.DEBUG:
                                print("restarting radio with new audio output")
                            self.set_radio_state(True)
                        break
            
            except Exception as ex:
                print("Error in set_audio_output: " + str(ex))




    def scrape_url_from_playlist(self, url):
        response = requests.get(url)
        data = response.text
        url = None
        #if self.DEBUG:
        #    print("playlist data: " + str(data))
        for line in data.splitlines():
            if self.DEBUG:
                print(str(line))

            if 'http' in line:
                url_part = line.split("http",1)[1]
                if url_part != None:
                    url = "http" + str(url_part)
                    if self.DEBUG:
                        print("Extracted URL: " + str(url))
                    break
                    
        if url == None:
            set_status_on_thing("Error with station")
            
        return url



    def unload(self):
        if self.DEBUG:
            print("Shutting down Internet Radio.")
        self.set_status_on_thing("Bye")
        #self.devices['internet-radio'].connected_notify(False)
        self.save_persistent_data()
        self.set_radio_state(False)
        self.running = False
        #if self.player != None:
        #    self.player.stdin.write(b'q')
        #os.system('pkill omxplayer')


    def remove_thing(self, device_id):
        try:
            self.set_radio_state(False)
            obj = self.get_device(device_id)
            self.handle_device_removed(obj)                     # Remove from device dictionary
            if self.DEBUG:
                print("User removed Internet Radio device")
        except:
            print("Could not remove things from devices")



    def save_persistent_data(self):
        if self.DEBUG:
            print("Saving to persistence data store")

        try:
            if not os.path.isfile(self.persistence_file_path):
                open(self.persistence_file_path, 'a').close()
                if self.DEBUG:
                    print("Created an empty persistence file")
            else:
                if self.DEBUG:
                    print("Persistence file existed. Will try to save to it.")

            with open(self.persistence_file_path) as f:
                if self.DEBUG:
                    print("saving: " + str(self.persistent_data))
                try:
                    json.dump( self.persistent_data, open( self.persistence_file_path, 'w+' ) )
                except Exception as ex:
                    print("Error saving to persistence file: " + str(ex))
                return True
            #self.previous_persistent_data = self.persistent_data.copy()

        except Exception as ex:
            if self.DEBUG:
                print("Error: could not store data in persistent store: " + str(ex) )
            return False







#
# DEVICE
#

class InternetRadioDevice(Device):
    """Internet Radio device type."""

    def __init__(self, adapter, radio_station_names_list, audio_output_list):
        """
        Initialize the object.
        adapter -- the Adapter managing this device
        """

        Device.__init__(self, adapter, 'internet-radio')

        self._id = 'internet-radio'
        self.id = 'internet-radio'
        self.adapter = adapter
        self.DEBUG = adapter.DEBUG

        self.name = 'Radio'
        self.title = 'Radio'
        self.description = 'Listen to internet radio stations'
        self._type = ['MultiLevelSwitch']
        #self.connected = False

        self.radio_station_names_list = radio_station_names_list

        try:
            
            # this will also call handle_device_added
            self.update_stations_property(False)
            
            self.properties["power"] = InternetRadioProperty(
                            self,
                            "power",
                            {
                                '@type': 'OnOffProperty',
                                'title': "State",
                                'readOnly': False,
                                'type': 'boolean'
                            },
                            self.adapter.persistent_data['power'])
                            
            self.properties["volume"] = InternetRadioProperty(
                            self,
                            "volume",
                            {
                                '@type': 'LevelProperty',
                                'title': "Volume",
                                'type': 'integer',
                                'readOnly': False,
                                'minimum': 0,
                                'maximum': 100,
                                'unit': 'percent'
                            },
                            self.adapter.persistent_data['volume'])
                            
            self.properties["status"] = InternetRadioProperty(
                            self,
                            "status",
                            {
                                'title': "Status",
                                'type': 'string',
                                'readOnly': True
                            },
                            "Hello")

            self.properties["artist"] = InternetRadioProperty(
                            self,
                            "artist",
                            {
                                'title': "Artist",
                                'type': 'string',
                                'readOnly': True
                            },
                            None)

            self.properties["song"] = InternetRadioProperty(
                            self,
                            "song",
                            {
                                'title': "Song",
                                'type': 'string',
                                'readOnly': True
                            },
                            None)



            if sys.platform != 'darwin': #darwin = Mac OS
                if self.DEBUG:
                    print("adding audio output property with list: " + str(audio_output_list))
                self.properties["audio output"] = InternetRadioProperty(
                                self,
                                "audio output",
                                {
                                    'title': "Audio output",
                                    'type': 'string',
                                    'readOnly': False,
                                    'enum': audio_output_list,
                                },
                                self.adapter.persistent_data['audio_output'])


        except Exception as ex:
            if self.DEBUG:
                print("error adding properties: " + str(ex))

        if self.DEBUG:
            print("Internet Radio thing has been created.")


    # Creates these options "on the fly", as radio stations get added and removed.
    def update_stations_property(self, call_handle_device_added=True):
        #print("in update_stations_property")
        # Create list of radio station names for the radio thing.
        radio_stations_names = []
        for station in self.adapter.persistent_data['stations']:
            if self.DEBUG:
                print("Adding station: " + str(station))
                #print("adding station: " + str(station['name']))
            radio_stations_names.append(str(station['name']))
        
        self.adapter.radio_station_names_list = radio_stations_names
        #print("remaking property? List: " + str(radio_stations_names))
        self.properties["station"] = InternetRadioProperty(
                        self,
                        "station",
                        {
                            'title': "Station",
                            'type': 'string',
                            'enum': radio_stations_names,
                        },
                        self.adapter.persistent_data['station'])

        self.adapter.handle_device_added(self);
        self.notify_property_changed(self.properties["station"])



#
# PROPERTY
#

class InternetRadioProperty(Property):

    def __init__(self, device, name, description, value):
        # This creates the initial property, and saves information aobut. Most importantly, its value.
        # calling "set_cached_value" communicates the value to the controller, and must be called whenever you want to propertty value to be updated in the interface
        
        # properties have:
        # - name - a unique id
        # - a human-readable title
        # value. The current value of this property
        
        Property.__init__(self, device, name, description)
        
        self.device = device # a way to easily access the parent device, of which this property is a child.
        
        # you could go up a few levels to get values from the adapter:
        # print("debugging? " + str( self.device.adapter.DEBUG ))
        
        
        self.name = name
        self.title = name
        self.description = description # dictionary
        self.value = value
        
        # Tell the controller that this property has a (new) value
        self.set_cached_value(value)
        self.device.notify_property_changed(self)
        


    def set_value(self, value):
        # This gets called by the controller whenever the user changes the value inside the interface. For example if they press a button, or use a slider.
        print("property: set_value called for " + str(self.title))
        print("property: set value to: " + str(value))
        
        # First, let's set the new value. The controller is waiting 60 seconds for a response from the addon that the new value is indeed set. If "notify_property_changed" isn't used before then, it wil revert the value in the interface back to what it was.
        self.update(value)
        
        # Depending on which property this is, you could have it do something. That method could be anywhere, but in general it's clean to keep the methods at a higher level (the adapter)
        
        if self.id == 'state':
            self.device.adapter.set_state(bool(value))
        
        if self.id == 'slider':
            self.device.adapter.set_slider(int(value))
        
        except Exception as ex:
            print("set_value error: " + str(ex))



    def update(self, value):
        # This is a quick way to set the value of this property. It checks that the value is indeed new, and then notifies the controller.
        
        print("property -> update. value: " + str(value))
         
        if value != self.value:
            self.value = value
            self.set_cached_value(value)
            self.device.notify_property_changed(self)



















#
#  Helper functions
#

def run_command(cmd, timeout_seconds=20):
    try:
        p = subprocess.run(cmd, timeout=timeout_seconds, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)

        if p.returncode == 0:
            return p.stdout
        else:
            if p.stderr:
                return "Error: " + str(p.stderr)

    except Exception as e:
        print("Error running command: "  + str(e))
        