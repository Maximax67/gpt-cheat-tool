from typing import List, Tuple

import services.record_audio.custom_speech_recognition as sr


class AudioDevices:
    @staticmethod
    def get_audio_input_devices() -> List[Tuple[int, str]]:
        """
        Get the list of audio input devices with their index and name.
        """
        p = sr.Microphone.get_pyaudio().PyAudio()
        input_devices = []
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info.get("maxInputChannels") > 0:
                input_devices.append((i, device_info["name"]))

        p.terminate()

        return input_devices

    @staticmethod
    def get_audio_output_devices() -> List[Tuple[int, str]]:
        """
        Get the list of audio output devices with their index and name.
        """
        p = sr.Microphone.get_pyaudio().PyAudio()
        output_devices = []
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info.get("maxOutputChannels") > 0:
                output_devices.append((i, device_info["name"]))

        p.terminate()

        return output_devices

    @staticmethod
    def get_default_audio_input_device() -> Tuple[int, str]:
        """
        Get the default audio input device.
        """
        p = sr.Microphone.get_pyaudio().PyAudio()
        default_input_index = p.get_default_input_device_info()["index"]
        default_input_name = p.get_device_info_by_index(default_input_index)["name"]
        p.terminate()

        return default_input_index, default_input_name

    @staticmethod
    def get_default_audio_output_device() -> Tuple[int, str]:
        """
        Get the default audio output device.
        """
        p = sr.Microphone.get_pyaudio().PyAudio()
        default_output_index = p.get_default_output_device_info()["index"]
        default_output_name = p.get_device_info_by_index(default_output_index)["name"]
        p.terminate()

        return default_output_index, default_output_name
