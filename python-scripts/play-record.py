import audio_layer
import multiprocess_functions
import os
import sys

# Default parameters
SAMPLE_RATE = 44100
EXCITATION_SIGNAL_LENGTH = 1.0
SWEEP_START_FREQ = 20
SWEEP_STOP_FREQ = int(SAMPLE_RATE / 2.0)
DEFAULT_LOGARITHMIC = 1


def askForFloat(inputText="Enter value: ", errorText="Invalid value entered! Try again ...", defaultValue=0):

    # Added this code for python 2.7
    try:
        _enteredValue = input(inputText)
    except:
        return defaultValue

    if _enteredValue == "":
        _enteredValue = defaultValue
    else:
        try:
            _enteredValue = float(_enteredValue)
        except:
            print("     -> Invalid value entered! Try again ...")
            _enteredValue = askForFloat(inputText, errorText, defaultValue)

    return _enteredValue


def plotThing(thing):
    # This function must be run on a separate process to avoid the interaction
    # with the PyAudio
    import matplotlib.pyplot as plot

    for n in range(len(thing)):
        plot.plot(thing[n])
        plot.hold(1)
    plot.grid(1)
    plot.show()


if __name__ == "__main__":

    print("\n--Audio loop test-- Joe\n")

    # Get info from all audio devices
    try:
        print(">> Getting information from available audio cards ...")
        _allCards = audio_layer.getAllSoundCardsInfo()
    except Exception as ex:
        print("ERROR: could not obtain information! Error:", ex)
        quit()

    # Check that defult devices were actually found
    _inputCard = None
    _outputCard = None
    for _newCard in _allCards:
        if _newCard.isDefaultInputInterface:
            _inputCard = _newCard
        else:
            if _newCard.isDefaultOutputInterface:
                _outputCard = _newCard
    if _inputCard == None:
        print("ERROR: no default input card could be found!")
        quit()
    if _outputCard == None:
        print("ERROR: no default output card could be found!")
        quit()
    print("   * Default input device:\n       ID: %d\tInputs: %d\tName: %s" % (_inputCard.interfaceID, _inputCard.countOfInputChannels, _inputCard.interfaceName))
    print("   * Default output device:\n       ID: %d\tOutputs: %d\tName: %s" % (_outputCard.interfaceID, _outputCard.countOfOutputChannels, _outputCard.interfaceName))

    # Ask for parameters of test
    print(">> Experiment parameters (press ENTER for default values):")

    _selectedSampleRate = askForFloat("   * Sample rate (default: %.0f Hz): " % SAMPLE_RATE, "     -> Invalid value entered! Try again ...", SAMPLE_RATE)

    _selectedExcitationLength = askForFloat("   * Excitation signal length (default: %.1f sec): " % EXCITATION_SIGNAL_LENGTH, "     -> Invalid value entered! Try again ...", EXCITATION_SIGNAL_LENGTH)
    _selectedStartFreq = askForFloat("   * Start freq (default: %.1f Hz): " % SWEEP_START_FREQ, "     -> Invalid value entered! Try again ...", SWEEP_START_FREQ)
    _selectedStopFreq = askForFloat("   * Stop freq (default: %.1f Hz): " % SWEEP_STOP_FREQ, "     -> Invalid value entered! Try again ...", SWEEP_STOP_FREQ)
    _selectedSweepMode = askForFloat("   * Sweep mode logarithmic (default: %d): " % DEFAULT_LOGARITHMIC, "     -> Invalid value entered! Try again ...", bool(DEFAULT_LOGARITHMIC))

    # Generate excitation signal(s)
    _excitationSignal = audio_layer.generateSweepSine(sampleRate=_selectedSampleRate, length=_selectedExcitationLength, startFreq=_selectedStartFreq, stopFreq=_selectedStopFreq, logarithmic=_selectedSweepMode)
    _signalsToPlay = [[0] * len(_excitationSignal) ] * _outputCard.countOfOutputChannels
    _signalsToPlay[0][:] = _excitationSignal

    # This must be run on a separate process to avoid the interaction with PyAudio
    multiprocess_functions.runInSeparateProcess(plotThing, [_signalsToPlay])

    # Create two processes, send the signal and recording parameters
    _recordedSignals = audio_layer.playAndRecord(signalsToPlay=_signalsToPlay, recordingLength=int(2.0*_selectedExcitationLength*_selectedSampleRate), recordChannelsCount=_inputCard.countOfInputChannels, inputCard=_inputCard, outputCard=_outputCard, sampleRateRecord=_selectedSampleRate, sampleRatePlayback=_selectedSampleRate, normalizePlayback=False)

    # Show recorded data
    multiprocess_functions.runInSeparateProcess(plotThing, [_recordedSignals])
