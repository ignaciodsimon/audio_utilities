"""
    Functions to play and record signals using audio interfaces. It includes test code,
    so it can be executed directly.

    Note:
        The warning that appears when using the PortAudio library (used by pyaudio), is
        "by-design", as they try to maintain compatibility with with OSX 10.4, so as of
        now it is "just a message", but it could change in future versions. For more
        information see: https://app.assembla.com/spaces/portaudio/tickets/218

    Joe.
"""

import pyaudio
import numpy
import multiprocess_functions
import scipy.signal as cps
import math

class SoundCard:
    """
        Sound card definition class. Used to provide information about audio interfaces.
        Joe.
    """
    # Class constructor
    def __init__(self):
        self.data = []

    # Public 'fields'
    interfaceID = -1
    interfaceName = ""
    isDefaultInputInterface = False
    isDefaultOutputInterface = False
    countOfInputChannels = -1
    countOfOutputChannels = -1
    samplingRates = -1
    bitDepths = -1
    inputLatency = -1
    outputLatency = -1


def playAndRecord(signalsToPlay, recordingLength, recordChannelsCount=1, inputCard=None, outputCard=None, sampleRateRecord=44100, sampleRatePlayback=44100, normalizePlayback=False):

    # Pass the ID (integer) if a device was specified
    if not inputCard is None:
        inputCard = inputCard.interfaceID
    if not outputCard is None:
        outputCard = outputCard.interfaceID

    # Create vectors with the passed arguments for each function
    _recorderArguments = [recordingLength, recordChannelsCount, sampleRateRecord, inputCard, None]
    _playerArguments = [signalsToPlay, sampleRatePlayback, normalizePlayback, outputCard]

    # Run player and recorder on two processes "simultaneously"
    [_returnRecorder, _returnPlayer] = multiprocess_functions.runInParallel(recordSignals,
                                                                            _recorderArguments,
                                                                            playSignals,
                                                                            _playerArguments)

    return _returnRecorder


def generateSweepSine(sampleRate=44100, length=1.0, startFreq=1.0, stopFreq=10000.0, logarithmic=True):

    # Generate sweep using scipy function "chirp"
    _timeStamps = [float(n) / float(sampleRate) for n in range(int(length * sampleRate))]

    # Using this iterative method for compatibility with Python 2.7, since it can not do the operation: "<list> / <float>"
    if logarithmic:
            _sweepSine = [cps.chirp(t=_t, f0=startFreq, t1=_timeStamps[-1], f1=stopFreq, method='logarithmic', phi=-90) for _t in _timeStamps]
    else:
        _sweepSine = [cps.chirp(t=_t, f0=startFreq, t1=_timeStamps[-1], f1=stopFreq, method='linear', phi=-90) for _t in _timeStamps]

    # Generate window
    _window = numpy.power(numpy.hanning(len(_timeStamps)), 0.0025)

    # Use window to soften up borders of excitation signal (make it circular)
    _sweepSine = numpy.multiply(_sweepSine, _window)

    return _sweepSine


def recordSignals(recordingLength, numOfChannels=1, samplFreq=44100, recordingDevice=None, outputDataSharedObject=None):
    """
        Captures signals from the selected/default sound card.
        Joe.
        
        :param recordingLength: Duration of the recording, in samples
        :param numOfChannels: Number of channels to record (default=1)
        :param samplFreq: Sampling frequency (default=44100)
        :return: Recorded data
    """

    # Adjusts recording length to an integer number of frames
    _bufferSize = 1024
    _realRecordingLength = int(numpy.ceil(1.0 * recordingLength / _bufferSize))*_bufferSize
    recordingLength = round(recordingLength)

    # Create the audio player
    _audioPlayer = pyaudio.PyAudio()

    # Uses device index in case it is chosen, default device otherwise
    try:
        _recordingStream = _audioPlayer.open(format=pyaudio.paInt32,
                                               channels=numOfChannels,
                                               rate=samplFreq,
                                               input=True,
                                               frames_per_buffer=_bufferSize,
                                               output_device_index=recordingDevice)
    except Exception as ex:
        print("[ERROR]: could not open recording device. Message: %s" % ex)
        return

    # Records the necessary amount of frames
    _recordedFrames = _recordingStream.read(_realRecordingLength)

    # Convert received frames to individual channels
    _convertedData = numpy.zeros([numOfChannels, int(len(_recordedFrames)/numOfChannels/4)])
    _outputSampleCounter = 0
    for n in range(0, len(_recordedFrames), numOfChannels * 4):
        for m in range(numOfChannels):
            # The lowest byte is discarded, since it's only noise
            _convertedData[m][_outputSampleCounter] = 0**0*   int(_recordedFrames[n + (m * 4) + 0]) + \
                                                      2**0*   int(_recordedFrames[n + (m * 4) + 1]) + \
                                                      2**8*   int(_recordedFrames[n + (m * 4) + 2]) + \
                                                      2**16*  int(_recordedFrames[n + (m * 4) + 3])
            # Correct for the 2-complement sign bit
            if _recordedFrames[n + (m * 4) + 3] > 128:
                _convertedData[m][_outputSampleCounter] -= 2**24
    
        _outputSampleCounter += 1
        
        # Stop converting if the required length has been reached
        if _outputSampleCounter > recordingLength:
            break

    # Trim data to desired length (eliminating last samples)
    _returnedData = numpy.zeros([numOfChannels, recordingLength])
    for n in range(numOfChannels):
        _returnedData[n] = _convertedData[n][0 : recordingLength]

    _audioPlayer.terminate()

    # Provide recording data as function output if the shared object is not received
    if outputDataSharedObject is None:
        return _returnedData
    else:
        outputDataSharedObject.append(_returnedData)


def playSignals(inputSignals, samplingFreq=44100, normalize=False, recordingDevice=None):
    """
        Plays back signals to the selected/default sound card.
        Joe.

        :param inputSignals: Set of vectors with output signals, one vector per channel
        :param normalize: Should normalize all signals before playing them (default=False)
        :param samplingFreq: Sampling frequency (default=44100)
        :param deviceIndex: Device ID (default=-1)
        :return: Recording data
    """

    # Get input signal(s) dimensions
    _channelCount = len(inputSignals)
    _signalsLength = len(inputSignals[0])

    # Calculates normalization value
    if normalize:
        _normalizationValue = numpy.amax(inputSignals)
        inputSignals = numpy.multiply(inputSignals, 1 / _normalizationValue)

    # Create the audio player
    audioPlayer = pyaudio.PyAudio()

    # Configures audio player with input parameters
    # Uses device given in case it is chosen, default device otherwise
    try:
        _stream = audioPlayer.open(output_device_index=recordingDevice,
                                    format=pyaudio.paFloat32,
                                    channels=_channelCount,
                                    rate=samplingFreq,
                                    output=True)
    except Exception as ex:
        print("[ERROR] Could not open audioplayer. Message:", ex)
        return

    # Interleave audio from all channels
    _interleavedData = [0] * _signalsLength * _channelCount
    _sampleCounter = 0
    for n in range(0, len(_interleavedData), _channelCount):
        for m in range(_channelCount):
            _interleavedData[n+m] = inputSignals[m][_sampleCounter]
        _sampleCounter += 1

    # Converts samples to individual bytes
    _bytes = []
    _bytes.append(_interleavedData)
    _bytes = numpy.concatenate(_bytes) * 1.0

    # Sends stream to audio player
    _stream.write(_bytes.astype(numpy.float32).tostring())

    # Stop, close and free
    _stream.stop_stream()
    _stream.close()
    audioPlayer.terminate()


def _countSoundCards():
    """
        Returns the amount of available audio devices.
        Joe.

        :return: Amount of audio devices.
    """

    _audioPlayer = pyaudio.PyAudio()
    return _audioPlayer.get_device_count()


def getAllSoundCardsInfo():
    # This must be done on a separate process, since the exceptions that may occur will
    # render the audio library useless
    return multiprocess_functions.runInSeparateProcess(_getAllSoundCardsInfo, [])


def _getAllSoundCardsInfo():
    """
        Returns the information on all available audio devices. Information is returned as
        instances of the class "SoundCard".
        Joe.

        :return: All available devices as a vector of SoundCard[]
    """

    _soundCards = []

    audioPlayer = pyaudio.PyAudio()

    for n in range(_countSoundCards()):

        # Gets an available audio device
        _currentDevice = audioPlayer.get_device_info_by_index(n)
        _currentSoundCard = SoundCard()

        # Bit depth is expressed in number of bytes (8 bits per byte)
        _currentSoundCard.bitDepths = _currentDevice.get("structVersion", -1)
        if _currentSoundCard.bitDepths != 0:
            _currentSoundCard.bitDepths *= 8

        # Extracts information of current device
        _currentSoundCard.countOfInputChannels = _currentDevice.get("maxInputChannels", -1)
        _currentSoundCard.countOfOutputChannels = _currentDevice.get("maxOutputChannels", -1)
        _currentSoundCard.inputLatency = [_currentDevice.get("defaultLowInputLatency", -1),
                                          _currentDevice.get("defaultHighInputLatency", -1)]
        _currentSoundCard.interfaceID = _currentDevice.get("index", -1)
        _currentSoundCard.interfaceName = _currentDevice.get("name", "No name provided.")
        _currentSoundCard.outputLatency = [_currentDevice.get("defaultLowOutputLatency", -1),
                                           _currentDevice.get("defaultHighOutputLatency", -1)]

        try:
            # Checks if it is default input / output device
            if (audioPlayer.get_default_input_device_info()).get("index", -1) == _currentSoundCard.interfaceID:
                _currentSoundCard.isDefaultInputInterface = True
        except Exception as ex:
            print("Warning: could not detect if device #%d is set as default input!" % n)

        try:
            if (audioPlayer.get_default_output_device_info()).get("index", -1) == _currentSoundCard.interfaceID:
                _currentSoundCard.isDefaultOutputInterface = True
        except Exception as ex:
            print("Warning: could not detect if device %d is set as default output!" % n)

        # Saves default accepted sampling rate
        _currentSoundCard.samplingRates = [_currentDevice.get("defaultSampleRate", -1)]

        # Tests other sampling rates and add them if they are valid
        for _sampleRateUnderTest in [22050.0, 48000.0, 96000.0, 192000.0]:
            try:
                if audioPlayer.is_format_supported(rate=_sampleRateUnderTest,
                                                input_channels=_currentSoundCard.countOfInputChannels,
                                                output_channels=_currentSoundCard.countOfOutputChannels,
                                                input_format=_currentDevice.get("structVersion", 2),
                                                output_format=_currentDevice.get("structVersion", 2),
                                                input_device=_currentSoundCard.interfaceID,
                                                output_device=_currentSoundCard.interfaceID):

                    _currentSoundCard.samplingRates.append(_sampleRateUnderTest)
            except ValueError:
                pass

        _soundCards.append(_currentSoundCard)

    audioPlayer.terminate()
    return _soundCards


if __name__ == "__main__":

    SAMPLE_RATE = 44100     # In Hz
    SIGNALS_LENGTH = 1.0    # In seconds

    print("--------------------------\n Audio-tests script - Joe\n--------------------------\n")
    print(">> Trying to get information from all audio devices ...")

    # Code to test the function
    try:
        allCards = getAllSoundCardsInfo()
    except Exception as ex:
        print("ERROR: could not obtain information! Error:", ex)
        quit()

    print("\n>> Summary of all information obtained:")
    print("  --------")
    n = 0;
    for _card in allCards:
        print("  Device #%d info:" % n)
        print("    Interface ID:             ", _card.interfaceID)
        print("    Interface name:           ", _card.interfaceName)
        print("    Is default input device:  ", _card.isDefaultInputInterface)
        print("    Is default output device: ", _card.isDefaultOutputInterface)
        print("    Input channels:           ", _card.countOfInputChannels)
        print("    Output channels:          ", _card.countOfOutputChannels)
        print("    Sampling rates:           ", _card.samplingRates)
        print("    Bit dephts:               ", _card.bitDepths)
        print("    Input latency (min, max): ", _card.inputLatency)
        print("    Output latency (min, max):", _card.outputLatency)
        print("  --------")
        n += 1

    print("\n>> Testing all devices outputs ... ")

    for _card in allCards:
        if _card.countOfOutputChannels > 0:
            _signals = [[0] * int(SIGNALS_LENGTH * SAMPLE_RATE) ] * _card.countOfOutputChannels
            for _channelNumber in range(_card.countOfOutputChannels):
                _signals[_channelNumber] = [1.0 * numpy.sin(1.0 * numpy.pi * 500 * (_channelNumber + 1) * n/SAMPLE_RATE) for n in range(int(SIGNALS_LENGTH * SAMPLE_RATE))]

            print("  Playing signal through device-%d ..." % _card.interfaceID)
            playSignals(inputSignals=_signals, samplingFreq=SAMPLE_RATE, normalize=True)
        if _card.countOfInputChannels > 0:
            # Perform a recording and display the data ...
            print("  Recording signals through device-%d" % _card.interfaceID)
            _recordedData = recordSignals(recordingLength=SIGNALS_LENGTH * SAMPLE_RATE, numOfChannels=_card.countOfInputChannels, samplFreq=SAMPLE_RATE, recordingDevice=_card.interfaceID)
#            for i in range(_card.countOfInputChannels):
#                plot.plot(_recordedData[i])
#                plot.hold(1)
#            plot.show()

        if _card.countOfInputChannels <= 0 and _card.countOfOutputChannels <= 0:
            print("  <device-%d> has no inputs/outputs. Ignoring ..." % _card.interfaceID)

    print("\n>> Test finished.")
