# VST_HOST
A project to host, install, select and control music plugins easily (for midi controller and guitar electric), on a raspberry pi, with an ios app or vocal commands

List of available plugins for the moment:
- (MIDI&Audio)Carla
- (MIDI)Organteq (demo version only)
- (MIDI)Pianoteq (demo version only)
- (MIDI)ZynAddSubFx
- (MIDI)Analog Lab 4 (via wine and box64 and with a desktop OS version only / work well with no CPU-intensive VST)
- (Audio)Guitarix
- (Audio)Rakarrack-Plus

If you don't find the plugin you looking for, you can add its class file in the "Plugins" folder by referring to the other plugin classes and your plugin's API (like MIDI, OSC, JSON-RPC... if it has one).


---------------------------
    System Requirements    
---------------------------

Hardware devices:
- Raspberry PI 5, PI 4B or PI 400 (with at least 2Go of RAM / 4Go recommended)
- Raspeberry pi 3b+ (can be sufficient but limited with CPU-intensive VST or try overclocking) 

OS:
- VST_HOST has been tested on Raspberry pi OS 64-bit Trixie and Bookworm
- note that some plugins works only on 64-bit OS
- VST_HOST work with or without os desktop (without recommended)

You also need a sound card like your faithful Scarlett and of course your favorite midi ou audio instrument


--------------------
    Installation    
--------------------

=> The programm will run automatically when you turn up your Raspberry PI by creating vst_host systemd service
git clone https://github.com/TheophileDAL/VST_HOST.git
cd VST_HOST
chmod +x setup.sh
sudo ./setup.sh
sudo reboot

=> To disable the service at startup: 
sudo systemctl disable vst_host.service 2>/dev/null

=> To stop the service:
systemctl stop vst_host.service 2>/dev/null

=> To restart the service:
sudo systemctl start vst_host.service

=> You can also simply run the programm with:
sudo python3 vst_host.py
sudo python3 vst_host.py --vc (to enable vocal commands if you have a microphone for)

! You need to be in root mode if you count to install plugins by using VST_HOST with the app !


