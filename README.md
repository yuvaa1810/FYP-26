Files to be dumped in raspberry pi. Do not distrub anything for now. This solely contains stuff that deals with the model. 

'requirements.txt' file has the list of libraries that needs to installed in Pi before running the main code. When your Raspberry Pi arrives, you will simply open the terminal in that folder and run: pip install -r requirements.txt

'scaler.pkl' and 'wastewater_autoencoder.pkl' are pickle files. i.e they are binary files. It is not human readable. 

'Receiver_controller.py' is the main code that is capable of reading sensor data from esp via 1.mqtt or 2.serial (usb). This loads the pre-trained autoencoder model - 'wasterwater_autoencoder.pkl' and the data translator - 'scaler.pkl' that analyzes the realtionship between our ph, orp, tempand turbidity stuff.
Find below the work done by 'Receiver_controller.py' guys:
- Closed-Loop Feedback Control: Upon detecting an anomaly, the script immediately publishes a divert: true command via MQTT. This triggers the ESP32 to activate a physical relay/valve, preventing contaminated water from entering the environment.
- Fail-Safe Redundancy: In the event that the Machine Learning model fails to load, the script automatically switches to a Fallback Rule system based on hardcoded safety thresholds for pH and Conductivity.
- Data Logging & Secure Ledger Support: Every incoming reading is timestamped and appended to wastewater_log.csv. This serves as an immutable record of effluent quality, which can be piped into Grafana for real-time visualization.


<img width="922" height="414" alt="Screenshot 2026-01-05 225804" src="https://github.com/user-attachments/assets/edd76526-bbc7-4055-af65-3c5343c16096" />

<img width="900" height="401" alt="Screenshot 2026-01-05 215623" src="https://github.com/user-attachments/assets/98fb026b-b10c-46de-aa44-e1f1bd4c4fa7" />

<img width="943" height="457" alt="Screenshot 2026-01-05 233812" src="https://github.com/user-attachments/assets/ff7a57d3-4774-4146-b943-3dbe4ae83d0f" />


