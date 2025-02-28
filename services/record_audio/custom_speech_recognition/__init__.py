#!/usr/bin/env python3

"""Library for performing speech recognition, with support for several engines and APIs, online and offline."""

import io
import os
import tempfile
import subprocess
import wave
import aifc
import math
import audioop
import collections
import json
import threading
import uuid

__author__ = "Anthony Zhang (Uberi)"
__version__ = "3.10.0"
__license__ = "BSD"

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from .audio import AudioData, get_flac_converter
from .exceptions import (
    RequestError,
    UnknownValueError,
    WaitTimeoutError,
)


class AudioSource(object):
    def __init__(self):
        raise NotImplementedError("this is an abstract class")

    def __enter__(self):
        raise NotImplementedError("this is an abstract class")

    def __exit__(self, exc_type, exc_value, traceback):
        raise NotImplementedError("this is an abstract class")


class Microphone(AudioSource):
    """
    Creates a new ``Microphone`` instance, which represents a physical microphone on the computer. Subclass of ``AudioSource``.

    This will throw an ``AttributeError`` if you don't have PyAudio 0.2.11 or later installed.

    If ``device_index`` is unspecified or ``None``, the default microphone is used as the audio source. Otherwise, ``device_index`` should be the index of the device to use for audio input.

    A device index is an integer between 0 and ``pyaudio.get_device_count() - 1`` (assume we have used ``import pyaudio`` beforehand) inclusive. It represents an audio device such as a microphone or speaker. See the `PyAudio documentation <http://people.csail.mit.edu/hubert/pyaudio/docs/>`__ for more details.

    The microphone audio is recorded in chunks of ``chunk_size`` samples, at a rate of ``sample_rate`` samples per second (Hertz). If not specified, the value of ``sample_rate`` is determined automatically from the system's microphone settings.

    Higher ``sample_rate`` values result in better audio quality, but also more bandwidth (and therefore, slower recognition). Additionally, some CPUs, such as those in older Raspberry Pi models, can't keep up if this value is too high.

    Higher ``chunk_size`` values help avoid triggering on rapidly changing ambient noise, but also makes detection less sensitive. This value, generally, should be left at its default.
    """

    def __init__(
        self,
        device_index=None,
        sample_rate=None,
        chunk_size=1024,
        speaker=False,
        channels=1,
    ):
        assert device_index is None or isinstance(
            device_index, int
        ), "Device index must be None or an integer"
        assert sample_rate is None or (
            isinstance(sample_rate, int) and sample_rate > 0
        ), "Sample rate must be None or a positive integer"
        assert (
            isinstance(chunk_size, int) and chunk_size > 0
        ), "Chunk size must be a positive integer"

        # set up PyAudio
        self.speaker = speaker
        self.pyaudio_module = self.get_pyaudio()
        audio = self.pyaudio_module.PyAudio()
        try:
            count = audio.get_device_count()  # obtain device count
            if device_index is not None:  # ensure device index is in range
                assert (
                    0 <= device_index < count
                ), "Device index out of range ({} devices available; device index should be between 0 and {} inclusive)".format(
                    count, count - 1
                )
            if (
                sample_rate is None
            ):  # automatically set the sample rate to the hardware's default sample rate if not specified
                device_info = (
                    audio.get_device_info_by_index(device_index)
                    if device_index is not None
                    else audio.get_default_input_device_info()
                )
                assert (
                    isinstance(device_info.get("defaultSampleRate"), (float, int))
                    and device_info["defaultSampleRate"] > 0
                ), "Invalid device info returned from PyAudio: {}".format(device_info)
                sample_rate = int(device_info["defaultSampleRate"])
        finally:
            audio.terminate()

        self.device_index = device_index
        self.format = self.pyaudio_module.paInt16  # 16-bit int sampling
        self.SAMPLE_WIDTH = self.pyaudio_module.get_sample_size(
            self.format
        )  # size of each sample
        self.SAMPLE_RATE = sample_rate  # sampling rate in Hertz
        self.CHUNK = chunk_size  # number of frames stored in each buffer
        self.channels = channels

        self.audio = None
        self.stream = None

    @staticmethod
    def get_pyaudio():
        """
        Imports the pyaudio module and checks its version. Throws exceptions if pyaudio can't be found or a wrong version is installed
        """
        try:
            import pyaudiowpatch as pyaudio
        except ImportError:
            raise AttributeError("Could not find PyAudio; check installation")
        from distutils.version import LooseVersion

        if LooseVersion(pyaudio.__version__) < LooseVersion("0.2.11"):
            raise AttributeError(
                "PyAudio 0.2.11 or later is required (found version {})".format(
                    pyaudio.__version__
                )
            )
        return pyaudio

    @staticmethod
    def list_microphone_names():
        """
        Returns a list of the names of all available microphones. For microphones where the name can't be retrieved, the list entry contains ``None`` instead.

        The index of each microphone's name in the returned list is the same as its device index when creating a ``Microphone`` instance - if you want to use the microphone at index 3 in the returned list, use ``Microphone(device_index=3)``.
        """
        audio = Microphone.get_pyaudio().PyAudio()
        try:
            result = []
            for i in range(audio.get_device_count()):
                device_info = audio.get_device_info_by_index(i)
                result.append(device_info.get("name"))
        finally:
            audio.terminate()
        return result

    @staticmethod
    def list_working_microphones():
        """
        Returns a dictionary mapping device indices to microphone names, for microphones that are currently hearing sounds. When using this function, ensure that your microphone is unmuted and make some noise at it to ensure it will be detected as working.

        Each key in the returned dictionary can be passed to the ``Microphone`` constructor to use that microphone. For example, if the return value is ``{3: "HDA Intel PCH: ALC3232 Analog (hw:1,0)"}``, you can do ``Microphone(device_index=3)`` to use that microphone.
        """
        pyaudio_module = Microphone.get_pyaudio()
        audio = pyaudio_module.PyAudio()
        try:
            result = {}
            for device_index in range(audio.get_device_count()):
                device_info = audio.get_device_info_by_index(device_index)
                device_name = device_info.get("name")
                assert (
                    isinstance(device_info.get("defaultSampleRate"), (float, int))
                    and device_info["defaultSampleRate"] > 0
                ), "Invalid device info returned from PyAudio: {}".format(device_info)
                try:
                    # read audio
                    pyaudio_stream = audio.open(
                        input_device_index=device_index,
                        channels=1,
                        format=pyaudio_module.paInt16,
                        rate=int(device_info["defaultSampleRate"]),
                        input=True,
                    )
                    try:
                        buffer = pyaudio_stream.read(1024)
                        if not pyaudio_stream.is_stopped():
                            pyaudio_stream.stop_stream()
                    finally:
                        pyaudio_stream.close()
                except Exception:
                    continue

                # compute RMS of debiased audio
                energy = -audioop.rms(buffer, 2)
                energy_bytes = bytes([energy & 0xFF, (energy >> 8) & 0xFF])
                debiased_energy = audioop.rms(
                    audioop.add(buffer, energy_bytes * (len(buffer) // 2), 2), 2
                )

                if debiased_energy > 30:  # probably actually audio
                    result[device_index] = device_name
        finally:
            audio.terminate()
        return result

    def __enter__(self):
        assert (
            self.stream is None
        ), "This audio source is already inside a context manager"
        self.audio = self.pyaudio_module.PyAudio()

        try:
            if self.speaker:
                self.stream = Microphone.MicrophoneStream(
                    self.audio.open(
                        input_device_index=self.device_index,
                        channels=self.channels,
                        format=self.format,
                        rate=self.SAMPLE_RATE,
                        frames_per_buffer=self.CHUNK,
                        input=True,
                    )
                )
            else:
                self.stream = Microphone.MicrophoneStream(
                    self.audio.open(
                        input_device_index=self.device_index,
                        channels=1,
                        format=self.format,
                        rate=self.SAMPLE_RATE,
                        frames_per_buffer=self.CHUNK,
                        input=True,
                    )
                )
        except Exception as e:
            self.audio.terminate()
            raise e

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self.stream.close()
        finally:
            self.stream = None
            self.audio.terminate()

    class MicrophoneStream(object):
        def __init__(self, pyaudio_stream):
            self.pyaudio_stream = pyaudio_stream

        def read(self, size):
            return self.pyaudio_stream.read(size, exception_on_overflow=False)

        def close(self):
            try:
                # sometimes, if the stream isn't stopped, closing the stream throws an exception
                if not self.pyaudio_stream.is_stopped():
                    self.pyaudio_stream.stop_stream()
            finally:
                self.pyaudio_stream.close()


class AudioFile(AudioSource):
    """
    Creates a new ``AudioFile`` instance given a WAV/AIFF/FLAC audio file ``filename_or_fileobject``. Subclass of ``AudioSource``.

    If ``filename_or_fileobject`` is a string, then it is interpreted as a path to an audio file on the filesystem. Otherwise, ``filename_or_fileobject`` should be a file-like object such as ``io.BytesIO`` or similar.

    Note that functions that read from the audio (such as ``recognizer_instance.record`` or ``recognizer_instance.listen``) will move ahead in the stream. For example, if you execute ``recognizer_instance.record(audiofile_instance, duration=10)`` twice, the first time it will return the first 10 seconds of audio, and the second time it will return the 10 seconds of audio right after that. This is always reset to the beginning when entering an ``AudioFile`` context.

    WAV files must be in PCM/LPCM format; WAVE_FORMAT_EXTENSIBLE and compressed WAV are not supported and may result in undefined behaviour.

    Both AIFF and AIFF-C (compressed AIFF) formats are supported.

    FLAC files must be in native FLAC format; OGG-FLAC is not supported and may result in undefined behaviour.
    """

    def __init__(self, filename_or_fileobject):
        assert isinstance(filename_or_fileobject, (type(""), type(""))) or hasattr(
            filename_or_fileobject, "read"
        ), "Given audio file must be a filename string or a file-like object"
        self.filename_or_fileobject = filename_or_fileobject
        self.stream = None
        self.DURATION = None

        self.audio_reader = None
        self.little_endian = False
        self.SAMPLE_RATE = None
        self.CHUNK = None
        self.FRAME_COUNT = None

    def __enter__(self):
        assert (
            self.stream is None
        ), "This audio source is already inside a context manager"
        try:
            # attempt to read the file as WAV
            self.audio_reader = wave.open(self.filename_or_fileobject, "rb")
            self.little_endian = True  # RIFF WAV is a little-endian format (most ``audioop`` operations assume that the frames are stored in little-endian form)
        except (wave.Error, EOFError):
            try:
                # attempt to read the file as AIFF
                self.audio_reader = aifc.open(self.filename_or_fileobject, "rb")
                self.little_endian = False  # AIFF is a big-endian format
            except (aifc.Error, EOFError):
                # attempt to read the file as FLAC
                if hasattr(self.filename_or_fileobject, "read"):
                    flac_data = self.filename_or_fileobject.read()
                else:
                    with open(self.filename_or_fileobject, "rb") as f:
                        flac_data = f.read()

                # run the FLAC converter with the FLAC data to get the AIFF data
                flac_converter = get_flac_converter()
                if (
                    os.name == "nt"
                ):  # on Windows, specify that the process is to be started without showing a console window
                    startup_info = subprocess.STARTUPINFO()
                    startup_info.dwFlags |= (
                        subprocess.STARTF_USESHOWWINDOW
                    )  # specify that the wShowWindow field of `startup_info` contains a value
                    startup_info.wShowWindow = (
                        subprocess.SW_HIDE
                    )  # specify that the console window should be hidden
                else:
                    startup_info = None  # default startupinfo
                process = subprocess.Popen(
                    [
                        flac_converter,
                        "--stdout",
                        "--totally-silent",  # put the resulting AIFF file in stdout, and make sure it's not mixed with any program output
                        "--decode",
                        "--force-aiff-format",  # decode the FLAC file into an AIFF file
                        "-",  # the input FLAC file contents will be given in stdin
                    ],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    startupinfo=startup_info,
                )
                aiff_data, _ = process.communicate(flac_data)
                aiff_file = io.BytesIO(aiff_data)
                try:
                    self.audio_reader = aifc.open(aiff_file, "rb")
                except (aifc.Error, EOFError):
                    raise ValueError(
                        "Audio file could not be read as PCM WAV, AIFF/AIFF-C, or Native FLAC; check if file is corrupted or in another format"
                    )
                self.little_endian = False  # AIFF is a big-endian format
        assert (
            1 <= self.audio_reader.getnchannels() <= 2
        ), "Audio must be mono or stereo"
        self.SAMPLE_WIDTH = self.audio_reader.getsampwidth()

        # 24-bit audio needs some special handling for old Python versions (workaround for https://bugs.python.org/issue12866)
        samples_24_bit_pretending_to_be_32_bit = False
        if self.SAMPLE_WIDTH == 3:  # 24-bit audio
            try:
                audioop.bias(
                    b"", self.SAMPLE_WIDTH, 0
                )  # test whether this sample width is supported (for example, ``audioop`` in Python 3.3 and below don't support sample width 3, while Python 3.4+ do)
            except (
                audioop.error
            ):  # this version of audioop doesn't support 24-bit audio (probably Python 3.3 or less)
                samples_24_bit_pretending_to_be_32_bit = True  # while the ``AudioFile`` instance will outwardly appear to be 32-bit, it will actually internally be 24-bit
                self.SAMPLE_WIDTH = 4  # the ``AudioFile`` instance should present itself as a 32-bit stream now, since we'll be converting into 32-bit on the fly when reading

        self.SAMPLE_RATE = self.audio_reader.getframerate()
        self.CHUNK = 4096
        self.FRAME_COUNT = self.audio_reader.getnframes()
        self.DURATION = self.FRAME_COUNT / float(self.SAMPLE_RATE)
        self.stream = AudioFile.AudioFileStream(
            self.audio_reader,
            self.little_endian,
            samples_24_bit_pretending_to_be_32_bit,
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not hasattr(
            self.filename_or_fileobject, "read"
        ):  # only close the file if it was opened by this class in the first place (if the file was originally given as a path)
            self.audio_reader.close()
        self.stream = None
        self.DURATION = None

    class AudioFileStream(object):
        def __init__(
            self, audio_reader, little_endian, samples_24_bit_pretending_to_be_32_bit
        ):
            self.audio_reader = (
                audio_reader  # an audio file object (e.g., a `wave.Wave_read` instance)
            )
            self.little_endian = little_endian  # whether the audio data is little-endian (when working with big-endian things, we'll have to convert it to little-endian before we process it)
            self.samples_24_bit_pretending_to_be_32_bit = samples_24_bit_pretending_to_be_32_bit  # this is true if the audio is 24-bit audio, but 24-bit audio isn't supported, so we have to pretend that this is 32-bit audio and convert it on the fly

        def read(self, size=-1):
            buffer = self.audio_reader.readframes(
                self.audio_reader.getnframes() if size == -1 else size
            )
            if not isinstance(buffer, bytes):
                buffer = b""  # workaround for https://bugs.python.org/issue24608

            sample_width = self.audio_reader.getsampwidth()
            if (
                not self.little_endian
            ):  # big endian format, convert to little endian on the fly
                if hasattr(
                    audioop, "byteswap"
                ):  # ``audioop.byteswap`` was only added in Python 3.4 (incidentally, that also means that we don't need to worry about 24-bit audio being unsupported, since Python 3.4+ always has that functionality)
                    buffer = audioop.byteswap(buffer, sample_width)
                else:  # manually reverse the bytes of each sample, which is slower but works well enough as a fallback
                    buffer = buffer[sample_width - 1 :: -1] + b"".join(
                        buffer[i + sample_width : i : -1]
                        for i in range(sample_width - 1, len(buffer), sample_width)
                    )

            # workaround for https://bugs.python.org/issue12866
            if (
                self.samples_24_bit_pretending_to_be_32_bit
            ):  # we need to convert samples from 24-bit to 32-bit before we can process them with ``audioop`` functions
                buffer = b"".join(
                    b"\x00" + buffer[i : i + sample_width]
                    for i in range(0, len(buffer), sample_width)
                )  # since we're in little endian, we prepend a zero byte to each 24-bit sample to get a 32-bit sample
                sample_width = 4  # make sure we thread the buffer as 32-bit audio now, after converting it from 24-bit audio
            if self.audio_reader.getnchannels() != 1:  # stereo audio
                buffer = audioop.tomono(
                    buffer, sample_width, 1, 1
                )  # convert stereo audio data to mono
            return buffer


class Recognizer(AudioSource):
    def __init__(self):
        """
        Creates a new ``Recognizer`` instance, which represents a collection of speech recognition functionality.
        """
        self.energy_threshold = 300  # minimum audio energy to consider for recording
        self.dynamic_energy_threshold = True
        self.dynamic_energy_adjustment_damping = 0.15
        self.dynamic_energy_ratio = 1.5
        self.pause_threshold = (
            0.8  # seconds of non-speaking audio before a phrase is considered complete
        )
        self.operation_timeout = None  # seconds after an internal operation (e.g., an API request) starts before it times out, or ``None`` for no timeout

        self.phrase_threshold = 0.3  # minimum seconds of speaking audio before we consider the speaking audio a phrase - values below this are ignored (for filtering out clicks and pops)
        self.non_speaking_duration = (
            0.5  # seconds of non-speaking audio to keep on both sides of the recording
        )

    def record(self, source, duration=None, offset=None):
        """
        Records up to ``duration`` seconds of audio from ``source`` (an ``AudioSource`` instance) starting at ``offset`` (or at the beginning if not specified) into an ``AudioData`` instance, which it returns.

        If ``duration`` is not specified, then it will record until there is no more audio input.
        """
        assert isinstance(source, AudioSource), "Source must be an audio source"
        assert (
            source.stream is not None
        ), "Audio source must be entered before recording, see documentation for ``AudioSource``; are you using ``source`` outside of a ``with`` statement?"

        frames = io.BytesIO()
        seconds_per_buffer = (source.CHUNK + 0.0) / source.SAMPLE_RATE
        elapsed_time = 0
        offset_time = 0
        offset_reached = False
        while True:  # loop for the total number of chunks needed
            if offset and not offset_reached:
                offset_time += seconds_per_buffer
                if offset_time > offset:
                    offset_reached = True

            buffer = source.stream.read(source.CHUNK)
            if len(buffer) == 0:
                break

            if offset_reached or not offset:
                elapsed_time += seconds_per_buffer
                if duration and elapsed_time > duration:
                    break

                frames.write(buffer)

        frame_data = frames.getvalue()
        frames.close()
        return AudioData(frame_data, source.SAMPLE_RATE, source.SAMPLE_WIDTH)

    def adjust_for_ambient_noise(self, source, duration=1):
        """
        Adjusts the energy threshold dynamically using audio from ``source`` (an ``AudioSource`` instance) to account for ambient noise.

        Intended to calibrate the energy threshold with the ambient energy level. Should be used on periods of audio without speech - will stop early if any speech is detected.

        The ``duration`` parameter is the maximum number of seconds that it will dynamically adjust the threshold for before returning. This value should be at least 0.5 in order to get a representative sample of the ambient noise.
        """
        assert isinstance(source, AudioSource), "Source must be an audio source"
        assert (
            source.stream is not None
        ), "Audio source must be entered before adjusting, see documentation for ``AudioSource``; are you using ``source`` outside of a ``with`` statement?"
        assert self.pause_threshold >= self.non_speaking_duration >= 0

        seconds_per_buffer = (source.CHUNK + 0.0) / source.SAMPLE_RATE
        elapsed_time = 0

        # adjust energy threshold until a phrase starts
        while True:
            elapsed_time += seconds_per_buffer
            if elapsed_time > duration:
                break
            buffer = source.stream.read(source.CHUNK)
            energy = audioop.rms(
                buffer, source.SAMPLE_WIDTH
            )  # energy of the audio signal

            # dynamically adjust the energy threshold using asymmetric weighted average
            damping = (
                self.dynamic_energy_adjustment_damping**seconds_per_buffer
            )  # account for different chunk sizes and rates
            target_energy = energy * self.dynamic_energy_ratio
            self.energy_threshold = self.energy_threshold * damping + target_energy * (
                1 - damping
            )

    def listen(
        self, source, timeout=None, phrase_time_limit=None, stopper=lambda: False
    ):
        """
        Records a single phrase from ``source`` (an ``AudioSource`` instance) into an ``AudioData`` instance, which it returns.

        This is done by waiting until the audio has an energy above ``recognizer_instance.energy_threshold`` (the user has started speaking), and then recording until it encounters ``recognizer_instance.pause_threshold`` seconds of non-speaking or there is no more audio input. The ending silence is not included.

        The ``timeout`` parameter is the maximum number of seconds that this will wait for a phrase to start before giving up and throwing an ``speech_recognition.WaitTimeoutError`` exception. If ``timeout`` is ``None``, there will be no wait timeout.

        The ``phrase_time_limit`` parameter is the maximum number of seconds that this will allow a phrase to continue before stopping and returning the part of the phrase processed before the time limit was reached. The resulting audio will be the phrase cut off at the time limit. If ``phrase_timeout`` is ``None``, there will be no phrase time limit.

        This operation will always complete within ``timeout + phrase_timeout`` seconds if both are numbers, either by returning the audio data, or by raising a ``speech_recognition.WaitTimeoutError`` exception.
        """
        assert isinstance(source, AudioSource), "Source must be an audio source"
        assert (
            source.stream is not None
        ), "Audio source must be entered before listening, see documentation for ``AudioSource``; are you using ``source`` outside of a ``with`` statement?"
        assert self.pause_threshold >= self.non_speaking_duration >= 0

        seconds_per_buffer = float(source.CHUNK) / source.SAMPLE_RATE
        pause_buffer_count = int(
            math.ceil(self.pause_threshold / seconds_per_buffer)
        )  # number of buffers of non-speaking audio during a phrase, before the phrase should be considered complete
        phrase_buffer_count = int(
            math.ceil(self.phrase_threshold / seconds_per_buffer)
        )  # minimum number of buffers of speaking audio before we consider the speaking audio a phrase
        non_speaking_buffer_count = int(
            math.ceil(self.non_speaking_duration / seconds_per_buffer)
        )  # maximum number of buffers of non-speaking audio to retain before and after a phrase

        # read audio input for phrases until there is a phrase that is long enough
        elapsed_time = 0  # number of seconds of audio read
        buffer = b""  # an empty buffer means that the stream has ended and there is no data left to read
        while True:
            frames = collections.deque()

            # store audio input until the phrase starts
            while True:
                if stopper():
                    raise InterruptedError("Interrupted via stopper")

                # handle waiting too long for phrase by raising an exception
                elapsed_time += seconds_per_buffer
                if timeout and elapsed_time > timeout:
                    raise WaitTimeoutError(
                        "listening timed out while waiting for phrase to start"
                    )

                buffer = source.stream.read(source.CHUNK)
                if len(buffer) == 0:
                    break  # reached end of the stream
                frames.append(buffer)
                if (
                    len(frames) > non_speaking_buffer_count
                ):  # ensure we only keep the needed amount of non-speaking buffers
                    frames.popleft()

                # detect whether speaking has started on audio input
                energy = audioop.rms(
                    buffer, source.SAMPLE_WIDTH
                )  # energy of the audio signal
                if energy > self.energy_threshold:
                    break

                # dynamically adjust the energy threshold using asymmetric weighted average
                if self.dynamic_energy_threshold:
                    damping = (
                        self.dynamic_energy_adjustment_damping**seconds_per_buffer
                    )  # account for different chunk sizes and rates
                    target_energy = energy * self.dynamic_energy_ratio
                    self.energy_threshold = (
                        self.energy_threshold * damping + target_energy * (1 - damping)
                    )

            # read audio input until the phrase ends
            pause_count, phrase_count = 0, 0
            phrase_start_time = elapsed_time
            while not stopper():
                # handle phrase being too long by cutting off the audio
                elapsed_time += seconds_per_buffer
                if (
                    phrase_time_limit
                    and elapsed_time - phrase_start_time > phrase_time_limit
                ):
                    break

                buffer = source.stream.read(source.CHUNK)
                if len(buffer) == 0:
                    break  # reached end of the stream
                frames.append(buffer)
                phrase_count += 1

                # check if speaking has stopped for longer than the pause threshold on the audio input
                energy = audioop.rms(
                    buffer, source.SAMPLE_WIDTH
                )  # unit energy of the audio signal within the buffer
                if energy > self.energy_threshold:
                    pause_count = 0
                else:
                    pause_count += 1
                if pause_count > pause_buffer_count:  # end of the phrase
                    break

            # check how long the detected phrase is, and retry listening if the phrase is too short
            phrase_count -= (
                pause_count  # exclude the buffers for the pause before the phrase
            )
            if phrase_count >= phrase_buffer_count or len(buffer) == 0:
                break  # phrase is long enough or we've reached the end of the stream, so stop listening

        # obtain frame data
        for i in range(pause_count - non_speaking_buffer_count):
            frames.pop()  # remove extra non-speaking frames at the end
        frame_data = b"".join(frames)

        return AudioData(frame_data, source.SAMPLE_RATE, source.SAMPLE_WIDTH)

    def listen_in_background(self, source, callback, phrase_time_limit=None):
        """
        Spawns a thread to repeatedly record phrases from ``source`` (an ``AudioSource`` instance) into an ``AudioData`` instance and call ``callback`` with that ``AudioData`` instance as soon as each phrase are detected.

        Returns a function object that, when called, requests that the background listener thread stop. The background thread is a daemon and will not stop the program from exiting if there are no other non-daemon threads. The function accepts one parameter, ``wait_for_stop``: if truthy, the function will wait for the background listener to stop before returning, otherwise it will return immediately and the background listener thread might still be running for a second or two afterwards. Additionally, if you are using a truthy value for ``wait_for_stop``, you must call the function from the same thread you originally called ``listen_in_background`` from.

        Phrase recognition uses the exact same mechanism as ``recognizer_instance.listen(source)``. The ``phrase_time_limit`` parameter works in the same way as the ``phrase_time_limit`` parameter for ``recognizer_instance.listen(source)``, as well.

        The ``callback`` parameter is a function that should accept two parameters - the ``recognizer_instance``, and an ``AudioData`` instance representing the captured audio. Note that ``callback`` function will be called from a non-main thread.
        """
        assert isinstance(source, AudioSource), "Source must be an audio source"
        running = [True, False]

        def is_listen_stopped():
            return not running[0]

        def threaded_listen():
            with source as s:
                while running[0]:
                    try:  # listen for 1 second, then check again if the stop function has been called
                        audio = self.listen(s, 1, phrase_time_limit, is_listen_stopped)
                    except WaitTimeoutError:  # listening timed out, just try again
                        pass
                    except InterruptedError:  # listening interrupted
                        pass
                    else:
                        if running[0] or running[1]:
                            callback(self, audio)

        def stopper(wait_for_stop=True, callback_last_audio_chunk=False):
            running[0] = False
            running[1] = callback_last_audio_chunk
            if wait_for_stop:
                listener_thread.join()  # block until the background thread is done, which can take around 1 second

        listener_thread = threading.Thread(target=threaded_listen)
        listener_thread.daemon = True
        listener_thread.start()

        return stopper


class PortableNamedTemporaryFile(object):
    """Limited replacement for ``tempfile.NamedTemporaryFile``, except unlike ``tempfile.NamedTemporaryFile``, the file can be opened again while it's currently open, even on Windows."""

    def __init__(self, mode="w+b"):
        self.mode = mode

    def __enter__(self):
        # create the temporary file and open it
        file_descriptor, file_path = tempfile.mkstemp()
        self._file = os.fdopen(file_descriptor, self.mode)

        # the name property is a public field
        self.name = file_path
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._file.close()
        os.remove(self.name)

    def write(self, *args, **kwargs):
        return self._file.write(*args, **kwargs)

    def writelines(self, *args, **kwargs):
        return self._file.writelines(*args, **kwargs)

    def flush(self, *args, **kwargs):
        return self._file.flush(*args, **kwargs)
