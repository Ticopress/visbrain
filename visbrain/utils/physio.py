"""Group of functions for physiological processing."""
import numpy as np
from re import findall

__all__ = ['find_nonEEG', 'rereferencing', 'bipolarization', 'commonaverage']


def find_nonEEG(channels, pattern=['eog', 'emg', 'ecg', 'abd']):
    """Find non-EEG channels.

    Args:
        channels: list
            List of channel names.

    Kargs:
        pattern: list, optional, (def: ['eog', 'emg', 'ecg', 'abd'])
            List of patterns for non-EEG channels.

    Returns:
        iseeg: np.ndarray
            NumPy vector of boolean values.
    """
    # Set channels in lower case :
    channels = np.char.lower(np.asarray(channels))
    # Pre-allocation :
    iseeg = np.zeros((len(channels),), dtype=bool)
    # Search patterns :
    for k in pattern:
        iseeg += np.invert(np.char.find(channels, k).astype(bool))
    return iseeg


def rereferencing(data, chans, reference, to_ignore=None):
    """Re-reference data.

    Args:
        data: np.ndarray
            The array of data of shape (nchan, npts).

        chans: list
            List of channel names of length nchan.

        reference: int
            The index of the channel to consider as a reference.

    Kargs:
        to_ignore: list, optional, (def: None)
            List of channels to ignore in the re-referencing.

    Returns:
        datar: np.ndarray
            The re-referenced data.

        channelsr: list
            List of re-referenced channel names.

        consider: list
            List of boolean values of channels that have to be considered
            during the ploting processus.
    """
    # Get shapes :
    nchan, npts = data.shape
    # Get data to use as the reference :
    ref = data[[reference], :]
    name = chans[reference]
    # Build ignore vector :
    consider = np.ones((nchan,), dtype=bool)
    consider[reference] = False
    # Find if some channels have to be ignored :
    if to_ignore is None:
        sl = slice(nchan)
    else:
        sl = np.arange(nchan)[~to_ignore]
        consider[to_ignore] = False
    # Re-reference data :
    data[sl, :] -= ref
    # Build channel names :
    chan = [k+'-'+name if consider[num] else k for num, k in enumerate(chans)]

    return data, chan, consider


def bipolarization(data, chans, to_ignore=None, sep='.'):
    """Bipolarize data.

    Args:
        data: np.ndarray
            The array of data of shape (nchan, npts).

        chans: list
            List of channel names of length nchan.

    Kargs:
        to_ignore: list, optional, (def: None)
            List of channels to ignore in the re-referencing.

        sep: string, optional, (def: '.')
            Separator to simplify electrode names by removing undesired name
            after the sep. For example, if channel = ['h1.025', 'h2.578']
            and sep='.', the final name will be 'h2-h1'.

    Returns:
        datar: np.ndarray
            The re-referenced data.

        channelsr: list
            List of re-referenced channel names.

        consider: list
            List of boolean values of channels that have to be considered
            during the ploting processus.
    """
    # Variables :
    nchan, npts = data.shape
    consider = np.ones((nchan,), dtype=bool)

    # Preprocess channel names by separating channel names / number:
    chnames, chnums = [], []
    for num, k in enumerate(chans):
        # Remove spaces and separation :
        chans[num] = k.strip().replace(' ', '').split(sep)[0]
        # Get only the name / number :
        if findall(r'\d+', k):
            number = findall(r'\d+', k)[0]
            chnums.append(number)
            chnames.append(k.split(number)[0])
        else:
            chnums.append('')
            chnames.append(k)

    # Find if some channels have to be ignored :
    if to_ignore is None:
        sl = range(nchan)
    else:
        sl = np.arange(nchan)[~to_ignore]
        consider[to_ignore] = False

    # Bipolarize :
    for num in reversed(range(nchan)):
        # If there's a number :
        if chnums[num] and (num in sl):
            # Get the name of the channel to find :
            chanTofind = chnames[num] + str(int(chnums[num]) - 1)
            # Search if exist in channel list :
            if chanTofind in chans:
                # Get the index :
                ind = chans.index(chanTofind)
                # Substract to data :
                data[num, :] -= data[ind, :]
                # Update channel name :
                chans[num] = chans[num] + '-' + chanTofind
            else:
                consider[num] = False
        else:
            consider[num] = False

    return data, chans, consider


def commonaverage(data, chans, to_ignore=None):
    """Re-referencement using common average.

    Args:
        data: np.ndarray
            The array of data of shape (nchan, npts).

        chans: list
            List of channel names of length nchan.

    Kargs:
        to_ignore: list, optional, (def: None)
            List of channels to ignore in the re-referencing.

    Returns:
        datar: np.ndarray
            The re-referenced data.

        channelsr: list
            List of re-referenced channel names.

        consider: list
            List of boolean values of channels that have to be considered
            during the ploting processus.
    """
    # Variables :
    nchan, npts = data.shape
    consider = np.ones((nchan,), dtype=bool)
    # Find if some channels have to be ignored :
    if to_ignore is not None:
        consider[to_ignore] = False
    # Get the mean across  EEG channels :
    eegmean = data[consider].mean(0, keepdims=True)
    # Remove the mean on EEG channels :
    data[consider, :] -= eegmean
    # Update channel name :
    for k in range(len(chans)):
        chans[k] = chans[k] + '-m' if consider[k] else chans[k]
    return data, chans, consider
